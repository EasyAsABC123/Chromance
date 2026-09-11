"""Revision008: short wall-supported lid bosses replace full-height columns.

The corner gaps close, supported by paired underside wedges. Only the body and
the lid's local corner skirt segments change; thirteen other print parts and
all hardware, desk transforms and PCB/button positions remain unchanged from007.
This compatibility update does not integrate the separate measured-board fit test.
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
DEFAULTS=_base.DEFAULTS | _base.BUTTON_DEFAULTS | MOUNT_DEFAULTS


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

    source_params={k:v for k,v in p.items() if k not in MOUNT_DEFAULTS}
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
             'source_frame':'Preserved case coordinates; revision008 changes only lid corner supports and local skirt relief',
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
            'desk_bracket':'Four existing blind heat-set pilots; exported geometry unchanged',
            'actuators':'Contact heat sets; guide/magnet pockets are functional capture features',
            'unused_source_bracket':'Legacy nut cuts and nut-slot helper removed; wrapper replaces this source bracket',
            'remaining_nuts':'Two exposed nylon contact jam nuts are hardware; no printed nut traps',
        },
        'corner_bosses':corner_info,
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
    result['title']='ESP32 / short wall-supported lid corner bosses · revision008'
    # Older orientation instructions remain in the explicitly local reference only.
    result['reference_notes']=list(result['notes'])
    result['notes']=[
        'Revision008 replaces the four tall lid columns with short solid corner pads and paired sloping supports. Reprint the body and lid; only the four local skirt segments change on the lid. Thirteen other printed parts and every hardware axis remain unchanged from007. All older revisions and board-fit tests remain preserved.',
        f'Each upper corner pad projects {p["lid_corner_projection"]:g} mm inward from both adjacent walls and overlaps them by {p["lid_corner_wall_overlap"]:g} mm. The pad runs from localZ{corner_info["pad_bottom_local_z_mm"]:g} to{h:g}, leaving {corner_info["pilot_floor_thickness_mm"]:g} mm of solid material below the entire blind pilot.',
        f'Two joined {p["lid_corner_support_angle"]:g}-degree underside wedges begin at localZ{corner_info["wall_root_local_z_mm"]:g} on the inner wall faces. Their union grows each print layer from the nearer wall, including diagonal regions. No modeled supports are added for these bosses; inspect the actual slicer preview.',
        f'The filled corner gaps formerly housed small lid-skirt segments. These are removed locally with {p["lid_fit_clearance"]:g} mm clearance; the exterior lid face, screw holes and remaining skirt are retained.',
        f'CAD body volume changes from {corner_info["body_old_full_height_volume_mm3"]/1000:.3f} to {corner_info["body_new_volume_mm3"]/1000:.3f} cm3, a reduction of {corner_info["body_volume_saved_mm3"]/1000:.3f} cm3 ({corner_info["body_volume_saved_percent"]:.2f}%). Raw and net corner-feature volumes are recorded separately. These are geometry volumes, not print-time or strength predictions.',
        f'The enclosure and its hardware rotate 180 degrees about X, then translate by Z={ceiling:g} mm. The USB/button side stays -X; the cable end changes from +Y to -Y. World +Z points toward the desk.',
        f'The floor faces the desk with {gap:g} mm clearance below the bracket plate. The lid and extended paddle faces point downward: reach from below and press upward through {p["button_stroke"]:g} mm nominal travel.',
        f'Each existing finger pad is extended {p["finger_pad_extension"]:g} mm in its original local +Z direction, with 0.6 mm overlap and a new 0.5 mm top chamfer. Guide, magnets, contact insert, nylon tip and positive stops are unchanged; motion remains rigid 1:1.',
        'All button parameters and their original measurement fields remain in the source frame. Use mount_transform for world placement and slider_pad_extensions for the added pads; buttons[name].pad_world gives the new exposed faces and press direction.',
        f'Desk contact remains at Z={desk_z:g} mm and all four desk screw positions are unchanged. Straight bracket legs leave {p["bracket_belt_clearance"]:g} mm belt clearance along the full insertion path and {(9.2-leg_y)/2:g} mm clearance to the existing ear gussets.',
        f'The existing bracket uses four M3x{insert_length:g} heat-set inserts. Its M3x10 screws pass upward through the flipped5 mm ears for {insert_engagement:g} mm nominal insert engagement and {insert_depth-5:g} mm blind-tip clearance. Neither lid nor PCB clamps require captive hex nuts.',
        f'PCB clamps use four M3x{pcb_insert_length:g} inserts and M3x{p["pcb_clamp_screw_length"]:g} socket screws. Their holes move {p["pcb_clamp_screw_offset_from_edge"]-4.5:g} mm outward while the ledges, locating shoulders and PCB capture slots stay unchanged. The new diameter{pcb_boss_d:g} mm bosses retain {(pcb_boss_d-pcb_insert_od)/2:g} mm nominal radial polymer around provisional OD{pcb_insert_od:g} mm inserts.',
        f'PCB pilots are diameter{pcb_pilot:g} x{pcb_depth:g} mm deep, from localZ{pcb_clamp_z:g} down to{pcb_bore_bottom:g}. M3x{p["pcb_clamp_screw_length"]:g} screws through the2 mm clamps give {pcb_engagement:g} mm engagement and {pcb_tip-pcb_bore_bottom:g} mm blind-tip margin. Do not reuse the old M3x8 PCB screws, which bottom in the new pilots. No washers are assumed.',
        f'Install PCB inserts before the board/cartridges. The modeled access uses a diameter6 mm narrow tool reaching at least{h-pcb_clamp_z:g} mm from each boss top to the shell rim, with only{p["side_margin"]-p["pcb_clamp_screw_offset_from_edge"]-3:g} mm nominal side-wall clearance. A bulky iron cannot follow that straight path; verify the actual tool. Remove the BOOT cartridge for later left-front clamp screw service.',
        'All printed captive-nut pockets and their lower side-entry slots are removed. The narrow PCB-edge capture slots, magnetic-guide openings and magnet keeper pockets are intentional and remain. Two exposed nylon contact jam nuts remain separate hardware, with no printed nut traps.',
        f'Lid hardware remains four M3x{lid_insert_length:g} heat-set inserts, provisional OD{lid_insert_od:g} mm, and four M3x{p["lid_screw_length"]:g} socket screws. The pilot is diameter{lid_pilot:g} x{lid_depth:g} mm deep; the new {corner_info["pad_square_width_mm"]:g} mm square corner pad retains at least {corner_info["minimum_inboard_material_to_insert_mm"]:g} mm of material to the insert envelope.',
        f'Each lid screw passes through {p["lid_thickness"]:g} mm of lid and projects {lid_projection:g} mm, engaging the full {min(lid_projection,lid_insert_length):g} mm insert with {lid_depth-lid_projection:g} mm blind-tip clearance. Do not reuse revision005 M3x10 lid screws: they bottom in these blind pilots. No washers are assumed.',
        'Install the four lid inserts flush from the open body rim before closing the lid. Actual insert outside diameter and the pilot fit remain provisional; verify the purchased insert and the intended filament with a fit coupon.',
        f'Bracket insert OD {insert_od:g} mm and pilot {insert_pilot:g} mm remain provisional. Blind pilot depth is {insert_depth:g} mm; the printed legs retain {inner_insert_wall:g} mm inboard and {side_insert_wall:g} mm Y material to the insert envelope. Verify the actual insert drawing and a printed fit coupon.',
        'Install the bracket inserts from the lower leg faces on the bench. Fix the bracket to the desk, raise the enclosure vertically between its legs, and fit the four M3x10 screws from below. Select desk screw penetration after measuring desk material and thickness.',
        'Each bracket insert intentionally displaces its own pilot. The exact insert/desk_bracket host pairs are declared separately from unexpected interference; hardware proxies are excluded from printed exports.',
        'The original ears and their ribs carry enclosure weight through the four M3 screws into the bracket posts and crossbars. Top gussets distribute post load. No strength or creep load rating is assigned.',
        f'With the PCB inverted, its four removable edge clamps support board weight. Confirm the provisional {p["board_edge_overlap"]:g} mm bare-edge overlap and retention; secure heavy cables independently.',
        'Print the new bracket with its desk-contact face on the bed. Print the extended sliders with their new finger-pad faces on the bed, matching the original slider rotation; the longer extensions raise the arms and guides farther from the bed, so local removable supports are needed. Protect guide and magnet fits from support scars.',
        'All remaining parts retain revision004 print orientation. The M3x5 contact inserts, nylon M3x12 adjusters, short M3x4 body inserts, magnets and travel stops remain unchanged at default settings. Contact adjustment requires lid access; the BOOT-side PCB clamp requires cartridge removal.',
        'Support the electronics when opening the downward-facing lid. Remove the enclosure for initial wiring, slider service and calibration. Do not substitute metal contact tips over the PCB.',
        f'Current board outline {p["pcb_width"]:g}x{p["pcb_length"]:g} mm, PCB {p["pcb_thickness"]:g} mm, solder clearance {p["solder_clearance"]:g} mm and component/wire clearance {p["component_clearance"]:g} mm remain provisional. Actual connectors, switch positions, magnetic force, printed fit, strength, temperature and RF behavior require physical validation.',
        'The separate fit-tests/002-board-fit-heatsets experiment uses the measured49x70x1 mm PCB and heat-set edge clamps. Those new measurements and fourteen-millimeter button spacing are not integrated into this compatibility revision; the archived revision005 PCB/button layout is retained here.',
        'Retain base_model.py, button_module.py and mounting.py beside this wrapper. The base source defines the new lid corner supports and skirt relief; button_module.py and mounting.py remain byte-identical to007. The unexported full-height comparison body is only for volume and preservation checks.',
    ]
    return result
