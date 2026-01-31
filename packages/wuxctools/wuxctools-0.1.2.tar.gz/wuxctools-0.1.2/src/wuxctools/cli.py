import tyro

from .plot.cli import Plot
from .vasp.cli import Vasp

App = Plot | Vasp

app = tyro.cli(
    App,
    config=[
        tyro.conf.OmitSubcommandPrefixes,
        tyro.conf.OmitArgPrefixes,
    ],
)  # ty:ignore[no-matching-overload]
