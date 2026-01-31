import inspect
import itertools
from functools import cached_property
from pathlib import Path

import matplotlib as mpl
import numpy as np
import numpy.typing as npt
from matplotlib.artist import Artist
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

from wuxctools.utils import HAS_PYMATGEN, get_fig_ax, log

from ..dataread import VaspData, read_vasp_file
from . import Band
from .parsepro import Group


class BandPlot:
    def __init__(self, params: Band, data: VaspData):
        self.params = params
        self.fig, self.ax = get_fig_ax()
        self.data = data

        if isinstance(self.params.efermi, str):
            efermi: float = read_vasp_file(Path(self.params.efermi)).fermi
            self.plot_fermi = efermi
        elif self.params.efermi is not None:
            self.plot_fermi = self.params.efermi
        else:
            self.plot_fermi = self.data.fermi

        self.eigenvalues = (
            np.sort(self.data.eigenvalues, axis=2)
            if self.params.fix_order
            else self.data.eigenvalues
        )

        self.handles: list[Artist] = []

        self.set_style()
        self.gap = self.get_gap()
        if self.params.pro.project == []:
            self.plot_band()
        else:
            self.groups = self.params.pro.parse(
                self.data, self.params.basefigset.colors
            )
            self.plot_proband()

        if self.params.legend:
            self.ax.legend(handles=self.handles, loc="best")

        if self.params.export:
            self.export()
            ...

    @cached_property
    def xlist(self) -> list[float]:
        kpoints_real = [
            np.dot(kpoint, self.data.rec_cell) for kpoint in self.data.kpoints
        ]

        length = (
            np.linalg.norm(kpoint1 - kpoint2)
            for kpoint1, kpoint2 in zip(
                kpoints_real, kpoints_real[0:1] + list(kpoints_real)[:-1]
            )
        )
        return [float(i) * np.pi * 2 for i in itertools.accumulate(length)]

    @cached_property
    def k_tick_labels(self) -> dict[float, str]:
        def symbol_to_latex(symbol: str) -> str:
            if not symbol[0].isalpha() and not (
                symbol.startswith("$") and symbol.endswith("$")
            ):
                return f"${symbol}$"
            return symbol

        def handle_kpoint_labels(klist: list[str]) -> list[str]:
            result: list[str] = []
            result.append(symbol_to_latex(klist[0]))
            for k1, k2 in zip(klist[2::2], klist[1:-1:2]):
                k1_new, k2_new = symbol_to_latex(k1), symbol_to_latex(k2)
                if k1_new == k2_new:
                    result.append(k1_new)
                else:
                    result.append(f"{k2_new}/{k1_new}")
            result.append(klist[-1])
            return result

        def get_k_labels(
            ks: list[np.ndarray],
            labels_dict: dict[str, tuple[float, float, float]] = {},
            default_labels_dict: dict[str, tuple[float, float, float]] = {
                r"\Gamma": (0.0, 0.0, 0.0),
                "K": (1 / 3, 1 / 3, 0.0),
                "M": (0.5, 0.0, 0.0),
            },
        ):
            """Assign labels to K-points based on nearest distance."""
            result: list[str] = []
            if labels_dict == {}:
                if HAS_PYMATGEN:
                    log.info(
                        "No label dictionary provided. Attempting to infer k-point labels using pymatgen..."
                    )
                    from pymatgen.core import (  # pyright: ignore[reportMissingTypeStubs]
                        Lattice,
                        Structure,
                    )
                    from pymatgen.symmetry.bandstructure import (  # pyright: ignore[reportMissingTypeStubs]
                        HighSymmKpath,  # pyright: ignore[reportMissingTypeStubs]
                    )

                    lattice = Lattice(self.data.real_cell)

                    structure = Structure(
                        lattice, self.data.symbols, self.data.positions
                    )

                    try:
                        kpath = HighSymmKpath(structure).kpath
                        raw_dict: dict[str, np.ndarray] = kpath["kpoints"]  # pyright: ignore[reportUnknownVariableType, reportOptionalSubscript]
                        labels_dict = {
                            label: (
                                float(coords[0]),  # pyright: ignore[reportUnknownArgumentType]
                                float(coords[1]),  # pyright: ignore[reportUnknownArgumentType]
                                float(coords[2]),  # pyright: ignore[reportUnknownArgumentType]
                            )
                            for label, coords in raw_dict.items()  # pyright: ignore[reportUnknownVariableType]
                        }
                    except Exception:
                        log.warning(
                            "Pymatgen failed to determine k-point labels. Falling back to default labels."
                        )
                        labels_dict = default_labels_dict
                else:
                    log.warning("No label dictionary provided. Using  default  labels.")
                    labels_dict = default_labels_dict

            log.warning(
                f"Assigning labels based on k-point distance:\n {labels_dict} \n Results may be inaccurate."
            )

            for k in ks:
                nearest_label: str = min(
                    labels_dict.keys(),
                    key=lambda label: float(
                        np.linalg.norm(k - np.asarray(labels_dict[label]))
                    ),
                )
                result.append(symbol_to_latex(nearest_label))
            return result

        k_rec = list(self.data.kpoints[:: self.data.kpoints_division])
        k_rec.append(self.data.kpoints[-1])

        k_x = ([0.0] + self.xlist)[:: self.data.kpoints_division]
        k_labels = (
            get_k_labels(k_rec)
            if self.data.labels_kpoints is None
            else handle_kpoint_labels(self.data.labels_kpoints)
        )

        return dict(zip(k_x, k_labels))

    @cached_property
    def ylist(self) -> npt.NDArray[np.floating]:
        return self.eigenvalues - self.plot_fermi

    def get_gap(
        self,
        vbms: list[int] | None = None,
    ) -> list[float]:
        def is_metal_or_vbm(ylist: np.ndarray) -> bool | int:
            nbands = ylist.shape[1]
            extremum = np.array(
                [[ylist[:, n].min(), ylist[:, n].max()] for n in range(nbands)]
            )

            if (extremum[:, 0] * extremum[:, 1]).min() > 0:
                maxs = extremum[:, 1]
                vbm = int(np.count_nonzero(abs(maxs) - maxs))
                return vbm
            else:
                return True

        def get_kpoints_vbm(ylist: np.ndarray, kpoints: np.ndarray):
            index = np.where(ylist == ylist.max())
            return kpoints[index]

        def get_kpoints_cbm(ylist: np.ndarray, kpoints: np.ndarray):
            index = np.where(ylist == ylist.min())
            return kpoints[index]

        gaps: list[float] = []
        log_str = (
            inspect.cleandoc(
                f"""
            Fermi level used for plotting is {self.plot_fermi:.6f} eV. (read from specified file: {Path(self.params.efermi)}).
            Fermi level in the plot file is {self.data.fermi:.6f} eV.
            """
            )
            if isinstance(self.params.efermi, str)
            else f"Fermi level used for plotting is {self.plot_fermi:.6f} eV\n"
        )

        for i, spin in enumerate(self.ylist):
            vbm = is_metal_or_vbm(spin) if vbms is None else vbms[i]
            log_str += f"[yellow]{'=' * 30} {i + 1}th spin {'=' * 30} [/yellow]\n"
            if vbm is True:
                gaps.append(0.0)
                log_str += "Fermi level intersects energy bands, [blue]Metal[/blue]\n"
            else:
                e_vbm = float(spin[:, vbm - 1].max())
                k_vbm = get_kpoints_vbm(spin[:, vbm - 1], self.data.kpoints)
                vbm_energy = spin[:, vbm - 1].max() + self.data.fermi
                cbm_energy = spin[:, vbm].min() + self.data.fermi
                e_cbm = float(spin[:, vbm].min())
                k_cbm = get_kpoints_cbm(spin[:, vbm], self.data.kpoints)
                gap = e_cbm - e_vbm
                if gap <= 0:
                    gaps.append(0.0)
                    log_str += (
                        "Fermi level intersects energy bands, [blue]Metal[/blue]\n"
                    )

                else:
                    gaps.append(gap)
                    log_str += f"vbm locates at{k_vbm} of [red]{vbm}th[/red] band, vbm energy is [orange1]{vbm_energy:.6f} eV[/orange1]\n"

                    log_str += f"cbm locates at {k_cbm} of [red]{vbm + 1}th[/red] band, cbm energy is [orange1]{cbm_energy:.6f}[/orange1] eV\n"
                    log_str += f"band gap is {gap}\n"
        log.info(log_str)

        return gaps

    def set_style(self):
        self.params.basefigset.xrange = (min(self.xlist), max(self.xlist))
        k_ticks = sorted(self.k_tick_labels.keys())
        self.params.basefigset.xticks = k_ticks
        self.params.basefigset.xticklabels = [self.k_tick_labels[k] for k in k_ticks]

        y_major_tick_size = mpl.rcParams["ytick.major.size"]
        self.ax.axhline(
            0,
            ls=(0, (y_major_tick_size, y_major_tick_size)),
            c="black",
            lw=mpl.rcParams["ytick.major.width"],
            zorder=0,
        )

        for i in k_ticks:
            self.ax.axvline(
                i, c="lightgrey", zorder=1, lw=mpl.rcParams["ytick.major.width"]
            )

    @cached_property
    def lc_list(self) -> list[LineCollection]:
        x = np.array(self.xlist)  # (K,)
        x_mid = (x[:-1] + x[1:]) / 2  # (K-1,)
        x_left, x_right = np.r_[x[0], x_mid], np.r_[x_mid, x[-1]]  # (K,)
        x_left2 = np.broadcast_to(x_left[None, :, None], self.ylist.shape)  # (S,K,B)
        x_right2 = np.broadcast_to(x_right[None, :, None], self.ylist.shape)  # (S,K,B)
        y_mid = (self.ylist[:, :-1, :] + self.ylist[:, 1:, :]) / 2  # (S, K-1, B)
        y_left = np.concatenate([self.ylist[:, 0:1, :], y_mid], axis=1)  # (S, K, B)
        y_right = np.concatenate([y_mid, self.ylist[:, -1:, :]], axis=1)  # (S, K, B)

        segments_list = [
            np.stack(
                [
                    np.stack([x_left2[i], x_right2[i]], axis=-1),  # (S,K,B,2)
                    np.stack([y_left[i], y_right[i]], axis=-1),  # (S,K,B,2)
                ],
                axis=-1,
            ).reshape(-1, 2, 2)
            for i in range(self.ylist.shape[0])
        ]
        lc_list = [
            LineCollection(list(segments), rasterized=True)
            for segments in segments_list
        ]

        for lc in lc_list:
            lc.set_capstyle("round")

        return lc_list

    def plot_band(self):
        labels = ["↑", "↓"] if self.params.labels is None else self.params.labels
        lc_list = (
            [self.lc_list[self.params.spin]]
            if self.params.spin is not None
            else self.lc_list
        )
        for lc, color, label in zip(lc_list, self.params.basefigset.colors, labels):
            self.ax.add_collection(lc)
            lc.set_color(color)
            lc.set_zorder(2)
            self.handles.append(Line2D([], [], c=color, label=label))

    def export(self):
        filenames = ["band_up.txt", "band_down.txt"]
        for i, eigen in enumerate(self.eigenvalues):
            self.export_band(filenames[i], eigen)
        # self.save_pro_band()

    def export_band(
        self,
        filename: str,
        eigen: npt.NDArray[np.floating],
        weight: npt.NDArray[np.floating] | None = None,
    ):
        with open(filename, "w") as f:
            for i in range(eigen.shape[1]):  # 遍历每条能带
                if weight is None:
                    data = np.column_stack((self.xlist, eigen[:, i]))
                else:
                    data = np.column_stack((self.xlist, eigen[:, i], weight[:, i]))

                np.savetxt(f, data, fmt="%.10f")
                f.write("\n")

    def save_pro_band(self):
        proarray_list = [self.get_proarray(group) for group in self.groups]
        spins: list[int] = []
        if self.params.spin is None:
            if len(self.eigenvalues) == 1:
                spins = [0]
            elif len(self.eigenvalues) == 2:
                spins = [0, 1]
            elif len(self.eigenvalues) == 4:
                spins[0]
        else:
            spin = [self.params.spin]

        for spin in spins:
            eigen = self.eigenvalues[int(spin)]

            for i, pro in enumerate(proarray_list):
                weight = pro[spin]
                self.export_band(f"fatband_spin{spin}_{i}.txt", eigen, weight)

    def get_proarray(self, group: Group) -> np.ndarray:
        if not group:
            raise ValueError

        proarray = np.add.reduce(
            [
                self.data.projected[:, atoms][:, :, orbitals].sum(axis=(1, 2))
                for atoms, orbitals in group
            ]
        )
        if self.params.spin is not None:
            proarray = proarray[self.params.spin : self.params.spin + 1]
        elif len(self.data.projected) == 2 and self.params.pro.pmode == 1:
            proarray[1] = -proarray[1]
        elif len(self.data.projected) == 2 and self.params.pro.pmode != 1:
            ...
        else:
            proarray = proarray[0:1, :, :]
        return proarray

    def plot_proband(self):
        if self.params.pro.pmode == 1:
            pass
            self.pband1()
        elif self.params.pro.pmode == 2:
            self.pband2()

    def pband1(self):
        proarray = self.get_proarray(self.groups[0])
        lc_array = proarray.reshape(-1)
        if proarray.shape[0] == 2:
            segments_list = [seg for lc in self.lc_list for seg in lc.get_segments()]
            lc = LineCollection(segments_list)
        else:
            lc = self.lc_list[0]

        lc.set_capstyle("round")
        lc.set_array(lc_array)
        self.ax.add_collection(lc)
        self.params.pro.heatparams(lc)

    def pband2(self):
        colors = iter(self.params.basefigset.colors)
        xlist = np.broadcast_to(np.array(self.xlist)[None, :, None], self.ylist.shape)

        pro_max = max(self.get_proarray(group).max() for group in self.groups)

        labels = (
            self.params.labels
            if self.params.labels
            else [group.label for group in self.groups]
        )

        for group, label in zip(self.groups, labels):
            proarray = self.get_proarray(group)
            color = next(colors)
            for x, y, z in zip(xlist, self.ylist, proarray):
                z_norm = z / pro_max
                alpha = np.power(z_norm, self.params.pro.alpha_gamma)

                if self.params.pro.fill == "hollow":
                    fc = "none"
                    ec = color
                    alpha = 1

                elif self.params.pro.fill == "solid":
                    fc = color
                    ec = "none"
                else:
                    fc = color
                    ec = fc
                self.ax.scatter(
                    x,
                    y,
                    s=z_norm * self.params.pro.scale,
                    fc=fc,
                    ec=ec,
                    alpha=alpha,
                    label=label,
                )

                self.handles.append(
                    Line2D([], [], c=color, marker="o", ls="", label=label)
                )
