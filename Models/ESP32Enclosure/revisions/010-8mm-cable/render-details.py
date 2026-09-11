"""Render actual revision010 geometry and illustrative cable/tie routing."""
from pathlib import Path
import json
import sys
from fdm_cad.build import load_model, print_layout
from fdm_cad import preview
from build123d import Align, Box, Compound, Pos, export_step


def box_from_bounds(bounds):
    lo,hi=bounds
    return Pos(*lo)*Box(*(b-a for a,b in zip(lo,hi)),align=(Align.MIN,Align.MIN,Align.MIN))


def render(shapes,path,title,subtitle,elevation=30,azimuth=-65):
    palette={'body':'#59606e','lid':'#9aa5b5','desk_bracket':'#454c56',
             'shell_section':'#798391','rounded_cable_support':'#55aaba',
             'cable':'#e2a750','zip_tie_route':'#9db557','zip_tie_head':'#b89acb',
             'desk_reference':'#b89976','EN_RESET_paddle':'#55aaba','BOOT_paddle':'#e2a750'}
    preview.PALETTE=[palette.get(k,'#7e8b9a') for k in shapes]
    preview.render(shapes,path,title=title,subtitle=subtitle,elevation=elevation,azimuth=azimuth)


def grouped(parts, lid=True, bracket=True):
    result={k:parts[k] for k in ['body']+(['lid'] if lid else [])+(['desk_bracket'] if bracket else [])}
    result['guides_keepers_and_PCB_clamps']=Compound(children=[v for k,v in parts.items() if k.startswith('pcb_clamp_') or (k.startswith(('reset_','boot_')) and not k.endswith('_slider'))])
    result['EN_RESET_paddle']=parts['reset_slider']
    result['BOOT_paddle']=parts['boot_slider']
    return result


def main():
    output=Path(sys.argv[1]).resolve()
    model=load_model(output/'model.py',json.loads((output/'parameters.json').read_text()))
    parts=model['assembly']
    render(grouped(parts),output/'preview.png','ESP32 / cable retention',
           'Revision 010 · measured 8 mm cable · existing parts remain compatible',-25,-145)
    scene=grouped(parts)
    desk_z=model['measurements']['desk_contact_z']
    scene['desk_reference']=Pos(0,0,desk_z)*Box(150,125,6,align=(Align.CENTER,Align.CENTER,Align.MIN))
    render(scene,output/'under-desk.png','Under-desk cable retention',
           'Desk reference is not printable · lid and button faces point downward',-18,-145)
    render(grouped(parts,lid=False,bracket=False),output/'interior.png','Cable retention / lid removed',
           'Actual assembled geometry · rounded support at the end opening',-48,-145)
    exploded={k:(Pos(0,0,-24)*v if k=='lid' else Pos(0,0,30)*v if k=='desk_bracket' else v) for k,v in parts.items()}
    render(grouped(exploded),output/'exploded.png','Enclosure / assembly access',
           'Lid lowered for illustration · all fifteen revision009 parts remain compatible',-25,-145)
    render(grouped(print_layout(model['parts'])),output/'print-layout.png','Revision 010 / 15 printable parts',
           'All fifteen revision009 parts remain compatible',52,-65)
    info=model['measurements']['cable_retention']
    crop=box_from_bounds(info['coupon_bounds_local_mm'])
    body=model['case_local_assembly']['body'] & crop
    feature=model['cable_retention_local']
    if isinstance(feature,dict):
        feature=Compound(children=list(feature.values()))
    feature=feature & body
    section={'shell_section':body-feature,'rounded_cable_support':feature}
    render(section,output/'cable-anchor.png','Cable anchor / actual enclosure section',
           'Rounded cable contact · transverse zip-tie passage · wall and floor retained',32,-65)
    refs={k:v for k,v in model['cable_retention_references_local'].items() if k!='zip_tie_straight_threading_segment'}
    render(section | refs,output/'cable-routing.png','Measured 8 mm cable / provisional tie fit',
           'Measured 8 mm cable · loose tie/head envelopes · not printable hardware',32,-65)
    closed={'body':body,'lid':model['case_local_assembly']['lid'] & crop} | refs
    render(closed,output/'cable-closure.png','Cable anchor / lid clearance',
           'Actual lid section · reference cable/tie fit still requires a physical check',12,60)
    export_step(Compound(children=list(model['hardware'].values())),output/'hardware-reference.step')


if __name__=='__main__':
    main()
