"""Observable geometry and file contracts, including negative cases."""

import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

import fdm_cad  # process-local CAD/font environment before importing the kernel
from fdm_cad.build import build_project, export_mesh
import build123d as bd
import numpy as np
import pytest
import trimesh

from fdm_cad.geometry import load_mesh_instances, mesh_inspect


def test_source_build_roundtrip_and_parameter_change(tmp_path):
    model = tmp_path / "plate.py"
    model.write_text('''from build123d import *
def build(p):
    if p["length"] <= 12:
        raise ValueError("length must exceed 12 mm")
    block = Box(p["length"], 23, 11, align=(Align.MIN, Align.MIN, Align.MIN))
    hole = Pos(8, 10, -1) * Cylinder(2, 13, align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate = block - hole
    return {"parts": {"plate": plate}, "assembly": {"plate": plate}, "notes": []}
''')
    parameter = tmp_path / "params.json"
    for length in [37, 49]:
        parameter.write_text(json.dumps({"length": length}))
        out = tmp_path / str(length)
        report = build_project(model, parameter, out, previews=False)
        assert report["status"] == "passed"
        assert report["parts"]["plate"]["cad"]["size_mm"] == pytest.approx([length, 23, 11])
        assert report["parts"]["plate"]["cad"]["volume_mm3"] == pytest.approx(length*23*11 - np.pi*4*11)
        part = bd.import_step(out / "parts/plate.step")
        assert not part.is_inside((8, 10, 5))
        assert part.is_inside((20, 10, 5))
        assert (out / "model.py").read_bytes() == model.read_bytes()
    parameter.write_text('{"length": 8}')
    with pytest.raises(ValueError, match="length must"):
        build_project(model, parameter, tmp_path / "invalid", previews=False)
    assert not (tmp_path / "invalid").exists()


def test_model_3mf_instances_and_inch_units(tmp_path):
    scene = trimesh.Scene()
    block = trimesh.creation.box([1, 2, 3])
    scene.add_geometry(block, geom_name="shared", node_name="first")
    transform = np.eye(4); transform[0, 3] = 4
    scene.graph.update(frame_to="second", matrix=transform, geometry="shared")
    file = tmp_path / "inches.3mf"
    raw = scene.export(file_type="3mf")
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(raw)) as src, zipfile.ZipFile(file, "w") as dst:
        for entry in src.infolist():
            contents = src.read(entry.filename)
            if entry.filename.endswith(".model"):
                root = ET.fromstring(contents); root.set("unit", "inch")
                contents = ET.tostring(root)
            dst.writestr(entry, contents)
    instances = load_mesh_instances(file)
    assert len(instances) == 2
    assert all(np.allclose(mesh.extents, [25.4, 50.8, 76.2]) for _, mesh in instances)
    centers = sorted(mesh.centroid[0] for _, mesh in instances)
    assert centers[1]-centers[0] == pytest.approx(101.6)
    with pytest.raises(ValueError, match="conflicts"):
        mesh_inspect(file, "mm")


def test_stl_requires_scale_and_mesh_boolean(tmp_path):
    block = trimesh.creation.box([40, 30, 12])
    path = tmp_path / "original.stl"; block.export(path)
    with pytest.raises(ValueError, match="STL has no defined units"):
        mesh_inspect(path)
    assert mesh_inspect(path, "mm")["size_mm"] == pytest.approx([40, 30, 12])
    cutter = trimesh.creation.cylinder(radius=3, height=20, sections=128)
    cutter.apply_translation([7, 0, 0])
    edited = trimesh.boolean.difference([block, cutter], engine="manifold")
    expected_volume = 40*30*12 - np.pi*9*12
    assert edited.is_volume
    assert edited.volume == pytest.approx(expected_volume, rel=0.0001)
    assert edited.extents == pytest.approx([40, 30, 12])
    invalid = block.copy(); invalid.update_faces(np.arange(len(invalid.faces)-1))
    with pytest.raises(ValueError):
        trimesh.boolean.difference([invalid, cutter], engine="manifold")


def test_reject_interfering_assembly(tmp_path):
    model = tmp_path / "overlap.py"
    model.write_text('''from build123d import *
def build(p):
    a=Box(10,10,10,align=(Align.MIN,Align.MIN,Align.MIN))
    return {"parts":{"a":a,"b":a},"assembly":{"a":a,"b":Pos(5,0,0)*a}}
''')
    params = tmp_path / "params.json"; params.write_text('{}')
    with pytest.raises(ValueError, match="intersect"):
        build_project(model, params, tmp_path / "invalid", previews=False)
    assert not (tmp_path / "invalid").exists()


def test_preview_preserves_hole_and_occlusion():
    from fdm_cad.preview import _rasterize
    from matplotlib.colors import to_rgb
    plate = trimesh.creation.box([40, 30, 4])
    hole = trimesh.creation.cylinder(radius=4, height=10, sections=64)
    plate = trimesh.boolean.difference([plate, hole], engine="manifold")
    behind = trimesh.creation.box([40, 30, 1]); behind.apply_translation([0, 0, -5])
    # Camera looks down Z. The rear plate must be visible only through the hole.
    pixels = _rasterize([("#0000ff", plate), ("#ff0000", behind)], 90, 0, width=400, height=300)
    center = pixels[150, 200]
    assert center[0] > 0.5 and center[2] == 0  # red below the hole
    surface = pixels[150, 270]
    assert surface[2] > 0.5 and surface[0] == 0  # blue front surface
    visible = pixels[..., 2] > 0.5
    # Flat face shading must not invent different diagonal facets.
    blue_only = visible & (pixels[..., 0] == 0)
    assert np.ptp(pixels[..., 2][blue_only]) < 1e-6
