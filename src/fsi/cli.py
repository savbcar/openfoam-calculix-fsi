from __future__ import annotations

import argparse
import json
from pathlib import Path

from .calculix import write_calculix_input
from .config import load_config
from .geometry import structured_shell_mesh
from .io import read_surface_csv, write_mapping_csv, write_surface_csv
from .mapping import map_pressure
from .openfoam import extract_patch_pressure
from .pipeline import run_synthetic_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fsi-demo",
        description="OpenFOAM -> CalculiX one-way FSI demonstrator",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="run deterministic synthetic end-to-end verification")
    demo.add_argument("--config", default="config/baseline.yaml")
    demo.add_argument("--out", default="results/reference")

    extract = sub.add_parser(
        "extract-openfoam",
        help="extract a wall patch pressure field from an ASCII OpenFOAM case",
    )
    extract.add_argument("--case", required=True)
    extract.add_argument("--patch", default="panel")
    extract.add_argument("--time", default="latest")
    extract.add_argument("--density", type=float, default=1.2)
    extract.add_argument("--out", required=True)

    couple = sub.add_parser("couple", help="map a CFD surface CSV and write CalculiX input")
    couple.add_argument("--config", default="config/baseline.yaml")
    couple.add_argument("--surface", required=True)
    couple.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.cmd == "demo":
        payload = run_synthetic_demo(load_config(args.config), args.out)
        print(json.dumps(payload, indent=2))
        return

    if args.cmd == "extract-openfoam":
        surface = extract_patch_pressure(args.case, args.patch, args.density, args.time)
        write_surface_csv(args.out, surface)
        print(f"wrote {len(surface.areas)} faces to {args.out}")
        return

    if args.cmd == "couple":
        cfg = load_config(args.config)
        geometry = cfg.geometry
        material = cfg.material
        surface = read_surface_csv(args.surface)
        mesh = structured_shell_mesh(
            geometry.length_m,
            geometry.width_m,
            geometry.shell_ny,
            geometry.shell_nz,
        )
        mapping = map_pressure(
            surface,
            mesh,
            cfg.mapping.method,
            cfg.mapping.normal_threshold,
        )
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        write_mapping_csv(out / "mapped_pressure.csv", mapping)
        write_calculix_input(
            out / "panel.inp",
            mesh,
            mapping,
            geometry.thickness_m,
            material.youngs_modulus_pa,
            material.poisson_ratio,
            cfg.calculix.pressure_sign,
        )
        print(f"wrote {out / 'mapped_pressure.csv'} and {out / 'panel.inp'}")


if __name__ == "__main__":
    main()
