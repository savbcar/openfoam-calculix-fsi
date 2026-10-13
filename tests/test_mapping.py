import numpy as np

from fsi.geometry import structured_shell_mesh
from fsi.mapping import classify_faces, map_pressure
from fsi.synthetic import synthetic_surface


def test_classification_and_linear_mapping():
    surface = synthetic_surface(0.3, 0.12, 0.002, 18, 8, 160.0)
    front, back, edge = classify_faces(surface)
    assert front.sum() == back.sum() > 0
    assert edge.sum() == 0

    mesh = structured_shell_mesh(0.3, 0.12, 24, 10)
    mapping = map_pressure(surface, mesh, "linear")
    assert np.all(np.isfinite(mapping.delta_p_pa))
    assert mapping.delta_p_pa.min() > 100
