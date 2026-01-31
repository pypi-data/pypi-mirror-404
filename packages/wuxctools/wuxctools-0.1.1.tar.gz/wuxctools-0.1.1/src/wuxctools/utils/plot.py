from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Callable, Literal, TypeVar, cast, override

import numpy as np
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.projections.polar import PolarAxes

CTX_FIG: "ContextVar[Figure | None]" = ContextVar("CTX_FIG", default=None)
CTX_AX: "ContextVar[Axes | list[Axes] | None]" = ContextVar("CTX_AX", default=None)
CTX_AX_INDEX: ContextVar[int] = ContextVar("CTX_AX_INDEX", default=0)


def normalize_axes(ax: "Axes | list[Axes] | np.ndarray | None"):
    import numpy as np
    from matplotlib.axes import Axes

    if isinstance(ax, Axes):
        return ax
    if isinstance(ax, np.ndarray):
        return list(ax.flatten())  # ty:ignore[invalid-argument-type]
    if isinstance(ax, list):
        return ax
    else:
        return None


def get_fig_ax(idx: None | int = None):
    import matplotlib.pyplot as plt

    fig = CTX_FIG.get()
    ax = normalize_axes(CTX_AX.get())

    idx = idx if idx else CTX_AX_INDEX.get()

    if fig is None:
        fig = plt.figure()
        CTX_FIG.set(fig)
    if ax is None:
        ax = fig.add_subplot(1, 1, 1)
        CTX_AX.set(ax)

    if isinstance(ax, list):
        CTX_AX_INDEX.set(idx + 1)
        print(f"now plot on the ax of index {idx % len(ax)}")
        return fig, ax[idx % len(ax)]
    else:
        return fig, ax


@contextmanager
def figure_context(fig: "Figure", ax: "Axes | list[Axes]"):
    token_fig = CTX_FIG.set(fig)
    token_ax = CTX_AX.set(ax)
    token_idx = CTX_AX_INDEX.set(0)
    try:
        yield
    finally:
        CTX_FIG.reset(token_fig)
        CTX_AX.reset(token_ax)
        CTX_AX_INDEX.reset(token_idx)


def set_style(
    rc_file: Path | None = None,
    ncols: int = 1,
    nrows: int = 1,
    use_tex: bool | None = None,
):
    from importlib import resources

    import matplotlib as mpl

    if rc_file is None or not rc_file.exists():
        with resources.path("wuxctools", "wuxc.mplstyle") as rc_path:
            mpl.rc_file(rc_path)
    else:
        mpl.rc_file(rc_file)
    base_size = mpl.rcParams.get("figure.figsize", [3.5433070866, 2.3622047244])
    mpl.rcParams["figure.figsize"] = [
        base_size[0] / 2 * ncols,
        base_size[1] / 2 * nrows,
    ]
    mpl.rcParams["figure.figsize"] = [
        base_size[0] / 2 * ncols,
        base_size[1] / 2 * nrows,
    ]
    if use_tex is not None:
        mpl.rcParams["text.usetex"] = use_tex


T = TypeVar("T", Path, str)


def plot_series(
    single_obj: list[T],
    save: list[str],
    plt_fn: Callable[[T], None],
):
    import matplotlib.pyplot as plt
    from matplotlib.backend_bases import KeyEvent

    fig, ax = get_fig_ax()
    num_figures = len(single_obj)

    if num_figures == 1:
        plt_fn(single_obj[0])
        for savefile in save:
            plt.savefig(savefile)
        return

    if len(save) > 1:
        raise ValueError(
            "only support one save arg which is savedir when plot multiple figures"
        )
    elif len(save) == 1:
        savedir = Path(save[0])
        savedir.mkdir(exist_ok=True, parents=True)
        from tqdm import tqdm

        for file in tqdm(single_obj, desc="Saving figures"):
            save_name = f"{save[0]}/{file}.png"
            plt_fn(file)
            plt.savefig(save_name)
            ax.clear()

    current_index = 0
    path_title = True

    def update_figure(files: list[T], index: int, path_title: bool):
        file = files[index]
        ax.clear()
        plt_fn(file)
        if path_title:
            ax.set_title(f"{file}")

    update_figure(single_obj, 0, path_title)

    fig.canvas.draw()

    def on_key(event: KeyEvent):
        nonlocal current_index, path_title
        if event.key in ["right", "down", "j", "l"]:
            current_index = (current_index + 1) % num_figures
        elif event.key in ["left", "up", "k", "h"]:
            current_index = (current_index - 1) % num_figures
        elif event.key == "t":
            path_title = not path_title
        else:
            return

        update_figure(single_obj, current_index, path_title)
        fig.canvas.draw()

    fig.canvas.mpl_connect("key_press_event", on_key)  # type: ignore


class MyCustomNormalize(colors.Normalize):
    """
    Modified from https://stackoverflow.com/questions/7404116/defining-the-midpoint-of-a-colormap-in-matplotlib
    """

    def __init__(
        self, vmin: float, vmax: float, midpoint: float = 0.0, clip: bool = False
    ):
        self.midpoint: float = midpoint
        colors.Normalize.__init__(self, vmin, vmax, clip)

    @override
    def __call__(self, value: float, clip: bool | None = None):  # type:ignore
        vmin = cast(float, self.vmin)
        vmax = cast(float, self.vmax)
        import numpy as np

        if vmin == vmax:
            return np.full_like(value, 0.5, dtype=np.float64)
        midpoint = self.midpoint

        normalized_min = (
            max(
                0,
                1 / 2 * (1 - abs((midpoint - vmin) / (midpoint - vmax))),
            )
            if (self.midpoint != self.vmax)
            else 0
        )
        normalized_max = (
            min(
                1,
                1 / 2 * (1 + abs((vmax - midpoint) / (midpoint - vmin))),
            )
            if (self.midpoint != self.vmin)
            else 1.0
        )
        normalized_mid = 0.5
        x, y = (
            np.array([self.vmin, self.midpoint, self.vmax]),
            [normalized_min, normalized_mid, normalized_max],
        )
        return np.ma.masked_array(np.interp(value, x, y))


def add_axis(
    ax: Axes,
    direction: Literal["x", "y"] = "y",
    position: float = 1.1,
    ticks: list[float] | None = None,
    ticklabels: list[str] | None = None,
):
    if ax.name != "polar":
        raise ValueError("Axes must be polar")

    polar_ax = cast(PolarAxes, ax)

    if ticks is None:
        data_min, data_max = polar_ax.dataLim.y0, polar_ax.dataLim.y1
        ticks = [data_max, (data_max + data_min) / 2, data_min]

    xmin, xmax = (polar_ax.dataLim.x0, polar_ax.dataLim.x1)
    rmin, rmax = polar_ax.get_rmin(), polar_ax.get_rmax()

    def map_to_symmetric_range(
        y: list[float],
        data_range: tuple[float, float],
        coord_xrange: tuple[float, float],
        labels: list[str] | None = None,
        ndigits: int = 0,
    ) -> tuple[list[float], list[str]]:
        (c_min, c_max), (d_min, d_max) = coord_xrange, data_range
        y_array = np.asanyarray(y)
        mid = (c_min + c_max) / 2
        if d_max == d_min:
            neg = pos = np.full_like(y_array, mid)
        else:
            ratio = (y_array - d_min) / (d_max - d_min)
            pos = mid + ratio * (c_max - mid)
            neg = mid - ratio * (mid - c_min)
        if labels is None:
            labels = [f"{v:.{ndigits}f}" for v in y_array]

        ticks = neg.tolist() + pos[::-1].tolist()
        ticklabels = list(labels) + list(reversed(labels))
        return ticks, ticklabels

    if direction == "x":
        sax = polar_ax.secondary_xaxis(position)

        target_range = (xmin, xmax)
    else:
        sax = polar_ax.secondary_yaxis(position)

        target_range = (rmin, rmax)

    ticks, ticklabels = map_to_symmetric_range(
        ticks, (rmin, rmax), target_range, ticklabels
    )
    sax.set_ticks(ticks, ticklabels)

    return sax
