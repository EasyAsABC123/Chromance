"""Extract revision009's actual cable anchor, exit wall and lid into a quick fit print."""
from pathlib import Path

from fdm_cad.build import load_model
from build123d import Align, Box, Pos, Rot


def build(params):
    full = load_model(Path(__file__).with_name('enclosure_model.py'), params)
    info = full['measurements']['cable_retention']
    lower, upper = info['coupon_bounds_local_mm']
    crop = Pos(*lower)*Box(*(b-a for a,b in zip(lower,upper)),
                          align=(Align.MIN,Align.MIN,Align.MIN))
    cropped = {name: full['case_local_assembly'][name] & crop for name in ('body','lid')}
    shift = Pos(-(lower[0]+upper[0])/2, -(lower[1]+upper[1])/2, 0)
    assembled = {f'cable_fit_{name}':shift*shape for name,shape in cropped.items()}
    parts = {'cable_fit_body':assembled['cable_fit_body']}
    lid = Rot(180,0,0)*assembled['cable_fit_lid']
    parts['cable_fit_lid'] = Pos(0,0,-lid.bounding_box().min.Z)*lid
    assert abs(parts['cable_fit_body'].bounding_box().min.Z) < .001
    # Reference solids are never included in printable parts or assembly STEP.
    refs = {name:shift*shape for name,shape in full['cable_retention_references_local'].items()}
    return {
        'parts': parts, 'assembly':assembled,
        'title':'Cable retention / quick fit test 003',
        'reference_geometry':refs,
        'coupon_crop_local':crop,
        'full_model':full,
        'measurements':{
            'source_revision':'009-cable-retention',
            'crop_bounds_in_enclosure_local_mm':[lower,upper],
            'cable_retention':info,
            'physical_fit_tested':False,
            'physical_load_tested':False,
            'scope':'Exact end-wall/body crop and matching lid crop; cable/tie threading, seating and closure only. Full shell stiffness, electronics fit and pull strength are not established.',
        },
        'notes':[
            'Quick iterative fit print extracted from the full revision009 source and parameters at true scale; previous fit tests remain preserved.',
            'Print the body floor-down and the lid exterior-down, matching the full enclosure. Use the intended final material, nozzle, layer height and compensation; these are not a slicer project or G-code.',
            'Start with supports off for the new anchor, inspect its ramp and tie passage in your slicer, and avoid support scars in cable/tie contact surfaces.',
            'Thread the actual zip tie through the passage, place the cable against the rounded support, then snug the tie around both. Check head position and trimming access before tightening.',
            'Seat the matching lid section by hand; it must sit flush without compressing the cable or zip-tie head. This coupon has no lid screws and does not test the full lid joint.',
            'Record cable/bundle dimensions, tie dimensions, material and print settings, whether threading/closure work, any sharp contact or slipping during gentle handling, and any measured clearance error.',
            'Physical results are pending. Do not infer a rated strain-relief force, full enclosure fit, whole-shell stiffness or long-term material behavior from this coupon.',
        ],
    }
