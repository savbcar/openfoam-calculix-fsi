from __future__ import annotations

from pathlib import Path

from .calculix import write_calculix_input
from .config import ProjectConfig
from .conservation import conservation_metrics, mapped_resultant, surface_resultant_on_structure
from .geometry import structured_shell_mesh
from .io import write_mapping_csv, write_surface_csv
from .mapping import map_pressure
from .plots import plot_conservation, plot_convergence, plot_deflection, plot_pressure_mapping
from .report import write_report
from .structural import (
    line_load_from_mapping,
    root_bending_stress,
    solve_euler_bernoulli_cantilever,
)
from .synthetic import synthetic_surface


def run_synthetic_demo(cfg: ProjectConfig, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    geometry = cfg.geometry
    material = cfg.material
    synthetic_cfg = cfg.synthetic

    shell = structured_shell_mesh(
        geometry.length_m,
        geometry.width_m,
        geometry.shell_ny,
        geometry.shell_nz,
    )
    surface = synthetic_surface(
        geometry.length_m,
        geometry.width_m,
        geometry.thickness_m,
        synthetic_cfg.source_ny,
        synthetic_cfg.source_nz,
        synthetic_cfg.pressure_scale_pa,
    )
    mapping = map_pressure(
        surface,
        shell,
        cfg.mapping.method,
        cfg.mapping.normal_threshold,
    )
    cfd_resultant = surface_resultant_on_structure(surface)
    mapped_load_resultant = mapped_resultant(mapping)
    metrics = conservation_metrics(cfd_resultant, mapped_load_resultant)

    line_load = line_load_from_mapping(
        mapping,
        geometry.shell_ny,
        geometry.shell_nz,
        geometry.width_m,
    )
    beam = solve_euler_bernoulli_cantilever(
        line_load,
        geometry.length_m,
        material.youngs_modulus_pa,
        geometry.width_m,
        geometry.thickness_m,
    )
    stress = root_bending_stress(
        beam["root_moment_nm"],
        geometry.width_m,
        geometry.thickness_m,
    )

    write_surface_csv(out / "cfd_surface.csv", surface)
    write_mapping_csv(out / "mapped_pressure.csv", mapping)
    write_calculix_input(
        out / "calculix" / "panel.inp",
        shell,
        mapping,
        geometry.thickness_m,
        material.youngs_modulus_pa,
        material.poisson_ratio,
        cfg.calculix.pressure_sign,
    )
    plot_pressure_mapping(surface, mapping, out / "figures" / "pressure_mapping.png")
    plot_deflection(
        beam["y_m"],
        beam["deflection_m"],
        out / "figures" / "beam_reference_deflection.png",
    )
    plot_conservation(metrics, out / "figures" / "conservation.png")

    convergence: list[dict[str, float]] = []
    for ny, nz in [(9, 4), (18, 8), (36, 16), (72, 32)]:
        source = synthetic_surface(
            geometry.length_m,
            geometry.width_m,
            geometry.thickness_m,
            ny,
            nz,
            synthetic_cfg.pressure_scale_pa,
        )
        mapped = map_pressure(
            source,
            shell,
            cfg.mapping.method,
            cfg.mapping.normal_threshold,
        )
        source_metrics = conservation_metrics(
            surface_resultant_on_structure(source),
            mapped_resultant(mapped),
        )
        convergence.append(
            {
                "source_faces": float(len(source.areas)),
                "force_error_pct": source_metrics["force_x_error_pct"],
                "moment_error_pct": source_metrics["root_moment_z_error_pct"],
            }
        )
    plot_convergence(convergence, out / "figures" / "mapping_convergence.png")

    payload = {
        "mode": "synthetic_verification",
        "conservation": metrics,
        "structural_reference": {
            "tip_deflection_m": beam["tip_deflection_m"],
            "root_shear_n": beam["root_shear_n"],
            "root_moment_nm": beam["root_moment_nm"],
            "root_bending_stress_pa": stress,
        },
        "mapping_convergence": convergence,
        "acceptance": {
            "max_force_error_pct": cfg.mapping.max_force_error_pct,
            "max_moment_error_pct": cfg.mapping.max_moment_error_pct,
            "force_pass": metrics["force_x_error_pct"] <= cfg.mapping.max_force_error_pct,
            "moment_pass": (
                metrics["root_moment_z_error_pct"] <= cfg.mapping.max_moment_error_pct
            ),
        },
    }
    write_report(out, payload)
    return payload
