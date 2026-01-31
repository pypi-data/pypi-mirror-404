from pathlib import Path
from typing import Annotated, Literal

import tyro
from msgspec import Struct, field

from wuxctools.plot.common_params import BaseFigSet
from wuxctools.vasp.dataread import read_vasp_file
from wuxctools.vasp.subcommand.parsepro import ProParams


class DosBaseFigSet(BaseFigSet):
    xlabel = "Energy (eV)"
    ylabel = "DOS (states/eV)"
    save = ["dos.png"]


class Dos(Struct, tag="dos"):
    basefigset: DosBaseFigSet = field(default_factory=DosBaseFigSet)
    pro: ProParams = field(default_factory=ProParams)

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

    style: Literal["line", "fill", "grad"] = "grad"
    "Plot style"

    tdos: bool = True
    "Whether plot tdos"
    tlabel: str = "TDOS"
    "plot tdos label"

    tdos_style: Literal["line", "fill", "grad"] = "line"
    "total dos plot style"

    tdos_color: str = "black"
    "total dos plot color"

    legend: bool = False
    """Whether show legend"""

    def plot_single_file(self, file: Path):
        from .dosplot import DosPlot

        data = read_vasp_file(file)

        DosPlot(self, data)

        self.basefigset()
        pass

    def __call__(self) -> None:
        import matplotlib.pyplot as plt

        from wuxctools.utils import plot_series, set_style

        set_style(self.basefigset.matplotlibrc)
        plot_series(self.files, self.basefigset.save, self.plot_single_file)

        if self.basefigset.show:
            plt.show()
