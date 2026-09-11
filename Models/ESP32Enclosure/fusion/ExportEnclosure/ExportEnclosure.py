"""Run inside Autodesk Fusion to export and reopen native enclosure archives.

No build123d installation is needed in Fusion. Ordinary Python can inspect the
conversion plan with --check-inputs, but cannot perform the native conversion.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import traceback
import uuid

REVISION = "006-lid-heatsets"
PACKAGE = Path(__file__).resolve().parents[2]
BOUNDS_TOLERANCE_MM = 0.05
VOLUME_RELATIVE_TOLERANCE = 0.001


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def conversion_plan(revision):
    revision = Path(revision).resolve()
    reference = json.loads((revision / "validation.json").read_text())
    if reference.get("status") != "passed" or reference.get("units") != "mm":
        raise ValueError("The revision needs a passed validation report in millimeters.")
    jobs = [("assembly", revision / "assembly.step", reference["assembly_step"])]
    for name, info in reference["parts"].items():
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            raise ValueError("Invalid part name in validation report: " + name)
        jobs.append((name, revision / "parts" / (name + ".step"), info["step"]))
    result = []
    for name, source, expected in jobs:
        if not source.is_file():
            raise FileNotFoundError(source)
        result.append({"name": name, "source": str(source),
                       "source_sha256": digest(source), "expected": expected})
    return result


def check_properties(actual, expected):
    if actual["solid_count"] != expected["solid_count"]:
        raise ValueError("Solid count changed during conversion.")
    if not math.isclose(actual["volume_mm3"], expected["volume_mm3"],
                        rel_tol=VOLUME_RELATIVE_TOLERANCE, abs_tol=0.001):
        raise ValueError("Volume changed during conversion; check units and geometry.")
    if any(not math.isfinite(a) or abs(a - b) > BOUNDS_TOLERANCE_MM
           for edge_a, edge_b in zip(actual["bounds_mm"], expected["bounds_mm"])
           for a, b in zip(edge_a, edge_b)):
        raise ValueError("Bounding coordinates changed during conversion.")


def bodies_in_assembly(root):
    # Each occurrence contributes its own bodies, including repeated instances.
    # Proxies from root.allOccurrences use the root assembly coordinate system.
    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    for i in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(i)
        bodies.extend(occurrence.bRepBodies.item(j)
                      for j in range(occurrence.bRepBodies.count))
    return bodies


def properties(design):
    import adsk.fusion
    bodies = bodies_in_assembly(design.rootComponent)
    if not bodies or any(not body.isSolid for body in bodies):
        raise ValueError("Expected only solid B-Rep bodies after import.")
    bounds = [body.preciseBoundingBox for body in bodies]
    # Fusion's API uses centimeters and cubic centimeters internally.
    lower = [min(getattr(box.minPoint, axis) for box in bounds) * 10
             for axis in ("x", "y", "z")]
    upper = [max(getattr(box.maxPoint, axis) for box in bounds) * 10
             for axis in ("x", "y", "z")]
    accuracy = adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy
    volumes = [body.getPhysicalProperties(accuracy).volume for body in bodies]
    if any(not math.isfinite(volume) or volume <= 0 for volume in volumes):
        raise ValueError("Expected finite positive solid volumes.")
    return {"solid_count": len(bodies),
            "volume_mm3": sum(volumes) * 1000,
            "bounds_mm": [lower, upper]}


def design_in(document):
    import adsk.fusion
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType"))
    if not design:
        raise RuntimeError("Fusion did not create a Design product.")
    return design


def convert(app, job, destination):
    manager = app.importManager
    source = Path(job["source"])
    if digest(source) != job["source_sha256"]:
        raise RuntimeError("STEP input changed during this run: " + str(source))
    if destination.exists():
        raise FileExistsError(destination)
    options = manager.createSTEPImportOptions(str(source))
    options.isViewFit = False
    document = manager.importToNewDocument(options)
    if not document:
        raise RuntimeError("Fusion could not import " + str(source))
    try:
        design = design_in(document)
        design.rootComponent.name = "ESP32 " + REVISION + " " + job["name"]
        if job["name"] != "assembly":
            for body in bodies_in_assembly(design.rootComponent):
                body.name = job["name"]
        imported = properties(design)
        check_properties(imported, job["expected"])
        exporter = design.exportManager
        options = exporter.createFusionArchiveExportOptions(str(destination))
        if not options or not exporter.execute(options):
            raise RuntimeError("Fusion archive export failed: " + str(destination))
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError("Fusion did not write a nonempty archive.")
    finally:
        document.close(False)  # Only the new temporary import document.

    options = manager.createFusionArchiveImportOptions(str(destination))
    options.isViewFit = False
    reopened = manager.importToNewDocument(options)
    if not reopened:
        raise RuntimeError("Fusion could not reopen " + str(destination))
    try:
        roundtrip = properties(design_in(reopened))
        check_properties(roundtrip, job["expected"])
    finally:
        reopened.close(False)
    if digest(source) != job["source_sha256"]:
        raise RuntimeError("STEP input changed during conversion: " + str(source))
    return {"name": job["name"], "file": destination.name,
            "source_sha256": job["source_sha256"], "f3d_sha256": digest(destination),
            "step_import": imported, "f3d_reopened": roundtrip, "status": "passed"}


def run(context):
    import adsk.core
    app = adsk.core.Application.get()
    ui = app.userInterface
    previous = app.activeDocument
    report = None
    report_path = None
    try:
        revision = PACKAGE / "revisions" / REVISION
        jobs = conversion_plan(revision)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = PACKAGE / "fusion" / "exports" / (REVISION + "-" + stamp + "-" + uuid.uuid4().hex[:6])
        output.mkdir(parents=True, exist_ok=False)
        report_path = output / "fusion-validation.json"
        report = {"status": "running", "fusion_version": app.version,
                  "revision": REVISION, "script_sha256": digest(__file__),
                  "reference_report_sha256": digest(revision / "validation.json"),
                  "units": "mm", "bounds_tolerance_mm": BOUNDS_TOLERANCE_MM,
                  "volume_relative_tolerance": VOLUME_RELATIVE_TOLERANCE,
                  "parametric_history_reconstructed": False, "files": []}
        for job in jobs:
            target = output / ("esp32-" + REVISION + "-" + job["name"] + ".f3d")
            report["files"].append(convert(app, job, target))
            report_path.write_text(json.dumps(report, indent=2) + "\n")
        report["status"] = "passed"
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        ui.messageBox("Exported and reopened {} F3D files.\n\n{}\n\n"
                      "These contain imported solids, not reconstructed Python feature history."
                      .format(len(jobs), output))
    except Exception:
        failure = traceback.format_exc()
        if report is not None and report_path is not None:
            report["status"] = "failed"
            report["error"] = failure
            report_path.write_text(json.dumps(report, indent=2) + "\n")
        ui.messageBox("Enclosure F3D export did not finish.\n\n" + failure)
    finally:
        if previous and previous.isValid:
            previous.activate()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-inputs", action="store_true", required=True)
    args = parser.parse_args()
    jobs = conversion_plan(PACKAGE / "revisions" / REVISION)
    print(json.dumps({"status": "inputs_checked_only", "native_conversion_run": False,
                      "revision": REVISION, "archive_count": len(jobs),
                      "files": [{"name": j["name"], "solid_count": j["expected"]["solid_count"]}
                                for j in jobs]}, indent=2))
