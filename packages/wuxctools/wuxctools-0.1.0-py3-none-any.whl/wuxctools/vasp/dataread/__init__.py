from pathlib import Path

from .vaspdata import VaspData
from .vaspout import ReadVaspout
from .vasprun import ReadVasprun

__all__ = ["VaspData", "ReadVaspout", "ReadVasprun"]


def read_vasp_file(
    file: Path, vaspfileformat: str = "auto", auto_select_k: bool = False
) -> VaspData:
    if vaspfileformat == "auto":
        if file.suffix in [".h5", ".hdf5"]:
            return ReadVaspout(file, auto_select_k)
        elif file.suffix == ".xml":
            return ReadVasprun(file, auto_select_k)
        else:
            raise ValueError(
                f"Unsupported VASP file format: {file.suffix} for {file.name}"
            )
    elif vaspfileformat in ["h5", "hdf5"]:
        return ReadVaspout(file, auto_select_k)
    elif vaspfileformat == "xml":
        return ReadVasprun(file, auto_select_k)
    else:
        raise ValueError(f"Unsupported VASP file format: {vaspfileformat}")
