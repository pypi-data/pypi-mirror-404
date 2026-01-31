from functools import cached_property
from pathlib import Path
from typing import Any, Callable

import matplotlib as mpl
import numpy as np
from matplotlib import colors
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.typing import ColorType

from wuxctools.utils import get_fig_ax

from ..dataread import read_vasp_file
from ..dataread.vaspdata import VaspData
from . import Dos


def fillplot(x: np.ndarray, y: np.ndarray, ax: Axes, **kwargs: Any):
    ax.fill(x, y, **kwargs)


def lineplot(x: np.ndarray, y: np.ndarray, ax: Axes, **kwargs: Any):
    ax.plot(x, y, **kwargs)


# copy from https://stackoverflow.com/questions/29321835/is-it-possible-to-get-color-gradients-under-curve-in-matplotlib
def gradient_fill(
    x: np.ndarray,
    y: np.ndarray,
    ax: Axes,
    fill_color: None | ColorType = None,
    **kwargs: Any,
):
    """
    Plot a line with a linear alpha gradient filled beneath it.

    Parameters
    ----------
    x, y : array-like
        The data values of the line.
    fill_color : a matplotlib color specifier (string, tuple) or None
        The color for the fill. If None, the color of the line will be used.
    ax : a matplotlib Axes instance
        The axes to plot on. If None, the current pyplot axes will be used.
    Additional arguments are passed on to matplotlib's ``plot`` function.

    """

    (line,) = ax.plot(x, y, **kwargs)
    if fill_color is None:
        fill_color = line.get_color()

    zorder = line.get_zorder()
    alpha = line.get_alpha()
    alpha = 1.0 if alpha is None else alpha

    z = np.empty((100, 1, 4), dtype=float)
    rgb = colors.colorConverter.to_rgb(fill_color)
    z[:, :, :3] = rgb
    z[:, :, -1] = np.linspace(0, alpha, 100)[:, None]
    xmin, xmax, ymin, ymax = x.min(), x.max(), y.min(), y.max()
    if ymin < 0:
        ymin, ymax = ymax, ymin
    im = ax.imshow(
        z, aspect="auto", extent=(xmin, xmax, ymin, ymax), origin="lower", zorder=zorder
    )

    xy = np.column_stack([x, y])
    xy = np.vstack([[xmin, ymin], xy, [xmax, ymin], [xmin, ymin]])
    clip_path = Polygon(xy, facecolor="none", edgecolor="none", closed=True)
    ax.add_patch(clip_path)
    im.set_clip_path(clip_path)

    ax.autoscale(True)


class DosPlot:
    def __init__(self, params: Dos, data: VaspData):
        self.params = params
        self.fig, self.ax = get_fig_ax()

        self.data = data

        if isinstance(self.params.efermi, str):
            efermi: float = read_vasp_file(Path(self.params.efermi)).fermi
            self.plot_fermi = efermi
        elif self.params.efermi is not None:
            self.plot_fermi = self.params.efermi
        else:
            self.plot_fermi = self.data.fermi

        plot_fn_dict = {"grad": gradient_fill, "fill": fillplot, "line": lineplot}
        self.plot_fn = plot_fn_dict[self.params.style]
        self.handles: list[Artist] = []

        if self.params.tdos:
            self._plotdos(
                self.total_dos, plot_fn_dict[self.params.tdos_style], color="black"
            )
            self.handles.append(Line2D([], [], c="black", label=self.params.tlabel))
        self.plot_pdos()
        if self.params.legend:
            self.ax.legend(handles=self.handles, loc="best")
        self.set_style()

    @cached_property
    def xlist(self) -> np.ndarray:
        return self.data.dose - self.plot_fermi

    @cached_property
    def total_dos(self) -> np.ndarray:
        return self.data.dos

    def _plotdos(self, dos: np.ndarray, plot_fn: Callable[..., None], **kwargs: Any):
        if self.params.spin is not None:
            plot_fn(self.xlist, dos[self.params.spin], self.ax, **kwargs)
        elif len(self.total_dos) == 2:
            plot_fn(self.xlist, dos[0], self.ax, **kwargs)
            plot_fn(self.xlist, -dos[1], self.ax, **kwargs)
        else:
            plot_fn(self.xlist, dos[0], self.ax, **kwargs)

    def plot_pdos(self):
        groups = self.params.pro.parse(self.data, self.params.basefigset.colors)
        for group, color in zip(groups, self.params.basefigset.colors):
            pdos = np.add.reduce(
                [
                    self.data.dospar[:, atoms][:, :, orbitals].sum(axis=(1, 2))
                    for atoms, orbitals in group
                ]
            )
            self._plotdos(pdos, self.plot_fn, c=color)
            self.handles.append(Line2D([], [], c=color, label=group.label))

    def set_style(self):
        self.params.basefigset.xrange = (min(self.xlist), max(self.xlist))

        self.ax.axhline(
            0,
            c="black",
            lw=mpl.rcParams["ytick.major.width"],
            zorder=0,
        )
