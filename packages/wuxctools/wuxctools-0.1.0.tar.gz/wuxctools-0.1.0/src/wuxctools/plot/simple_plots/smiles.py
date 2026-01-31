from pathlib import Path

import tyro
from msgspec import Struct, field

from wuxctools.plot import BaseFigSet


class Smiles(Struct, tag="Smiles"):
    """
    Plot Smiles figure
    """

    smiles_str: tyro.conf.Positional[list[str] | None] = None
    file: Path | None = None
    unpack: bool = True
    cols: int = 1
    width: int = 800
    height: int = 800
    basefigset: BaseFigSet = field(default_factory=BaseFigSet)

    def plot_sigle_smiles(self, smiles_str: str) -> None:
        from rdkit import Chem
        from rdkit.Chem import Draw

        from wuxctools.utils import get_fig_ax, log

        log.info(f"Current Plot smiles is [yellow]{smiles_str}[/yellow]")
        mol = Chem.MolFromSmiles(smiles_str)
        if mol is None:  # pyright: ignore[reportUnnecessaryComparison]
            return
        _, ax = get_fig_ax()

        img = Draw.MolToImage(mol, size=(1000, 1000))  # pyright: ignore[reportUnknownVariableType]
        ax.imshow(img)  # pyright: ignore[reportUnknownArgumentType]
        ax.axis("off")

        self.basefigset()

    def __call__(self) -> None:
        import matplotlib.pyplot as plt

        from wuxctools.utils import plot_series, set_style

        set_style(self.basefigset.matplotlibrc, use_tex=False)
        if self.smiles_str:
            plot_series(self.smiles_str, self.basefigset.save, self.plot_sigle_smiles)
        if self.file:
            import polars as pl

            df = pl.read_csv(self.file)
            smiles_list: list[str] = df[:, 0].to_list()

            plot_series(smiles_list, self.basefigset.save, self.plot_sigle_smiles)

        if self.basefigset.show:
            plt.show()
