import numpy as np

from fsi.structural import solve_euler_bernoulli_cantilever, uniform_pressure_tip_deflection


def test_beam_fe_matches_uniform_pressure_solution():
    length = 0.3
    width = 0.12
    thickness = 0.002
    youngs = 69e9
    pressure = 160.0
    n_elements = 40
    line_load = np.full(n_elements, pressure * width)
    solution = solve_euler_bernoulli_cantilever(
        line_load,
        length,
        youngs,
        width,
        thickness,
    )
    exact = uniform_pressure_tip_deflection(pressure, length, thickness, youngs)
    assert abs(solution["tip_deflection_m"] - exact) / exact < 1e-9
