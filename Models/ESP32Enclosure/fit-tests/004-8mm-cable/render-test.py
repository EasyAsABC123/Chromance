"""Inspect a cable-retention test using its exported source geometry."""
from pathlib import Path
import json
import sys
from fdm_cad.build import load_model,print_layout
from fdm_cad import preview


def main():
    output=Path(sys.argv[1]).resolve()
    model=load_model(output/'model.py',json.loads((output/'parameters.json').read_text()))
    parts=model['assembly']
    preview.PALETTE=['#59606e','#9aa5b5']
    preview.render(print_layout(model['parts']),output/'print-layout.png',
                   title='Quick cable fit / two small parts',
                   subtitle='Print floor-down body and exterior-down lid at 100% scale · no cable or tie printed',
                   elevation=40,azimuth=-65)
    preview.render(parts,output/'preview.png',
                   title='8 mm cable fit / wall and lid',
                   subtitle='Exact revision010 geometry crop · physically untested',
                   elevation=25,azimuth=-65)
    refs={k:v for k,v in model['reference_geometry'].items() if k!='zip_tie_straight_threading_segment'}
    shapes={'cable_fit_body':parts['cable_fit_body']} | refs
    colors={'cable_fit_body':'#798391','cable':'#e2a750','zip_tie_route':'#9db557','zip_tie_head':'#b89acb'}
    preview.PALETTE=[colors.get(k,'#bb9d62') for k in shapes]
    preview.render(shapes,output/'fit-reference.png',
                   title='8 mm cable fit / thread, seat, snug',
                   subtitle='Cable and zip tie are reference geometry only · check the actual hardware',
                   elevation=32,azimuth=-65)


if __name__=='__main__':
    main()
