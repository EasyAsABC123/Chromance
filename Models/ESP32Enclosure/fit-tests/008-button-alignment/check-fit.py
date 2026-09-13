"""Check exact production interfaces, reusable parts and sampled button-jig motion."""
import argparse
import hashlib
import json
from pathlib import Path
from math import pi

from fdm_cad.build import load_model,print_layout
from fdm_cad.geometry import load_mesh_instances
from build123d import Align,Box,Cylinder,Pos,Rot,import_step
import numpy as np
import trimesh


def require(ok,message,**detail):
    if not ok:raise AssertionError({'check':message,**detail})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def volume(shape):
    if shape is None:return 0.0
    members=[shape] if hasattr(shape,'solids') else list(shape)
    return sum(abs(float(s.volume)) for m in members for s in m.solids())


def overlap(a,b):
    aa,bb=a.bounding_box(),b.bounding_box()
    if any(min(tuple(aa.max)[i],tuple(bb.max)[i])-max(tuple(aa.min)[i],tuple(bb.min)[i])<1e-8 for i in range(3)):
        return 0.0
    return volume(a.intersect(b))


def mesh(shape):
    v,f=shape.tessellate(.01,.1)
    m=trimesh.Trimesh(vertices=[list(x) for x in v],faces=f,process=True)
    require(m.is_volume,'Comparison geometry must be a closed mesh')
    return m


def same(a,b,label):
    require(abs(volume(a)-volume(b))<.001,label+' volume',first=volume(a),second=volume(b))
    aa,bb=mesh(a),mesh(b)
    require(np.allclose(aa.bounds,bb.bounds,atol=.001,rtol=0),label+' bounds')
    if aa.vertices.shape==bb.vertices.shape and aa.faces.shape==bb.faces.shape and np.allclose(aa.vertices,bb.vertices,atol=1e-7,rtol=0) and np.array_equal(aa.faces,bb.faces):return
    differences=[trimesh.boolean.difference([x,y],engine='manifold') for x,y in ((aa,bb),(bb,aa))]
    require(max(abs(float(m.volume)) if len(m.faces) else 0 for m in differences)<.005,label+' geometry')


def box(lo,hi):
    return Pos(*lo)*Box(*(b-a for a,b in zip(lo,hi)),align=(Align.MIN,Align.MIN,Align.MIN))


def hits(probe,items):
    return {n:v for n,s in items.items() if (v:=overlap(probe,s))>.001}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--production',type=Path,required=True)
    parser.add_argument('--reuse-frame',type=Path,required=True)
    parser.add_argument('--reuse-enclosure',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    source,production=args.source.resolve(),args.production.resolve()
    p=json.loads((source/'parameters.json').read_text())
    require(p==json.loads((production/'parameters.json').read_text()),'Trial parameters differ from compared production build')
    provenance=json.loads((source/'production-source.json').read_text())
    source_hashes={}
    for original,entry in provenance['source_files'].items():
        local=source/entry['local_file']
        require(sha(local)==sha(production/original)==entry['sha256'],'Copied production source differs',file=original)
        source_hashes[entry['local_file']]=sha(local)
    source_hashes['model.py']=sha(source/'model.py')
    print('Build trial and verify exact production STEP interfaces',flush=True)
    m=load_model(source/'model.py',p)
    require(len(m['parts'])==13 and len(m['hardware'])==26,'Trial inventory must be13 printed pieces and26 hardware proxies')
    full=m['full_model']
    production_body=import_step(production/'parts/body.step')
    bounds=production_body.bounding_box()
    height=m['measurements']['frame_height_mm']
    crop=box([bounds.min.X-1,bounds.min.Y-1,0],[bounds.max.X+1,bounds.max.Y+1,height])
    window=Pos(0,0,-1)*Box(p['pcb_width']-5,p['pcb_length']-4,height+2,align=(Align.CENTER,Align.CENTER,Align.MIN))
    same(m['parts']['button_fit_frame'],(production_body & crop)-window,'Frame vs actual production STEP crop')
    for name,shape in m['parts'].items():
        require(shape.is_valid and len(shape.solids())==1 and abs(shape.bounding_box().min.Z)<.001,'Invalid trial print part',part=name)
        if name!='button_fit_frame':same(shape,import_step(production/'parts'/f'{name}.step'),name+' vs production STEP')
    same(m['parts']['button_fit_frame'],import_step(args.reuse_frame/'parts/board_fit_frame.step'),'Reuse test007 frame')
    for name in (n for n in m['parts'] if n.startswith('pcb_clamp_')):
        same(m['parts'][name],import_step(args.reuse_frame/'parts'/f'{name}.step'),name+' reuse test007 clamp')
    unchanged=[]
    for name,shape in full['parts'].items():
        if name.endswith('_slider'):continue
        same(shape,import_step(args.reuse_enclosure/'parts'/f'{name}.step'),name+' reuse revision012')
        unchanged.append(name)
    require(len(unchanged)==13,'Expected thirteen unchanged full-enclosure parts')
    instances=load_mesh_instances(source/'sliders-only.3mf')
    require(len(instances)==2,'Slider-only 3MF must contain exactly two instances')
    expected_layout=print_layout(m['slider_only_parts'])
    actual_bounds=sorted([x.bounds.tolist() for _,x in instances],key=lambda x:x[0])
    expected_bounds=sorted([[list(s.bounding_box().min),list(s.bounding_box().max)] for s in expected_layout.values()],key=lambda x:x[0])
    require(np.allclose(actual_bounds,expected_bounds,atol=.05,rtol=0),'Slider-only layout changed scale or placement')
    actual_volume=sum(abs(float(s.volume)) for _,s in instances)
    require(abs(actual_volume/sum(float(s.volume) for s in expected_layout.values())-1)<.005,'Slider-only mesh volume changed')
    measured={}
    for name,bottom in (('reset',30.),('boot',16.)):
        bp=full['buttons'][name]['params']
        xy=[bp['tip_x'],bp['tip_y']]
        require(np.allclose(xy,[-p['pcb_width']/2+3.3,-p['pcb_length']/2+bottom],atol=1e-8,rtol=0),'Measured tip XY changed',button=name,xy=xy)
        measured[name]={'tip_center_local_xy_mm':xy,'from_left_mm':3.3,'from_bottom_mm':bottom,
                        'switch_height_is_provisional':True}
    print('Check all27 board seating positions',flush=True)
    xp=m['measurements']['x_play_each_direction_mm']
    for dx in (-xp,0,xp):
        for dy in (-.4,0,.4):
            for dz in (0,p['board_vertical_play']/2,p['board_vertical_play']):
                findings=hits(Pos(dx,dy,dz)*m['reference_pcb'],m['assembly']|m['hardware'])
                require(not findings,'PCB movement envelope obstructed',position=[dx,dy,dz],hits=findings)
    expected={(e['hardware'],e['printed']):e['nominal_displaced_envelope_volume_mm3'] for e in m['expected_hardware_intersections']}
    require(len(expected)==len(m['expected_hardware_intersections']),'Duplicate hardware allowlist')
    reset_bp=full['buttons']['reset']['params'];boot_bp=full['buttons']['boot']['params']
    face=reset_bp['mounting_face_x'];mid_y=(reset_bp['tip_y']+boot_bp['tip_y'])/2
    board_top=m['measurements']['board_top_z_mm']
    internal_bounds=[[face+.25,mid_y-4,board_top+2.3],[reset_bp['tip_x'],mid_y+4,board_top+8.3]]
    outer_bounds=[[face-21.25,mid_y-4,board_top+2.3],[face+.25,mid_y+4,board_top+8.3]]
    internal_usb=box(*internal_bounds);outer_usb=box(*outer_bounds)
    # A3.6 mm cable through the old outer gap is a sample, not a measured cable.
    cable=Pos(face-21.25,mid_y,board_top+5.3)*Rot(Y=90)*Cylinder(1.8,21.5,align=(Align.CENTER,Align.CENTER,Align.MIN))
    states=[]
    stroke=p['button_stroke']
    for reset_travel,boot_travel in ((0,0),(stroke/2,stroke/2),(stroke,stroke),(stroke,0),(0,stroke)):
        printed=dict(m['assembly']);hardware=dict(m['hardware'])
        tips={}
        for button,travel in (('reset',reset_travel),('boot',boot_travel)):
            data=full['buttons'][button]
            for name in data['moving_names']:printed[name]=Pos(0,0,-travel)*m['assembly'][name]
            for suffix in ('moving_magnet','nylon_adjuster','contact_heatset_insert','nylon_jam_nut'):
                name=f'{button}_{suffix}';hardware[name]=Pos(0,0,-travel)*m['hardware'][name]
            tip_z=hardware[f'{button}_nylon_adjuster'].bounding_box().min.Z
            expected_tip=data['params']['switch_top_z']+stroke-p['modeled_switch_depression']-travel
            require(abs(tip_z-expected_tip)<1e-6,'Contact screw does not follow intended stroke',button=button)
            tips[button]={'travel_mm':travel,'nylon_tip_z_mm':tip_z,
                          'nominal_switch_gap_mm':tip_z-data['params']['switch_top_z']}
        items=list(printed.items())
        for i,(name,s) in enumerate(items):
            for other,t in items[i+1:]:require(overlap(s,t)<.001,'Printed motion interference',parts=[name,other],travel=[reset_travel,boot_travel])
        for hn,h in hardware.items():
            for sn,s in printed.items():
                v=overlap(h,s)
                require(abs(v-expected.get((hn,sn),0))<.001,'Unexpected hardware motion interference',hardware=hn,printed=sn,volume=v,travel=[reset_travel,boot_travel])
        items=list(hardware.items())
        for i,(name,s) in enumerate(items):
            for other,t in items[i+1:]:require(overlap(s,t)<.001,'Hardware motion interference',parts=[name,other])
        states.append({'buttons':tips,'unexpected_motion_interference':[],
                       'provisional_internal_usb_probe_hits_mm3':hits(internal_usb,printed|hardware),
                       'provisional_outer_plug_approach_hits_mm3':hits(outer_usb,printed|hardware),
                       'provisional_outer_cable_probe_hits_mm3':hits(cable,printed|hardware)})
    stop_contacts={}
    for button,data in full['buttons'].items():
        fixed={n:s for n,s in m['assembly'].items() if n.startswith(button+'_') and n not in data['moving_names']}
        moving=m['assembly'][button+'_slider']
        lower=hits(Pos(0,0,-stroke-.05)*moving,fixed)
        upper=hits(Pos(0,0,.05)*moving,fixed)
        require(lower and upper,'Printed stops must block overtravel in both directions',button=button,lower=lower,upper=upper)
        stop_contacts[button]={'lower_overtravel_contacts_mm3':lower,'upper_overtravel_contacts_mm3':upper}
    report={'status':'passed','source_hashes':source_hashes,'checker_sha256':sha(__file__),
            'production_revision':provenance['revision'],'print_part_count':13,'hardware_proxy_count':26,
            'exact_production_interfaces':True,'reuse_test007_frame_and_clamps':True,
            'unchanged_revision012_full_parts':unchanged,'only_two_sliders_need_reprinting':True,
            'sliders_only_3mf_instances':2,'measured_button_xy':measured,'board_seating_poses_checked':27,
            'sampled_motion_states':states,'positive_stop_checks':stop_contacts,
            'usb_probe_definition':{'internal_plug_box_local_mm':internal_bounds,
                'outer_plug_approach_box_local_mm':outer_bounds,
                'outer_cable_diameter_mm':3.6,'outer_cable_center_yz_mm':[mid_y,board_top+5.3],
                'actual_plug_or_cable_measured':False,'straight_plug_insertion_claimed':False},
            'physical_fit_tested':False,'limitations':[
                'USB probe intersections are reported, not hidden or used to certify an unmeasured plug. Fit the real plug before the cartridges and check travel.',
                'Five motion combinations are finite samples; actual switch height/travel, return force, guide fit and conductor clearance require physical checks.',
                'The PCB is loose by the production fit allowance. Nominal measured XY assumes it is centered; evaluate contact at its movement limits.',
                'The floor window and omitted upper enclosure cannot validate central underside solder clearance, lid fit, shell stiffness or mounted loads.']}
    for original,entry in provenance['source_files'].items():require(sha(source/entry['local_file'])==entry['sha256'],'Source changed during validation')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'passed','report':str(args.output),'two_slider_reuse_checked':True,
                      'usb_probe_has_obstructions':any(s['provisional_internal_usb_probe_hits_mm3'] or s['provisional_outer_plug_approach_hits_mm3'] or s['provisional_outer_cable_probe_hits_mm3'] for s in states)}))


if __name__=='__main__':main()
