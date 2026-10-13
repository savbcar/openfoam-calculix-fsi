from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SurfaceData:
    centres: np.ndarray  # (N, 3)
    normals: np.ndarray  # outward normal of the FLUID domain at the wall
    areas: np.ndarray  # (N,)
    pressure_pa: np.ndarray  # gauge pressure, Pa
    face_ids: np.ndarray

    def __post_init__(self) -> None:
        n = len(self.areas)
        if self.centres.shape != (n, 3) or self.normals.shape != (n, 3):
            raise ValueError("centres/normals must have shape (N, 3)")
        if self.pressure_pa.shape != (n,) or self.face_ids.shape != (n,):
            raise ValueError("pressure_pa/face_ids must have shape (N,)")
        if np.any(self.areas <= 0):
            raise ValueError("All face areas must be positive")


@dataclass(frozen=True)
class ShellMesh:
    nodes: np.ndarray  # (Nn, 3)
    elements: np.ndarray  # (Ne, 4), zero-based node indices
    element_ids: np.ndarray  # (Ne,)
    centroids: np.ndarray  # (Ne, 3)
    areas: np.ndarray  # (Ne,)
    normal: np.ndarray  # nominal shell normal, (3,)
    ny: int
    nz: int


@dataclass(frozen=True)
class MappingResult:
    element_ids: np.ndarray
    centroids: np.ndarray
    p_front_pa: np.ndarray
    p_back_pa: np.ndarray
    delta_p_pa: np.ndarray
    areas: np.ndarray
    method: str


@dataclass(frozen=True)
class Resultant:
    force_n: np.ndarray
    moment_nm: np.ndarray
