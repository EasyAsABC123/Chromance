"""Revision 011: narrow the full enclosure by 3 mm and add a concave cable cradle.

Measured PCB is 49 x 70 x 1 mm; its top remains at local Z10. The open cradle
uses an 8.4 mm cylindrical cut for the measured 8 mm cable. Button Y positions
remain provisional pending a dedicated mechanism revision for the measured spacing.
Cable/tie/head references are excluded from all printed part collections.
"""
from copy import deepcopy
from math import isfinite, pi
from pathlib import Path
import importlib.util

from build123d import Align, Axis, Box, Cylinder, Plane, Polygon, Pos, Rot, chamfer, extrude


def _module(filename):
    path=Path(__file__).resolve().parent/filename
    spec=importlib.util.spec_from_file_location('downward_'+path.stem,path)
    module=importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
    return module


_base=_module('base_model.py')
MOUNT_DEFAULTS={
    'desk_gap_above_case_floor':2.0,
    'bracket_leg_width_y':8.6,
    'bracket_belt_clearance':0.6,
    'bracket_root_gusset_height':4.0,
    'finger_pad_extension':7.0,
}
CABLE_DEFAULTS={
    'cable_cradle_radial_clearance':0.2,
    'cable_cradle_side_wall':2.0,
    'cable_cradle_floor_above_tunnel':2.0,
    'cable_saddle_projection':7.0,
    'cable_saddle_wall_overlap':1.0,
    'cable_diameter_provisional':8.0,
    'zip_tie_width_provisional':2.5,
    'zip_tie_thickness_provisional':1.0,
    'zip_tie_slot_side_clearance':0.35,
    'zip_tie_slot_vertical_clearance':0.2,
    'zip_tie_slot_floor_below_sill':1.0,
    'zip_tie_head_width_provisional':5.0,
    'zip_tie_head_length_provisional':5.0,
    'zip_tie_head_height_provisional':4.0,
}
DEFAULTS=_base.DEFAULTS | _base.BUTTON_DEFAULTS | MOUNT_DEFAULTS | CABLE_DEFAULTS


def _box(w,d,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Box(w,d,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def _cylinder(r,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))


def _bounds(shapes):
    boxes=[s.bounding_box() for s in shapes]
    return [[min(tuple(b.min)[i] for b in boxes) for i in range(3)],
            [max(tuple(b.max)[i] for b in boxes) for i in range(3)]]


def _overlap(a,b):
    aa,bb=a.bounding_box(),b.bounding_box()
    if any(min(tuple(aa.max)[i],tuple(bb.max)[i])-max(tuple(aa.min)[i],tuple(bb.min)[i])<1e-8 for i in range(3)):
        return 0.0
    common=a.intersect(b)
    if common is None:return 0.0
    members=[common] if hasattr(common,'solids') else list(common)
    return sum(abs(float(s.volume)) for m in members for s in m.solids())


def _cable_saddle(p, cavity_end_y, sill_z, rim_z):
    """Subtract an open-top cylindrical cable seat from a wall-rooted block.

    Local coordinates follow body print orientation. Cable and groove run +Y.
    The tie feeds along X through the45-degree roofed tunnel under the groove.
    The returned cable is seated at the bottom of the clearance groove, rather
    than floating concentrically inside it. Tie/head shapes are loose routing
    envelopes; final flexible tie bends and grip require the physical coupon.
    """
    projection=p['cable_saddle_projection']; overlap=p['cable_saddle_wall_overlap']
    cable_d=p['cable_diameter_provisional']
    radial_clearance=p['cable_cradle_radial_clearance']
    side_wall=p['cable_cradle_side_wall']
    floor_thickness=p['cable_cradle_floor_above_tunnel']
    groove_radius=cable_d/2+radial_clearance
    half_width=groove_radius+side_wall
    tie_w=p['zip_tie_width_provisional']; tie_t=p['zip_tie_thickness_provisional']
    gap_y=p['zip_tie_slot_side_clearance']; gap_z=p['zip_tie_slot_vertical_clearance']
    slot_w=tie_w+2*gap_y
    y0=cavity_end_y-projection; y1=cavity_end_y+overlap
    tie_y=(y0+cavity_end_y)/2
    slot_bottom=sill_z-p['zip_tie_slot_floor_below_sill']
    slot_eave=slot_bottom+tie_t+2*gap_z
    slot_apex=slot_eave+slot_w/2
    groove_bottom=slot_apex+floor_thickness
    groove_center_z=groove_bottom+groove_radius
    block_top=groove_center_z
    root_z=sill_z-projection
    head_w=p['zip_tie_head_width_provisional']
    head_l=p['zip_tie_head_length_provisional']
    head_h=p['zip_tie_head_height_provisional']
    if not 0.1<=radial_clearance<=0.4:
        raise ValueError('Cradle radial cable clearance must be0.1..0.4 mm pending coupon fit')
    if not 2.0<=side_wall<=2.8 or not 2.0<=floor_thickness<=3.0:
        raise ValueError('Cradle needs2..2.8 mm side walls and2..3 mm floor over the tunnel')
    if not 6.0<=projection<=p['end_margin']-1.5:
        raise ValueError('Cradle must retain1.5 mm nominal space beyond the PCB end')
    if not 0.6<=overlap<=p['wall']-0.6:
        raise ValueError('Cradle must overlap the end wall without extending outside it')
    if not 4<=cable_d<=8:
        raise ValueError('Cable diameter must be4..8 mm for this exit')
    if not 2<=tie_w<=3.2 or not 0.7<=tie_t<=1.2:
        raise ValueError('Tie band envelope must be2..3.2 mm wide and0.7..1.2 mm thick')
    if not 0.25<=gap_y<=0.5 or not 0.1<=gap_z<=0.3:
        raise ValueError('Tie clearances must stay0.25..0.5 mm per side and0.1..0.3 vertically')
    if root_z<p['floor']+2:
        raise ValueError('Cradle root must start at least2 mm above the floor')
    tunnel_floor=slot_bottom-(sill_z-projection/2+slot_w/2)
    if tunnel_floor<0.8-1e-8:
        raise ValueError('Tunnel must retain0.8 mm over the underside wedge at its inboard eave')
    if slot_w>projection-2.5:
        raise ValueError('Tunnel must leave end material to connect the cradle')
    if groove_bottom<sill_z+2:
        raise ValueError('Cable seat must stay at least2 mm above the existing exit sill')
    # The subtraction is the actual concave surface, with its center at the
    # block top so the complete8.4 mm mouth remains open for laying in a cable.
    upper=_box(2*half_width,y1-y0,block_top-sill_z,0,(y0+y1)/2,sill_z)
    wedge=extrude(Plane.YZ*Polygon((y0,sill_z),(y1,sill_z),
        (y1,root_z),(cavity_end_y,root_z),align=None),amount=half_width,both=True)
    stock=upper+wedge
    groove=Pos(0,(y0+y1)/2,groove_center_z)*Rot(X=90)*Cylinder(
        groove_radius,y1-y0+2,align=(Align.CENTER,Align.CENTER,Align.CENTER))
    tunnel=extrude(Plane.YZ*Polygon(
        (tie_y-slot_w/2,slot_bottom),(tie_y+slot_w/2,slot_bottom),
        (tie_y+slot_w/2,slot_eave),(tie_y,slot_apex),
        (tie_y-slot_w/2,slot_eave),align=None),amount=half_width+2,both=True)
    saddle=stock-groove-tunnel
    underpass=_box(2*half_width+4,tie_w,tie_t,0,tie_y,slot_bottom+gap_z)
    loop_inner_x=half_width+0.25
    loop_outer_x=loop_inner_x+tie_t
    cable_center_z=groove_bottom+cable_d/2
    loop_bottom=slot_bottom+gap_z
    loop_inner_top=groove_bottom+cable_d+0.3
    loop_top=loop_inner_top+tie_t
    loop=_box(2*loop_outer_x,tie_w,loop_top-loop_bottom,0,tie_y,loop_bottom)
    loop-=_box(2*loop_inner_x,tie_w+2,loop_inner_top-loop_bottom-tie_t,
        0,tie_y,loop_bottom+tie_t)
    # Keep the head above the right shoulder, alongside the upper cable arc.
    # A beside-the-block head would be too wide for the preserved24 mm exit.
    head_x=half_width+0.5
    head_bottom=loop_top-head_h
    head=_box(head_w,head_l,head_h,head_x,tie_y,head_bottom)
    if min(head_w,head_l,head_h)<=0:
        raise ValueError('Provisional tie-head envelope dimensions must be positive')
    if max(loop_top,head_bottom+head_h)>rim_z-2:
        raise ValueError('Cable/tie/head envelope must stay2 mm below the lid plane')
    if max(loop_outer_x,head_x+head_w/2)>p['end_cable_width']/2-0.5:
        raise ValueError('Tie head and route need0.5 mm margin inside the cable-exit width')
    if head_bottom<block_top+0.5:
        raise ValueError('Tie head must clear the cradle shoulder by at least0.5 mm')
    if head_l>projection-0.6:
        raise ValueError('Tie-head envelope must retain access within the end-margin pocket')
    if y0<p['pcb_length']/2+1.5-1e-8:
        raise ValueError('Cradle intrudes into the reserved board-end margin')
    cable_y0=y0; cable_y1=cavity_end_y+p['wall']+6
    cable=Pos(0,(cable_y0+cable_y1)/2,cable_center_z)*Rot(X=90)*Cylinder(
        cable_d/2,cable_y1-cable_y0,align=(Align.CENTER,Align.CENTER,Align.CENTER))
    references={'cable':cable,'zip_tie_route':loop,'zip_tie_head':head,
                'zip_tie_straight_threading_segment':underpass}
    for name,shape in references.items():
        if _overlap(shape,saddle)>1e-6:
            raise ValueError(f'Cable cradle obstructs the {name} envelope')
    if _overlap(cable,head)>1e-6 or _overlap(cable,loop)>1e-6:
        raise ValueError('Loose tie/head envelopes must leave the seated cable clear')
    if not saddle.is_valid or len(saddle.solids())!=1:
        raise ValueError('Cable cradle must be one valid solid')
    region=_box(2*half_width+0.2,y1-y0+0.2,block_top-root_z+0.2,
                0,(y0+y1)/2,root_z-0.1)
    info={
        'status':'Cable diameter supplied by user; concave-cradle and tie coupon fit pending',
        'geometry':'Block minus an open-top cylindrical groove; cable seated at groove bottom',
        'cable_diameter_mm':cable_d,
        'cable_diameter_status':'user_supplied' if cable_d==8.0 else 'alternate_unmeasured_parameter',
        'cable_measurement_record':'measurements/2026-09-11-cable.json',
        'legacy_parameter_note':'cable_diameter_provisional remains an input key; default8 mm is measured. Groove clearance and tie/head values are provisional.',
        'cradle_groove_diameter_mm':2*groove_radius,
        'cradle_radial_clearance_mm':radial_clearance,
        'cradle_groove_center_local_xz_mm':[0.0,groove_center_z],
        'cradle_groove_bottom_local_z_mm':groove_bottom,
        'cradle_top_local_z_mm':block_top,
        'cradle_width_mm':2*half_width,
        'cradle_side_wall_mm':side_wall,
        'cradle_floor_above_tunnel_mm':floor_thickness,
        'cradle_cylindrical_cut_volume_mm3':float((stock & groove).volume),
        'saddle_length_y_mm':y1-y0,
        'saddle_x_range_mm':[-half_width,half_width],'saddle_y_range_mm':[y0,y1],
        'saddle_wall_root_local_z_mm':root_z,
        'saddle_underside_angle_degrees':45.0,'saddle_wall_overlap_mm':overlap,
        'cable_axis':'local+Y, world-Y','cable_diameter_provisional_mm':cable_d,
        'cable_axis_local_xz_mm':[0.0,cable_center_z],
        'tie_band_width_provisional_mm':tie_w,'tie_band_thickness_provisional_mm':tie_t,
        'tie_slot_width_y_mm':slot_w,'tie_slot_floor_local_z_mm':slot_bottom,
        'tie_slot_eave_local_z_mm':slot_eave,'tie_slot_apex_local_z_mm':slot_apex,
        'tie_slot_roof_angle_degrees':45.0,'tie_center_local_y_mm':tie_y,
        'tie_slot_side_clearance_each_mm':gap_y,'tie_slot_vertical_clearance_each_mm':gap_z,
        'crown_material_above_tunnel_apex_mm':floor_thickness,
        'minimum_tunnel_floor_above_wedge_mm':tunnel_floor,
        'tie_head_envelope_xyz_mm':[head_w,head_l,head_h],
        'tie_head_center_local_xyz_mm':[head_x,tie_y,head_bottom+head_h/2],
        'tie_head_bottom_to_shoulder_mm':head_bottom-block_top,
        'tie_and_head_top_to_lid_plane_mm':rim_z-max(loop_top,head_bottom+head_h),
        'saddle_to_nominal_pcb_end_mm':y0-p['pcb_length']/2,
        'raw_support_volume_mm3':float(saddle.volume),
        'local_change_bounds_mm':_bounds([region]),
        'coupon_bounds_local_mm':[[-p['end_cable_width']/2-4,y0-1,0],
            [p['end_cable_width']/2+4,cavity_end_y+p['wall']+p['belt_projection'],rim_z+p['lid_thickness']]],
        'installation':'With lid open, feed tie along X through the cradle tunnel, lay the insulated cable along+Y into the open concave groove, and close the tie with its head above the right shoulder. Tighten only enough to retain the jacket; leave internal slack before the electrical termination.',
        'reference_geometry':'Cable is seated on the true groove bottom. Loose rectangular tie route/head are fit/clearance envelopes, not printable parts or exact flexible bends. Bend radius, grip force and pull rating are unverified.',
    }
    return saddle,stock,tunnel,groove,region,references,info


def build(params:dict)->dict:
    unknown=set(params)-set(DEFAULTS)
    if unknown:raise ValueError(f'Unknown parameters: {sorted(unknown)}')
    p=DEFAULTS | params
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) for v in p.values()):
        raise ValueError('All model parameters must be finite numbers')
    gap=p['desk_gap_above_case_floor'];leg_y=p['bracket_leg_width_y']
    if not 1.0<=gap<=p['bracket_clearance_above_body']-p['lid_thickness']-.5:
        raise ValueError('Case-floor gap must be >=1mm and leave the lid above world Z0')
    if not 8.6<=leg_y<=8.8:
        raise ValueError('Leg Y width must be 8.6..8.8 mm to retain gusset clearance')
    if not .3<=p['bracket_belt_clearance']<=1.0:
        raise ValueError('Upper-leg belt clearance must be0.3..1.0mm')
    if not 3.0<=p['bracket_root_gusset_height']<=6.0:
        raise ValueError('Root gusset height must be3..6mm')
    if not 6.5<=p['finger_pad_extension']<=10.0:
        raise ValueError('Finger pad extension must be 6.5..10 mm')

    source_params={k:v for k,v in p.items() if k not in MOUNT_DEFAULTS and k not in CABLE_DEFAULTS}
    result=_base.build(source_params)
    original_measurements=deepcopy(result['measurements'])
    original_assembly=dict(result['assembly'])
    original_hardware=dict(result['hardware'])
    corner_info=deepcopy(original_measurements['corner_bosses'])
    corner_info['body_new_volume_mm3']=float(original_assembly['body'].volume)
    corner_info['body_old_full_height_volume_mm3']=float(result['reference_full_height_body_local'].volume)
    corner_info['body_volume_saved_mm3']=corner_info['body_old_full_height_volume_mm3']-corner_info['body_new_volume_mm3']
    corner_info['body_volume_saved_percent']=100*corner_info['body_volume_saved_mm3']/corner_info['body_old_full_height_volume_mm3']
    h=original_measurements['pcb_top_z']+p['component_clearance']
    ow,ol=original_measurements['main_shell_xy']
    plate_z=h+p['bracket_clearance_above_body']
    desk_z=plate_z+p['bracket_plate_thickness']
    ceiling=plate_z-gap
    transform=Pos(0,0,ceiling)*Rot(X=180)
    world=lambda q:[q[0],-q[1],ceiling-q[2]]
    # The flipped ear's original underside is now the upper mounting face.
    interface_z=ceiling-(h-5)
    screw_head_plane=interface_z-5
    mount_points=[(x,-y) for x,y in original_measurements['body_mount_centers_xy']]
    desk_points=original_measurements['desk_screw_centers_xy']
    lug_y=max(abs(y) for _,y in mount_points)
    inner_x=ow/2+p['belt_projection']+p['bracket_belt_clearance']
    outer_x=ow/2+12.0
    insert_od=p['button_contact_insert_outer_diameter']
    insert_length=p['button_contact_insert_length']
    insert_pilot=p['button_contact_insert_pilot_diameter']
    insert_depth=insert_length+.4
    insert_engagement=min(5.0,insert_length)
    if insert_depth-5.0<.3-1e-8:
        raise ValueError('Bracket insert bore must clear the 5 mm projection of the M3x10 screw')
    if insert_engagement<4.0:
        raise ValueError('Bracket inserts require at least 4 mm nominal screw engagement')
    inner_insert_wall=min(abs(x)-insert_od/2-inner_x for x,_ in mount_points)
    side_insert_wall=(leg_y-insert_od)/2
    if min(inner_insert_wall,side_insert_wall)<1.5-1e-8:
        raise ValueError('Bracket insert envelopes require at least 1.5 mm wall material')
    if interface_z+insert_depth+2>=plate_z-p['bracket_root_gusset_height']:
        raise ValueError('Blind bracket insert bore must stay below the top root gussets')

    # Extend only each external finger pad, in the preserved local case frame.
    # A 0.6 mm overlap fills its old top chamfer and gives one connected solid.
    case_local=dict(original_assembly)
    saddle, saddle_stock, tie_tunnel, cable_groove, saddle_region, cable_references, cable_info = _cable_saddle(
        p, p['pcb_length']/2+p['end_margin'], h-p['end_cable_height'], h)
    baseline_body=case_local['body']
    case_local['body']=baseline_body+saddle
    result['parts']['body']=_base._on_bed(case_local['body'])
    cable_info['body_before_volume_mm3']=float(baseline_body.volume)
    cable_info['body_after_volume_mm3']=float(case_local['body'].volume)
    cable_info['net_added_volume_mm3']=float(case_local['body'].volume-baseline_body.volume)
    for name,shape in case_local.items():
        if name in ('body','desk_bracket'): continue
        if _overlap(saddle,shape)>1e-6:
            raise ValueError(f'Cable retention interferes with {name}')
    for name,shape in cable_references.items():
        for part_name in ('body','lid'):
            if _overlap(shape,case_local[part_name])>1e-6:
                raise ValueError(f'Cable routing envelope {name} interferes with {part_name}')
    result['cable_retention_local']=saddle
    result['cable_retention_stock_local']=saddle_stock
    result['cable_retention_tunnel_local']=tie_tunnel
    result['cable_retention_groove_cutter_local']=cable_groove
    result['cable_retention_change_region_local']=saddle_region
    result['cable_retention_added_local']=case_local['body']-baseline_body
    result['cable_retention_reference_body_local']=baseline_body
    result['cable_retention_references_local']=cable_references
    pad_extensions={}
    for name,data in result['buttons'].items():
        bp=data['params'];gap_xy=bp['guide_clearance'];old_top=bp['arm_bottom_z']+7.8
        width=9.4-2*gap_xy
        center_x=bp['mounting_face_x']-7.1
        extra=_box(width,12,p['finger_pad_extension']+.6,center_x,bp['housing_y'],old_top-.6)
        extra=chamfer(extra.edges().group_by(Axis.Z)[-1],.5)
        slider=case_local[name+'_slider']+extra
        case_local[name+'_slider']=slider
        result['parts'][name+'_slider']=_base._on_bed(Rot(Y=180)*slider)
        at_stop_z=ceiling-old_top-p['finger_pad_extension']+bp['stroke']
        if at_stop_z>screw_head_plane-.5:
            raise ValueError('Extended finger pad must stay at least 0.5 mm below the mounting ears at full stroke')
        pad_extensions[name]={'local_z_range_mm':[old_top-.6,old_top+p['finger_pad_extension']],
            'old_face_local_z_mm':old_top,'extension_mm':p['finger_pad_extension'],
            'footprint_center_xy_mm':[center_x,bp['housing_y']],
            'footprint_xy_mm':[width,12.0],'new_top_chamfer_mm':.5,
            'minimum_ear_clearance_at_stop_mm':screw_head_plane-at_stop_z}

    bracket=_box(10,2*lug_y+14,p['bracket_plate_thickness'],z=plate_z)
    for y in (-lug_y,lug_y):
        bracket+=_box(ow+44,14,p['bracket_plate_thickness'],0,y,plate_z)
    for x,y in mount_points:
        sx=1 if x>0 else -1
        bracket+=_box(outer_x-inner_x,leg_y,plate_z-interface_z+.05,
                      sx*(inner_x+outer_x)/2,y,interface_z)
        # Root triangles distribute each long post into the desk crossbar.
        # They sit outboard of the case and print as supported tapers from the bed.
        gusset_projection=(14-leg_y)/2-.2
        for sy in (-1,1):
            edge_y=y+sy*leg_y/2
            profile=Plane.YZ*Polygon(
                (edge_y,plate_z-p['bracket_root_gusset_height']),
                (edge_y,plate_z+.05),
                (edge_y+sy*gusset_projection,plate_z+.05),align=None)
            bracket+=Pos(sx*(inner_x+outer_x)/2,0,0)*extrude(
                profile,amount=(outer_x-inner_x)/2,both=True)
        # Heat-set from the lower mounting face before fitting the enclosure.
        # Blind pilot relieves the M3x10 tip and leaves the desk-contact plate solid.
        bracket-=_cylinder(insert_pilot/2,insert_depth+.01,x,y,interface_z-.01)
    for x,y in desk_points:
        bracket-=_cylinder(p['desk_screw_clearance']/2,p['bracket_plate_thickness']+1,x,y,plate_z-.5)

    assembly={name:transform*shape for name,shape in case_local.items() if name!='desk_bracket'}
    assembly['desk_bracket']=bracket
    hardware={name:transform*shape for name,shape in original_hardware.items()}
    expected=[entry for data in result['buttons'].values() for entry in data['expected_hardware_intersections']]
    bracket_insert_names=[]
    nominal_displacement=pi*(insert_od**2-insert_pilot**2)/4*insert_length
    for index,(x,y) in enumerate(mount_points,1):
        name=f'bracket_mount_insert_{index}'
        insert=_cylinder(insert_od/2,insert_length,x,y,interface_z)
        insert-=_cylinder(1.51,insert_length+.2,x,y,interface_z-.1)
        hardware[name]=insert
        bracket_insert_names.append(name)
        expected.append({'hardware':name,'printed':'desk_bracket',
            'reason':'Heat-set insert knurls intentionally displace the smaller pre-installation pilot.',
            'nominal_displaced_envelope_volume_mm3':nominal_displacement})
    # Revision006 adds only the lid hardware. The base source creates the
    # circular blind pilots directly and no longer subtracts hex nut entries.
    lid_local={}
    lid_insert_names=[]
    lid_screw_names=[]
    lid_insert_od=p['lid_insert_outer_diameter']
    lid_insert_length=p['lid_insert_length']
    lid_pilot=p['lid_insert_pilot_diameter']
    lid_depth=p['lid_insert_bore_depth']
    lid_projection=p['lid_screw_length']-p['lid_thickness']
    lid_insert_bottom=h-lid_insert_length
    lid_bore_bottom=h-lid_depth
    lid_bearing=h+p['lid_thickness']
    lid_tip=lid_bearing-p['lid_screw_length']
    lid_displacement=pi/4*(lid_insert_od**2-lid_pilot**2)*lid_insert_length
    for index,(x,y) in enumerate(original_measurements['lid_screw_centers_xy'],1):
        insert_name=f'lid_insert_{index}'
        screw_name=f'lid_screw_{index}'
        insert=_cylinder(lid_insert_od/2,lid_insert_length,x,y,lid_insert_bottom)
        insert-=_cylinder(1.51,lid_insert_length+.2,x,y,lid_insert_bottom-.1)
        screw=_cylinder(1.5,p['lid_screw_length'],x,y,lid_tip)
        screw+=_cylinder(2.75,3.0,x,y,lid_bearing)
        lid_local[insert_name]=insert
        lid_local[screw_name]=screw
        hardware[insert_name]=transform*insert
        hardware[screw_name]=transform*screw
        lid_insert_names.append(insert_name)
        lid_screw_names.append(screw_name)
        expected.append({'hardware':insert_name,'printed':'body',
            'reason':'Only the named lid insert displaces its undersized circular pilot.',
            'nominal_displaced_envelope_volume_mm3':lid_displacement})
    for name,shape in lid_local.items():
        for part_name,part in original_assembly.items():
            if part_name=='desk_bracket':continue
            overlap=_overlap(shape,part)
            intended=lid_displacement if name in lid_insert_names and part_name=='body' else 0.0
            if abs(overlap-intended)>.001:
                raise ValueError(f'Unexpected lid hardware interference: {name}/{part_name}: {overlap:g} mm3')
    # Revision007 PCB retention: screws remain outside the board substrate.
    # Side entries/hex pockets are removed at source; capture slots stay intact.
    pcb_local={}
    pcb_insert_names=[]
    pcb_screw_names=[]
    pcb_points=original_measurements['pcb_clamp_screw_centers_xy']
    pcb_clamp_z=original_measurements['pcb_clamp_underside_z']
    pcb_insert_od=p['pcb_insert_outer_diameter']
    pcb_insert_length=p['pcb_insert_length']
    pcb_pilot=p['pcb_insert_pilot_diameter']
    pcb_depth=p['pcb_insert_bore_depth']
    pcb_boss_d=p['pcb_clamp_boss_diameter']
    pcb_bearing=pcb_clamp_z+2.0
    pcb_tip=pcb_bearing-p['pcb_clamp_screw_length']
    pcb_insert_bottom=pcb_clamp_z-pcb_insert_length
    pcb_bore_bottom=pcb_clamp_z-pcb_depth
    pcb_engagement=pcb_clamp_z-max(pcb_tip,pcb_insert_bottom)
    pcb_displacement=pi/4*(pcb_insert_od**2-pcb_pilot**2)*pcb_insert_length
    pcb_clamp_names=[n for n in original_assembly if n.startswith('pcb_clamp_')]
    for clamp_name,(x,y) in zip(pcb_clamp_names,pcb_points):
        insert_name=clamp_name+'_insert'
        screw_name=clamp_name+'_screw'
        insert=_cylinder(pcb_insert_od/2,pcb_insert_length,x,y,pcb_insert_bottom)
        insert-=_cylinder(1.51,pcb_insert_length+.2,x,y,pcb_insert_bottom-.1)
        screw=_cylinder(1.5,p['pcb_clamp_screw_length'],x,y,pcb_tip)
        screw+=_cylinder(2.75,3.0,x,y,pcb_bearing)
        pcb_local[insert_name]=insert
        pcb_local[screw_name]=screw
        hardware[insert_name]=transform*insert
        hardware[screw_name]=transform*screw
        pcb_insert_names.append(insert_name)
        pcb_screw_names.append(screw_name)
        expected.append({'hardware':insert_name,'printed':'body',
            'reason':'Only the named PCB-clamp insert displaces its reinforced circular pilot.',
            'nominal_displaced_envelope_volume_mm3':pcb_displacement})
    for name,shape in pcb_local.items():
        for part_name,part in case_local.items():
            if part_name=='desk_bracket':continue
            overlap=_overlap(shape,part)
            intended=pcb_displacement if name in pcb_insert_names and part_name=='body' else 0.0
            if abs(overlap-intended)>.001:
                raise ValueError(f'Unexpected PCB hardware interference: {name}/{part_name}: {overlap:g} mm3')
        for old_name,old in original_hardware.items():
            if _overlap(shape,old)>.001:
                raise ValueError(f'PCB clamp hardware interferes with {old_name}')
    for name,shape in (assembly | hardware).items():
        if name=='desk_bracket':continue
        overlap=_overlap(bracket,shape)
        if name in bracket_insert_names:
            if abs(overlap-nominal_displacement)>.001:
                raise ValueError(f'Unexpected insert/host displacement for {name}')
        elif overlap>.001:
            raise ValueError(f'New desk bracket interferes with {name}')
    result['expected_hardware_intersections']=expected
    result['bracket_insert_names']=bracket_insert_names
    result['lid_insert_names']=lid_insert_names
    result['lid_screw_names']=lid_screw_names
    result['lid_hardware_local']=lid_local
    result['pcb_insert_names']=pcb_insert_names
    result['pcb_screw_names']=pcb_screw_names
    result['pcb_hardware_local']=pcb_local
    result['assembly']=assembly
    result['hardware']=hardware
    result['parts']['desk_bracket']=_base._on_bed(Rot(X=180)*bracket)
    for name,shape in result['parts'].items():
        if not shape.is_valid or len(shape.solids())!=1 or shape.volume<=0:
            raise ValueError(f'Printed part {name} is not one valid connected solid')
        if abs(shape.bounding_box().min.Z)>1e-6:
            raise ValueError(f'Printed part {name} does not rest on Z0')

    mapping={'rotation_x_degrees':180.0,'translation_xyz_mm':[0.,0.,ceiling],
             'point_mapping':'world[x,y,z] = source[x,-y,ceiling-z]',
             'source_frame':'Case coordinates: 49 mm PCB, 3 mm narrower shell, PCB top at Z10, concave cable cradle',
             'world_frame':'+Z toward desk; floor faces desk; lid and finger pads face downward',
             'press_vector_world':[0.,0.,1.]}
    pads={}
    for name,data in result['buttons'].items():
        bp=data['params']
        # The exposed central flat of the original finger pad is its local +Z face.
        local_pad=[bp['mounting_face_x']-7.1,bp['housing_y'],bp['arm_bottom_z']+7.8+p['finger_pad_extension']]
        pads[name]={'at_rest_xyz_mm':world(local_pad),
                    'at_stop_xyz_mm':world([local_pad[0],local_pad[1],local_pad[2]-bp['stroke']]),
                    'surface_normal_world':[0.,0.,-1.],
                    'press_direction_world':[0.,0.,1.]}
        data['coordinate_system']='params and measurements use the preserved revision004 source frame'
        data['mount_transform']=mapping
        data['pad_world']=pads[name]
    bounds=_bounds(assembly.values())
    result['mount_transform']=transform
    result['assembly_transform']=mapping
    result['reference_assembly']=original_assembly
    result['case_local_assembly']=case_local
    result['slider_pad_extensions']=pad_extensions
    result['reference_hardware']=original_hardware
    result['reference_measurements']=original_measurements
    result['corner_supports']={name:transform*shape for name,shape in result['corner_supports_local'].items()}
    result['measurements']={
        'units':'mm','pcb_assumed':original_measurements['pcb_assumed'],
        'main_shell_xy':[ow,ol],'desk_contact_z':desk_z,
        'desk_plate_bottom_z':plate_z,'case_floor_outer_z':ceiling,
        'body_bounds_world_mm':_bounds([assembly['body']]),
        'lid_bounds_world_mm':_bounds([assembly['lid']]),
        'pcb_bounds_world_z_mm':[ceiling-original_measurements['pcb_top_z'],ceiling-original_measurements['pcb_bottom_z']],
        'pcb_component_side_normal_world':[0.,0.,-1.],
        'desk_screw_centers_xy':desk_points,
        'body_mount_centers_xy':[list(q) for q in mount_points],
        'lid_screw_centers_xy':[[x,-y] for x,y in original_measurements['lid_screw_centers_xy']],
        'lid_fasteners':{
            'insert_specification':'M3x5 heat-set, actual OD/pilot provisional',
            'insert_outer_diameter_mm':lid_insert_od,'insert_length_mm':lid_insert_length,
            'pilot_diameter_mm':lid_pilot,'pilot_depth_mm':lid_depth,
            'screw_length_mm':p['lid_screw_length'],'lid_thickness_mm':p['lid_thickness'],
            'screw_projection_into_post_mm':lid_projection,
            'nominal_insert_engagement_mm':min(lid_projection,lid_insert_length),
            'screw_tip_to_bore_bottom_mm':lid_depth-lid_projection,
            'support_shape':'Square corner pad connected to two walls, with paired underside wedges',
            'pad_square_width_mm':corner_info['pad_square_width_mm'],
            'pad_footprint_xy_mm':[corner_info['pad_square_width_mm']]*2,
            'minimum_radial_polymer_mm':corner_info['minimum_inboard_material_to_insert_mm'],
            'pilot_floor_thickness_mm':corner_info['pilot_floor_thickness_mm'],
            'post_rim_local_z_mm':h,'insert_bottom_local_z_mm':lid_insert_bottom,
            'pilot_bottom_local_z_mm':lid_bore_bottom,'screw_tip_local_z_mm':lid_tip,
            'head_bearing_local_z_mm':lid_bearing,'screw_head_diameter_mm':5.5,'screw_head_height_mm':3.0,
            'centers_local_xy_mm':original_measurements['lid_screw_centers_xy'],
            'rim_centers_world_xyz_mm':[world([x,y,h]) for x,y in original_measurements['lid_screw_centers_xy']],
            'head_bearing_centers_world_xyz_mm':[world([x,y,lid_bearing]) for x,y in original_measurements['lid_screw_centers_xy']],
            'nominal_displacement_each_mm3':lid_displacement,
            'installation':'Heat-set from the open rim with lid removed; installed screws approach upward from below in the desk orientation',
            'old_lid_hex_pockets_and_side_entries_removed':True,
        },
        'pcb_fasteners':{
            'insert_specification':'M3x5 heat-set; actual OD/pilot provisional',
            'insert_outer_diameter_mm':pcb_insert_od,'insert_length_mm':pcb_insert_length,
            'pilot_diameter_mm':pcb_pilot,'pilot_depth_mm':pcb_depth,
            'screw_length_mm':p['pcb_clamp_screw_length'],'clamp_thickness_mm':2.0,
            'screw_projection_into_post_mm':p['pcb_clamp_screw_length']-2.0,
            'nominal_insert_engagement_mm':pcb_engagement,
            'screw_tip_to_bore_bottom_mm':pcb_tip-pcb_bore_bottom,
            'boss_diameter_mm':pcb_boss_d,
            'minimum_radial_polymer_mm':(pcb_boss_d-pcb_insert_od)/2,
            'minimum_inboard_wall_to_locating_shoulder_mm':p['pcb_clamp_screw_offset_from_edge']-.4-pcb_insert_od/2,
            'boss_to_pcb_lateral_play_envelope_mm':p['pcb_clamp_screw_offset_from_edge']-pcb_boss_d/2-.4,
            'clamp_outer_hole_ligament_mm':8-p['pcb_clamp_screw_offset_from_edge']-p['m3_clearance']/2,
            'head_to_clamp_outer_edge_mm':8-p['pcb_clamp_screw_offset_from_edge']-2.75,
            'board_bottom_local_z_mm':original_measurements['pcb_bottom_z'],
            'board_top_local_z_mm':original_measurements['pcb_top_z'],
            'post_rim_local_z_mm':pcb_clamp_z,'clamp_underside_local_z_mm':pcb_clamp_z,
            'clamp_top_local_z_mm':pcb_bearing,'head_bearing_local_z_mm':pcb_bearing,
            'insert_bottom_local_z_mm':pcb_insert_bottom,'pilot_bottom_local_z_mm':pcb_bore_bottom,
            'screw_tip_local_z_mm':pcb_tip,
            'post_polymer_above_floor_below_pilot_mm':pcb_bore_bottom-p['floor'],
            'centers_local_xy_mm':pcb_points,
            'centers_world_rim_xyz_mm':[world([x,y,pcb_clamp_z]) for x,y in pcb_points],
            'centers_world_head_bearing_xyz_mm':[world([x,y,pcb_bearing]) for x,y in pcb_points],
            'screw_head_diameter_mm':5.5,'screw_head_height_mm':3.0,
            'screw_hole_outward_shift_from_006_mm':p['pcb_clamp_screw_offset_from_edge']-4.5,
            'nominal_displacement_each_mm3':pcb_displacement,
            'tool_access_probe':{'diameter_mm':6.0,'narrow_reach_from_post_rim_to_case_rim_mm':h-pcb_clamp_z,
                'nominal_side_wall_clearance_mm':p['side_margin']-p['pcb_clamp_screw_offset_from_edge']-3.0,
                'installation':'Lid and PCB clamps removed; install inserts before PCB/cartridges. BOOT cartridge must be removed for later left-front clamp screw access. Actual iron geometry must match the long narrow approach.'},
            'old_pcb_hex_pockets_and_lower_side_entries_removed':True,
            'narrow_board_capture_slots_retained':True,
        },
        'nut_trap_inventory':{
            'printed_captive_nut_pockets':0,
            'lid':'Four circular blind heat-set pilots, preserved from006',
            'pcb_clamps':'Four circular blind heat-set pilots; lower hex/side entries removed in007',
            'desk_bracket':'Four blind heat-set pilots; bracket width reduced by 3 mm',
            'actuators':'Contact heat sets; guide/magnet pockets are functional capture features',
            'unused_source_bracket':'Legacy nut cuts and nut-slot helper removed; wrapper replaces this source bracket',
            'remaining_nuts':'Two exposed nylon contact jam nuts are hardware; no printed nut traps',
        },
        'corner_bosses':corner_info,
        'cable_retention':cable_info,
        'body_mount_interface_z':interface_z,
        'body_mount_screw_head_bearing_z':screw_head_plane,
        'bracket_insert_centers_xyz':[[x,y,interface_z] for x,y in mount_points],
        'bracket_inserts':{'outer_diameter_provisional_mm':insert_od,'length_mm':insert_length,
            'pilot_diameter_provisional_mm':insert_pilot,'pilot_depth_mm':insert_depth,
            'm3x10_engagement_mm':insert_engagement,'screw_tip_clearance_mm':insert_depth-5,
            'inner_wall_to_insert_envelope_mm':inner_insert_wall,
            'y_wall_to_insert_envelope_mm':side_insert_wall,
            'nominal_displacement_each_mm3':nominal_displacement},
        'slider_pad_extensions':pad_extensions,
        'overall_assembled':[b-a for a,b in zip(*bounds)],
        'overall_bounds_world_mm':bounds,
        'mounting_orientation':mapping | {'case_floor_to_bracket_gap_mm':gap,'pads_world':pads},
        'bracket_leg_geometry':{'width_y_mm':leg_y,'height_mm':plate_z-interface_z,
            'inner_abs_x_mm':inner_x,'outer_abs_x_mm':outer_x,
            'gusset_side_clearance_mm':(9.2-leg_y)/2,
            'upper_belt_clearance_mm':p['bracket_belt_clearance'],
            'root_gusset_height_mm':p['bracket_root_gusset_height']},
        'source_local':original_measurements,
    }
    result['title']='ESP32 / narrower enclosure and concave cable cradle · revision 011'
    # Older orientation instructions remain in the explicitly local reference only.
    result['reference_notes']=list(result['notes'])
    result['notes']=[
        'Revision 011 reduces the full enclosure width by 3 mm total after the user reported the locking shelves 3 mm too far apart. Each retention side moves inward 1.5 mm. Body, lid and bracket must be replaced together; previous revisions are preserved.',
        f'Measured PCB is {p["pcb_width"]:g} x {p["pcb_length"]:g} x {p["pcb_thickness"]:g} mm. Solder allowance is deliberately {p["solder_clearance"]:g} mm to preserve the PCB top at local Z10 and the case rim at Z32; this allowance is a placement choice, not a measured solder height. The 52 mm populated ESP32 span is separate from the substrate.',
        'The existing button Y layout and 3 mm left-edge inset remain provisional. Confirmed centers at 30/16 mm from the bottom and 3.3 mm from the left need a dedicated actuator revision; this board-width correction does not claim button alignment.',
        f'The {cable_info["cradle_groove_diameter_mm"]:g} mm cylindrical cut forms an open concave groove for the measured 8 mm cable. Radial allowance is {cable_info["cradle_radial_clearance_mm"]:g} mm, with {cable_info["cradle_side_wall_mm"]:g} mm side walls and {cable_info["cradle_floor_above_tunnel_mm"]:g} mm material above the tie tunnel.',
        f'The cradle extends along the cable for {cable_info["saddle_length_y_mm"]:g} mm. Its underside and tie-tunnel roof use 45 degree slopes. The tunnel is {cable_info["tie_slot_width_y_mm"]:g} mm wide for a provisional {p["zip_tie_width_provisional"]:g} x {p["zip_tie_thickness_provisional"]:g} mm strap. Thread with the lid open, seat the cable in the groove, and snug the tie over it with the head above the right shoulder.',
        'Cable diameter is measured; groove clearance, zip-tie dimensions, head size and physical fit remain unverified. Keep slack between the retention point and terminals. Standard ties may need cutting and replacing for removal.',
        'Print fit-tests/005-board-width and fit-tests/006-cable-cradle before a full replacement. Both derive their interfaces from this same full-model source. Record dimensions, material/settings and pass/fail observations; coupons do not establish full-part strength or warping.',
        f'PCB edge clamps retain M3x{pcb_insert_length:g} heat-set inserts and M3x{p["pcb_clamp_screw_length"]:g} screws, with {pcb_engagement:g} mm engagement and {pcb_tip-pcb_bore_bottom:g} mm blind-tip margin. No screws pass through the PCB. The capture slot is PCB thickness plus {p["board_vertical_play"]:g} mm play; verify bare-edge overlap and solder clearance.',
        f'Install PCB inserts before board/cartridges. The diameter 6 mm tool probe needs at least {h-pcb_clamp_z:g} mm narrow reach with {p["side_margin"]-p["pcb_clamp_screw_offset_from_edge"]-3:g} mm nominal wall clearance. Actual iron access needs checking; remove the BOOT cartridge for left-front screw service.',
        f'Lid joints retain M3x{lid_insert_length:g} heat sets and M3x{p["lid_screw_length"]:g} screws in short corner pads with paired 45 degree ribs. Pilot diameter/depth are {lid_pilot:g}/{lid_depth:g} mm; screw engagement is {min(lid_projection,lid_insert_length):g} mm with {lid_depth-lid_projection:g} mm blind-tip margin. Install flush from the open rim. Do not reuse M3x10 lid screws.',
        'Four bracket M3x5 inserts use M3x10 screws; two contact M3x5 inserts use nylon M3x12 adjusters and exposed jam nuts. Four cartridge inserts remain M3x4 with M3x18 screws. No printed captive hex-nut pockets remain. M3x5 specifies thread and length, not insert outside diameter: OD4.6/pilot4.0 remain provisional.',
        f'The lid and extended finger pads face downward when mounted; press upward through {p["button_stroke"]:g} mm nominal travel. Desk contact remains at Z{desk_z:g}, but the desk/bracket screw X positions move inward 1.5 mm per side with the narrower case.',
        'Print the body floor-down, lid exterior-down and bracket desk-contact-face down. Start with supports off for the cradle/corner ribs and inspect their ramps and short bridges in the slicer. Sliders require local removable support beneath stepped arms; protect guide and magnet seats. No supports are modeled.',
        'Use the intended final material/nozzle/layer settings for coupons. Unfilled PETG remains the initial candidate; material choice and settings are not validated here. Geometry 3MFs are not slicer projects or G-code. No print-time, strain-relief-force, mounting-strength or creep rating is assigned.',
        'Support electronics when opening the downward-facing lid. Return force, contact height/travel, connector envelopes, thermal behavior and RF performance require physical checks; use nylon contact tips. The low-voltage controller is enclosed separately from the external PSU.',
        'Retain all five CAD inputs and the build/render helpers together. Reference cable/tie/hardware solids are excluded from printable exports; hardware STEP contains simplified proxies and is not a complete fastener assembly.',
    ]
    return result
