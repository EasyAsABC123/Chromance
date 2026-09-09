"""Regenerate source models, export manufacturing geometry, and check read-back."""

from contextlib import redirect_stdout
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import tempfile

from OCP.Font import Font_FontMgr

# build123d 0.11.1 otherwise replaces the process-local font configuration with
# distribution XML newer than OCCT's bundled fontconfig can parse.
_font_environment = {key: os.environ.get(key) for key in ("FONTCONFIG_FILE", "FONTCONFIG_PATH")}
Font_FontMgr.GetInstance_s()
import build123d as bd
for _key, _value in _font_environment.items():
    if _value is None:
        os.environ.pop(_key, None)
    else:
        os.environ[_key] = _value
import numpy as np

from .geometry import check_solid, check_mesh_against_solid, solid_properties, mesh_inspect, load_mesh_instances
from .preview import render


def load_model(path, params, source=None):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("fdm_user_model", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes() if source is None else source, str(path), "exec"), module.__dict__)
    result = module.build(params)
    if not isinstance(result, dict) or not result.get("parts"):
        raise ValueError("Model build(params) must return a nonempty 'parts' mapping")
    if set(result["parts"]) != set(result.get("assembly", {})):
        raise ValueError("parts and assembly must contain the same names")
    for name in result["parts"]:
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            raise ValueError(f"Unsafe or invalid part name: {name!r}")
    return result


def print_layout(parts, row_width=220.0, gap=8.0):
    layout = {}
    x = y = row_height = 0.0
    # Stable order makes repeated builds easy to compare; no target printer assumed.
    for name, part in parts.items():
        bbox = part.bounding_box()
        if x and x + bbox.size.X > row_width:
            x = 0.0; y += row_height + gap; row_height = 0.0
        layout[name] = part.moved(bd.Location((x-bbox.min.X, y-bbox.min.Y, -bbox.min.Z)))
        x += bbox.size.X + gap
        row_height = max(row_height, bbox.size.Y)
    return layout


def export_mesh(parts, path):
    mesher = bd.Mesher(unit=bd.Unit.MM)
    for name, shape in parts.items():
        shape = shape.moved(bd.Location())
        shape.label = name
        mesher.add_shape(shape, linear_deflection=0.02, angular_deflection=0.1)
    mesher.write(path)


def intersection_volumes(parts):
    findings = []
    items = list(parts.items())
    for i, (name, shape) in enumerate(items):
        for other, solid in items[i+1:]:
            common = shape.intersect(solid)
            volume = (0.0 if common is None else
                      sum(float(item.volume) for item in common) if isinstance(common, (list, bd.ShapeList))
                      else float(common.volume))
            if volume > 0.001:
                findings.append({"parts": [name, other], "volume_mm3": volume})
    return findings


def build_project(model_path, params_path, output, previews=True):
    model_path, params_path = Path(model_path).resolve(), Path(params_path).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise ValueError(f"Output already exists: {output}. Choose a new revision directory.")
    model_source, parameter_source = model_path.read_bytes(), params_path.read_bytes()
    params = json.loads(parameter_source)
    result = load_model(model_path, params, source=model_source)
    report = {
        "status": "checking", "units": "mm", "parts": {},
        "measurements": result.get("measurements", {}),
        "versions": {"python": platform.python_version(), **{
            p: importlib.metadata.version(p) for p in
            ["build123d", "cadquery-ocp-novtk", "trimesh", "manifold3d", "lib3mf"]}},
        "inputs": {"model_sha256": hashlib.sha256(model_source).hexdigest(),
                   "parameters_sha256": hashlib.sha256(parameter_source).hexdigest()},
        "thresholds": {"step_dimension_mm": 0.001, "step_volume_relative": 0.0001,
                       "mesh_dimension_mm": 0.05, "mesh_volume_relative": 0.005,
                       "assembly_overlap_mm3": 0.001},
        "physical_fit_tested": False, "physical_strength_tested": False,
        "slicer_profile_applied": False,
    }
    for name, shape in result["parts"].items():
        report["parts"][name] = {"cad": check_solid(shape, name, print_orientation=True)}
        check_solid(result["assembly"][name], f"assembled {name}")
    overlaps = intersection_volumes(result["assembly"])
    if overlaps:
        raise ValueError(f"Assembled printed parts intersect: {overlaps}")
    report["assembly_overlaps"] = overlaps
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cad-build-", dir=output.parent) as temp:
        temp = Path(temp)
        (temp / "parts").mkdir()
        for name, shape in result["parts"].items():
            step_path = temp / "parts" / f"{name}.step"
            mesh_path = temp / "parts" / f"{name}.3mf"
            bd.export_step(shape, step_path)
            reread = bd.import_step(step_path)
            step_prop = check_solid(reread, f"STEP {name}")
            expected = report["parts"][name]["cad"]
            if not np.allclose(step_prop["bounds_mm"], expected["bounds_mm"], atol=0.001, rtol=0):
                raise ValueError(f"STEP dimensions differ for {name}")
            if not math.isclose(step_prop["volume_mm3"], expected["volume_mm3"], rel_tol=0.0001):
                raise ValueError(f"STEP volume differs for {name}")
            export_mesh({name: shape}, mesh_path)
            report["parts"][name]["step"] = step_prop
            report["parts"][name]["mesh"] = check_mesh_against_solid(mesh_path, shape)
        assembly = bd.Compound(children=list(result["assembly"].values()))
        bd.export_step(assembly, temp / "assembly.step")
        read_assembly = bd.import_step(temp / "assembly.step")
        if len(read_assembly.solids()) != len(result["parts"]):
            raise ValueError("STEP assembly did not preserve intended solid count")
        report["assembly_step"] = solid_properties(read_assembly)
        layout = print_layout(result["parts"])
        export_mesh(layout, temp / "print-layout.3mf")
        layout_report = mesh_inspect(temp / "print-layout.3mf")
        if layout_report["instance_count"] != len(layout):
            raise ValueError("3MF print layout did not preserve separate parts")
        # Compare transformed positions as well as local part extents.
        expected_bounds = sorted([solid_properties(s)["bounds_mm"] for s in layout.values()], key=lambda x: x[0])
        actual_bounds = sorted([m.bounds.tolist() for _, m in load_mesh_instances(temp / "print-layout.3mf")], key=lambda x: x[0])
        if not np.allclose(actual_bounds, expected_bounds, atol=0.05, rtol=0):
            raise ValueError("3MF print layout transforms or dimensions differ")
        report["print_layout"] = layout_report
        report["status"] = "passed"
        (temp / "model.py").write_bytes(model_source)
        (temp / "parameters.json").write_bytes(parameter_source)
        (temp / "validation.json").write_text(json.dumps(report, indent=2)+"\n")
        notes = ["# Printing and assembly notes", "", "Model geometry in millimeters; no slicer profile or physical testing applied.", ""]
        notes += [f"- {note}" for note in result.get("notes", [])]
        (temp / "printing-notes.md").write_text("\n".join(notes)+"\n")
        if previews:
            title = result.get("title", model_path.parent.name.replace("-", " ").title())
            render(result["assembly"], temp / "preview.png", title=title, subtitle="Assembled geometry · source and parameters retained")
            render(layout, temp / "print-layout.png", title=f"{title} / print layout", subtitle="All parts rest on Z=0 · dimensions remain adjustable", elevation=48)
        temp.rename(output)
    return report
