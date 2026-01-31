from rich.console import Console
from rich.panel import Panel

from .plot import figure_context, get_fig_ax, plot_series, set_style

__all__ = ["get_fig_ax", "plot_series", "set_style", "figure_context"]

console = Console()


class SimplePanelLogger:
    def __init__(self, name: str):
        self.name = name

    def log(self, level: str, message: str):
        panel = Panel(
            message,
            title=f"{self.name}: {level}",
            border_style={"INFO": "blue", "WARNING": "yellow", "ERROR": "red"}.get(
                level, "white"
            ),
            highlight=True,
        )
        console.print(panel)

    def info(self, msg: str):
        self.log("INFO", msg)

    def warning(self, msg: str):
        self.log("WARNING", msg)

    def error(self, msg: str):
        self.log("ERROR", msg)


# 使用
log = SimplePanelLogger("wuxctools")


def _try_import(module_name: str):
    try:
        module = __import__(module_name)
        return module, True
    except ImportError:
        return None, False


pymatgen, HAS_PYMATGEN = _try_import("pymatgen")
