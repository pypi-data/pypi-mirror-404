import os
from pathlib import Path
from typing import Annotated, Literal

import tyro
from msgspec import Struct, field

from wuxctools.plot import BaseFigSet, HeatFigSet
from wuxctools.vasp.dataread import read_vasp_file

from .parsepro import ProParams


class BandBaseFigSet(BaseFigSet):
    xrange: Annotated[tuple[int, int], tyro.conf.arg(aliases=["-xr"])] = (0, -1)  # pyright: ignore[reportIncompatibleVariableOverride]
    """x index range for figure"""

    yrange: Annotated[tuple[float, float] | None, tyro.conf.arg(aliases=["-yr"])] = (
        field(default_factory=lambda: (-4, 6))
    )

    hide_xticks = True
    ylabel = "Energy (eV)"
    save = ["band.png"]


class BandProParams(ProParams):
    heatparams: Annotated[HeatFigSet, tyro.conf.arg(name="")] = field(
        default_factory=HeatFigSet
    )

    scale: float = 5
    """Specific scatter line scale for pmode 1"""

    fill: Literal["auto", "hollow", "solid"] = "auto"

    """Scatter filling mode:
    - auto: decide based on fc
    - hollow: empty facecolor
    - solid: filled, requires fc or default
    """

    alpha_gamma: float = 0.3
    """use gamma mapping for alpha = (z_norm)^gamma"""


class Band(Struct, tag="band"):
    """
    Plot vasp band figure
    """

    basefigset: BaseFigSet = field(default_factory=BandBaseFigSet)
    pro: BandProParams = field(default_factory=BandProParams)

    files: tyro.conf.Positional[list[Path]] = field(
        default_factory=lambda: [Path("vaspout.h5")]
    )
    """files that vasp read"""

    vaspfileformat: Annotated[
        Literal["h5", "xml", "auto"], tyro.conf.arg(aliases=["-vf"])
    ] = "auto"
    """read vaspfile format [env var: WUXC_VASP_FILE_FORMAT]"""

    efermi: Annotated[float | str | None, tyro.conf.arg(aliases=["-ef"])] = None
    """Fermi energy value, or a path to a file from which the Fermi level is read."""

    spin: Annotated[int | None, tyro.conf.arg(aliases=["-s"])] = None
    """Specify which spin to plot"""

    fix_order: bool = False
    """reorder band for vasp give the wrong order when ncore > 1"""

    labels: Annotated[list[str] | None, tyro.conf.arg(aliases=["-l"])] = None
    """labels for lines"""

    legend: bool = False
    """Whether show legend"""

    export: bool = True
    """Whether export band data"""

    def __post_init__(self):
        from wuxctools.utils import log

        v = os.getenv("WUXC_VASP_FILE_FORMAT", "auto")
        if v == "h5":
            self.vaspfileformat = "h5"
        if v == "xml":
            self.vaspfileformat = "xml"
        elif v == "auto":
            self.vaspfileformat = "auto"
        else:
            log.warning(
                f"Invalid WUXC_VASP_FILE_FORMAT={v!r}, falling back to 'auto'.",
            )
            self.vaspfileformat = "auto"

    def plot_single_file(self, file: Path):
        from .bandplot import BandPlot

        data = read_vasp_file(file, vaspfileformat=self.vaspfileformat)
        BandPlot(self, data)
        self.basefigset()

    def __call__(self):
        import matplotlib.pyplot as plt

        from wuxctools.utils import plot_series, set_style

        set_style(self.basefigset.matplotlibrc)
        plot_series(self.files, self.basefigset.save, self.plot_single_file)

        if self.basefigset.show:
            plt.show()
