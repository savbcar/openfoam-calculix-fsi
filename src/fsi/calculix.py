from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import numpy as np

from .geometry import root_node_ids
from .types import MappingResult, ShellMesh


def write_calculix_input(
    path: str | Path,
    mesh: ShellMesh,
    mapping: MappingResult,
    thickness: float,
    youngs: float,
    poisson: float,
    pressure_sign: float = 1.0,
) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    roots = root_node_ids(mesh)
    lines = [
        "** OpenFOAM -> CalculiX one-way FSI generated deck",
        "** Units: N, m, Pa",
        "*HEADING",
        "Cantilever panel under mapped CFD pressure",
        "*NODE, NSET=NALL",
    ]
    for i, xyz in enumerate(mesh.nodes, start=1):
        lines.append(f"{i}, {xyz[0]:.12g}, {xyz[1]:.12g}, {xyz[2]:.12g}")
    lines += ["*ELEMENT, TYPE=S4, ELSET=EALL"]
    for eid, conn in zip(mesh.element_ids, mesh.elements, strict=True):
        n = conn + 1
        lines.append(f"{int(eid)}, {n[0]}, {n[1]}, {n[2]}, {n[3]}")
    lines += [
        "*MATERIAL, NAME=ALUMINIUM",
        "*ELASTIC",
        f"{youngs:.12g}, {poisson:.12g}",
        "*SHELL SECTION, ELSET=EALL, MATERIAL=ALUMINIUM",
        f"{thickness:.12g}",
        "*NSET, NSET=ROOT",
        ", ".join(str(int(n)) for n in roots),
        "*BOUNDARY",
        "ROOT, 1, 6, 0.0",
        "*STEP",
        "*STATIC",
        "*DLOAD",
    ]
    for eid, p in zip(mapping.element_ids, mapping.delta_p_pa, strict=True):
        lines.append(f"{int(eid)}, P, {pressure_sign * float(p):.12g}")
    lines += [
        "*NODE PRINT, NSET=NALL",
        "U",
        "RF",
        "*EL PRINT, ELSET=EALL",
        "S",
        "*NODE FILE",
        "U, RF",
        "*EL FILE",
        "S",
        "*END STEP",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_calculix(inp_path: str | Path, executable: str = "ccx") -> subprocess.CompletedProcess[str]:
    inp = Path(inp_path).resolve()
    exe = shutil.which(executable)
    if exe is None:
        raise FileNotFoundError(f"CalculiX executable '{executable}' not found on PATH")
    job = inp.stem
    return subprocess.run([exe, "-i", job], cwd=inp.parent, text=True, capture_output=True, check=True)


def parse_dat_displacements(path: str | Path) -> dict[int, np.ndarray]:
    """Parse the common CalculiX .dat displacement table.

    CalculiX textual output varies slightly by version/options; this parser looks
    for a 'displacements' heading and then accepts rows: node ux uy uz.
    """
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    rows: dict[int, np.ndarray] = {}
    active = False
    num = re.compile(r"^\s*(\d+)\s+([-+0-9.eEdD]+)\s+([-+0-9.eEdD]+)\s+([-+0-9.eEdD]+)\s*$")
    for line in text.splitlines():
        low = line.lower()
        if "displacements" in low:
            active = True
            continue
        if active:
            m = num.match(line)
            if m:
                vals = [float(x.replace("D", "E").replace("d", "e")) for x in m.groups()[1:]]
                rows[int(m.group(1))] = np.asarray(vals)
            elif rows and line.strip() == "":
                break
    return rows


def parse_dat_stresses(path: str | Path) -> list[dict[str, float]]:
    """Parse common *EL PRINT, S integration-point stress rows.

    Expected numeric row layout after a heading containing ``stresses`` is
    ``element integration_point sxx syy szz sxy sxz syz``. Extra columns are
    ignored. A von-Mises value is calculated from the six tensor components.
    """
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    rows: list[dict[str, float]] = []
    active = False
    for line in text.splitlines():
        low = line.lower()
        if "stresses" in low:
            active = True
            continue
        if not active:
            continue
        parts = line.replace("D", "E").replace("d", "e").split()
        if len(parts) >= 8:
            try:
                eid = int(parts[0])
                ip = int(parts[1])
                sxx, syy, szz, sxy, sxz, syz = map(float, parts[2:8])
            except ValueError:
                continue
            vm = (
                0.5
                * (
                    (sxx - syy) ** 2
                    + (syy - szz) ** 2
                    + (szz - sxx) ** 2
                    + 6.0 * (sxy**2 + sxz**2 + syz**2)
                )
            ) ** 0.5
            rows.append(
                {
                    "element": float(eid),
                    "integration_point": float(ip),
                    "sxx": sxx,
                    "syy": syy,
                    "szz": szz,
                    "sxy": sxy,
                    "sxz": sxz,
                    "syz": syz,
                    "von_mises_pa": vm,
                }
            )
        elif rows and not line.strip():
            break
    return rows
