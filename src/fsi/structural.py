from __future__ import annotations

import numpy as np

from .types import MappingResult


def beam_properties(width: float, thickness: float) -> tuple[float, float]:
    area = width * thickness
    inertia = width * thickness**3 / 12.0
    return area, inertia


def uniform_pressure_tip_deflection(p: float, length: float, thickness: float, youngs: float) -> float:
    return 3.0 * p * length**4 / (2.0 * youngs * thickness**3)


def uniform_pressure_root_stress(p: float, length: float, thickness: float) -> float:
    return 3.0 * p * length**2 / thickness**2


def line_load_from_mapping(mapping: MappingResult, ny: int, nz: int, width: float) -> np.ndarray:
    """Collapse shell-element pressures into a width-integrated line load per y row."""
    if len(mapping.delta_p_pa) != ny * nz:
        raise ValueError("Mapping size does not match structured shell mesh")
    p = mapping.delta_p_pa.reshape(ny, nz)
    dz = width / nz
    return np.sum(p * dz, axis=1)


def solve_euler_bernoulli_cantilever(line_load: np.ndarray, length: float, youngs: float, width: float, thickness: float):
    """Euler-Bernoulli beam FE reference model with 2 DOF/node (w, theta)."""
    ne = len(line_load)
    nn = ne + 1
    ndof = 2 * nn
    le = length / ne
    _, inertia = beam_properties(width, thickness)
    kfac = youngs * inertia / le**3
    ke = kfac * np.array(
        [[12, 6 * le, -12, 6 * le],
         [6 * le, 4 * le**2, -6 * le, 2 * le**2],
         [-12, -6 * le, 12, -6 * le],
         [6 * le, 2 * le**2, -6 * le, 4 * le**2]], dtype=float
    )
    K = np.zeros((ndof, ndof), dtype=float)
    F = np.zeros(ndof, dtype=float)
    for e, q in enumerate(line_load):
        dofs = np.array([2*e, 2*e+1, 2*(e+1), 2*(e+1)+1])
        K[np.ix_(dofs, dofs)] += ke
        # Consistent nodal load for uniform q on this beam element.
        fe = q * np.array([le/2, le**2/12, le/2, -le**2/12], dtype=float)
        F[dofs] += fe
    free = np.arange(2, ndof)
    u = np.zeros(ndof, dtype=float)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    reaction = K @ u - F
    y = np.linspace(0.0, length, nn)
    return {
        "y_m": y,
        "deflection_m": u[0::2],
        "rotation_rad": u[1::2],
        "tip_deflection_m": float(u[-2]),
        "root_shear_n": float(-reaction[0]),
        "root_moment_nm": float(-reaction[1]),
    }


def root_bending_stress(moment_nm: float, width: float, thickness: float) -> float:
    _, inertia = beam_properties(width, thickness)
    return abs(moment_nm) * (thickness / 2.0) / inertia
