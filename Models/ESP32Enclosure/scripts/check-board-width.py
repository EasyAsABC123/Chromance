"""Verify the 3 mm narrowing, measured PCB capture and exact quick-print STEP crop."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from itertools import product
from fdm_cad.build import load_model
from build123d import Align, Box, Pos, import_step


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def box(w,d,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Box(w,d,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('full','baseline','test','output'):
        parser.add_argument('--'+flag,type=Path,required=True)
    args=parser.parse_args()
    full,old,test=args.full.resolve(),args.baseline.resolve(),args.test.resolve()
    helper_path=Path(__file__).with_name('check-pcb-heatsets.py')
    spec=importlib.util.spec_from_file_location('pcb_geometry_helpers',helper_path)
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    p=json.loads((full/'parameters.json').read_text())
    op=json.loads((old/'parameters.json').read_text())
    assert [p[k] for k in ('pcb_width','pcb_length','pcb_thickness')]==[49,70,1]
    assert op['pcb_width']-p['pcb_width']==3
    new=load_model(full/'model.py',p)
    data=new['measurements'];src=data['source_local'];hw=data['pcb_fasteners']
    original=json.loads((old/'validation.json').read_text())
    assert abs(src['pcb_top_z']-10)<1e-6 and abs(hw['post_rim_local_z_mm']-10.2)<1e-6
    assert abs(src['pcb_bottom_z']-9)<1e-6
    assert abs(hw['clamp_underside_local_z_mm']-src['pcb_bottom_z']-1.2)<1e-6
    assert abs(src['cavity_xy'][0]-65)<1e-6
    assert abs(data['main_shell_xy'][0]-69.8)<1e-6
    for a,b,expected in zip(original['measurements']['overall_assembled'],data['overall_assembled'],[3,0,0]):
        assert abs(a-b-expected)<1e-6
    widths={};reusable=[]
    for name in new['parts']:
        old_s=import_step(old/'parts'/f'{name}.step').solids()[0]
        cur=import_step(full/'parts'/f'{name}.step').solids()[0]
        if name in ('body','lid','desk_bracket'):
            delta=[a-b for a,b in zip(old_s.bounding_box().size,cur.bounding_box().size)]
            assert max(abs(a-b) for a,b in zip(delta,[3,0,0]))<1e-6,(name,delta)
            widths[name]={'old_size_mm':list(old_s.bounding_box().size),'new_size_mm':list(cur.bounding_box().size),'reduction_xyz_mm':delta}
        else:
            # Printing coordinates can shift when the assembly gets narrower.
            a=Pos(*(-v for v in cur.bounding_box().min))*cur
            b=Pos(*(-v for v in old_s.bounding_box().min))*old_s
            g.same(a,b,name+' reusable after placement normalization')
            reusable.append(name)
    assert len(reusable)==12
    shifts={}
    for key in ('desk_screw_centers_xy','body_mount_centers_xy','lid_screw_centers_xy'):
        before=sorted(original['measurements'][key]);after=sorted(data[key])
        assert len(before)==len(after)==4
        for (ox,oy),(nx,ny) in zip(before,after):
            assert abs(abs(ox)-abs(nx)-1.5)<1e-6 and abs(oy-ny)<1e-6,key
        shifts[key]={'before':before,'after':after}
    before=sorted(original['measurements']['pcb_fasteners']['centers_local_xy_mm'])
    after=sorted(hw['centers_local_xy_mm'])
    for (ox,oy),(nx,ny) in zip(before,after):
        assert abs(abs(ox)-abs(nx)-1.5)<1e-6 and abs(oy-ny)<1e-6
    shifts['pcb_clamp_centers_local_xy_mm']={'before':before,'after':after}
    body=new['case_local_assembly']['body']
    clamps={n:s for n,s in new['case_local_assembly'].items() if n.startswith('pcb_clamp_')}
    # Independent point probes locate the shelf edge, shoulder and clamp face.
    for sx,sy in product((-1,1),repeat=2):
        y=sy*17
        assert body.is_inside((sx*23.71,y,8.9))
        assert not body.is_inside((sx*23.69,y,8.9))
        assert body.is_inside((sx*24.91,y,9.5))
        assert not body.is_inside((sx*24.89,y,9.5))
        name=f"pcb_clamp_{'left' if sx<0 else 'right'}_{'front' if sy<0 else 'rear'}"
        assert clamps[name].is_inside((sx*24.1,y,10.21))
        assert not clamps[name].is_inside((sx*24.1,y,10.19))
    poses=[]
    # Bare substrate only; actual solder/components are a physical coupon check.
    for dx,dy,dz in product((-.4,0,.4),(-.4,0,.4),(0,.2)):
        pcb=box(49,70,1,dx,dy,9+dz)
        for n,s in ({'body':body}|clamps).items():
            hit=g.overlap(pcb,s);assert hit<1e-5,(dx,dy,dz,n,hit)
        poses.append([dx,dy,9+dz])
    assert (test/'parameters.json').read_bytes()==(full/'parameters.json').read_bytes()
    identities={}
    for a,b in [('model.py','enclosure_model.py'),('base_model.py','base_model.py'),('button_module.py','button_module.py'),('mounting.py','mounting.py')]:
        assert sha(full/a)==sha(test/b),b
        identities[b]=sha(test/b)
    actual=import_step(test/'parts/board_fit_frame.step').solids()[0]
    exported=import_step(full/'parts/body.step').solids()[0]
    bb=exported.bounding_box()
    crop=box(bb.size.X+2,bb.size.Y+2,12.2,(bb.min.X+bb.max.X)/2,(bb.min.Y+bb.max.Y)/2)
    window=box(44,66,14.2,z=-1)
    expected=(exported & crop)-window
    diffs=[g.volume(actual-expected),g.volume(expected-actual)]
    assert max(diffs)<.001,diffs
    for name in clamps:
        g.same(import_step(test/'parts'/f'{name}.step').solids()[0],import_step(full/'parts'/f'{name}.step').solids()[0],name+' exact full clamp')
    # Exact shelf/boss/root preservation through coupon top, outside its window.
    assert g.overlap(window,box(1.6,8,12.2,24.5,17))<1e-6
    assert actual.is_valid and len(actual.solids())==1 and abs(actual.bounding_box().min.Z)<1e-6
    report={
        'status':'passed','checker_sha256':sha(__file__),'geometry_helper_sha256':sha(helper_path),
        'source_revision':full.name,'baseline_revision':old.name,
        'source_hashes':{n:sha(full/n) for n in ('model.py','base_model.py','button_module.py','mounting.py','parameters.json')},
        'full_export_hashes':{n:sha(full/'parts'/f'{n}.step') for n in new['parts']},
        'baseline_export_hashes':{n:sha(old/'parts'/f'{n}.step') for n in new['parts']},
        'replacement_parts':widths,'physically_reusable_print_geometry_after_translation':reusable,
        'fastener_center_changes':shifts,'overall_size_mm':data['overall_assembled'],
        'main_shell_width_mm':69.8,'cavity_width_mm':65,'pcb_xyz_mm':[49,70,1],
        'capture':{'ledge_inner_gap_mm':47.4,'locating_gap_mm':49.8,'slot_height_mm':1.2,'minimum_edge_overlap_mm':.4,'bare_pcb_collision_free_poses_xyz_mm':poses},
        'coupon':{'test':test.name,'matched_sources':identities,'model_sha256':sha(test/'model.py'),'frame_step_sha256':sha(test/'parts/board_fit_frame.step'),'exact_crop_differences_mm3':diffs,'frame_size_mm':list(actual.bounding_box().size),'all_four_full_clamps_preserved':True},
        'physical_fit_tested':False,
        'limitations':['Sampled bare-board poses do not check components/solder or bowed PCB.','Measured 14 mm button spacing and 3.3 mm inset still need a separate actuator layout; current button alignment is provisional.','Open low frame omits upper shell and central underside collision, full stiffness/warping, full-height tool access and strength.'],
    }
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'passed','replacement_parts':list(widths),'reusable_part_count':len(reusable),'board_poses':len(poses),'coupon_difference_mm3':diffs}))


if __name__=='__main__':
    main()
