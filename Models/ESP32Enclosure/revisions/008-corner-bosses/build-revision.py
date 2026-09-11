"""Freeze all local CAD modules before exporting a fresh corner-boss revision."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from fdm_cad.build import build_project


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--params", type=Path)
    args = parser.parse_args()
    params = args.params or (here/"params.json" if (here/"params.json").exists() else here/"parameters.json")
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Choose a fresh revision directory; existing revisions are preserved")
    sources = ["model.py", "base_model.py", "button_module.py", "mounting.py", "build-revision.py", "render-details.py"]
    with tempfile.TemporaryDirectory(prefix="corner-boss-sources-") as tmp:
        snapshot = Path(tmp)
        for name in sources:
            shutil.copy2(here/name, snapshot/name)
        shutil.copy2(params, snapshot/"parameters.json")
        build_project(snapshot/"model.py", snapshot/"parameters.json", output)
        for name in sources[1:]:
            shutil.copy2(snapshot/name, output/name)
        names = sources+["parameters.json"]
        hashes = {name: hashlib.sha256((snapshot/name).read_bytes()).hexdigest() for name in names}
        (output/"source-files.json").write_text(json.dumps(hashes, indent=2)+"\n")
    print(json.dumps({"status": "passed", "output": str(output), "frozen_sources": names}))


if __name__ == "__main__":
    main()
