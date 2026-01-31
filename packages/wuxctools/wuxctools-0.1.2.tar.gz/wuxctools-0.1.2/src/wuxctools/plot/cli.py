from typing import Annotated

import tyro

from .simple_plots import Bar, Line, Scatter, Smiles

Plot = Annotated[
    Line | Scatter | Bar | Smiles,
    tyro.conf.subcommand(description="Some useful plot cli", name="plot"),
]
