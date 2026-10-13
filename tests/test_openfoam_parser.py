import numpy as np

from fsi.openfoam import (
    read_boundary_patch,
    read_faces,
    read_internal_scalar_field,
    read_labels,
    read_points,
)

HEADER = "FoamFile { format ascii; class x; object x; }\n"


def test_ascii_mesh_parsers(tmp_path):
    points = tmp_path / "points"
    points.write_text(
        HEADER + "4\n(\n(0 0 0)\n(0 1 0)\n(0 1 1)\n(0 0 1)\n)\n",
        encoding="utf-8",
    )
    faces = tmp_path / "faces"
    faces.write_text(HEADER + "1\n(\n4(0 1 2 3)\n)\n", encoding="utf-8")
    owner = tmp_path / "owner"
    owner.write_text(HEADER + "1\n(\n0\n)\n", encoding="utf-8")
    boundary = tmp_path / "boundary"
    boundary.write_text(
        HEADER + "1\n(\npanel { type wall; nFaces 1; startFace 0; }\n)\n",
        encoding="utf-8",
    )

    assert read_points(points).shape == (4, 3)
    assert read_faces(faces)[0].tolist() == [0, 1, 2, 3]
    assert read_labels(owner).tolist() == [0]
    assert read_boundary_patch(boundary, "panel") == (0, 1)


def test_scalar_field_parser(tmp_path):
    pressure = tmp_path / "p"
    pressure.write_text(
        HEADER + "internalField nonuniform List<scalar> 3\n(\n1\n2\n3\n);\n",
        encoding="utf-8",
    )
    assert np.allclose(read_internal_scalar_field(pressure, 3), [1, 2, 3])
