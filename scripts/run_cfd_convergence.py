#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
from pathlib import Path

from fsi.config import load_config
from fsi.conservation import conservation_metrics, mapped_resultant, surface_resultant_on_structure
from fsi.geometry import structured_shell_mesh
from fsi.mapping import map_pressure
from fsi.openfoam import extract_patch_pressure

PROFILES = {
    "coarse": ((48, 24, 24), (2, 3)),
    "medium": ((72, 36, 36), (3, 4)),
    "fine": ((96, 48, 48), (4, 5)),
}


def patch_case(case: Path, cells: tuple[int, int, int], levels: tuple[int, int]) -> None:
    block_mesh = case / "system/blockMeshDict"
    text = block_mesh.read_text(encoding="utf-8")
    text = re.sub(
        r"hex \(0 1 2 3 4 5 6 7\) \(\d+ \d+ \d+\)",
        f"hex (0 1 2 3 4 5 6 7) ({cells[0]} {cells[1]} {cells[2]})",
        text,
    )
    block_mesh.write_text(text, encoding="utf-8")

    snappy = case / "system/snappyHexMeshDict"
    text = snappy.read_text(encoding="utf-8")
    text = re.sub(
        r"panel \{ level \(\d+ \d+\); \}",
        f"panel {{ level ({levels[0]} {levels[1]}); }}",
        text,
    )
    snappy.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpenFOAM-13 CFD mesh-convergence campaign")
    parser.add_argument("--config", default="config/baseline.yaml")
    parser.add_argument("--out", default="results/cfd_convergence")
    args = parser.parse_args()

    if shutil.which("foamRun") is None:
        raise SystemExit("foamRun not found; source /opt/openfoam13/etc/bashrc first")

    cfg = load_config(args.config)
    geometry = cfg.geometry
    base = Path("cases/openfoam13/panel")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    shell = structured_shell_mesh(
        geometry.length_m,
        geometry.width_m,
        geometry.shell_ny,
        geometry.shell_nz,
    )

    rows: list[dict] = []
    for label, (cells, levels) in PROFILES.items():
        case = out / f"case_{label}"
        if case.exists():
            shutil.rmtree(case)
        shutil.copytree(base, case)
        patch_case(case, cells, levels)
        subprocess.run(["bash", "./Allrun"], cwd=case, check=True)
        surface = extract_patch_pressure(
            case,
            "panel",
            cfg.fluid.density_kg_m3,
            "latest",
        )
        mapped = map_pressure(
            surface,
            shell,
            cfg.mapping.method,
            cfg.mapping.normal_threshold,
        )
        metrics = conservation_metrics(
            surface_resultant_on_structure(surface),
            mapped_resultant(mapped),
        )
        rows.append(
            {
                "mesh": label,
                "background_cells": str(cells),
                "surface_levels": str(levels),
                **metrics,
            }
        )

    summary = out / "summary.csv"
    with summary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(summary)


if __name__ == "__main__":
    main()
