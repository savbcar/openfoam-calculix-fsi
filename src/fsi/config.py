from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GeometryConfig:
    length_m: float
    width_m: float
    thickness_m: float
    shell_ny: int
    shell_nz: int


@dataclass(frozen=True)
class MaterialConfig:
    youngs_modulus_pa: float
    poisson_ratio: float


@dataclass(frozen=True)
class FluidConfig:
    density_kg_m3: float
    dynamic_viscosity_pa_s: float
    velocity_m_s: float


@dataclass(frozen=True)
class MappingConfig:
    method: str
    normal_threshold: float
    max_force_error_pct: float
    max_moment_error_pct: float


@dataclass(frozen=True)
class SyntheticConfig:
    source_ny: int
    source_nz: int
    pressure_scale_pa: float


@dataclass(frozen=True)
class CalculixConfig:
    executable: str
    job_name: str
    pressure_sign: float


@dataclass(frozen=True)
class ProjectConfig:
    geometry: GeometryConfig
    material: MaterialConfig
    fluid: FluidConfig
    mapping: MappingConfig
    synthetic: SyntheticConfig
    calculix: CalculixConfig


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    if name not in data or not isinstance(data[name], dict):
        raise ValueError(f"Missing configuration section: {name}")
    return data[name]


def load_config(path: str | Path) -> ProjectConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return ProjectConfig(
        geometry=GeometryConfig(**_section(raw, "geometry")),
        material=MaterialConfig(**_section(raw, "material")),
        fluid=FluidConfig(**_section(raw, "fluid")),
        mapping=MappingConfig(**_section(raw, "mapping")),
        synthetic=SyntheticConfig(**_section(raw, "synthetic")),
        calculix=CalculixConfig(**_section(raw, "calculix")),
    )
