from __future__ import annotations

import numpy as np

from .geometry import polygon_area_normal
from .types import SurfaceData


def delta_pressure(y: np.ndarray, z: np.ndarray, length: float, width: float, p0: float) -> np.ndarray:
    """Smooth, non-uniform synthetic net pressure used for deterministic verification."""
    yn = y / length
    zn = z / (width / 2.0)
    shape = (
        1.0
        + 0.22 * np.cos(0.5 * np.pi * zn) * (1.0 - 0.55 * yn)
        + 0.12 * np.sin(np.pi * yn)
        + 0.04 * np.cos(2.0 * np.pi * yn) * np.cos(np.pi * zn)
    )
    return p0 * shape


def _tri_surface(x: float, length: float, width: float, ny: int, nz: int, fluid_normal: np.ndarray, p0: float, side: str):
    ys = np.linspace(0.0, length, ny + 1)
    zs = np.linspace(-width / 2.0, width / 2.0, nz + 1)
    centres, normals, areas, pressures = [], [], [], []
    for iy in range(ny):
        for iz in range(nz):
            p00 = np.array([x, ys[iy], zs[iz]])
            p10 = np.array([x, ys[iy + 1], zs[iz]])
            p11 = np.array([x, ys[iy + 1], zs[iz + 1]])
            p01 = np.array([x, ys[iy], zs[iz + 1]])
            tris = [(p00, p10, p11), (p00, p11, p01)]
            for tri in tris:
                pts = np.asarray(tri)
                centre = pts.mean(axis=0)
                area, _ = polygon_area_normal(pts)
                dp = float(delta_pressure(np.array([centre[1]]), np.array([centre[2]]), length, width, p0)[0])
                # Split net pressure into physically plausible front positive / back suction.
                pressure = 0.65 * dp if side == "front" else -0.35 * dp
                centres.append(centre)
                normals.append(fluid_normal)
                areas.append(area)
                pressures.append(pressure)
    return centres, normals, areas, pressures


def synthetic_surface(length: float, width: float, thickness: float, ny: int, nz: int, p0: float) -> SurfaceData:
    """Create front/back face samples that follow OpenFOAM fluid-domain normal convention.

    Flow is +x. At an immersed solid, the fluid-domain outward normal points into the
    solid: +x on the upstream/front face and -x on the downstream/back face.
    """
    f = _tri_surface(-thickness / 2.0, length, width, ny, nz, np.array([1.0, 0.0, 0.0]), p0, "front")
    b = _tri_surface(+thickness / 2.0, length, width, ny, nz, np.array([-1.0, 0.0, 0.0]), p0, "back")
    centres = np.asarray(f[0] + b[0], dtype=float)
    normals = np.asarray(f[1] + b[1], dtype=float)
    areas = np.asarray(f[2] + b[2], dtype=float)
    pressure = np.asarray(f[3] + b[3], dtype=float)
    return SurfaceData(centres, normals, areas, pressure, np.arange(1, len(areas) + 1))
