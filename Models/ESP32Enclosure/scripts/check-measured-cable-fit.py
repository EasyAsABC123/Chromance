"""Compare the quick cable test against independently reopened full-part STEP exports."""
import argparse
import hashlib
import json
from pathlib import Path
import fdm_cad.build
from build123d import Align, Box, Pos, Rot, import_step


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def volume(shape):
    if shape is None:
        return 0.0
    if hasattr(shape,'solids'):
        return sum(abs(float(s.volume)) for s in shape.solids())
    return sum(volume(s) for s in shape)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full',type=Path,required=True)
    parser.add_argument('--test',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    full,test=args.full.resolve(),args.test.resolve()
    params=json.loads((full/'parameters.json').read_text())
    assert (test/'parameters.json').read_bytes()==(full/'parameters.json').read_bytes()
    matched={}
    for src,dest in [('model.py','enclosure_model.py'),('base_model.py','base_model.py'),('button_module.py','button_module.py'),('mounting.py','mounting.py')]:
        assert digest(full/src)==digest(test/dest),dest
        matched[dest]=digest(test/dest)
    validation=json.loads((test/'validation.json').read_text())
    assert params['cable_diameter_provisional']==8.0, 'Expected measured8 mm cable preset'
    assert validation['status']=='passed' and set(validation['parts'])=={'cable_fit_body','cable_fit_lid'}
    bounds=validation['measurements']['crop_bounds_in_enclosure_local_mm']
    lo,hi=bounds
    crop=Pos(*lo)*Box(*(b-a for a,b in zip(lo,hi)),align=(Align.MIN,Align.MIN,Align.MIN))
    shift=Pos(-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,0)
    rim=params['floor']+params['solder_clearance']+params['pcb_thickness']+params['component_clearance']
    lid_top=rim+params['lid_thickness']
    full_body=import_step(full/'parts/body.step').solids()[0]
    full_lid_local=Pos(0,0,lid_top)*Rot(180,0,0)*import_step(full/'parts/lid.step').solids()[0]
    expected_body=shift*(full_body & crop)
    expected_lid=Pos(0,0,lid_top)*Rot(180,0,0)*shift*(full_lid_local & crop)
    details={}
    for name,expected in [('cable_fit_body',expected_body),('cable_fit_lid',expected_lid)]:
        path=test/'parts'/f'{name}.step'
        actual=import_step(path).solids()[0]
        added,missing=volume(actual-expected),volume(expected-actual)
        assert added<.001 and missing<.001,(name,added,missing)
        assert actual.is_valid and len(actual.solids())==1 and abs(actual.bounding_box().min.Z)<.001,name
        details[name]={'added_vs_full_step_crop_mm3':added,'missing_vs_full_step_crop_mm3':missing,'size_mm':list(actual.bounding_box().size),'volume_mm3':float(actual.volume),'step_sha256':digest(path)}
    full_info=json.loads((full/'validation.json').read_text())['measurements']['cable_retention']
    change_lo,change_hi=full_info['local_change_bounds_mm']
    assert all(a<=b for a,b in zip(lo,change_lo)) and all(a>=b for a,b in zip(hi,change_hi))
    assert lo[0]<=-params['end_cable_width']/2-4 and hi[0]>=params['end_cable_width']/2+4
    assert hi[2]>=lid_top and lo[2]==0
    report={'status':'passed','kind':'Source identity and independent STEP crop comparison','source_revision':full.name,'matched_source_hashes':matched,'parameters_sha256':digest(test/'parameters.json'),'checker_sha256':digest(__file__),'full_step_hashes':{name:digest(full/'parts'/f'{name}.step') for name in ('body','lid')},'parts':details,'full_anchor_region_preserved':True,'print_orientation_matches_full_parts':True,'physical_fit_tested':False,'physical_strength_tested':False,'scope':'Local threading, seating and lid-clearance coupon; full-shell stiffness and wiring/board fit remain outside this crop.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'passed','parts':details}))


if __name__=='__main__':
    main()
