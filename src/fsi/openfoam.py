from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from .geometry import polygon_area_normal
from .types import SurfaceData

_COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.M | re.S)
_FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def _clean(text: str) -> str:
    return _COMMENT_RE.sub("", text)


def _payload(text: str) -> str:
    """Return content inside the outer list following the declared count."""
    cleaned = _clean(text)
    match = re.search(r"\n\s*\d+\s*\n\s*\(", cleaned)
    if not match:
        match = re.search(r"\d+\s*\(", cleaned)
    if not match:
        raise ValueError("Could not locate OpenFOAM list payload")

    start = cleaned.find("(", match.start()) + 1
    depth = 1
    for i in range(start, len(cleaned)):
        if cleaned[i] == "(":
            depth += 1
        elif cleaned[i] == ")":
            depth -= 1
            if depth == 0:
                return cleaned[start:i]
    raise ValueError("Unterminated OpenFOAM list")


def read_points(path: str | Path) -> np.ndarray:
    payload = _payload(Path(path).read_text(encoding="utf-8", errors="ignore"))
    values = re.findall(rf"\(\s*({_FLOAT})\s+({_FLOAT})\s+({_FLOAT})\s*\)", payload)
    return np.asarray(
        [[float(a), float(b), float(c)] for a, b, c in values],
        dtype=float,
    )


def read_faces(path: str | Path) -> list[np.ndarray]:
    payload = _payload(Path(path).read_text(encoding="utf-8", errors="ignore"))
    faces: list[np.ndarray] = []
    for match in re.finditer(r"(\d+)\s*\(([^()]*)\)", payload):
        count = int(match.group(1))
        ids = [int(value) for value in match.group(2).split()]
        if len(ids) == count:
            faces.append(np.asarray(ids, dtype=int))
    return faces


def read_labels(path: str | Path) -> np.ndarray:
    payload = _payload(Path(path).read_text(encoding="utf-8", errors="ignore"))
    return np.asarray([int(value) for value in re.findall(r"\b\d+\b", payload)], dtype=int)


def read_boundary_patch(path: str | Path, patch: str) -> tuple[int, int]:
    text = _clean(Path(path).read_text(encoding="utf-8", errors="ignore"))
    match = re.search(rf"\b{re.escape(patch)}\s*\{{(.*?)\}}", text, re.S)
    if not match:
        raise KeyError(f"Patch '{patch}' not found")

    body = match.group(1)
    n_faces = re.search(r"\bnFaces\s+(\d+)\s*;", body)
    start_face = re.search(r"\bstartFace\s+(\d+)\s*;", body)
    if not n_faces or not start_face:
        raise ValueError(f"Malformed boundary entry for patch '{patch}'")
    return int(start_face.group(1)), int(n_faces.group(1))


def read_internal_scalar_field(path: str | Path, n_cells: int) -> np.ndarray:
    text = _clean(Path(path).read_text(encoding="utf-8", errors="ignore"))
    uniform = re.search(rf"internalField\s+uniform\s+({_FLOAT})\s*;", text)
    if uniform:
        return np.full(n_cells, float(uniform.group(1)))

    nonuniform = re.search(
        r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",
        text,
        re.S,
    )
    if not nonuniform:
        raise ValueError("Only ASCII uniform/nonuniform scalar internalField is supported")

    values = np.asarray(
        [float(value) for value in re.findall(_FLOAT, nonuniform.group(2))],
        dtype=float,
    )
    if len(values) != int(nonuniform.group(1)):
        raise ValueError("Scalar list length mismatch")
    return values


def latest_time(case_dir: str | Path) -> str:
    case = Path(case_dir)
    times: list[tuple[float, str]] = []
    for path in case.iterdir():
        if not path.is_dir():
            continue
        try:
            times.append((float(path.name), path.name))
        except ValueError:
            continue
    if not times:
        raise FileNotFoundError("No numeric OpenFOAM time directories found")
    return max(times)[1]


def extract_patch_pressure(
    case_dir: str | Path,
    patch: str,
    density: float,
    time: str = "latest",
) -> SurfaceData:
    """Extract wall pressure from an ASCII OpenFOAM-13 case.

    For a zeroGradient wall p boundary, boundary p equals owner-cell p. The supplied
    case therefore uses the owner-cell internal p value for each boundary face.
    The case must use ``writeFormat ascii``; binary fields are intentionally rejected.
    """
    case = Path(case_dir)
    mesh = case / "constant" / "polyMesh"
    points = read_points(mesh / "points")
    faces = read_faces(mesh / "faces")
    owner = read_labels(mesh / "owner")
    start, count = read_boundary_patch(mesh / "boundary", patch)
    selected_time = latest_time(case) if time == "latest" else str(time)
    n_cells = int(owner.max()) + 1
    p_kinematic = read_internal_scalar_field(case / selected_time / "p", n_cells)

    centres: list[np.ndarray] = []
    normals: list[np.ndarray] = []
    areas: list[float] = []
    pressures: list[float] = []
    face_ids: list[int] = []
    for face_id in range(start, start + count):
        face_points = points[faces[face_id]]
        area, normal = polygon_area_normal(face_points)
        centres.append(face_points.mean(axis=0))
        normals.append(normal)
        areas.append(area)
        pressures.append(density * p_kinematic[owner[face_id]])
        face_ids.append(face_id)

    return SurfaceData(
        np.asarray(centres),
        np.asarray(normals),
        np.asarray(areas),
        np.asarray(pressures),
        np.asarray(face_ids),
    )
