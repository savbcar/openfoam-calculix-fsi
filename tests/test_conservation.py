from fsi.conservation import conservation_metrics, mapped_resultant, surface_resultant_on_structure
from fsi.geometry import structured_shell_mesh
from fsi.mapping import map_pressure
from fsi.synthetic import synthetic_surface


def test_mapping_conserves_force_and_moment_tightly():
    surface = synthetic_surface(0.3, 0.12, 0.002, 36, 16, 160.0)
    mesh = structured_shell_mesh(0.3, 0.12, 30, 12)
    mapping = map_pressure(surface, mesh, "linear")
    metrics = conservation_metrics(
        surface_resultant_on_structure(surface),
        mapped_resultant(mapping),
    )
    assert metrics["force_x_error_pct"] < 0.5
    assert metrics["root_moment_z_error_pct"] < 0.5
