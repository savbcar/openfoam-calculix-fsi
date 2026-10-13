import numpy as np

from fsi.geometry import root_node_ids, structured_shell_mesh


def test_shell_mesh_area_and_normal():
    mesh = structured_shell_mesh(0.3, 0.12, 6, 4)
    assert len(mesh.elements) == 24
    assert np.isclose(mesh.areas.sum(), 0.3 * 0.12)
    assert np.allclose(mesh.normal, [-1, 0, 0])
    assert len(root_node_ids(mesh)) == 5
