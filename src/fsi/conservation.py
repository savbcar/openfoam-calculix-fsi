from __future__ import annotations

import numpy as np

from .types import MappingResult, Resultant, SurfaceData


def surface_resultant_on_structure(surface: SurfaceData, origin=(0.0, 0.0, 0.0)) -> Resultant:
    """Pressure resultant exerted by fluid on the immersed structure.

    OpenFOAM boundary normals point outward from the fluid domain. On an immersed
    wall that direction points into the solid, so pressure force on the solid is
    +p*n_fluid*A.
    """
    forces = surface.pressure_pa[:, None] * surface.normals * surface.areas[:, None]
    r = surface.centres - np.asarray(origin, dtype=float)
    return Resultant(force_n=forces.sum(axis=0), moment_nm=np.cross(r, forces).sum(axis=0))


def mapped_resultant(mapping: MappingResult, origin=(0.0, 0.0, 0.0)) -> Resultant:
    forces = np.zeros((len(mapping.areas), 3), dtype=float)
    forces[:, 0] = mapping.delta_p_pa * mapping.areas
    r = mapping.centroids - np.asarray(origin, dtype=float)
    return Resultant(force_n=forces.sum(axis=0), moment_nm=np.cross(r, forces).sum(axis=0))


def relative_error_pct(reference: float, value: float) -> float:
    if abs(reference) < 1e-14:
        return 0.0 if abs(value) < 1e-14 else float("inf")
    return abs(value - reference) / abs(reference) * 100.0


def conservation_metrics(cfd: Resultant, mapped: Resultant) -> dict[str, float]:
    return {
        "force_x_cfd_n": float(cfd.force_n[0]),
        "force_x_mapped_n": float(mapped.force_n[0]),
        "force_x_error_pct": relative_error_pct(float(cfd.force_n[0]), float(mapped.force_n[0])),
        "root_moment_z_cfd_nm": float(cfd.moment_nm[2]),
        "root_moment_z_mapped_nm": float(mapped.moment_nm[2]),
        "root_moment_z_error_pct": relative_error_pct(float(cfd.moment_nm[2]), float(mapped.moment_nm[2])),
        "force_vector_error_pct": float(np.linalg.norm(mapped.force_n - cfd.force_n) / max(np.linalg.norm(cfd.force_n), 1e-14) * 100.0),
    }
