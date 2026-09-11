"""Verify added PCB clearance, deeper capture shelves and an exact full-model coupon."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from itertools import product
from fdm_cad.build import load_model
from build123d import Align, Box, Pos, Rot, import_step


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def box(w,d,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Box(w,d,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def check_capture(model,p,g):
    width=p['pcb_width']
    half=width/2
    extra=p['board_fit_width_extra']
    side_play=.4+extra/2
    overlap=p['board_edge_overlap']
    inner=half-overlap
    shoulder=half+side_play
    floor=p['floor']
    bottom=floor+p['solder_clearance']
    top=bottom+p['pcb_thickness']
    clamp_bottom=top+p['board_vertical_play']
    local=model['case_local_assembly'];body=local['body']
    clamps={n:s for n,s in local.items() if n.startswith('pcb_clamp_')}
    probes=[]
    for sx,sy in product((-1,1),repeat=2):
        y=sy*p['clamp_y']
        assert body.is_inside((sx*(inner+.01),y,bottom-.1))
        assert not body.is_inside((sx*(inner-.01),y,bottom-.1))
        assert body.is_inside((sx*(shoulder+.01),y,bottom+p['pcb_thickness']/2))
        assert not body.is_inside((sx*(shoulder-.01),y,bottom+p['pcb_thickness']/2))
        name=f"pcb_clamp_{'left' if sx<0 else 'right'}_{'front' if sy<0 else 'rear'}"
        assert clamps[name].is_inside((sx*(inner+.01),y,clamp_bottom+.01))
        assert not clamps[name].is_inside((sx*(inner-.01),y,clamp_bottom+.01))
        assert not clamps[name].is_inside((sx*(inner+.01),y,clamp_bottom-.01))
        # The entire intended support strip, not only a face point, is plastic.
        strip=box(overlap,8,.1,sx*(half-overlap/2),y,bottom-.1)
        assert abs(g.overlap(strip,body)-strip.volume)<1e-6
        probes.append({'side':sx,'y_mm':y,'shelf_inner_abs_x_mm':inner,'shoulder_abs_x_mm':shoulder})
    poses=[]
    for dx,dy,dz in product((-side_play,0,side_play),(-.4,0,.4),(0,p['board_vertical_play'])):
        pcb=box(width,p['pcb_length'],p['pcb_thickness'],dx,dy,bottom+dz)
        for n,s in ({'body':body}|clamps).items():
            hit=g.overlap(pcb,s);assert hit<1e-5,(dx,dy,dz,n,hit)
        poses.append([dx,dy,bottom+dz])
    assert overlap-side_play>0
    return {'actual_pcb_xyz_mm':[width,p['pcb_length'],p['pcb_thickness']],
            'fit_width_extra_total_mm':extra,'locating_gap_mm':2*shoulder,'shelf_inner_gap_mm':2*inner,
            'centered_edge_overlap_mm':overlap,'minimum_edge_overlap_mm':overlap-side_play,
            'slot_height_mm':clamp_bottom-bottom,'x_play_each_direction_mm':side_play,'y_play_each_direction_mm':.4,
            'board_top_local_z_mm':top,'probes':probes,'clear_bare_board_poses_xyz_mm':poses}


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
    assert p['pcb_width']==op['pcb_width'] and p['board_fit_width_extra']==.5
    assert abs(p['board_edge_overlap']-op['board_edge_overlap']-.5)<1e-8
    before={n:sha(full/n) for n in ('model.py','base_model.py','button_module.py','mounting.py','parameters.json')}
    new=load_model(full/'model.py',p)
    data=new['measurements'];src=data['source_local'];hw=data['pcb_fasteners']
    original=json.loads((old/'validation.json').read_text())
    capture=check_capture(new,p,g)
    assert abs(capture['locating_gap_mm']-50.3)<1e-6
    assert abs(capture['shelf_inner_gap_mm']-46.4)<1e-6
    assert abs(capture['slot_height_mm']-1.2)<1e-6
    assert abs(capture['minimum_edge_overlap_mm']-.65)<1e-6
    assert abs(src['cavity_xy'][0]-65.5)<1e-6
    assert abs(data['main_shell_xy'][0]-70.3)<1e-6
    for a,b,expected in zip(original['measurements']['overall_assembled'],data['overall_assembled'],[.5,0,0]):
        assert abs(b-a-expected)<1e-6
    widths={};reusable=[];changed={}
    for name in new['parts']:
        old_s=import_step(old/'parts'/f'{name}.step').solids()[0]
        cur=import_step(full/'parts'/f'{name}.step').solids()[0]
        delta=[b-a for a,b in zip(old_s.bounding_box().size,cur.bounding_box().size)]
        if name in ('body','lid','desk_bracket'):
            assert max(abs(a-b) for a,b in zip(delta,[.5,0,0]))<1e-6,(name,delta)
            widths[name]={'old_size_mm':list(old_s.bounding_box().size),'new_size_mm':list(cur.bounding_box().size),'increase_xyz_mm':delta}
        elif name.startswith('pcb_clamp_'):
            assert max(abs(a-b) for a,b in zip(delta,[.75,0,0]))<1e-6,(name,delta)
            assert abs(cur.volume-old_s.volume-12)<1e-5,(name,cur.volume-old_s.volume)
            changed[name]={'width_increase_mm':.75,'volume_increase_mm3':cur.volume-old_s.volume,'reason':'0.25 mm outward datum shift plus 0.5 mm deeper coverage; screw moves with datum'}
        elif name.endswith('_slider'):
            assert abs(cur.volume-old_s.volume)>1e-3,name
            # Contacts remain relative to the actual PCB, while guide moves out.
            label=name.split('_')[0]
            bp=new['buttons'][label]['params']
            assert abs(bp['tip_x']-(-p['pcb_width']/2+p['button_inset_from_left_pcb_edge']))<1e-6
            changed[name]={'volume_change_mm3':cur.volume-old_s.volume,'reason':'Guide shifts outward 0.25 mm; contact tip keeps its board-relative X position'}
        else:
            a=Pos(*(-v for v in cur.bounding_box().min))*cur
            b=Pos(*(-v for v in old_s.bounding_box().min))*old_s
            g.same(a,b,name+' reusable after placement normalization')
            reusable.append(name)
    assert len(reusable)==6 and len(changed)==6
    shifts={}
    for key in ('desk_screw_centers_xy','body_mount_centers_xy','lid_screw_centers_xy'):
        before_xy=sorted(original['measurements'][key]);after=sorted(data[key])
        assert len(before_xy)==len(after)==4
        for (ox,oy),(nx,ny) in zip(before_xy,after):
            assert abs(abs(nx)-abs(ox)-.25)<1e-6 and abs(oy-ny)<1e-6,key
        shifts[key]={'before':before_xy,'after':after}
    before_xy=sorted(original['measurements']['pcb_fasteners']['centers_local_xy_mm']);after=sorted(hw['centers_local_xy_mm'])
    for (ox,oy),(nx,ny) in zip(before_xy,after):
        assert abs(abs(nx)-abs(ox)-.25)<1e-6 and abs(oy-ny)<1e-6
    shifts['pcb_clamp_centers_local_xy_mm']={'before':before_xy,'after':after}
    assert (test/'parameters.json').read_bytes()==(full/'parameters.json').read_bytes()
    identities={}
    for a,b in [('model.py','enclosure_model.py'),('base_model.py','base_model.py'),('button_module.py','button_module.py'),('mounting.py','mounting.py')]:
        assert sha(full/a)==sha(test/b),b
        identities[b]=sha(test/b)
    actual=import_step(test/'parts/board_fit_frame.step').solids()[0]
    exported=import_step(full/'parts/body.step').solids()[0]
    bb=exported.bounding_box()
    crop=box(bb.size.X+2,bb.size.Y+2,12.2,(bb.min.X+bb.max.X)/2,(bb.min.Y+bb.max.Y)/2)
    # Retain the earlier window size; its edge is still 1.2 mm inboard of shelf.
    window=box(44,66,14.2,z=-1)
    expected=(exported & crop)-window
    diffs=[g.volume(actual-expected),g.volume(expected-actual)]
    assert max(diffs)<.001,diffs
    for name in [n for n in new['parts'] if n.startswith('pcb_clamp_')]:
        g.same(import_step(test/'parts'/f'{name}.step').solids()[0],import_step(full/'parts'/f'{name}.step').solids()[0],name+' exact full clamp')
    assert actual.is_valid and len(actual.solids())==1 and abs(actual.bounding_box().min.Z)<1e-6
    # Use the existing local cable coupon when the independently reopened
    # production crop remains identical. No duplicate cable test is needed.
    cable_test=old.parent.parent/'fit-tests/006-cable-cradle'
    crop=box(34,11.6,34.4,0,41.8)
    cbody=Pos(0,-41.8,0)*(exported & crop)
    rim=32;lid_top=34.4
    full_lid_local=Pos(0,0,lid_top)*Rot(X=180)*import_step(full/'parts/lid.step').solids()[0]
    clid=Pos(0,0,lid_top)*Rot(X=180)*Pos(0,-41.8,0)*(full_lid_local & crop)
    cable_diffs={}
    for name,expected in [('cable_fit_body',cbody),('cable_fit_lid',clid)]:
        saved=import_step(cable_test/'parts'/f'{name}.step').solids()[0]
        dv=[g.volume(saved-expected),g.volume(expected-saved)]
        assert max(dv)<.001,(name,dv)
        cable_diffs[name]={'differences_mm3':dv,'saved_step_sha256':sha(cable_test/'parts'/f'{name}.step')}
    variant_p=p|{'board_fit_width_extra':.8,'board_edge_overlap':1.4}
    variant=load_model(full/'model.py',variant_p)
    variant_capture=check_capture(variant,variant_p,g)
    assert abs(variant_capture['locating_gap_mm']-50.6)<1e-6
    assert abs(variant_capture['minimum_edge_overlap_mm']-.6)<1e-6
    assert abs(variant['measurements']['main_shell_xy'][0]-70.6)<1e-6
    zero_p=p|{'board_fit_width_extra':0.,'board_edge_overlap':.8}
    zero=load_model(full/'model.py',zero_p)
    zero_capture=check_capture(zero,zero_p,g)
    assert abs(zero_capture['locating_gap_mm']-49.8)<1e-6
    assert abs(zero_capture['shelf_inner_gap_mm']-47.4)<1e-6
    assert abs(zero['measurements']['main_shell_xy'][0]-69.8)<1e-6
    rejected=[]
    for label,override in [('negative_fit_width',{'board_fit_width_extra':-.01}),
                           ('excess_fit_width',{'board_fit_width_extra':1.01}),
                           ('excess_edge_coverage',{'board_edge_overlap':1.51}),
                           ('zero_retained_edge',{'board_fit_width_extra':1.,'board_edge_overlap':.9})]:
        try:
            load_model(full/'model.py',p|override)
        except ValueError as error:
            rejected.append({'case':label,'overrides':override,'error':str(error)})
        else:
            raise AssertionError('Unsafe parameter case accepted: '+label)
    assert before=={n:sha(full/n) for n in before},'Source changed during checks'
    report={
        'status':'passed','checker_sha256':sha(__file__),'geometry_helper_sha256':sha(helper_path),
        'source_revision':full.name,'baseline_revision':old.name,'source_hashes':before,
        'full_export_hashes':{n:sha(full/'parts'/f'{n}.step') for n in new['parts']},
        'baseline_export_hashes':{n:sha(old/'parts'/f'{n}.step') for n in new['parts']},
        'width_changes':widths,'other_changed_parts':changed,'physically_reusable_geometry_after_translation':reusable,
        'fastener_center_changes':shifts,'overall_size_mm':data['overall_assembled'],
        'nominal_capture':capture,'variant_capture':variant_capture,
        'zero_extra_width_capture':zero_capture,'rejected_parameter_cases':rejected,
        'coupon':{'test':test.name,'matched_sources':identities,'model_sha256':sha(test/'model.py'),'frame_step_sha256':sha(test/'parts/board_fit_frame.step'),'exact_crop_differences_mm3':diffs,'frame_size_mm':list(actual.bounding_box().size),'all_four_full_clamps_preserved':True},
        'existing_cable_coupon_reuse':{'test':'006-cable-cradle','exact_production_crop_comparison':cable_diffs},
        'physical_fit_tested':False,
        'limitations':['Bare-board poses do not check components/solder or bowed PCB; deeper top/bottom capture needs actual bare board.','Measured button Y spacing and 3.3 mm inset remain a separate actuator layout task.','Open low frame omits central underside collision, upper shell, full stiffness/warping, full-height tool access and strength.'],
    }
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'passed','changed_parts':list(widths)+list(changed),'reusable_part_count':len(reusable),'nominal_locating_gap_mm':capture['locating_gap_mm'],'coupon_difference_mm3':diffs,'cable_coupon_006_reusable':True}))


if __name__=='__main__':
    main()
