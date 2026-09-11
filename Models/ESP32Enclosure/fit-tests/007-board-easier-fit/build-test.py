"""Snapshot the board fit test and its full-enclosure dependencies, then export."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from fdm_cad.build import build_project


def main():
    here=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--params',type=Path)
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists():
        raise ValueError('Choose a fresh output directory; previous tests are preserved')
    names=['model.py','enclosure_model.py','base_model.py','button_module.py','mounting.py','build-test.py','render-test.py']
    with tempfile.TemporaryDirectory(prefix='board-fit-source-') as temp:
        snapshot=Path(temp)
        for name in names:
            shutil.copy2(here/name,snapshot/name)
        shutil.copy2(args.params or here/'parameters.json',snapshot/'parameters.json')
        build_project(snapshot/'model.py',snapshot/'parameters.json',output)
        for name in names[1:]:
            shutil.copy2(snapshot/name,output/name)
        (output/'source-files.json').write_text(json.dumps({name:hashlib.sha256((snapshot/name).read_bytes()).hexdigest() for name in names+['parameters.json']},indent=2)+'\n')
    print(json.dumps({'status':'passed','output':str(output)}))


if __name__=='__main__':
    main()
