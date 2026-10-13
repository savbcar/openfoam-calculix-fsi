from __future__ import annotations

import numpy as np

from .types import ShellMesh


def quad_area(points: np.ndarray) -> float:
    """Area of a planar quad via two triangles."""
    a, b, c, d = points
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a)) + 0.5 * np.linalg.norm(
        np.cross(c - a, d - a)
    )


def polygon_area_normal(points: np.ndarray) -> tuple[float, np.ndarray]:
    """Return polygon area and unit normal using a fan triangulation."""
    if len(points) < 3:
        raise ValueError("A face needs at least three points")
    area_vec = np.zeros(3)
    p0 = points[0]
    for i in range(1, len(points) - 1):
        area_vec += 0.5 * np.cross(points[i] - p0, points[i + 1] - p0)
    area = float(np.linalg.norm(area_vec))
    if area <= 0:
        raise ValueError("Degenerate face")
    return area, area_vec / area


def structured_shell_mesh(length: float, width: float, ny: int, nz: int) -> ShellMesh:
    """Generate an S4-compatible midsurface at x=0.

    Node ordering is chosen so the nominal shell normal is -x. This is useful for
    CalculiX pressure loading, where positive pressure is conventionally treated
    as compressive relative to the shell normal. The pressure sign remains
    configurable in the writer and should be sign-checked on a local ccx build.
    """
    if ny < 1 or nz < 1:
        raise ValueError("ny and nz must be >= 1")
    ys = np.linspace(0.0, length, ny + 1)
    zs = np.linspace(-width / 2.0, width / 2.0, nz + 1)
    nodes = np.array([[0.0, y, z] for y in ys for z in zs], dtype=float)

    def idx(iy: int, iz: int) -> int:
        return iy * (nz + 1) + iz

    elems = []
    for iy in range(ny):
        for iz in range(nz):
            # +z then +y => z x y = -x
            elems.append([idx(iy, iz), idx(iy, iz + 1), idx(iy + 1, iz + 1), idx(iy + 1, iz)])
    elements = np.asarray(elems, dtype=int)
    centroids = np.mean(nodes[elements], axis=1)
    areas = np.asarray([quad_area(nodes[e]) for e in elements])
    return ShellMesh(
        nodes=nodes,
        elements=elements,
        element_ids=np.arange(1, len(elements) + 1),
        centroids=centroids,
        areas=areas,
        normal=np.array([-1.0, 0.0, 0.0]),
        ny=ny,
        nz=nz,
    )


def root_node_ids(mesh: ShellMesh, tol: float = 1e-12) -> np.ndarray:
    return np.flatnonzero(np.abs(mesh.nodes[:, 1]) <= tol) + 1
