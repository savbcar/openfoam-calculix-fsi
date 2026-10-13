from __future__ import annotations

import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

from .types import MappingResult, ShellMesh, SurfaceData


def classify_faces(surface: SurfaceData, flow_direction=(1.0, 0.0, 0.0), threshold: float = 0.7):
    flow = np.asarray(flow_direction, dtype=float)
    flow /= np.linalg.norm(flow)
    dots = surface.normals @ flow
    # OpenFOAM wall normals point outward from the fluid domain (into an immersed solid).
    front = dots >= threshold
    back = dots <= -threshold
    edge = ~(front | back)
    return front, back, edge


def _interp(points: np.ndarray, values: np.ndarray, targets: np.ndarray, method: str) -> np.ndarray:
    if method == "nearest":
        return np.asarray(NearestNDInterpolator(points, values)(targets), dtype=float)
    if method != "linear":
        raise ValueError(f"Unsupported mapping method: {method}")
    lin = np.asarray(LinearNDInterpolator(points, values, fill_value=np.nan)(targets), dtype=float)
    if np.any(~np.isfinite(lin)):
        near = np.asarray(NearestNDInterpolator(points, values)(targets), dtype=float)
        lin = np.where(np.isfinite(lin), lin, near)
    return lin


def map_pressure(
    surface: SurfaceData,
    mesh: ShellMesh,
    method: str = "linear",
    normal_threshold: float = 0.7,
) -> MappingResult:
    front, back, _ = classify_faces(surface, threshold=normal_threshold)
    if front.sum() < 3 or back.sum() < 3:
        raise ValueError("Need at least 3 front and 3 back faces for 2-D pressure mapping")
    # Plate local coordinates: (cantilever y, span z). The CFD faces are projected
    # from x=+/-t/2 onto the structural midsurface x=0.
    tgt = mesh.centroids[:, 1:3]
    pf = _interp(surface.centres[front, 1:3], surface.pressure_pa[front], tgt, method)
    pb = _interp(surface.centres[back, 1:3], surface.pressure_pa[back], tgt, method)
    return MappingResult(
        element_ids=mesh.element_ids,
        centroids=mesh.centroids,
        p_front_pa=pf,
        p_back_pa=pb,
        delta_p_pa=pf - pb,
        areas=mesh.areas,
        method=method,
    )
