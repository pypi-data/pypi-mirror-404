from pathlib import Path

import tyro
from msgspec import Struct, field

from wuxctools.plot import BaseFigSet


class Scatter(Struct, tag="scatter"):
    """
    Plot Scatter figure
    """

    files: tyro.conf.Positional[list[Path]] = field(
        default_factory=lambda: [Path("data.txt")]
    )
    unpack: bool = True
    cols: tuple[int, int] = (0, 1)
    basefigset: BaseFigSet = field(default_factory=BaseFigSet)

    def plot_sigle_file(self, file: Path):
        import numpy as np

        from wuxctools.utils import get_fig_ax

        data = np.loadtxt(file, unpack=self.unpack)
        _, ax = get_fig_ax()
        ax.scatter(data[self.cols[0]], data[self.cols[1]])
        self.basefigset()

    def __call__(self) -> None:
        import matplotlib.pyplot as plt

        from wuxctools.utils import plot_series, set_style

        set_style(self.basefigset.matplotlibrc)
        plot_series(self.files, self.basefigset.save, self.plot_sigle_file)

        if self.basefigset.show:
            plt.show()
