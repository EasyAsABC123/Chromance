"""Freeze a button-alignment trial and export full and two-slider print layouts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from fdm_cad.build import build_project,export_mesh,load_model,print_layout
from build123d import Compound,export_step


def main():
    here=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--params',type=Path)
    parser.add_argument('--no-previews',action='store_true')
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists():
        raise ValueError('Choose a fresh output directory; previous trials are preserved')
    names=['model.py','enclosure_model.py','base_model.py','button_module.py','mounting.py',
           'build-test.py','check-fit.py','render-test.py','production-source.json']
    with tempfile.TemporaryDirectory(prefix='button-fit-sources-') as temp:
        snapshot=Path(temp)
        for name in names:shutil.copy2(here/name,snapshot/name)
        shutil.copy2(args.params or here/'parameters.json',snapshot/'parameters.json')
        report=build_project(snapshot/'model.py',snapshot/'parameters.json',output,previews=not args.no_previews)
        for name in names[1:]:shutil.copy2(snapshot/name,output/name)
        for name in ('README.md','fit-results.json'):
            if (here/name).exists():shutil.copy2(here/name,output/name)
        (output/'source-files.json').write_text(json.dumps({n:hashlib.sha256((snapshot/n).read_bytes()).hexdigest()
            for n in names+['parameters.json']},indent=2)+'\n')
    model=load_model(output/'model.py',json.loads((output/'parameters.json').read_text()))
    export_mesh(print_layout(model['slider_only_parts']),output/'sliders-only.3mf')
    export_step(Compound(children=list(model['hardware'].values())),output/'hardware-reference.step')
    print(json.dumps({'status':report['status'],'output':str(output),'print_parts':len(model['parts']),
                      'slider_only_parts':list(model['slider_only_parts'])}))


if __name__=='__main__':main()
