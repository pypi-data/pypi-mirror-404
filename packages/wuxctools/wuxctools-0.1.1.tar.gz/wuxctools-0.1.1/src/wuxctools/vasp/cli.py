from typing import Annotated

import tyro

from .subcommand import Band, Dos

Vasp = Annotated[
    Band | Dos,
    tyro.conf.subcommand(name="vasp", description="Some useful vasp tools"),
]
