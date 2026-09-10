"""Freeze the fit-test and its production sources, then validate STEP/3MF exports."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from fdm_cad.build import build_project, load_model
from fdm_cad.preview import render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--params", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    params = args.params or here / "parameters.json"
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Choose a fresh output directory; saved tests are preserved")
    files = ["model.py", "build-test.py", "check-fit.py", "enclosure/model.py",
             "enclosure/base_model.py", "enclosure/button_module.py", "enclosure/mounting.py",
             "enclosure/parameters.json"]
    with tempfile.TemporaryDirectory(prefix="board-fit-sources-") as temp:
        snapshot = Path(temp)
        for name in files:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(here / name, target)
        shutil.copy2(params, snapshot / "parameters.json")
        report = build_project(snapshot / "model.py", snapshot / "parameters.json", output)
        for name in files[1:]:
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snapshot / name, target)
        hashes = {name: hashlib.sha256((snapshot / name).read_bytes()).hexdigest()
                  for name in files + ["parameters.json"]}
        (output / "source-files.json").write_text(json.dumps(hashes, indent=2) + "\n")
    model = load_model(output / "model.py", json.loads((output / "parameters.json").read_text()))
    view = {"board_fit_tray": model["assembly"]["board_fit_tray"],
            "reference_pcb_not_for_printing": model["reference_pcb"],
            **{k: v for k, v in model["assembly"].items() if k != "board_fit_tray"}}
    width, length, _ = report["measurements"]["pcb_assumed_xyz_mm"]
    render(view, output / "fit-reference.png", title="Board-fit test / nominal PCB in place",
           subtitle=f"{width:g} x {length:g} mm is provisional; use the real board to check fit. PCB reference is not exported.",
           elevation=57, azimuth=-125)
    print(json.dumps({"status": "passed", "output": str(output),
                      "parts": len(report["parts"]), "measurements": report["measurements"]}))


if __name__ == "__main__":
    main()
