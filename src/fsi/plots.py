from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .types import MappingResult, SurfaceData


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_pressure_mapping(
    surface: SurfaceData,
    mapping: MappingResult,
    out: str | Path,
) -> None:
    """Plot mapped net pressure; ``surface`` is retained to make provenance explicit."""
    if len(surface.areas) == 0:
        raise ValueError("Surface contains no CFD faces")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    scatter = ax.scatter(
        mapping.centroids[:, 1],
        mapping.centroids[:, 2],
        c=mapping.delta_p_pa,
        s=22,
    )
    ax.set_xlabel("cantilever coordinate y [m]")
    ax.set_ylabel("span coordinate z [m]")
    ax.set_title("Mapped net pressure Δp = p_front - p_back")
    fig.colorbar(scatter, ax=ax, label="Δp [Pa]")
    _save(fig, Path(out))


def plot_deflection(y: np.ndarray, w: np.ndarray, out: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(y, w * 1e3, marker="o", markersize=3)
    ax.set_xlabel("y [m]")
    ax.set_ylabel("beam-reference deflection [mm]")
    ax.set_title("Mapped-load structural reference response")
    ax.grid(True, alpha=0.25)
    _save(fig, Path(out))


def plot_conservation(metrics: dict[str, float], out: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = ["Force Fx [N]", "Root Mz [N·m]"]
    cfd = [metrics["force_x_cfd_n"], metrics["root_moment_z_cfd_nm"]]
    mapped = [metrics["force_x_mapped_n"], metrics["root_moment_z_mapped_nm"]]
    x = np.arange(2)
    width = 0.35
    ax.bar(x - width / 2, cfd, width, label="CFD surface")
    ax.bar(x + width / 2, mapped, width, label="Mapped FEA load")
    ax.set_xticks(x, labels)
    ax.legend()
    ax.set_title("Load-transfer conservation")
    _save(fig, Path(out))


def plot_convergence(rows: list[dict[str, float]], out: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    face_counts = [row["source_faces"] for row in rows]
    force_errors = [row["force_error_pct"] for row in rows]
    moment_errors = [row["moment_error_pct"] for row in rows]
    ax.loglog(face_counts, force_errors, marker="o", label="force error")
    ax.loglog(face_counts, moment_errors, marker="s", label="root-moment error")
    ax.set_xlabel("synthetic CFD surface faces")
    ax.set_ylabel("mapping error [%]")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    ax.set_title("Mapping/source-mesh sensitivity")
    _save(fig, Path(out))
