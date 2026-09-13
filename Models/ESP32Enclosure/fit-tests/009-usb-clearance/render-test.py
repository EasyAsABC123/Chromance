"""Render actual button-fit geometry and separate non-printable PCB reference."""
from pathlib import Path
import json
import sys
from fdm_cad.build import load_model,print_layout
from fdm_cad import preview
from build123d import Compound


def grouped(shapes):
    """Keep the image legend readable; grouping affects previews only."""
    groups={'test_frame':[], 'four_pcb_clamps':[], 'frames_and_keepers':[], 'replacement_sliders':[]}
    for name,shape in shapes.items():
        key=('test_frame' if name=='button_fit_frame' else 'four_pcb_clamps' if name.startswith('pcb_clamp_')
             else 'replacement_sliders' if name.endswith('_slider') else 'frames_and_keepers')
        groups[key].append(shape)
    return {n:Compound(children=s) for n,s in groups.items() if s}


def main():
    output=Path(sys.argv[1]).resolve()
    model=load_model(output/'model.py',json.loads((output/'parameters.json').read_text()))
    preview.PALETTE=['#78899a','#62adb1','#d3934a','#6797c7']
    preview.render(grouped(model['assembly']),output/'preview.png',title='Measured USB clearance / quick trial',
                   subtitle='Exact production interfaces · low open frame · 13 printable parts',elevation=57,azimuth=-125)
    preview.render(grouped(print_layout(model['parts'])),output/'print-layout.png',title='Fresh setup / 13 pieces',
                   subtitle='Production print orientations · reference hardware and PCB excluded',elevation=62,azimuth=-65)
    preview.render(print_layout(model['replacement_parts']),output/'replacements-only.png',title='Start here / three replacement parts',
                   subtitle='Reuse verified revision 013 parts or test 008 frame · local arm supports required',elevation=52,azimuth=-115)
    preview.PALETTE+=['#679869','#c45f54']
    preview.render(grouped(model['assembly'])|{'reference_pcb':model['reference_pcb'],'measured_usb_box':model['reference_usb']},output/'fit-reference.png',
                   title='Actual test geometry / measured USB envelope',
                   subtitle='10 × 6 mm plug · 20 mm projection · nominal position; board-play limits need checking',elevation=70,azimuth=-125)


if __name__=='__main__':main()
