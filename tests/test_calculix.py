from fsi.calculix import parse_dat_displacements, parse_dat_stresses, write_calculix_input
from fsi.geometry import structured_shell_mesh
from fsi.mapping import map_pressure
from fsi.synthetic import synthetic_surface


def test_writer_contains_expected_keywords(tmp_path):
    mesh = structured_shell_mesh(0.3, 0.12, 4, 2)
    surface = synthetic_surface(0.3, 0.12, 0.002, 8, 4, 160)
    mapping = map_pressure(surface, mesh)
    path = tmp_path / "panel.inp"
    write_calculix_input(path, mesh, mapping, 0.002, 69e9, 0.33)
    text = path.read_text(encoding="utf-8")
    for token in ["*ELEMENT, TYPE=S4", "*SHELL SECTION", "*DLOAD", "ROOT, 1, 6"]:
        assert token in text
    assert text.count(", P, ") == len(mesh.elements)


def test_dat_parser(tmp_path):
    path = tmp_path / "x.dat"
    path.write_text(
        " displacements\n\n 1  1.0E-3 2.0E-3 3.0E-3\n 2  0.0 0.0 0.0\n\n",
        encoding="utf-8",
    )
    displacements = parse_dat_displacements(path)
    assert set(displacements) == {1, 2}
    assert displacements[1][0] == 1e-3


def test_stress_parser(tmp_path):
    path = tmp_path / "s.dat"
    path.write_text(
        "stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz)\n\n"
        " 1 1 100 0 0 0 0 0\n\n",
        encoding="utf-8",
    )
    rows = parse_dat_stresses(path)
    assert len(rows) == 1
    assert rows[0]["von_mises_pa"] == 100.0
