"""Geometry checks deliberately independent of a model's construction code."""

from pathlib import Path
import math
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import trimesh


UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}
THREEMF_UNITS = {"micron": 0.001, "millimeter": 1.0, "centimeter": 10.0,
                 "meter": 1000.0, "inch": 25.4, "foot": 304.8}


def solid_properties(shape):
    bbox = shape.bounding_box()
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(shape.solids()),
        "volume_mm3": float(shape.volume),
        "bounds_mm": [list(bbox.min), list(bbox.max)],
        "size_mm": list(bbox.size),
    }


def check_solid(shape, name, print_orientation=False):
    prop = solid_properties(shape)
    if not prop["valid"] or prop["solid_count"] != 1 or not prop["volume_mm3"] > 0:
        raise ValueError(f"{name}: expected one valid positive-volume solid; got {prop}")
    if print_orientation and abs(prop["bounds_mm"][0][2]) > 1e-5:
        raise ValueError(f"{name}: printable part must start at Z=0")
    return prop


def declared_3mf_scale(path):
    with zipfile.ZipFile(path) as archive:
        models = [n for n in archive.namelist() if n.lower().endswith('.model')]
        if not models:
            raise ValueError("3MF archive contains no model")
        scales = set()
        for name in models:
            root = ET.fromstring(archive.read(name))
            unit = root.attrib.get("unit", "millimeter")
            if unit not in THREEMF_UNITS:
                raise ValueError(f"Unsupported 3MF unit: {unit}")
            scales.add(THREEMF_UNITS[unit])
        if len(scales) != 1:
            raise ValueError("Mixed-unit 3MF submodels require explicit conversion before import")
        return scales.pop()


def load_mesh_instances(path, units=None):
    """Flatten scene instances exactly once and normalize coordinates to mm.

    Trimesh's 3MF reader retains file coordinates and unit metadata. Its exporter
    writes millimeters, so normalization here changes coordinates, not just labels.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".stl":
        if units is None:
            raise ValueError("STL has no defined units: specify --units mm, cm, m, or in")
        scale = UNIT_TO_MM[units]
    elif suffix == ".3mf":
        scale = declared_3mf_scale(path)
        if units is not None and not math.isclose(UNIT_TO_MM[units], scale):
            raise ValueError("--units conflicts with units declared in the 3MF")
    else:
        raise ValueError("Supported mesh inputs are .stl and .3mf")
    scene = trimesh.load_scene(path, process=True)
    instances = []
    for node in sorted(scene.graph.nodes_geometry):
        matrix, key = scene.graph[node]
        mesh = scene.geometry[key].copy()
        mesh.apply_transform(matrix)
        mesh.apply_scale(scale)
        mesh.units = "mm"
        instances.append((str(node), mesh))
    if not instances:
        raise ValueError(f"No mesh instances in {path}")
    return instances


def mesh_properties(mesh):
    return {
        "vertices": len(mesh.vertices), "triangles": len(mesh.faces),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "positive_volume": bool(mesh.is_volume),
        "volume_mm3": float(mesh.volume),
        "size_mm": mesh.extents.tolist(),
        "bounds_mm": mesh.bounds.tolist(),
        "connected_bodies": len(mesh.split(only_watertight=False)),
    }


def mesh_inspect(path, units=None):
    entries = load_mesh_instances(path, units)
    bounds = np.asarray([m.bounds for _, m in entries])
    return {
        "path": str(Path(path).resolve()), "normalized_units": "mm",
        "instance_count": len(entries),
        "size_mm": (bounds[:, 1].max(axis=0)-bounds[:, 0].min(axis=0)).tolist(),
        "instances": {name: mesh_properties(mesh) for name, mesh in entries},
    }


def check_mesh_against_solid(path, solid):
    entries = load_mesh_instances(path)
    if len(entries) != 1:
        raise ValueError(f"{path}: expected one mesh instance, found {len(entries)}")
    prop = mesh_properties(entries[0][1])
    reference = solid_properties(solid)
    if not prop["positive_volume"] or prop["connected_bodies"] != 1:
        raise ValueError(f"{path}: export is not a connected, watertight volume: {prop}")
    if not np.allclose(prop["bounds_mm"], reference["bounds_mm"], atol=0.05, rtol=0):
        raise ValueError(f"{path}: exported mesh dimensions/position differ from CAD")
    if not math.isclose(prop["volume_mm3"], reference["volume_mm3"], rel_tol=0.005):
        raise ValueError(f"{path}: exported mesh volume differs by more than 0.5%")
    return prop
