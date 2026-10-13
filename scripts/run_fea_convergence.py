#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import numpy as np

from fsi.calculix import (
    parse_dat_displacements,
    parse_dat_stresses,
    run_calculix,
    write_calculix_input,
)
from fsi.config import load_config
from fsi.geometry import structured_shell_mesh
from fsi.io import read_surface_csv
from fsi.mapping import map_pressure


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CalculiX shell mesh-convergence study")
    parser.add_argument("--surface", required=True)
    parser.add_argument("--config", default="config/baseline.yaml")
    parser.add_argument("--out", default="results/fea_convergence")
    args = parser.parse_args()

    if shutil.which("ccx") is None:
        raise SystemExit("ccx not found on PATH")

    cfg = load_config(args.config)
    geometry = cfg.geometry
    material = cfg.material
    surface = read_surface_csv(args.surface)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for label, ny, nz in [("coarse", 15, 6), ("medium", 30, 12), ("fine", 60, 24)]:
        case = out / label
        case.mkdir(parents=True, exist_ok=True)
        mesh = structured_shell_mesh(geometry.length_m, geometry.width_m, ny, nz)
        mapped = map_pressure(
            surface,
            mesh,
            cfg.mapping.method,
            cfg.mapping.normal_threshold,
        )
        input_path = case / "panel.inp"
        write_calculix_input(
            input_path,
            mesh,
            mapped,
            geometry.thickness_m,
            material.youngs_modulus_pa,
            material.poisson_ratio,
            cfg.calculix.pressure_sign,
        )
        run_calculix(input_path, cfg.calculix.executable)
        displacements = parse_dat_displacements(case / "panel.dat")
        tip_nodes = np.flatnonzero(np.isclose(mesh.nodes[:, 1], geometry.length_m)) + 1
        tip_ux = [displacements[int(node)][0] for node in tip_nodes if int(node) in displacements]
        stresses = parse_dat_stresses(case / "panel.dat")
        rows.append(
            {
                "mesh": label,
                "ny": ny,
                "nz": nz,
                "elements": ny * nz,
                "tip_ux_max_m": max(map(abs, tip_ux)) if tip_ux else float("nan"),
                "max_integration_point_von_mises_pa": max(
                    (row["von_mises_pa"] for row in stresses),
                    default=float("nan"),
                ),
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
