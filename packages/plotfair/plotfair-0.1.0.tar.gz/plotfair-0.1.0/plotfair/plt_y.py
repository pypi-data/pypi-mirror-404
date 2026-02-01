"""This module provides a Matplotlib-like plotting interface using Plotly as the backend.
It defines the Plty class which mimics familiar Matplotlib plotting functions such as plot,
hist, setting axis limits, titles, labels, and supports log-log scaling. The module also
includes predefined Plotly templates and themes for consistent styling."""

import subprocess
import tempfile

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

from . import colors


class Plty:
    """A Plotly-based Matplotlib-like interface for creating interactive plots.

    This class provides methods similar to Matplotlib's pyplot interface, enabling users
    to create line plots, histograms, set axis limits, labels, titles, and switch between
    linear and log-log scales, all using Plotly's interactive plotting capabilities.
    """
    def __init__(self):
        self.fig = go.Figure()

    def plot(self, *args, **kwargs):
        """
        Plot lines and/or markers. Usage mimics plt.plot.

        Supports:
        - plot(y)
        - plot(x, y)
        - plot(x, y, fmt)
        Optional keyword arguments include color, linestyle, marker, alpha, label, etc.
        """
        fmt = None
        if len(args) == 1:  # y only
            y = np.asarray(args[0])
            x = np.arange(len(y))
        elif len(args) == 2:  # x, y or y, fmt
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
            raise ValueError("Use plty.plot(y), plty.plot(x, y), or plty.plot(x, y, fmt)")

        name = kwargs.pop("label", None)
        color = kwargs.pop("color", None)
        linestyle = kwargs.pop("linestyle", None)
        marker = kwargs.pop("marker", None)
        fmt = kwargs.pop("fmt", fmt)
        alpha = kwargs.pop("alpha", None)
        kwargs['opacity'] = alpha

        # Parse format string
        if fmt:
            marker_map = {'o': 'circle', 's': 'square', '^': 'triangle-up', 'v': 'triangle-down',
                          'd': 'diamond', '*': 'star', '+': 'cross', 'x': 'x'}
            linestyle_map = {'--': 'dash', ':': 'dot', '-.': 'dashdot','-': 'solid'}

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

        self.fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers" if marker else "lines",
                                     name=name, line=line_dict, marker=marker_dict, **kwargs))

    def hist(self, data, bins=50, **kwargs):
        """
        Plot histograms similar to plt.hist.

        Data can be a list, numpy array, or a dictionary of {label: values}.
        Bins can be an integer or an array of bin edges.
        Supports density=True for normalized histograms.
        """
        opacity = kwargs.pop("alpha", 0.5)
        density = kwargs.pop("density", False)

        def add_hist_trace(arr, label=None):
            # Compute bin edges using matplotlib method
            if isinstance(bins, int):
                edges = np.histogram_bin_edges(arr, bins=bins)
            else:
                edges = np.asarray(bins)

            self.fig.add_trace(
                go.Histogram(
                    x=arr,
                    # copies mpl hist behavoiour
                    xbins=dict(
                        start=edges[0],
                        end=edges[-1],
                        size=edges[1] - edges[0] if len(edges) > 1 else None
                    ),
                    name=label,
                    opacity=opacity,
                    histnorm='probability density' if density else None
                )
            )

        if isinstance(data, dict):
            for label, values in data.items():
                add_hist_trace(values, label=label)
        else:
            add_hist_trace(data, label=kwargs.pop("label", "trace"))

        self.fig.update_layout(barmode='overlay')

    def xlim(self, xmin=None, xmax=None):
        """Set the limits of the x-axis."""
        current = self.fig.layout.xaxis
        new_range = [
            xmin if xmin is not None else current.range[0] if current.range else None,
            xmax if xmax is not None else current.range[1] if current.range else None
        ]
        self.fig.update_layout(xaxis=dict(range=new_range))
    def ylim(self, ymin=None, ymax=None):
        """Set the limits of the y-axis."""
        current = self.fig.layout.yaxis
        new_range = [
            ymin if ymin is not None else current.range[0] if current.range else None,
            ymax if ymax is not None else current.range[1] if current.range else None
        ]
        self.fig.update_layout(yaxis=dict(range=new_range))
    def title(self, text):
        """Set the figure title."""
        self.fig.update_layout(title=dict(text=text))
    def xlabel(self, text):
        """Set the x-axis label."""
        self.fig.update_layout(xaxis_title=text)

    def ylabel(self, text):
        """Set the y-axis label."""
        self.fig.update_layout(yaxis_title=text)
    def loglog(self):
        """Set both x and y axes to logarithmic scale."""
        self.fig.update_layout(xaxis_type='log', yaxis_type='log')
    def linear(self):
        """Set both x and y axes to linear scale."""
        self.fig.update_layout(xaxis_type='linear', yaxis_type='linear')

    def save_to_clipboard(self):
        """Saves figure to clipboard but uses script from https://alecjacobson.com/weblog/3816.html
        but can probably also use https://github.com/jcsalterego/pngpaste/"""
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            self.fig.write_image(tmp.name, scale=3)  # requires plotly + kaleido
            tmp.flush()
            # Copy to clipboard using impbcopy
            subprocess.run(["impbcopy", tmp.name])

    def show(self):
        """Display the figure and reset the figure object."""
        self.fig.show()
        self.fig = go.Figure()

    def show_(self):
        # self.fig.show()
        self.fig = go.Figure()

# Define Plotly Themes
# 1. Font definitions
font_main = dict(family="Arial", size=12, )
title_font = {**font_main, 'size':20}
axis_title_font = {**font_main, 'size':18}

# 2. Tick configuration (can toggle on/off by changing ticklen or ticks)
tick_settings = dict(
    ticks="outside",
    ticklen=6,
    tickwidth=1.0,
)

# 3. Axis base settings (x and y share most properties)
axis_base = dict(
    title=dict(text=""),
    showline=True,
    linewidth=1.8,
    mirror=False,   # turn off top/right spines
    showgrid=True,
    zeroline=False,
    title_standoff=1, # distance between title and axis
    tickfont={**font_main, 'size':16},
    **tick_settings
)

# 5. Legend
legend_settings = dict(
    orientation="v",
    yanchor="top",
    y=1,
    xanchor="left",
    x=1.02,
    font={**font_main, 'size':12},
    bgcolor="rgba(0,0,0,0)"
)

# 6. Combine into layout
pridepy_base_template = dict(
    title=dict(text="",x=0.5, xanchor='center'),
    title_font=title_font,
    xaxis=axis_base,
    xaxis_title_font=axis_title_font,
    yaxis=axis_base,
    yaxis_title_font=axis_title_font,

    legend=legend_settings,

    margin=dict(l=60, r=60, t=40, b=40),
    colorway= colors.plotly_scheme,
    hoverlabel=dict(namelength=-1)
    # font=font_main,
)
loglog_template = dict(xaxis_type='log', yaxis_type='log',)


pio.templates["pridepy"] = go.layout.Template(layout=pridepy_base_template)
pio.templates["loglog"] = go.layout.Template(layout=loglog_template)
# use plotly_white for paper graphs or plotly_dark for dark mode or plotly for default
# presentation makes lines slighlty thicker
pio.templates.default = 'plotly_white+presentation+pridepy'

# Usage
plty = Plty()
