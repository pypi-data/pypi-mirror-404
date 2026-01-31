import itertools
from typing import TYPE_CHECKING, Annotated, Literal

import tyro
from msgspec import Struct, field

if TYPE_CHECKING:
    from ..dataread import VaspData

ORBITALS_STR_ALL = (
    "s py pz px dxy dyz dz2 dxz dx2-y2 fy3x2 fxyz fyz2 fz3 fxz2 fzx2 fx3".split()
)

ORBITAL_GROUPS = {
    "p": ["px", "py", "pz"],
    "d": ["dxy", "dyz", "dz2", "dxz", "dx2-y2"],
    "f": ["fy3x2", "fxyz", "fyz2", "fz3", "fxz2", "fzx2", "fx3"],
}

ORBITAL_NUMBERS = {
    "p": ["p1", "p2", "p3"],
    "d": ["d4", "d5", "d6", "d7", "d8"],
    "f": ["f9", "f10", "f11", "f12", "f13", "f14", "f15"],
}


class Group(Struct):
    atoms_dict: dict[str, list[int]]
    orbitals_dict: dict[str, list[int]]
    colors: list[str]
    index: int = 0
    pairs: set[tuple[int, int]] = field(default_factory=set)
    atoms: list[list[int]] = field(default_factory=list)
    orbitals: list[list[int]] = field(default_factory=list)
    atoms_label_list: list[str] = field(default_factory=list)
    orbitals_label_list: list[str] = field(default_factory=list)
    label: str = ""

    def __iter__(self):
        return iter((list(zip(self.atoms, self.orbitals))))

    def __len__(self):
        return len(self.atoms)

    def _check_unique(self, name: str, lst: list[int]):
        import sys

        from wuxctools.utils import log

        if len(lst) != len(set(lst)):
            log.error(
                f"[red]{lst}[/red] expands to {lst} which contains duplicate {name} indices."
            )
            sys.exit(1)

    def add(self, atoms: list[int], orbitals: list[int]):
        self._check_unique("atom", atoms)
        self._check_unique("orbital", orbitals)
        self._get_atoms_label(atoms, orbitals)
        self.atoms.append(atoms)
        self.orbitals.append(orbitals)

    def check(self):
        import sys

        from wuxctools.utils import log

        for atoms_list, orbitals_list in zip(self.atoms, self.orbitals):
            for a, o in itertools.product(atoms_list, orbitals_list):
                pair = (a, o)
                if pair in self.pairs:
                    log.error(
                        f"Duplicate projection pair detected: atom={a}, orbital={o}. "
                        "Please check your projection rules."
                    )
                    sys.exit(1)
                self.pairs.add(pair)
        log_str = f"projected atoms and orbitals of your choice {self.index} is\n"

        label_list: list[str] = []
        for a, o in zip(self.atoms_label_list, self.orbitals_label_list):
            log_str += f"orbitals [yellow]{o}[/yellow] for atoms [yellow]{a}[/yellow]\n"
            label_list.append(f"{a}:{o}")
        self.label = "+".join(label_list)

        log.info(log_str)

    def _coverage_label(
        self, covered_indices: list[int], index_dict: dict[str, list[int]]
    ) -> str:
        result: list[str] = []

        for elem, idxs in index_dict.items():
            if not elem[0].isalpha():
                continue
            covered = sorted(i for i in idxs if i in covered_indices)
            if not covered:
                continue

            if len(covered) == len(idxs):
                result.append(elem)
            else:
                result.extend(list(f"{elem}{i}" for i in covered))

        cleaned = result[:]

        for group, subs in ORBITAL_GROUPS.items():
            has_group = group in result

            if has_group:
                cleaned = [x for x in cleaned if x not in subs]
            else:
                cleaned = [x for x in cleaned if x not in ORBITAL_NUMBERS[group]]
        return "+".join(cleaned)

    def _get_atoms_label(self, atoms: list[int], orbitals: list[int]):
        atoms_label = self._coverage_label(atoms, self.atoms_dict)
        orbitals_label = self._coverage_label(orbitals, self.orbitals_dict)
        self.atoms_label_list.append(atoms_label)
        self.orbitals_label_list.append(orbitals_label)


class ProParams(Struct):
    pmode: Literal[1, 2, 3] = 1

    project: Annotated[
        tyro.conf.UseAppendAction[list[list[str]]], tyro.conf.arg(aliases=["-p"])
    ] = field(default_factory=lambda: [])
    """
    Add a projection rule. Can be used multiple times.
    ATOMS:
      Atom selectors (comma-separated):
        SYMBOL        e.g. Mn, Bi
        SYMBOL+INDEX  e.g. Bi3   (3rd Bi)
        INDEX         e.g. 0, 1, 12
    ORBITS:
      Orbital selectors (comma-separated):
        Names: s, p, d, f, px, py, pz, dxy, dxz, dyz, dx2-y2, dz2
        Or indices: 0,1,2,3... (code-dependent ordering)
    Examples:
      -p Mn:p,d            (Mn: p + d)
      -p Bi3:p             (Bi3: p)
      -p Bi:1,2,3          (Bi atom #1,2,3: orbital index 1/2/3)
      -p 0,1:dxy           (atom 0 & 1: dxy)            
    """

    def parse(self, data: "VaspData", colors: list[str]) -> list[Group]:
        import sys

        from wuxctools.utils import log

        atoms_dict: dict[str, list[int]] = {}
        for i, symbol in enumerate(data.symbols):
            atoms_dict.setdefault(symbol, []).append(i)
            atoms_dict.setdefault(str(i), []).append(i)

        orbitals_dict: dict[str, list[int]] = {}
        for i, orbital in enumerate(ORBITALS_STR_ALL[0 : data.orbital_num]):
            orbitals_dict.setdefault(orbital, []).append(i)
            orbitals_dict.setdefault(str(i), []).append(i)
            if "p" in orbital:
                orbitals_dict.setdefault("p", []).append(i)
            if "d" in orbital:
                orbitals_dict.setdefault("d", []).append(i)
            if "f" in orbital:
                orbitals_dict.setdefault("f", []).append(i)

        def lookup(d: dict[str, list[int]], key: str, kind: str) -> list[int]:
            try:
                return d[key]
            except KeyError:
                log.error(
                    f"Invalid {kind!s} selector: {key!r}, you can only choose {kind!s} in {sorted(d.keys())}"
                )
                sys.exit(1)

        result: list[Group] = []
        for index, subpro in enumerate(self.project):
            group = Group(atoms_dict, orbitals_dict, colors, index)
            for subgroup in subpro:
                atoms, orbitals = subgroup.split(":")

                atoms_list = [
                    idx
                    for sel in atoms.split(",")
                    for idx in lookup(atoms_dict, sel, "atom")
                ]

                orbitals_list = [
                    idx
                    for sel in orbitals.split(",")
                    for idx in lookup(orbitals_dict, sel, "orbital")
                ]
                group.add(atoms_list, orbitals_list)
            group.check()

            result.append(group)
        return result
