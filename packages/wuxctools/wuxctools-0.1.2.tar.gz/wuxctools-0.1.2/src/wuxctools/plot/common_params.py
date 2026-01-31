import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

import tyro
from msgspec import Struct, field

if TYPE_CHECKING:
    from matplotlib.cm import ScalarMappable


class BaseFigSet(Struct):
    from_cli: Annotated[bool, tyro.conf.Suppress] = False

    matplotlibrc: Annotated[Path, tyro.conf.arg()] = field(
        default_factory=lambda: Path(
            os.getenv("WUXC_MATPLOTLIBRC_FILE", "~/.config/wuxctools/matplotlibrc")
        )
    )
    """ matplotlibrc style file [env var: WUXC_MATPLOTLIBRC_FILE] """

    figsize: tuple[float, float] | None = None
    """size for figure"""

    xrange: Annotated[tuple[float, float] | None, tyro.conf.arg(aliases=["-xr"])] = None
    """x range for figure"""

    yrange: Annotated[tuple[float, float] | None, tyro.conf.arg(aliases=["-yr"])] = None
    """y range for figure"""

    xticks: Annotated[list[float] | None, tyro.conf.arg(aliases=["-xt"])] = None
    """xtick list for Figure"""

    yticks: Annotated[list[float] | None, tyro.conf.arg(aliases=["-yt"])] = None
    """ytick list for Figure"""

    xticklabels: Annotated[list[str] | None, tyro.conf.arg(aliases=["-xtl"])] = None
    """xticklabel list for Figure"""

    yticklabels: Annotated[list[str] | None, tyro.conf.arg(aliases=["-ytl"])] = None
    """yticklabel list for Figure"""

    xlabel: Annotated[str, tyro.conf.arg(aliases=["-xl"])] = ""
    """xlabel for Figure"""

    ylabel: Annotated[str, tyro.conf.arg(aliases=["-yl"])] = ""
    """ylabel for Figure"""

    hide_xticks: bool = False
    """Whether hide xticks"""

    hide_yticks: bool = False
    """Whether hide yticks"""

    n_minor: int = 2
    "Number of minor ticks between two major ticks (AutoMinorLocator n)"

    colors: Annotated[list[str], tyro.conf.arg(aliases=["-c"])] = field(
        default_factory=lambda: [
            "red",
            "blue",
            "orange",
            "green",
            "pink",
            "brown",
        ]
    )
    """colors list for Figure."""

    title: Annotated[str, tyro.conf.arg(aliases=["-t"])] = ""
    """fitle for Figure."""

    show: bool = True
    """Whether show figure"""

    save: list[str] = field(default_factory=lambda: [])
    """Save figure names"""

    def __call__(self):
        from matplotlib.ticker import AutoLocator, AutoMinorLocator

        from wuxctools.utils import get_fig_ax, set_style

        set_style(self.matplotlibrc)

        fig, ax = get_fig_ax()
        if self.figsize:
            fig.set_size_inches(*self.figsize)

        ## title
        ax.set_title(self.title)

        ax.set_xlabel(self.xlabel)
        ax.set_xticks(
            self.xticks
        ) if self.xticks is not None else ax.xaxis.set_major_locator(AutoLocator())
        ax.set_xticklabels(self.xticklabels) if self.xticklabels is not None else ...
        ax.xaxis.set_minor_locator(AutoMinorLocator(self.n_minor))

        ax.set_ylabel(self.ylabel)
        ax.set_yticks(
            self.yticks
        ) if self.yticks is not None else ax.yaxis.set_major_locator(AutoLocator())
        ax.set_yticklabels(self.yticklabels) if self.yticklabels is not None else ...
        ax.yaxis.set_minor_locator(AutoMinorLocator(self.n_minor))

        ax.set_xlim(self.xrange)
        ax.set_ylim(self.yrange)
        if self.hide_xticks:
            ax.tick_params(which="both", bottom=False)
        if self.hide_yticks:
            ax.tick_params(which="both", left=False)


class HeatFigSet(Struct):
    colorbar: bool = True
    """Whether plot colorbar"""

    cmap: Annotated[str, tyro.conf.arg(aliases=["-cm"])] = "cet_coolwarm"
    """Colormap"""

    norm: Annotated[
        Literal[
            "MyCustom",
            "Normal",
            "Logarithmic",
            "Centered",
            "SymmetricLogarithmic",
            "PowerLaw",
            "TwoSlopeNorm",
        ],
        tyro.conf.arg(name="normalization", aliases=["--norm"]),
    ] = "MyCustom"
    """Choose normalization method for colormap ,see  https://matplotlib.org/stable/users/explain/colors/colormapnorms.html"""

    power: float = 2.0
    """specific the power of PowerLaw Normalization"""

    symlogparm: tuple[float, float] = (0.1, 0.1)
    """specific linthresh and linscale for SymmetricLogarithmic Normalization"""

    cticks: list[float] | None = None
    """colorbar ticks"""

    cticklabels: list[str] | None = None
    """colorbar ticklabels for Figure"""

    vrange: tuple[float, float] | None = None

    vcenter: float = 0.0

    def __call__(self, mappable: "ScalarMappable"):
        arr = mappable.get_array()
        if arr is None:
            raise ValueError
        vmin, vmax = (arr.min()), arr.max()

        self._set_norm(mappable, vmin, vmax)
        if self.colorbar:
            self._set_cbar(mappable, vmin, vmax)

    def _set_norm(self, mappable: "ScalarMappable", vmin: float, vmax: float):
        from matplotlib import colors

        from wuxctools.utils.plot import MyCustomNormalize

        if self.norm == "Normal":
            norm = colors.Normalize(vmin, vmax)
        elif self.norm == "Logarithmic":
            if vmin < 0:
                raise ValueError(
                    "Logarithmic Normalization doesn't support negative values"
                )
            norm = colors.LogNorm(vmin, vmax)
        elif self.norm == "Centered":
            norm = colors.CenteredNorm(self.vcenter)
        elif self.norm == "SymmetricLogarithmic":
            norm = colors.SymLogNorm(
                linthresh=self.symlogparm[0],
                linscale=self.symlogparm[1],
                vmin=vmin,
                vmax=vmax,
            )
        elif self.norm == "TwoSlopeNorm":
            norm = colors.TwoSlopeNorm(vmin=vmin, vcenter=self.vcenter, vmax=vmax)
        elif self.norm == "PowerLaw":
            norm = colors.PowerNorm(self.power, vmin, vmax)
        else:
            norm = MyCustomNormalize(vmin, vmax, self.vcenter)

        mappable.set_norm(norm)

    def _set_cbar(self, mappable: "ScalarMappable", vmin: float, vmax: float):
        import colorcet  # pyright: ignore[reportMissingTypeStubs]

        _ = colorcet.__version__

        from wuxctools.utils import get_fig_ax

        mappable.set_cmap(self.cmap)
        fig, ax = get_fig_ax()
        cbar = fig.colorbar(mappable, ax=ax)
        if self.cticks is None:
            if vmin * vmax > 0:
                self.cticks = [
                    vmin,
                    (vmin + vmax) / 4,
                    (vmin + vmax) / 2,
                    (vmin + vmax) / 4 * 3,
                    vmax,
                ]
            else:
                self.cticks = [
                    vmin,
                    (vmin + self.vcenter) / 2,
                    self.vcenter,
                    (vmax + self.vcenter) / 2,
                    vmax,
                ]

        else:
            ...
        cbar.set_ticks(self.cticks)

        if self.cticklabels is None:
            self.cticklabels = [f"{i:.2f}" for i in self.cticks]
        cbar.set_ticklabels(self.cticklabels)
