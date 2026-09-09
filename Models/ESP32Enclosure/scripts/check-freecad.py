"""Run with freecad-python; independently consume a completed build's STEP files."""
import json
import math
from pathlib import Path
import sys

import FreeCAD
import Part


def properties(shape):
    box = shape.BoundBox
    return {"valid": shape.isValid(), "solid_count": len(shape.Solids),
            "volume_mm3": shape.Volume, "size_mm": [box.XLength, box.YLength, box.ZLength]}


revision = Path(sys.argv[1]).resolve()
reference = json.loads((revision / "validation.json").read_text())
report = {"freecad_version": ".".join(FreeCAD.Version()[:3]), "parts": {}}
for name, info in reference["parts"].items():
    shape = Part.read(str(revision / "parts" / (name + ".step")))
    actual = properties(shape)
    expected = info["cad"]
    assert actual["valid"] and actual["solid_count"] == 1, name
    assert all(abs(a-b) <= 0.001 for a, b in zip(actual["size_mm"], expected["size_mm"])), name
    assert math.isclose(actual["volume_mm3"], expected["volume_mm3"], rel_tol=0.0001), name
    report["parts"][name] = actual

assembly = Part.read(str(revision / "assembly.step"))
report["assembly"] = properties(assembly)
assert report["assembly"]["valid"]
assert report["assembly"]["solid_count"] == len(report["parts"])
assert math.isclose(assembly.Volume, sum(p["volume_mm3"] for p in report["parts"].values()), rel_tol=0.0001)

document = FreeCAD.newDocument("CADInspection")
feature = document.addObject("Part::Feature", "Assembly")
feature.Label = "Imported assembly (editable source: model.py)"
feature.Shape = assembly
feature.addProperty("App::PropertyString", "SourceNotes")
feature.SourceNotes = "Geometry inspection copy. Parametric source and parameters accompany this file."
document.recompute()
document.saveAs(str(revision / "inspection.FCStd"))
FreeCAD.closeDocument(document.Name)
reopened = FreeCAD.openDocument(str(revision / "inspection.FCStd"))
assert reopened.getObject("Assembly").Shape.isValid()
FreeCAD.closeDocument(reopened.Name)
report["status"] = "passed"
(revision / "freecad-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": "passed", "freecad": report["freecad_version"], "parts": len(report["parts"])}))
