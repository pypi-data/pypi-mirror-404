"""
plotfair.presets

This module defines default plotting settings for matplotlib and seaborn to ensure
consistent and visually appealing figures across the project. It updates matplotlib's
rcParams with preferred defaults, applies a seaborn style, and monkey-patches
matplotlib.pyplot.savefig with a wrapper that saves figures to a specified folder by default.
"""
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

SAVE_FIGS = True

# Seaborn base style
sns.set_style("white")

# Update rcParams
mpl.rcParams.update({
    'figure.figsize': (6, 4),
    'figure.dpi': 150,
    'figure.facecolor': 'white',
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'axes.labelweight': 'bold',
    'axes.linewidth': 1.2,
    'axes.edgecolor': 'black',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.spines.left': True,
    'axes.spines.bottom': True,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.major.size': 6,
    'ytick.major.size': 6,
    'xtick.minor.size': 3,
    'ytick.minor.size': 3,
    'xtick.major.width': 1.0,
    'ytick.major.width': 1.0,
    'xtick.minor.width': 0.8,
    'ytick.minor.width': 0.8,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'xtick.minor.visible': False,
    'ytick.minor.visible': False,
    'lines.linewidth': 2.0,
    'lines.markersize': 6,
    'lines.markeredgewidth': 0.8,
    'font.size': 12,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
    'legend.fontsize': 12,
    'legend.frameon': False,
    'legend.loc': 'best',
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'savefig.transparent': True,
    'image.cmap': 'plasma',
    "errorbar.capsize" : 2.0,
})

sns.set_style("white", {
    "axes.spines.right": False,
    "axes.spines.top": False,
    "xtick.bottom": True,
    "ytick.left": True
})

_original_savefig = plt.savefig

def savefig_with_folder(fname, *args, folder="figs", **kwargs):
    """
    Save a matplotlib figure to a file, ensuring the output directory exists.

    Parameters:
        fname (str): The filename for the saved figure. If not an absolute path,
            it will be saved inside the specified folder.
        *args: Additional positional arguments passed to plt.savefig.
        folder (str): The folder to save the figure in (default: "figs").
        **kwargs: Additional keyword arguments passed to plt.savefig.

    Behavior:
        - If SAVE_FIGS is True, creates the folder if it doesn't exist and saves the figure.
        - If fname is not an absolute path, prepends the folder to the filename.
        - If SAVE_FIGS is False, prints a message and does not save.
    """
    if SAVE_FIGS:
        if not os.path.isabs(fname):
            os.makedirs(folder, exist_ok=True)
            fname = os.path.join(folder, fname)
        return _original_savefig(fname, *args, **kwargs)
    else:
        print('Currently not saving figures')

plt.savefig = savefig_with_folder
