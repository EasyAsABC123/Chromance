"""Independent geometry/service review of the enclosure's external cartridges.

This checks simplified CAD/hardware envelopes. It does not verify real switch
coordinates, magnetic force, strength, printer fit, wiring, or actual USB plugs.
"""
import argparse
import hashlib
import importlib.util
import json
from math import sqrt
from pathlib import Path

from fdm_cad.build import load_model
from build123d import Align, Box, Compound, Cylinder, Pos, RegularPolygon, Rot, extrude

TOL = 0.001


def module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
    return m


def box(w,d,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Box(w,d,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def cyl(r,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def xcyl(r,length,x,y,z):
    return Pos(x,y,z)*Rot(Y=90)*Cylinder(r,length,align=(Align.CENTER,Align.CENTER,Align.MIN))


def v(s):
    return abs(float(s.volume)) if s else 0.0


def common(a,b):
    if a is None or b is None:return None
    aa,bb=a.bounding_box(),b.bounding_box()
    if any(min(tuple(aa.max)[i],tuple(bb.max)[i])-max(tuple(aa.min)[i],tuple(bb.min)[i])<1e-8 for i in range(3)):
        return None
    c=a.intersect(b)
    if c is None:return None
    members=[c] if hasattr(c,'solids') else list(c)
    solids=[s for member in members for s in member.solids()]
    return (solids[0] if len(solids)==1 else Compound(solids)) if solids else None


def collisions(shapes):
    found=[]
    items=list(shapes.items())
    for i,(name,a) in enumerate(items):
        for other,b in items[i+1:]:
            volume=v(common(a,b))
            if volume>TOL:found.append({'parts':[name,other],'volume_mm3':volume})
    return found


def case(label, model_dir, baseline_path, params):
    result=load_model(model_dir/'model.py',params)
    bm=module(model_dir/'button_module.py','button_module_review')
    baseline_module=module(baseline_path,'baseline_review')
    base=baseline_module.build({k:params[k] for k in baseline_module.DEFAULTS})
    checks=[]; observations=[]

    def check(name,value,tol=TOL):
        checks.append({'name':name,'passed':abs(value)<=tol,'measured':value,'tolerance':tol})
    def same(name,a,b):check(name,v(a)+v(b)-2*v(common(a,b)))
    def empty(name,proxy,shapes):
        hits={n:v(common(proxy,s)) for n,s in shapes.items()}
        check(name,max(hits.values(),default=0))
        return {n:value for n,value in hits.items() if value>TOL}

    check('fifteen print parts',len(result['parts'])-15,0)
    for n,s in result['parts'].items():
        check(n+' valid single solid',int(not s.is_valid or len(s.solids())!=1),0)
        check(n+' print minimum Z',s.bounding_box().min.Z,1e-6)
    for n,s in base['assembly'].items():
        if n!='body':same('preserved styled part '+n,result['assembly'][n],s)
    for key in ['pcb_assumed','pcb_bottom_z','pcb_top_z','cavity_xy','lid_top_z','desk_contact_z',
                'desk_screw_centers_xy','body_mount_centers_xy','lid_screw_centers_xy','style']:
        check('preserved interface '+key,int(result['measurements'][key]!=base['measurements'][key]),0)

    p=params; bw,bl=p['pcb_width'],p['pcb_length'];floor=p['floor']
    cw,cl=result['measurements']['cavity_xy'];ow,ol=result['measurements']['main_shell_xy']
    bottom=result['measurements']['pcb_bottom_z'];top=result['measurements']['pcb_top_z']
    h=top+p['component_clearance'];face=-ow/2-3.6
    cavity=box(cw,cl,h+1,z=-.01)
    same('exact body cavity, board retention, floor and end stops',
         common(result['assembly']['body'],cavity),common(base['assembly']['body'],cavity))
    pad_regions=None
    for button in result['buttons'].values():
        region=box(5.1,14.1,9.5,face+2.45,button['params']['housing_y'],-.01)
        pad_regions=region if pad_regions is None else pad_regions+region
    same('style body unchanged outside attachment pads',result['assembly']['body']-pad_regions,
         base['assembly']['body']-pad_regions)

    original_parts={n:result['assembly'][n] for n in base['assembly']}
    clamp_heads={}
    for x in (-(bw/2+4.5),bw/2+4.5):
        for y in (-p['clamp_y'],p['clamp_y']):
            clamp_heads[f'clamp_head_{x}_{y}']=cyl(2.75,3,x,y,top+p['board_vertical_play']+2)
    body_mounts=result['measurements']['body_mount_centers_xy']
    # Existing body mount screws, lid screws and desk holes remain serviceable.
    for x,y in body_mounts:
        empty(f'body mount driver {x},{y}',cyl(3,h+4.95,x,y,-10),result['assembly'])
    for x,y in result['measurements']['desk_screw_centers_xy']:
        empty(f'desk mounting driver {x},{y}',cyl(4,h+p['bracket_clearance_above_body']-.05,x,y,0),result['assembly'])
    for x,y in result['measurements']['lid_screw_centers_xy']:
        empty(f'lid driver with bracket removed {x},{y}',cyl(2,15,x,y,h+p['lid_thickness']+.05),
              {n:s for n,s in result['assembly'].items() if n!='desk_bracket'})
    for x in (-(bw/2+4.5),bw/2+4.5):
        for y in (-p['clamp_y'],p['clamp_y']):
            driver=cyl(1.5,25,x,y,top+p['board_vertical_play']+5.05)
            hits=empty(f'PCB clamp driver before cartridges/lid {x},{y}',driver,
                       {n:s for n,s in original_parts.items() if n not in ('lid','desk_bracket')})
            installed_hits={n:v(common(s,driver)) for n,s in result['assembly'].items()
                            if n not in original_parts and v(common(s,driver))>TOL}
            if installed_hits:observations.append({'service_access':'PCB clamp requires cartridge removal',
                                                   'xy':[x,y],'blocking_parts':installed_hits})

    # Existing nut insertion sweeps must remain accessible before cartridge installation.
    ny=extrude(RegularPolygon(5.5/sqrt(3),6,rotation=30),amount=2.4)
    nx=extrude(RegularPolygon(5.5/sqrt(3),6),amount=2.4)
    for x,y in body_mounts:
        check(f'bracket nut path {x},{y}',max(v(common(original_parts['desk_bracket'],
            Pos(x+(1 if x>0 else -1)*s*.5,y,h+2.15)*nx)) for s in range(23)))
    for x,y in result['measurements']['lid_screw_centers_xy']:
        check(f'lid nut path {x},{y}',max(v(common(original_parts['body'],
            Pos(x,y+(-1 if y>0 else 1)*s*.5,h-5.35)*ny)) for s in range(20)))
    for x in (-(bw/2+4.5),bw/2+4.5):
        for y in (-p['clamp_y'],p['clamp_y']):
            check(f'PCB clamp nut path {x},{y}',max(v(common(original_parts['body'],
                Pos(x,y-s*.5,bottom-3.35)*ny)) for s in range(18)))

    for fraction in [0.,.5,1.]:
        pose=f'pose {fraction:g}'
        assembly=dict(original_parts); hardware={}; buttons={}
        for name,bdata in result['buttons'].items():
            bp=bdata['params']|{'travel':bdata['params']['stroke']*fraction}
            button=bm.make_button(bp,name);buttons[name]=button
            assembly.update(button['assembly']);hardware.update(button['hardware'])
        found=collisions(assembly)
        check(pose+' printed assembly overlaps',max([f['volume_mm3'] for f in found],default=0))
        if found:observations.append({'pose':fraction,'printed_collisions':found})
        hw_found=[]
        for hn,hs in hardware.items():
            for n,s in assembly.items():
                overlap=v(common(hs,s))
                if overlap>TOL:hw_found.append({'hardware':hn,'part':n,'volume_mm3':overlap})
        check(pose+' hardware versus print solids',max([f['volume_mm3'] for f in hw_found],default=0))
        if hw_found:observations.append({'pose':fraction,'hardware_print_collisions':hw_found})
        hw_pairs=collisions(hardware)
        check(pose+' hardware versus hardware',max([f['volume_mm3'] for f in hw_pairs],default=0))
        if hw_pairs:observations.append({'pose':fraction,'hardware_collisions':hw_pairs})
        all_shapes=assembly|hardware
        empty(pose+' nominal PCB keepout',box(bw,bl,p['pcb_thickness'],z=bottom),all_shapes)
        empty(pose+' underside non-edge solder keepout',
              box(bw-2*p['board_edge_overlap'],bl,p['solder_clearance']-.02,z=floor+.01),all_shapes)
        for n,head in clamp_heads.items():empty(pose+' '+n+' clearance',head,all_shapes)
        # Provisional switches are targeted by the nylon tip only, not the rigid arm.
        for name,button in buttons.items():
            bp=result['buttons'][name]['params'];tx,ty=bp['tip_x'],bp['tip_y'];switch=bp['switch_top_z']
            switch_proxy=cyl(2,1,tx,ty,switch-1)
            empty(pose+' '+name+' rigid geometry clears switch',switch_proxy,
                  {n:s for n,s in all_shapes.items() if n!=name+'_nylon_adjuster'})
            tip=button['hardware'][name+'_nylon_adjuster'].bounding_box().min.Z
            expected=switch+bp['stroke']-bp['switch_depression']-fraction*bp['stroke']
            check(pose+' '+name+' calibrated tip Z',tip-expected,1e-6)
            check(pose+' '+name+' maximum switch depression',max(0,switch-tip-bp['switch_depression']),1e-6)
            for _,y,z in button['mounting_centers']:
                head_plane=button['measurements']['rear_head_bearing_x_mm']
                empty(pose+f' cartridge driver {name}/{y}',xcyl(2,30,head_plane-33.05,y,z),all_shapes)
            # Contact driver is reachable with lid/bracket removed for adjustment.
            head_top=button['hardware'][name+'_nylon_adjuster'].bounding_box().max.Z
            empty(pose+' '+name+' contact adjustment driver with lid removed',cyl(1.5,15,tx,ty,head_top+.05),
                  {n:s for n,s in all_shapes.items() if n not in ('lid','desk_bracket')})

        ylo=result['buttons']['boot']['params']['housing_y']+7
        yhi=result['buttons']['reset']['params']['housing_y']-7
        empty(pose+' full housing corridor outside mounting face',
              box(30,yhi-ylo,23,face-15,(yhi+ylo)/2,9.5),all_shapes)
        # Inside the wall the existing clamp occupies the bottom rear corner.
        # Check a documented 11x6 mm provisional connector envelope below arms.
        corridor_height=6.0;corridor_z=top+p['board_vertical_play']+2+.1
        tip_x=result['buttons']['reset']['params']['tip_x']
        empty(pose+' provisional inner USB corridor 11x6 mm',
              box(tip_x-(face-30),yhi-ylo,corridor_height,
                  (tip_x+face-30)/2,(yhi+ylo)/2,corridor_z),all_shapes)

    # Body insert bores, intentionally undersized for heat setting.
    for x,y,z in result['measurements']['button_mount_centers_xyz']:
        pilot=xcyl(p['button_insert_pilot_diameter']/2-.01,p['button_insert_bore_depth']-.02,x+.01,y,z)
        empty(f'insert pilot void {y}',pilot,{'body':original_parts['body']})
        # Full insert is inside reserved material but excludes the threaded bore.
        insert=xcyl(2.3,4,x,y,z)-xcyl(1.5,4.1,x-.05,y,z)
        empty(f'insert does not enter PCB cavity {y}',insert,{'cavity':cavity})
        check(f'blind bore remaining wall >=1.5mm {y}',max(0,1.5-(-cw/2-(x+p['button_insert_bore_depth']))),1e-6)
        check(f'M3x18 nominal engagement3.8mm {y}',(18-14.2)-3.8,1e-6)
        check(f'M3x18 blind tip clearance >=0.5mm {y}',max(0,.5-(p['button_insert_bore_depth']-(18-14.2))),1e-6)

    for name,bdata in result['buttons'].items():
        bp=bdata['params'];r=bm.make_button(bp,name)
        frame=r['assembly'][name+'_frame'];keeper=r['assembly'][name+'_rear_keeper']
        fixed=frame+keeper
        moving_names=r['moving_names']
        # Stops reject travel beyond both ends; review final geometry, not only metadata.
        for label2,dz in [('upper',.05),('lower',-bp['stroke']-.05)]:
            collision=max(v(common(Pos(0,0,dz)*r['assembly'][n],fixed)) for n in moving_names)
            check(name+' positive '+label2+' stop exists',int(collision<=TOL),0)
        # The revised slider loads vertically with the rear keeper and nylon
        # contact hardware removed. The module is serviced with lid access.
        vertical_path=[]
        for dz in [i*.5 for i in range(1,71)]:
            overlap=max(v(common(Pos(0,0,dz)*r['assembly'][n],frame)) for n in moving_names)
            if overlap>TOL:vertical_path.append({'dz_mm':dz,'overlap_mm3':overlap})
        check(name+' vertical insertion/removal path with keeper removed',max([q['overlap_mm3'] for q in vertical_path],default=0))
        if vertical_path:observations.append({'service_path':name,'vertical_path_collisions':vertical_path})
        # Magnet escape is blocked by a mechanical keeper or surrounding walls.
        for suffix in ['fixed_magnet','moving_magnet']:
            magnet=r['hardware'][name+'_'+suffix]
            blockers=r['assembly']
            for axis,delta in [('rear',(-.5,0,0)),('front',(.5,0,0)),('side',(0,.4,0)),('up',(0,0,.3)),('down',(0,0,-.3))]:
                overlap=max(v(common(Pos(*delta)*magnet,s)) for s in blockers.values())
                check(name+' '+suffix+' '+axis+' capture',int(overlap<=TOL),0)

    return {'case':label,'passed':all(c['passed'] for c in checks),'checks':checks,
            'observations':observations,'measurements':result['measurements'],
            'limitations':['Real switch/plug/wiring dimensions remain unverified.',
                          'Simplified hardware and geometric captures do not establish strength or magnetic return force.',
                          'PCB clamp service requires cartridge removal; contact adjustment requires lid access.']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model-dir',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--baseline',type=Path,default=Path('/home/justin/github/cad-models/models/esp32-desk-enclosure/revisions/002-console/model.py'))
    parser.add_argument('--preserved-root',type=Path,default=Path('/home/justin/github/cad-models'))
    args=parser.parse_args();params=json.loads((args.model_dir/'params.json').read_text())
    result={'status':'running','inputs':{},'preserved_revision_checks':[],'cases':[]}
    for f in ['model.py','button_module.py','mounting.py','params.json']:
        path=args.model_dir/f
        result['inputs'][f]={'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    preservation=args.model_dir/'preserved-v2-sha256.json'
    if preservation.exists():
        for relative,expected in json.loads(preservation.read_text()).items():
            path=args.preserved_root/relative
            result['preserved_revision_checks'].append({'path':str(path),'passed':path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==expected})
    variants=[('default',{}),('smaller_stroke_wider_guide',{'button_stroke':.6,'button_guide_clearance':.35}),
              ('larger_board',{'pcb_width':60.,'pcb_length':80.})]
    if 'reset_contact_screw_length' in params:
        variants.append(('lower_switch_longer_contact',{'reset_switch_height_above_pcb':5.,'boot_switch_height_above_pcb':5.,
                         'reset_contact_screw_length':12.,'boot_contact_screw_length':12.}))
    for name,changes in variants:
        c=case(name,args.model_dir,args.baseline,params|changes);result['cases'].append(c)
        print(json.dumps({'case':name,'passed':c['passed'],'checks':len(c['checks']),
                          'failures':[q for q in c['checks'] if not q['passed']]}),flush=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    result['status']='passed' if all(c['passed'] for c in result['cases']) and all(c['passed'] for c in result['preserved_revision_checks']) else 'failed'
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    raise SystemExit(0 if result['status']=='passed' else 1)


if __name__=='__main__':main()
