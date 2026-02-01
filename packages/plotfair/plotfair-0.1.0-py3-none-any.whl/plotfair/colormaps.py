"""
PridePy.colormaps
Colormap creation utilities for perceptual and sRGB gradients.

This module provides functions to create colormaps that
are perceptually uniform or linear in sRGB space.
It supports generating colormaps with anchor colors
placed at nonuniform positions and visualizing colormaps.
"""

import numpy as np
from colorspacious import cspace_convert
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, to_rgb


def perceptual_colormap_nonuniform(colors, positions=None, n=256, space="CAM02-UCS"):
    """
    Generate a perceptually uniform colormap between fixed color anchors at nonuniform positions.

    Parameters:
        colors (list): List of color specifications (e.g., color names or RGB tuples).
        positions (list or None): Optional list of floats in [0, 1] specifying the
                                  relative positions of the anchor colors.
                                  Must start with 0.0 and end with 1.0 if provided.
                                  If None, colors are assumed to be evenly spaced.
        n (int): Number of points in the output colormap.
        space (str): The color space in which to perform interpolation (default is "CAM02-UCS").

    Returns:
        ListedColormap: A matplotlib ListedColormap object representing
                        the perceptually uniform colormap.
    """
    num_colors = len(colors)
    if positions is None:
        positions = np.linspace(0.0, 1.0, num_colors)
    else:
        assert len(colors) == len(positions)
        assert positions[0] == 0.0 and positions[-1] == 1.0
    rgb_colors = np.array([to_rgb(c) for c in colors])
    perceptual_colors = cspace_convert(rgb_colors, "sRGB1", space)
    steps = np.linspace(0, 1, n)
    interpolated = []
    for idx in range(len(positions) - 1):
        start_pos = positions[idx]
        end_pos = positions[idx + 1]
        start_col = perceptual_colors[idx]
        end_col = perceptual_colors[idx + 1]
        segment_mask = (steps >= start_pos) & (steps <= end_pos)
        local_t = (steps[segment_mask] - start_pos) / (end_pos - start_pos)
        for t in local_t:
            interpolated.append((1 - t) * start_col + t * end_col)
    interpolated = np.array(interpolated)
    rgb_interp = cspace_convert(interpolated, space, "sRGB1")
    rgb_interp = np.clip(rgb_interp, 0, 1)
    return ListedColormap(rgb_interp, name="perceptual_nonuniform")


def srgb_gradient_colormap(colors, positions=None, n=256, name="srgb_colormap"):
    """
    Create a linear sRGB gradient colormap from anchor colors.

    Parameters:
        colors (list): List of color specifications (e.g., color names or RGB tuples).
        positions (list or None): Optional list of floats in [0, 1] specifying the
                                  relative positions of the anchor colors.
                                  Must start with 0.0 and end with 1.0 if provided.
                                  If None, colors are assumed to be evenly spaced.
        n (int): Number of points in the output colormap.
        name (str): Name of the resulting colormap.

    Returns:
        LinearSegmentedColormap: A matplotlib LinearSegmentedColormap object
                                 representing the sRGB gradient colormap.
    """
    rgb_colors = [to_rgb(c) for c in colors]
    if positions is not None:
        assert len(positions) == len(rgb_colors)
        assert positions[0] == 0.0 and positions[-1] == 1.0
        return LinearSegmentedColormap.from_list(name, list(zip(positions, rgb_colors)), N=n)
    else:
        return LinearSegmentedColormap.from_list(name, rgb_colors, N=n)


def show_colormap(cmap, name=None, height=0.5):
    """
    Display a horizontal gradient of the given colormap.

    Parameters:
        cmap (Colormap): A matplotlib colormap instance to display.
        name (str or None): Optional title to display above the colormap.
        height (float): Height of the displayed gradient figure in inches.

    Behavior:
        Opens a matplotlib window showing the colormap gradient.
    """
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, height))
    ax.imshow(gradient, aspect="auto", cmap=cmap)
    ax.set_axis_off()
    if name:
        ax.set_title(name, fontsize=10)
    plt.show()
