from dz_lib.univariate.data import Sample
from dz_lib.utils import fonts, encode
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


class Distribution:
    def __init__(self, name, x_values, y_values):
        self.name = name
        self.x_values = x_values
        self.y_values = y_values

    def subset(self, x_min: float, x_max: float):
        mask = (self.x_values > x_min) & (self.x_values < x_max)
        new_y_vals = np.where(mask, self.y_values, 0)
        return Distribution(self.name, self.x_values, new_y_vals)


# ----------------------------------------------------------------------
# Peak detection (guaranteed, KDE-safe)
# ----------------------------------------------------------------------
def find_peaks(x: np.ndarray, y: np.ndarray, n_peaks: int):
    """
    Find up to n_peaks peaks in a smooth distribution.
    Always includes the global maximum.
    """
    if n_peaks <= 0:
        return []

    peaks = []

    max_idx = np.argmax(y)
    peaks.append((x[max_idx], y[max_idx]))

    if n_peaks == 1:
        return peaks

    dy = np.diff(y)
    signs = np.sign(dy)

    candidates = np.where(
        (signs[:-1] >= 0) & (signs[1:] <= 0)
    )[0] + 1

    candidates = [i for i in candidates if i != max_idx]
    candidates = sorted(candidates, key=lambda i: y[i], reverse=True)

    for i in candidates:
        peaks.append((x[i], y[i]))
        if len(peaks) >= n_peaks:
            break

    return peaks


def find_modes(x: np.ndarray, y: np.ndarray, n_modes: int):
    """
    Robust mode finder for smooth KDE/PDP curves.
    Always includes the global maximum.
    """
    modes = [(x[np.argmax(y)], np.max(y))]

    if n_modes == 1:
        return modes

    dy = np.diff(y)
    signs = np.sign(dy)

    candidates = np.where(
        (signs[:-1] >= 0) & (signs[1:] <= 0)
    )[0] + 1

    candidates = [i for i in candidates if i != np.argmax(y)]
    candidates = sorted(candidates, key=lambda i: y[i], reverse=True)

    for i in candidates:
        modes.append((x[i], y[i]))
        if len(modes) >= n_modes:
            break

    return modes


# ----------------------------------------------------------------------
# Distribution generators
# ----------------------------------------------------------------------
def kde_function(
    sample: Sample,
    bandwidth: float = 10,
    x_min: float = 0,
    x_max: float = 4500,
):
    n_steps = 10 * int(x_max - x_min + 1)
    x_values = np.linspace(x_min, x_max, n_steps)

    ages = np.array([grain.age for grain in sample.grains])

    ages_2d = ages[:, np.newaxis]
    x_2d = x_values[np.newaxis, :]

    diff_squared = (x_2d - ages_2d) ** 2
    variance_2 = 2 * bandwidth ** 2
    normalization = 1.0 / (np.sqrt(2 * np.pi) * bandwidth)

    kernels = normalization * np.exp(-diff_squared / variance_2)
    y_values = np.sum(kernels, axis=0)

    y_values /= np.sum(y_values)
    return Distribution(sample.name, x_values, y_values)


def pdp_function(sample: Sample, x_min: float = 0, x_max: float = 4500):
    n_steps = 10 * int(x_max - x_min + 1)
    x_values = np.linspace(x_min, x_max, n_steps)

    ages = np.array([grain.age for grain in sample.grains])
    bandwidths = np.array([grain.uncertainty for grain in sample.grains])

    ages_2d = ages[:, np.newaxis]
    bandwidths_2d = bandwidths[:, np.newaxis]
    x_2d = x_values[np.newaxis, :]

    diff_squared = (x_2d - ages_2d) ** 2
    variance_2 = 2 * bandwidths_2d ** 2
    normalization = 1.0 / (np.sqrt(2 * np.pi) * bandwidths_2d)

    kernels = normalization * np.exp(-diff_squared / variance_2)
    y_values = np.sum(kernels, axis=0)

    y_values /= np.sum(y_values)
    return Distribution(sample.name, x_values, y_values)


def cdf_function(distribution: Distribution):
    cdf = np.cumsum(distribution.y_values)
    cdf /= cdf[-1]
    return Distribution(distribution.name, distribution.x_values, cdf)


# ----------------------------------------------------------------------
# Smart label positioning
# ----------------------------------------------------------------------
def _position_mode_labels(modes, x_values, y_values, font_size, x_range):
    """
    Intelligently position mode labels to avoid overlaps with curves and other labels.
    Returns list of (mode_x, mode_y, label_x, label_y) tuples.

    Args:
        modes: List of (x, y) tuples representing mode positions
        x_values: X-axis values of the distribution curve
        y_values: Y-axis values of the distribution curve
        font_size: Font size for labels
        x_range: (x_min, x_max) tuple for the plot range

    Returns:
        List of (mode_x, mode_y, label_x_offset, label_y_offset) for each mode
    """
    if not modes:
        return []

    # Sort modes by x position (left to right)
    sorted_modes = sorted(modes, key=lambda m: m[0])

    y_max = np.max(y_values)
    y_min = np.min(y_values)
    y_range = y_max - y_min

    # Estimate label dimensions
    x_min, x_max = x_range
    plot_width = x_max - x_min
    char_width = plot_width / 80  # Approximate label width in data units
    label_width = 4 * char_width
    min_spacing = label_width * 1.5

    positions = []
    occupied_regions = []  # Track (x_center, y_center, level) of placed labels

    for i, (px, py) in enumerate(sorted_modes):
        # Try positions to the right and slightly below the peak
        # This is a classic readable position for peak labels
        candidate_offsets = [
            (15, -8),   # Right and slightly down (preferred)
            (20, -8),   # Further right, slightly down
            (10, -8),   # Close right, slightly down
            (15, -12),  # Right and more down
            (15, -4),   # Right and just below
            (25, -8),   # Far right, slightly down
            (30, -10),  # Further right and down
            (10, -12),  # Close right, more down
        ]

        best_offset = None
        best_score = -1

        for x_offset, y_offset in candidate_offsets:
            # Estimate where label would be in data coordinates
            # Conservative conversion: points to data space
            # Approximate: 100 points ≈ 10% of y_range
            y_offset_data = (y_offset / 100.0) * (y_range * 0.1)
            label_y = py + y_offset_data

            # STRICT bounds check - must be well within plot
            # Leave margin for text height (5% of range)
            margin = y_range * 0.05
            if label_y < (y_min + margin) or label_y > (y_max - margin):
                continue

            # Check for overlap with other labels
            # Account for horizontal offset when checking overlap
            # Convert x_offset from points to approximate data units
            x_offset_data = (x_offset / 100.0) * (plot_width * 0.02)
            label_x = px + x_offset_data

            overlaps_label = False
            for (ox, oy, olevel) in occupied_regions:
                x_dist = abs(label_x - ox)
                y_dist = abs(label_y - oy)
                # Consider overlap if within spacing threshold
                if x_dist < min_spacing and y_dist < y_range * 0.08:
                    overlaps_label = True
                    break

            if overlaps_label:
                continue

            # Check for overlap with curve (sample points around label position)
            overlaps_curve = False
            check_radius = label_width / 2

            # Sample x positions around where label will be
            for offset_x in [-check_radius, 0, check_radius]:
                check_x = px + offset_x
                if check_x < x_min or check_x > x_max:
                    continue

                # Find nearest point in distribution
                idx = np.argmin(np.abs(x_values - check_x))
                curve_y = y_values[idx]

                # Check if label would overlap curve (with margin)
                # Label occupies roughly ±4% of y_range vertically
                label_bottom = label_y - y_range * 0.04
                label_top = label_y + y_range * 0.04

                if label_bottom <= curve_y <= label_top:
                    overlaps_curve = True
                    break

            if overlaps_curve:
                continue

            # Calculate score: prefer positions to the right and slightly below
            # Prefer x_offset around 15 and y_offset around -8
            x_penalty = abs(x_offset - 15)
            y_penalty = abs(y_offset + 8)
            score = 100 - x_penalty - y_penalty

            if score > best_score:
                best_score = score
                best_offset = (x_offset, y_offset)

        # Use best position, or fallback to right and below with stacking
        if best_offset:
            x_offset, y_offset = best_offset
        else:
            # Fallback: place to right and below, stacking vertically if needed
            x_offset, y_offset = 15, -8 - (i * 8)

        # Record this position as occupied (using actual label coordinates)
        x_offset_data = (x_offset / 100.0) * (plot_width * 0.02)
        y_offset_data = (y_offset / 100.0) * (y_range * 0.1)
        label_x_final = px + x_offset_data
        label_y_final = py + y_offset_data
        occupied_regions.append((label_x_final, label_y_final, i))

        positions.append((px, py, x_offset, y_offset))

    return positions


# ----------------------------------------------------------------------
# Plotting
# ----------------------------------------------------------------------
def distribution_graph(
    distributions: list,
    x_min: float = 0,
    x_max: float = 4500,
    stacked: bool = False,
    legend: bool = True,
    title: str = None,
    font_path: str = None,
    font_size: float = 12,
    fig_width: float = 9,
    fig_height: float = 7,
    color_map: str = 'plasma',
    modes_labeled: int = 0,
    fill: bool = False,
    mode_label_lines: bool = True,
):
    num_samples = len(distributions)
    colors = plt.cm.get_cmap(color_map, num_samples)(
        np.linspace(0, 1, num_samples)
    )

    if font_path:
        font = fonts.get_font(font_path)
    else:
        font = fonts.get_default_font()

    if not stacked:
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100, squeeze=False)
        ax_list = [ax[0, 0]]

        for i, dist in enumerate(distributions):
            x, y = dist.x_values, dist.y_values

            ax[0, 0].plot(x, y, label=dist.name, color=colors[i])

            if fill:
                ax[0, 0].fill_between(
                    x, y, 0,
                    color=colors[i],
                    alpha=0.25,
                    linewidth=0
                )

            if modes_labeled > 0:
                modes = find_modes(x, y, modes_labeled)
                positions = _position_mode_labels(modes, x, y, font_size, (x_min, x_max))

                for (px, py, x_offset, y_offset) in positions:
                    # Configure connection line style
                    arrow_props = None
                    if mode_label_lines:
                        arrow_props = dict(
                            arrowstyle='-',
                            color='gray',
                            alpha=0.6,
                            linewidth=1,
                            linestyle='--'
                        )

                    ax[0, 0].annotate(
                        f'{px:.0f}',
                        xy=(px, py),
                        xytext=(x_offset, y_offset),
                        textcoords='offset points',
                        ha='left',
                        va='center',
                        fontsize=font_size * 0.85,
                        zorder=5,
                        clip_on=True,
                        arrowprops=arrow_props
                    )

        if legend:
            ax[0, 0].legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=font_size)

    else:
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=100)
        gs = gridspec.GridSpec(len(distributions), 1, figure=fig)
        ax_list = []

        for i, dist in enumerate(distributions):
            ax = fig.add_subplot(gs[i])
            ax_list.append(ax)

            x, y = dist.x_values, dist.y_values
            ax.plot(x, y, label=dist.name, color=colors[i])

            if fill:
                ax.fill_between(
                    x, y, 0,
                    color=colors[i],
                    alpha=0.25,
                    linewidth=0
                )

            if modes_labeled > 0:
                modes = find_modes(x, y, modes_labeled)
                positions = _position_mode_labels(modes, x, y, font_size, (x_min, x_max))

                for (px, py, x_offset, y_offset) in positions:
                    # Configure connection line style
                    arrow_props = None
                    if mode_label_lines:
                        arrow_props = dict(
                            arrowstyle='-',
                            color='gray',
                            alpha=0.6,
                            linewidth=1,
                            linestyle='--'
                        )

                    ax.annotate(
                        f'{px:.0f}',
                        xy=(px, py),
                        xytext=(x_offset, y_offset),
                        textcoords='offset points',
                        ha='left',
                        va='center',
                        fontsize=font_size * 0.85,
                        zorder=5,
                        clip_on=True,
                        arrowprops=arrow_props
                    )

            if legend:
                ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=font_size)

    for i, ax in enumerate(ax_list):
        ax.set_xlim(x_min, x_max)
        ax.tick_params(axis='both', which='major', labelsize=font_size)

        if stacked and i < len(ax_list) - 1:
            ax.tick_params(axis='x', labelbottom=False)
        else:
            plt.setp(ax.get_xticklabels(), fontproperties=font)

        plt.setp(ax.get_yticklabels(), fontproperties=font)

        ax.set_facecolor('white')
        ax.tick_params(axis='x', colors='black', width=2)
        ax.tick_params(axis='y', colors='black', width=2)

    fig.suptitle(title, fontsize=font_size * 1.75, fontproperties=font)
    fig.text(0.5, 0.02, 'Age (Ma)', ha='center', va='center',
             fontsize=font_size, fontproperties=font)
    fig.text(0.01, 0.5, 'Probability Differential', va='center',
             rotation='vertical', fontsize=font_size, fontproperties=font)

    fig.tight_layout(rect=[0.025, 0.025, 0.975, 1])
    plt.xlim(x_min, x_max)

    plt.close()
    return fig
