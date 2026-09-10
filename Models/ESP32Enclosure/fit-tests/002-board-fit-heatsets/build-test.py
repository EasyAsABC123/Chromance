"""Freeze the corrected board-fit source and export validated engineering models."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from fdm_cad.build import build_project, load_model
from fdm_cad.preview import render
from build123d import Compound, export_step, import_step


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--params", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    params = args.params or (here / "parameters.json" if (here / "parameters.json").exists() else here / "params.json")
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Choose a fresh output directory; existing fit tests are preserved")
    files = ["model.py", "base_model.py", "mounting.py", "build-test.py", "check-fit-heatsets.py"]
    with tempfile.TemporaryDirectory(prefix="heatset-fit-sources-") as tmp:
        snapshot = Path(tmp)
        for name in files:
            shutil.copy2(here / name, snapshot / name)
        shutil.copy2(params, snapshot / "parameters.json")
        report = build_project(snapshot / "model.py", snapshot / "parameters.json", output)
        for name in files[1:]:
            shutil.copy2(snapshot / name, output / name)
        hashes = {name: hashlib.sha256((snapshot / name).read_bytes()).hexdigest()
                  for name in files + ["parameters.json"]}
        (output / "source-files.json").write_text(json.dumps(hashes, indent=2) + "\n")
    result = load_model(output / "model.py", json.loads((output / "parameters.json").read_text()))
    hardware = result.get("hardware", {})
    if hardware:
        path = output / "hardware-reference.step"
        export_step(Compound(children=list(hardware.values())), path)
        actual = import_step(path)
        if not actual.is_valid or len(actual.solids()) != sum(len(s.solids()) for s in hardware.values()):
            raise ValueError("Hardware reference STEP read-back failed")
    pcb = result.get("reference_pcb")
    if pcb is None:
        pcb = result.get("reference_board")
    if pcb is not None:
        assembly = result["assembly"]
        tray_names = [n for n in assembly if "clamp" not in n]
        view = {**{n: assembly[n] for n in tray_names}, "reference_pcb_not_for_printing": pcb,
                **{n: s for n, s in assembly.items() if n not in tray_names}}
        dimensions = report["measurements"]["pcb_assumed_xyz_mm"]
        label = " x ".join(f"{d:g}" for d in dimensions)
        render(view, output / "fit-reference.png", title="PCB fit / heat-set clamp fasteners",
               subtitle=f"{label} mm substrate reference; ESP32 components are omitted.",
               elevation=57, azimuth=-125)
    print(json.dumps({"status": "passed", "output": str(output), "parts": len(report["parts"]),
                      "hardware_reference_solids": sum(len(s.solids()) for s in hardware.values()),
                      "measurements": report["measurements"]}))


if __name__ == "__main__":
    main()
