"""Render the actual board-fit frame and a non-printable PCB reference."""
from pathlib import Path
import json
import sys
from fdm_cad.build import load_model,print_layout
from fdm_cad import preview


def main():
    out=Path(sys.argv[1]).resolve()
    model=load_model(out/'model.py',json.loads((out/'parameters.json').read_text()))
    preview.PALETTE=['#798391','#55aaba','#55aaba','#55aaba','#55aaba']
    preview.render(model['assembly'],out/'preview.png',title='Easier board fit / deeper shelves',subtitle='Exact revision012 lower frame · four M3x5 insert / M3x6 screw clamps',elevation=52,azimuth=-65)
    preview.render(print_layout(model['parts']),out/'print-layout.png',title='Quick board fit / five printable pieces',subtitle='100% scale · frame floor-down · clamps flat · no PCB printed',elevation=60,azimuth=-65)
    preview.PALETTE+=['#65996b']
    preview.render(model['assembly']|{'reference_pcb':model['reference_pcb']},out/'fit-reference.png',title='49 × 70 × 1 mm PCB / fit reference',subtitle='50.3 mm locating gap · 1.3 mm edge coverage · check actual bare-board contact',elevation=52,azimuth=-65)


if __name__=='__main__':
    main()
