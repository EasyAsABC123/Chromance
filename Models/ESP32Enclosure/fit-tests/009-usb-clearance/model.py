"""Actual revision014 measured USB clearance on a low, open production fit frame.

The frame is cropped from the production body and has the same coupon-only
44x66 mm floor window as test007. Button parts and clamps retain exact production
geometry and print orientation. Reference electronics/hardware are not printed.
"""
from math import pi
from pathlib import Path

from fdm_cad.build import load_model
from build123d import Align, Box, Cylinder, Pos, Rot


def box(w,d,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Box(w,d,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def x_cylinder(r,h,x,y,z):
    return Pos(x,y,z)*Rot(Y=90)*Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def build(params):
    full=load_model(Path(__file__).with_name('enclosure_model.py'),params)
    p=params
    info=full['measurements']['pcb_fasteners']
    body=full['case_local_assembly']['body']
    height=info['clamp_top_local_z_mm']
    bounds=body.bounding_box()
    lower=[bounds.min.X-1,bounds.min.Y-1,0]
    upper=[bounds.max.X+1,bounds.max.Y+1,height]
    crop=Pos(*lower)*Box(*(b-a for a,b in zip(lower,upper)),align=(Align.MIN,Align.MIN,Align.MIN))
    win_w,win_l=p['pcb_width']-5,p['pcb_length']-4
    if p['pcb_width']/2-p['board_edge_overlap']-win_w/2 < 1-1e-8:
        raise ValueError('Floor window would approach the production ledges')
    window=box(win_w,win_l,height+2,z=-1)
    frame=(body & crop)-window
    selected={n:s for n,s in full['case_local_assembly'].items()
              if n.startswith(('pcb_clamp_','reset_','boot_'))}
    if len(selected)!=12:
        raise ValueError('Expected four clamps and eight button print parts')
    assembly={'button_fit_frame':frame}|selected
    parts={'button_fit_frame':frame}|{n:full['parts'][n] for n in selected}
    for name,shape in parts.items():
        if not shape.is_valid or len(shape.solids())!=1 or abs(shape.bounding_box().min.Z)>.001:
            raise ValueError(f'{name} must be one solid in production print orientation on Z0')
    inverse=full['mount_transform'].inverse()
    hardware={n:inverse*s for n,s in full['hardware'].items()
              if n.startswith(('pcb_clamp_','reset_','boot_'))}
    expected=[]
    for entry in full['expected_hardware_intersections']:
        if entry['hardware'] in hardware:
            expected.append(entry|{'printed':'button_fit_frame' if entry['printed']=='body' else entry['printed']})
    # Short cartridge inserts are not in the production hardware STEP. These
    # four reference rings follow the exact existing body pilots; no CAD cuts
    # are added. OD4.6/length4 remain provisional purchased-hardware assumptions.
    mounting_inserts=[]
    for name,data in full['buttons'].items():
        bp=data['params']
        for index,dy in enumerate((-bp['mount_hole_y_spacing']/2,bp['mount_hole_y_spacing']/2),1):
            x,y,z=bp['mounting_face_x'],bp['housing_y']+dy,bp['mount_hole_z']
            key=f'{name}_body_insert_{index}'
            insert=x_cylinder(2.3,4.0,x,y,z)-x_cylinder(1.51,4.2,x-.1,y,z)
            hardware[key]=insert
            mounting_inserts.append(key)
            expected.append({'hardware':key,'printed':'button_fit_frame',
                'reason':'Provisional short heat-set insert intentionally displaces its body pilot',
                'nominal_displaced_envelope_volume_mm3':pi/4*(4.6**2-p['button_insert_pilot_diameter']**2)*4.0})
    pcb=box(p['pcb_width'],p['pcb_length'],p['pcb_thickness'],z=info['board_bottom_local_z_mm'])
    xplay=.4+p['board_fit_width_extra']/2
    tips={name:{'center_local_xy_mm':[data['params']['tip_x'],data['params']['tip_y']],
                'from_left_mm':data['params']['tip_x']+p['pcb_width']/2,
                'from_bottom_mm':data['params']['tip_y']+p['pcb_length']/2,
                'switch_top_z_provisional_mm':data['params']['switch_top_z'],
                'housing_y_mm':data['params']['housing_y']}
          for name,data in full['buttons'].items()}
    replacement_names=('reset_slider','boot_slider','boot_frame')
    replacement_parts={n:parts[n] for n in replacement_names}
    # The plug is a conservative straight rectangular envelope, not a tapered reconstruction.
    board_top=info['board_top_local_z_mm']
    usb_lower=[-p['pcb_width']/2-p['usb_plug_projection'],
        -p['pcb_length']/2+p['usb_center_from_bottom']-p['usb_plug_width']/2,
        board_top+p['usb_plug_underside_above_pcb']]
    usb_upper=[-p['pcb_width']/2,
        -p['pcb_length']/2+p['usb_center_from_bottom']+p['usb_plug_width']/2,
        board_top+p['usb_plug_underside_above_pcb']+p['usb_plug_thickness']]
    usb_reference=Pos(*usb_lower)*Box(*(b-a for a,b in zip(usb_lower,usb_upper)),align=(Align.MIN,Align.MIN,Align.MIN))
    lid_plane=full['reference_measurements']['pcb_top_z']+p['component_clearance']
    return {
        'title':'Measured USB clearance / test009',
        'parts':parts,'assembly':assembly,'hardware':hardware,
        'expected_hardware_intersections':expected,'cartridge_insert_names':mounting_inserts,
        'reference_pcb':pcb,'full_model':full,'crop_volume':crop,'floor_window':window,
        'replacement_parts':replacement_parts,'reference_usb':usb_reference,
        'measurements':{
            'source_revision':'014-usb-clearance',
            'coordinate_system':'Case print frame: floor Z0, terminals +Y, USB/buttons -X; bench press is -Z, mounted press is world+Z',
            'pcb_xyz_mm':[p['pcb_width'],p['pcb_length'],p['pcb_thickness']],
            'frame_height_mm':height,'crop_bounds_local_mm':[lower,upper],
            'coupon_floor_window_xy_mm':[win_w,win_l],
            'board_bottom_z_mm':info['board_bottom_local_z_mm'],
            'board_top_z_mm':info['board_top_local_z_mm'],
            'locating_gap_width_mm':p['pcb_width']+2*xplay,
            'x_play_each_direction_mm':xplay,'y_play_each_direction_mm':.4,
            'vertical_play_mm':p['board_vertical_play'],
            'board_slot_height_mm':p['pcb_thickness']+p['board_vertical_play'],
            'nominal_edge_overlap_mm':p['board_edge_overlap'],
            'minimum_edge_overlap_mm':p['board_edge_overlap']-xplay,
            'button_tips':tips,'lid_inner_plane_local_z_mm':lid_plane,
            'button_stroke_mm':p['button_stroke'],
            'nominal_idle_gap_mm':p['button_stroke']-p['modeled_switch_depression'],
            'nominal_switch_depression_mm':p['modeled_switch_depression'],
            'pcb_fasteners':info,
            'printed_part_count':len(parts),'hardware_proxy_count':len(hardware),
            'all_parts_cad_volume_cm3':sum(float(s.volume) for s in parts.values())/1000,
            'replacement_parts':list(replacement_names),
            'replacement_parts_cad_volume_cm3':sum(float(s.volume) for s in replacement_parts.values())/1000,
            'usb_measured_envelope':{'width_mm':p['usb_plug_width'],'thickness_mm':p['usb_plug_thickness'],
                'projection_past_perfboard_edge_mm':p['usb_plug_projection'],'center_from_bottom_mm':p['usb_center_from_bottom'],
                'underside_above_pcb_mm':p['usb_plug_underside_above_pcb'],
                'top_above_pcb_mm':p['usb_plug_underside_above_pcb']+p['usb_plug_thickness'],
                'cable_diameter_mm':p['usb_cable_diameter'],
                'nominal_bounds_local_mm':[usb_lower,usb_upper],
                'shape_assumption':'Straight rectangular plug box; taper and cable bend are not reconstructed'},
            'cartridge_insert_assumptions':{'length_mm':4.0,'outside_diameter_mm':4.6,
                'pilot_diameter_mm':p['button_insert_pilot_diameter'],'pilot_depth_mm':p['button_insert_bore_depth']},
            'physical_fit_tested':False,
            'scope':'Actual board retention, cartridge interfaces and button parts; center floor and upper enclosure/lid/bracket omitted',
        },
        'notes':[
            'For an existing revision013 assembly or test008/test007 frame, print the RESET slider, BOOT slider and BOOT frame after the archived reuse comparison passes. replacements-only.3mf contains these three exact production parts.',
            'For a new setup, print the thirteen-part layout: low frame, four clamps and both four-piece button cartridges. All interfaces and button print orientations are exact revision014 geometry.',
            'Keep 100% scale and use the intended final filament, nozzle, layer height and compensation. Sliders retain their production pad-face-down orientation and need local support under the elevated arms/guides; protect sliding and magnet-fit surfaces.',
            'Hardware: four M3x5 PCB inserts and four M3x6 clamp screws; four short M3x4 cartridge inserts and four M3x18 mounting screws; two M3x5 contact inserts, two M3x12 nylon adjusters, two nylon jam nuts and four 4x2 mm magnets. Actual insert OD/pilot fit remains provisional.',
            'Heat-set before fitting the PCB or magnets. Install the board and its clamps before the cartridges. Do not substitute M3x8 PCB screws or metal contact screws.',
            'The frame uses the same low crop and central floor window as test007. It does not check central underside solder clearance, full-height walls, lid/tool access or case stiffness.',
            f'Place the 49x70x1 mm board on the ledges at Z{info["board_bottom_local_z_mm"]:g}; align by equal side/end gaps before checking the nominal measured tip centers. The board can move +/-{xplay:g} mm in X and+/-0.4 mm inY, so verify contact at its movement limits too.',
            'Switch XY is measured; switch height/travel remain provisional. Back the nylon tips away first, then adjust with the real board. Confirm both switches release at rest and that the printed stops act before damaging switch overtravel.',
            'Place like magnet poles facing each other. Check smooth return and repeatable hard stops through the entire stroke; magnetic force and actual sliding fit need physical testing.',
            'After a first bench check, support the board while inverting the jig and test press-up operation with the PCB seated against its clamps. Its 0.2 mm vertical play changes the effective idle gap.',
            'Fit the actual USB plug and route the actual wiring during travel checks. The shortened frame cannot establish every full-shell connector clearance; the preserved production interface and any digital probe are not a substitute for the real plug.',
            'The measured USB plug is modeled conservatively as a 10 mm wide, 6 mm thick box projecting 20 mm beyond the board edge, centered 23 mm from the bottom, with underside 9 mm above the PCB. Cable diameter is 3.5 mm. Nominal and PCB-play probe results are reported separately; do not infer physical fit at all board positions. This USB measurement does not resize the unchanged 8 mm power-cable cradle.',
            f'The omitted lid inner face is local Z{lid_plane:g}. Measure the adjusted contact head against that plane or close the real lid during the three-part trial; no fictitious component height or extra printed gauge is included.',
        ],
    }
