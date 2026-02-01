"""Presets and utilities for interplot plotting library.

This module configures default styles, behaviors, and helper classes for
interplot (iplot) plots. It customizes matplotlib and plotly plot appearances,
provides enhanced show and save methods, and defines a convenient plotting
interface via the Iplt class.
"""

from datetime import datetime
from pathlib import Path

import interplot as iplot
import matplotlib as mpl
import numpy as np
import plotly.graph_objects as go

mpl.rcParams.update({
    'figure.figsize': (6, 4),
    'savefig.bbox': 'tight',
    'savefig.transparent': False,
    'savefig.dpi': 'figure'
})

# iplot.conf.COLOR_CYCLE = pp.plotly_scheme
iplot.conf.INTERACTIVE = True
iplot.conf.MPL_FIG_SIZE = (700, 400)


def my_mpl_style(fig, ax):
    """Apply custom matplotlib style to figures and axes.

    Args:
        fig: Matplotlib figure object.
        ax: Axes array (2D even for 1x1).

    Returns:
        Tuple of (fig, ax) with style applied.
    """
    for a in ax.flat:
        # spines
        a.spines['top'].set_visible(False)
        a.spines['right'].set_visible(False)
        a.spines['left'].set_visible(True)
        a.spines['bottom'].set_visible(True)

        # major ticks
        a.tick_params(axis='x', which='major', direction='out',
                      length=6, width=1.0, labelsize=20)
        a.tick_params(axis='y', which='major', direction='out',
                      length=6, width=1.0, labelsize=20)

        # minor ticks
        a.tick_params(axis='x', which='minor', direction='out',
                      length=3, width=0.8)
        a.tick_params(axis='y', which='minor', direction='out',
                      length=3, width=0.8)

        # hide minor ticks if desired
        if False:  # set True to turn off minors
            a.minorticks_off()

    return fig, ax


iplot.conf.MPL_CUSTOM_FUNC = my_mpl_style

if iplot.Plot.show.__name__ != 'show_and_close':
    _original_show = iplot.Plot.show


def show_and_close(self, *args, **kwargs):
    """Enhanced show method that closes plot if not interactive."""
    self.post_process()
    try:
        return _original_show(self, *args, **kwargs)
    finally:
        if not self.interactive:
            self.close()
        # reset figure like in plt.show()
        self = iplot.Plot()
        if not self.interactive:
            self.close()


iplot.Plot.show = show_and_close

if iplot.Plot.save.__name__ != 'save_with_folder':
    _original_plot_save = iplot.Plot.save
iplot.conf.SAVE_FIGS = True
iplot.conf.FIG_FILE = 'figs'


def save_with_folder(
    self,
    path,
    *args,
    folder=iplot.conf.FIG_FILE,
    **kwargs,
):
    """Save plot to a specified folder, creating it if necessary.

    Args:
        self: Plot instance.
        path: Filename or boolean for default naming.
        folder: Folder to save figures into.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

    Returns:
        Result of original save method.
    """
    if not path:
        return
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    # Preserve original semantics
    if isinstance(path, bool):
        if self.title is not None and str(self.title).strip() != "":
            return _original_plot_save(
                self,
                folder / f"{self.title}_{datetime.now().strftime('%M:%H-%d_%m_%Y')}",
                *args,
                **kwargs
            )
        else:
            return _original_plot_save(
                self,
                folder / datetime.now().strftime("%M:%H-%d_%m_%Y"),
                *args,
                **kwargs
            )

    path = Path(path)

    # Only redirect relative paths
    if not path.is_absolute():
        path = folder / path

    return _original_plot_save(self, path, *args, **kwargs)


iplot.Plot.save = save_with_folder

PLOT_DEFAULTS = {
    "interactive": None,
    "rows": 1,
    "cols": 1,
    "title": None,
    "xlabel": None,
    "ylabel": None,
    "xlim": None,
    "ylim": None,
    "xlog": False,
    "ylog": False,
    "shared_xaxes": False,
    "shared_yaxes": False,
    "column_widths": None,
    "row_heights": None,
    "fig_size": None,
    "dpi": None,
    "legend_loc": None,
    "legend_title": None,
    "legend_togglegroup": None,
    "color_cycle": None,
    "save_fig": iplot.conf.SAVE_FIGS,
    "save_format": None,
    "save_config": None,
    "global_custom_func": None,
    "mpl_custom_func": None,
    "pty_custom_func": None,
    "pty_update_layout": None,
}


def rebuild_blank(self):
    """Clear plot by rebuilding with default parameters."""
    kwargs = {k: v for k, v in self.__dict__.items() if k in PLOT_DEFAULTS}
    return self.__class__(**kwargs)


iplot.conf.PLOT_DEFAULTS = PLOT_DEFAULTS
iplot.Plot.clear = rebuild_blank


class Iplt:
    """Convenient interface class wrapping interplot Plot object.

    Provides familiar plotting methods similar to matplotlib's pyplot,
    supporting both interactive and non-interactive modes.
    """

    def __init__(self, *args, **kwargs):
        """Initialize with an interplot Plot instance."""
        self.fig = iplot.Plot(*args, **kwargs)

    def new(self, *args, **kwargs):
        """Create a new plot, closing previous if non-interactive."""
        if not self.fig.interactive:
            self.fig.close()
        self.fig = iplot.Plot(*args, **kwargs)
        if not self.fig.interactive:
            self.fig.close()

    def show(self):
        """Show the current plot."""
        self.fig.show()

    def plot(self, *args, **kwargs):
        """Plot data with optional formatting.

        Supports calls like:
        - plot(y): y vs. index
        - plot(x, y): x vs. y
        - plot(x, y, fmt): with format string controlling marker and line style

        Optional kwargs: color, linestyle, marker, alpha, label, etc.
        .. todo::
            - Use `mode=lines+markers` instrad of scatter and line.
            - Compatability between markers in ploly and pyplot.
        """
        if not self.fig.interactive:
            self.fig.fig.gca().plot(*args, **kwargs)
            return

        fmt = None
        if len(args) == 1:  # y only
            y = np.asarray(args[0])
            x = np.arange(len(y))
        elif len(args) == 2:
            if isinstance(args[1], str):  # y, fmt
                y = np.asarray(args[0])
                x = np.arange(len(y))
                fmt = args[1]
            else:  # x, y
                x, y = map(np.asarray, args)
        elif len(args) == 3:  # x, y, fmt
            x, y = map(np.asarray, args[:2])
            fmt = args[2]
        else:
            raise ValueError(
                "Use plty.plot(y), plty.plot(x, y), or plty.plot(x, y, fmt)"
            )

        name = kwargs.pop("label", None)
        color = kwargs.pop("color", None)
        linestyle = kwargs.pop("linestyle", None)
        marker = kwargs.pop("marker", None)
        fmt = kwargs.pop("fmt", fmt)
        alpha = kwargs.pop("alpha", None)
        kwargs['opacity'] = alpha

        # Parse format string
        if fmt:
            marker_map = {
                'o': 'circle',
                's': 'square',
                '^': 'triangle-up',
                'v': 'triangle-down',
                'd': 'diamond',
                '*': 'star',
                '+': 'cross',
                'x': 'x'
            }
            linestyle_map = {
                '--': 'dash',
                ':': 'dot',
                '-.': 'dashdot',
                '-': 'solid'
            }

            for key, val in marker_map.items():
                if key in fmt:
                    marker = val
                    break
            for key, val in linestyle_map.items():
                if key in fmt:
                    linestyle = val
                    break

        line_dict = {}
        if color is not None:
            line_dict["color"] = color
        if linestyle is not None:
            line_dict["dash"] = linestyle

        marker_dict = {}
        if marker is not None:
            marker_dict["symbol"] = marker
            marker_dict["size"] = 8

        mode = "lines+markers" if marker else "lines"
        self.fig.fig.add_trace(
            go.Scatter(
                x=x, y=y, mode=mode, name=name,
                line=line_dict, marker=marker_dict, **kwargs
            )
        )

    def __getattr__(self, name):
        """Forward unknown attributes/methods to the internal Plot instance."""
        return getattr(self.fig, name)

    @staticmethod
    def parse_format_string(fmt):
        """Parse matplotlib-style format strings.

        Format strings can specify color, marker, and line style.

        Args:
            fmt (str): Format string (e.g., 'ro-', 'b--', 'g^:').

        Returns:
            dict: {'color': str or None, 'marker': str or None,
                   'linestyle': str or None}

        Examples:
            >>> parse_format_string('ro-')
            {'color': 'red', 'marker': 'circle', 'linestyle': 'solid'}
            >>> parse_format_string('b--')
            {'color': 'blue', 'marker': None, 'linestyle': 'dashed'}
            >>> parse_format_string('g^')
            {'color': 'green', 'marker': 'triangle-up', 'linestyle': None}
        """
        COLOR_CODES = {
            'b': 'blue',
            'g': 'green',
            'r': 'red',
            'c': 'cyan',
            'm': 'magenta',
            'y': 'yellow',
            'k': 'black',
            'w': 'white',
        }

        MARKER_SYMBOLS = {
            '.': 'circle',
            'o': 'circle',
            'v': 'triangle-down',
            '^': 'triangle-up',
            '<': 'triangle-left',
            '>': 'triangle-right',
            's': 'square',
            'p': 'pentagon',
            '*': 'star',
            'h': 'hexagon',
            'H': 'hexagon2',
            '+': 'cross',
            'x': 'x',
            'D': 'diamond',
            'd': 'diamond-thin',
            '|': 'line-ns',
            '_': 'line-ew',
        }

        LINE_STYLES = {
            '--': 'dashed',
            '-.': 'dashdot',
            ':': 'dotted',
            '-': 'solid',
        }

        result = {'color': None, 'marker': None, 'linestyle': None}
        remaining = fmt

        # Extract line style (longer patterns first)
        for ls_key in ['--', '-.', ':', '-']:
            if ls_key in remaining:
                result['linestyle'] = LINE_STYLES[ls_key]
                remaining = remaining.replace(ls_key, '', 1)
                break

        # Extract color (single char)
        for char in remaining:
            if char in COLOR_CODES:
                result['color'] = COLOR_CODES[char]
                remaining = remaining.replace(char, '', 1)
                break

        # Extract marker
        for char in remaining:
            if char in MARKER_SYMBOLS:
                result['marker'] = MARKER_SYMBOLS[char]
                remaining = remaining.replace(char, '', 1)
                break

        if remaining.strip():
            import warnings
            warnings.warn(f"Unrecognized format string components: '{remaining}'")

        return result


iplt = Iplt()
