from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .types import MappingResult, SurfaceData


def write_surface_csv(path: str | Path, surface: SurfaceData) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["face_id", "cx", "cy", "cz", "nx", "ny", "nz", "area_m2", "p_pa"])
        for i in range(len(surface.areas)):
            writer.writerow(
                [
                    int(surface.face_ids[i]),
                    *surface.centres[i],
                    *surface.normals[i],
                    surface.areas[i],
                    surface.pressure_pa[i],
                ]
            )


def read_surface_csv(path: str | Path) -> SurfaceData:
    data = np.genfromtxt(path, delimiter=",", names=True)
    return SurfaceData(
        centres=np.column_stack([data["cx"], data["cy"], data["cz"]]),
        normals=np.column_stack([data["nx"], data["ny"], data["nz"]]),
        areas=np.asarray(data["area_m2"], dtype=float),
        pressure_pa=np.asarray(data["p_pa"], dtype=float),
        face_ids=np.asarray(data["face_id"], dtype=int),
    )


def write_mapping_csv(path: str | Path, mapping: MappingResult) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "element_id",
                "cx",
                "cy",
                "cz",
                "area_m2",
                "p_front_pa",
                "p_back_pa",
                "delta_p_pa",
                "method",
            ]
        )
        for i in range(len(mapping.areas)):
            writer.writerow(
                [
                    int(mapping.element_ids[i]),
                    *mapping.centroids[i],
                    mapping.areas[i],
                    mapping.p_front_pa[i],
                    mapping.p_back_pa[i],
                    mapping.delta_p_pa[i],
                    mapping.method,
                ]
            )
