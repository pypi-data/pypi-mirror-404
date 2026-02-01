"""
faiirplot
Beautiful color and plotting utilities for matplotlib and plotly.

Main modules:
- colors: Color swatches, palettes, and utilities
- presets: Default plotting settings
- colormaps: Colormap creation utilities
- plt_y: Matplotlib-like Plotly wrapper
- interplot_presets: interplot presets and patches
"""

# Core utilities
from . import colormaps, presets
from .colors import floats_to_rgbstring, hex_to_rgb, paintkit, paintkit_to_colorway, show_colormap
from .interplot_presets import Iplt

# Optional plotting wrappers
from .plt_y import Plty

__all__ = [
    "paintkit",
    "paintkit_to_colorway",
    "show_colormap",
    "hex_to_rgb",
    "floats_to_rgbstring",
    "presets",
    "colormaps",
    "Plty",
    "Iplt",
]
