"""Independent measured-button alignment and finite mechanism-path review.

Tests nine button states, assembly/service paths, preserved revision012 parts,
and measured XY datums. Actual switch height/travel, USB plug, return force,
printer fit and ergonomics remain physical checks.
"""
import argparse
import importlib.util
import json
from math import pi
from itertools import product
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def check_model(source, c, p, label):
    require, overlap, clear = c.require, c.overlap, c.clear
    before = c.hashes(source)
    helper_path = Path(__file__).with_name("check-cable-retention.py")
    print(label+": build enclosure and mechanism paths", flush=True)
    new = load(source/"model.py", "narrowed_enclosure_mechanisms").build(p)
    button_module = load(source/"button_module.py", "narrowed_button_geometry")
    require(len(new["parts"]) == 15 and len(new["hardware"]) == 34, "Unexpected inventory")
    transform = new["mount_transform"]
    pcb_top = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]
    shell_height = pcb_top+p["component_clearance"]
    plate_bottom = shell_height+p["bracket_clearance_above_body"]
    desk_z = plate_bottom+p["bracket_plate_thickness"]
    ceiling = plate_bottom-p["desk_gap_above_case_floor"]
    point = lambda xyz: [xyz[0], -xyz[1], ceiling-xyz[2]]
    interface_z = ceiling-(shell_height-5)
    ear_bottom = ceiling-shell_height
    bracket = new["assembly"]["desk_bracket"]
    require(abs(bracket.bounding_box().max.Z-desk_z) < 1e-7, "Desk-contact plane changed")
    require(abs(new["assembly"]["body"].bounding_box().max.Z-ceiling) < 1e-7,
            "Case floor transform is inconsistent")
    inserts = set(new["bracket_insert_names"])
    require(len(inserts) == 4, "Expected four bracket inserts")
    expected = {(entry["hardware"], entry["printed"]): entry["nominal_displaced_envelope_volume_mm3"]
                for entry in new["expected_hardware_intersections"]}
    require(len(expected) == len(new["expected_hardware_intersections"]), "Duplicate expected interactions")
    insert_length = p["button_contact_insert_length"]
    insert_od = p["button_contact_insert_outer_diameter"]
    pilot_diameter = p["button_contact_insert_pilot_diameter"]
    insert_displacement = pi*(insert_od**2-pilot_diameter**2)/4*insert_length
    ow = p["pcb_width"]+p["board_fit_width_extra"]+2*p["side_margin"]+2*p["wall"]
    require(abs(new["measurements"]["main_shell_xy"][0]-ow) < 1e-7, "Effective shell width is inconsistent")
    independent_screws, mounting = {}, []
    print("Independent M3x10 bracket screws and driver paths", flush=True)
    for index, (x, source_y) in enumerate(new["reference_measurements"]["body_mount_centers_xy"], 1):
        y = -source_y
        screw = c.cyl(1.5, 10, x, y, ear_bottom)+c.cyl(2.75, 3, x, y, ear_bottom-3)
        clear(screw, new["assembly"], "Independent bracket screw intersects printed part")
        clear(screw, new["hardware"], "Independent bracket screw intersects exported hardware")
        independent_screws[f"independent_body_mount_screw_{index}"] = screw
        matches = [(name, new["hardware"][name]) for name in inserts
                   if abs(new["hardware"][name].bounding_box().center().X-x) < 1e-7
                   and abs(new["hardware"][name].bounding_box().center().Y-y) < 1e-7]
        require(len(matches) == 1, "Bracket insert is not on screw axis", x=x, y=y)
        name, insert = matches[0]
        require(abs(insert.bounding_box().min.Z-interface_z) < 1e-7, "Bracket insert entrance plane changed")
        require(abs(insert.bounding_box().max.Z-interface_z-insert_length) < 1e-7,
                "Bracket insert length changed")
        require(abs(overlap(insert, bracket)-insert_displacement) < 1e-5,
                "Unexpected bracket insert polymer displacement")
        engagement = min(ear_bottom+10-interface_z, insert_length)
        require(abs(engagement-5) < 1e-7, "M3x10 screw does not span5 mm insert")
        require(not bracket.is_inside((x, y, interface_z+insert_length+.3))
                and bracket.is_inside((x, y, interface_z+insert_length+.5)),
                "Bracket screw tip does not have expected0.4 mm blind relief")
        driver = c.cyl(3, 30, x, y, ear_bottom-3-30.02)
        clear(driver, new["assembly"], "Bracket screw driver approach blocked")
        clear(driver, new["hardware"], "Bracket screw driver blocked by hardware")
        inner = ow/2+p["belt_projection"]+p["bracket_belt_clearance"]
        wall = min(abs(x)-inner-insert_od/2, p["bracket_leg_width_y"]/2-insert_od/2)
        require(wall >= 1.8-1e-8, "Narrowed bracket insert boss wall too thin")
        mounting.append({"axis_world_xy_mm": [x, y], "insert": name,
                         "screw_length_mm": 10, "ear_thickness_mm": 5,
                         "insert_engagement_mm": engagement, "blind_tip_relief_mm": .4,
                         "minimum_insert_envelope_wall_mm": wall,
                         "driver_diameter_mm": 6, "driver_approach_length_mm": 30, "status": "clear"})
    desk_access = []
    for x, y in new["measurements"]["desk_screw_centers_xy"]:
        probe = c.cyl(p["desk_screw_clearance"]/2-.05, 40, x, y, plate_bottom-40)
        clear(probe, new["assembly"], "Desk screw axis obstructed")
        desk_access.append({"axis_world_xy_mm": [x, y], "probe_diameter_mm": p["desk_screw_clearance"]-.1,
                            "status": "clear"})

    print("Sample case installation into fixed bracket", flush=True)
    case_parts = {name: shape for name, shape in new["assembly"].items() if name != "desk_bracket"}
    moving_hardware = {name: shape for name, shape in new["hardware"].items() if name not in inserts}
    fixed = {"desk_bracket": bracket} | {name: new["hardware"][name] for name in inserts}
    offsets = (0, .25, 1, 2, 4, 6, 8, 10, 12, 16, 20, 25, 30, 40, 50)
    insertion = []
    for downward in offsets:
        for name, shape in case_parts.items():
            clear(c.Pos(0, 0, -downward)*shape, fixed, f"Printed case path blocked at offset{-downward:g}: {name}")
        for name, shape in moving_hardware.items():
            clear(c.Pos(0, 0, -downward)*shape, fixed, f"Case hardware path blocked at offset{-downward:g}: {name}")
        insertion.append({"case_offset_world_z_mm": -downward, "status": "clear"})

    print("Sample button travel with all printed and hardware interactions", flush=True)
    require(abs(p["button_stroke"]-.8) < 1e-7, "This review expects the existing0.8 mm button stroke")
    states = []
    for reset_travel, boot_travel in product((0, .4, .8), repeat=2):
        travel_by_name = {"reset": reset_travel, "boot": boot_travel}
        printed = dict(new["assembly"])
        hardware = new["hardware"] | independent_screws
        state_expected = dict(expected)
        buttons = {}
        for name in ("reset", "boot"):
            travel = travel_by_name[name]
            data = new["buttons"][name]
            local_params = data["params"] | {"travel": travel}
            local = button_module.make_button(local_params, name)
            for key in data["moving_names"]:
                printed[key] = c.Pos(0, 0, travel)*new["assembly"][key]
                if not key.endswith("_slider"):
                    c.same(printed[key], transform*local["assembly"][key], "Moving keeper follows button kinematics")
            for suffix in ("moving_magnet", "nylon_adjuster", "contact_heatset_insert", "nylon_jam_nut"):
                key = f"{name}_{suffix}"
                hardware[key] = c.Pos(0, 0, travel)*new["hardware"][key]
                c.same(hardware[key], transform*local["hardware"][key], key+" follows upward motion")
            for entry in local["expected_hardware_intersections"]:
                state_expected[entry["hardware"], entry["printed"]] = entry["nominal_displaced_envelope_volume_mm3"]
            source_pad = [local_params["mounting_face_x"]-7.1, local_params["housing_y"],
                          local_params["arm_bottom_z"]+7.8+p["finger_pad_extension"]-travel]
            px, py, pz = point(source_pad)
            require(printed[f"{name}_slider"].is_inside((px, py, pz+.05))
                    and not printed[f"{name}_slider"].is_inside((px, py, pz-.05)),
                    "Finger target is not the exposed lower pad surface")
            for diameter, reach, stand_off in ((12, 30, .02), (20, 20, .05)):
                finger = c.cyl(diameter/2, reach, px, py, pz-reach-stand_off)
                clear(finger, printed, f"{diameter} mm centered finger path blocked by print")
                clear(finger, hardware, f"{diameter} mm centered finger path blocked by hardware")
            fixed_magnet = hardware[f"{name}_fixed_magnet"].bounding_box()
            moving_magnet = hardware[f"{name}_moving_magnet"].bounding_box()
            magnet_gap = fixed_magnet.min.Z-moving_magnet.max.Z
            require(abs(magnet_gap-(3.6-travel)) < 1e-6, "Unexpected magnet gap")
            tip_z = hardware[f"{name}_nylon_adjuster"].bounding_box().max.Z
            switch_z = point([local_params["tip_x"], local_params["tip_y"], local_params["switch_top_z"]])[2]
            contact_gap = switch_z-tip_z
            require(abs(contact_gap-(p["button_stroke"]-p["modeled_switch_depression"]-travel)) < 1e-6,
                    "Unexpected modeled switch contact gap")
            buttons[name] = {"pad_surface_world_xyz_mm": [px, py, pz], "press_direction_world": [0, 0, 1],
                             "clear_centered_finger_diameters_mm": [12, 20],
                             "magnet_face_gap_mm": magnet_gap, "modeled_switch_contact_gap_mm": contact_gap}
        items = list(printed.items())
        for index, (name, shape) in enumerate(items):
            for other_name, other in items[index+1:]:
                require(overlap(shape, other) <= 1e-5, "Printed pieces collide during stroke",
                        travel=travel_by_name, pieces=[name, other_name])
        interactions = []
        for name, shape in hardware.items():
            for part_name, part in printed.items():
                hit = overlap(shape, part)
                nominal = state_expected.get((name, part_name), 0)
                require(abs(hit-nominal) <= 1e-5, "Unexpected hardware/printed collision during stroke",
                        travel=travel_by_name, hardware=name, printed=part_name, actual=hit, expected=nominal)
                if nominal:
                    interactions.append({"hardware": name, "printed": part_name, "expected_displacement_mm3": hit})
        items = list(hardware.items())
        for index, (name, shape) in enumerate(items):
            for other_name, other in items[index+1:]:
                require(overlap(shape, other) <= 1e-5, "Hardware collision during stroke",
                        travel=travel_by_name, hardware=[name, other_name])
        states.append({"travel_mm": travel_by_name, "buttons": buttons,
                       "expected_heatset_interactions": interactions, "unexpected_collisions": []})
        print(f"{label}: travel {travel_by_name} mm passed", flush=True)
    require(c.hashes(source) == before, "Source changed during validation")
    report = {"status": "passed", "scenario": label, "source_hashes": before, "checker_sha256": c.sha(Path(__file__)),
              "helper_checker_sha256": c.sha(helper_path), "printed_part_count": len(new["parts"]),
              "exported_hardware_count": len(new["hardware"]), "additional_independent_bracket_screws": 4,
              "mounting_access": mounting, "desk_screw_axis_access": desk_access,
              "sampled_case_installation": insertion, "button_states": states,
              "scope": "Finite digital samples for measured button axes, mounting and board service; root build validates exports and coupon identity separately.",
              "limitations": ["Installation is sampled at the listed offsets, not a continuous swept-volume proof.",
                              "Each button is independently sampled at 0, 0.4 and 0.8 mm travel (nine combined states); intermediate physical motion is untested.",
                              "Measured XY switch axes are integrated; real switch height/travel and assembled alignment still require the quick physical test.",
                              "Centered finger cylinders are clearance probes, not validated ergonomics.",
                              "No load rating, magnetic return force, real tool fit, insert installation or printer verification.",
                              "Cartridge mounting screws are included in the34 proxies; four cartridge insert proxies and actual desk screws are omitted."]}
    report["pcb_service_paths"] = check_pcb_service(c, p, new)
    return new, report


def check_pcb_service(c, p, new):
    require, overlap, clear = c.require, c.overlap, c.clear
    board_top = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]
    clamp_z = board_top+p["board_vertical_play"]
    rim = board_top+p["component_clearance"]
    structural_width = p["pcb_width"]+p["board_fit_width_extra"]
    expected_x = structural_width/2+p["pcb_clamp_screw_offset_from_edge"]
    body = new["case_local_assembly"]["body"]
    bearing_z = clamp_z+2
    screw_tip = bearing_z-p["pcb_clamp_screw_length"]
    records = []
    clamp_names = [name for name in new["case_local_assembly"] if name.startswith("pcb_clamp_")]
    require(len(clamp_names) == 4, "Expected four PCB clamps")
    for name in clamp_names:
        sign_x = -1 if "left" in name else 1
        sign_y = -1 if "front" in name else 1
        x, y = sign_x*expected_x, sign_y*p["clamp_y"]
        screw = c.cyl(1.5, p["pcb_clamp_screw_length"], x, y, screw_tip)
        screw += c.cyl(2.75, 3, x, y, bearing_z)
        c.same(new["mount_transform"]*screw, new["hardware"][name+"_screw"],
               "Independent PCB screw follows structural datum")
        clear(screw, new["case_local_assembly"], "PCB screw strikes printed geometry")
        engagement = clamp_z-max(screw_tip, clamp_z-p["pcb_insert_length"])
        tip_margin = screw_tip-(clamp_z-p["pcb_insert_bore_depth"])
        require(engagement >= 3-1e-8 and tip_margin >= .4-1e-8,
                "PCB screw has insufficient engagement or bottoms")
        # Heat-set iron approaches the open body before PCB/clamps/cartridges.
        heat_tool = c.cyl(3, rim-clamp_z+2, x, y, clamp_z+.01)
        require(overlap(heat_tool, body) < 1e-5, "Ø6 narrow heat-set tool path blocked")
        broad_tool = c.cyl(4, rim-clamp_z+2, x, y, clamp_z+.01)
        broad_hit = overlap(broad_tool, body)
        # The open left connector wall has more room above these bosses; the
        # retained right wall is what limits a wider shaft. Test that specific
        # obstruction instead of inventing the same restriction on both sides.
        if sign_x > 0:
            require(broad_hit > .1, "Ø8 tool right-wall negative control unexpectedly clear")
        # The existing BOOT cartridge blocks left-front screw service and must
        # be removed. All other cartridge geometry remains during this test.
        remove_boot = name == "pcb_clamp_left_front"
        service_parts = {key: shape for key, shape in new["case_local_assembly"].items()
                         if key != "lid" and not (remove_boot and key.startswith("boot_"))}
        driver_bottom = bearing_z+3+.02
        driver = c.cyl(3, rim+3-driver_bottom, x, y, driver_bottom)
        clear(driver, service_parts, "PCB screwdriver service path blocked")
        service_hardware = {key: shape for key, shape in new["hardware"].items()
                            if not key.startswith("lid_") and not (remove_boot and key.startswith("boot_"))}
        clear(new["mount_transform"]*driver, service_hardware, "PCB screwdriver strikes retained hardware")
        records.append({"clamp": name, "axis_local_xy_mm": [x, y],
                        "screw_length_mm": p["pcb_clamp_screw_length"],
                        "insert_engagement_mm": engagement, "tip_margin_mm": tip_margin,
                        "heatset_tool_diameter_mm": 6, "required_narrow_reach_mm": rim-clamp_z,
                        "nominal_right_wall_tool_margin_mm": p["side_margin"]-p["pcb_clamp_screw_offset_from_edge"]-3 if sign_x > 0 else None,
                        "diameter8_tool_overlap_mm3": broad_hit,
                        "screwdriver_diameter_mm": 6, "lid_removed_for_service": True,
                        "boot_cartridge_removed_for_service": remove_boot, "status": "clear"})
    return records


def local_state(c, new, travels):
    printed = dict(new['case_local_assembly'])
    # This transform is its own inverse: [x,y,z] -> [x,-y,38-z].
    hardware = {key: new['mount_transform']*value for key, value in new['hardware'].items()}
    for name, travel in travels.items():
        for key in new['buttons'][name]['moving_names']:
            printed[key] = c.Pos(0, 0, -travel)*printed[key]
        for suffix in ('moving_magnet', 'nylon_adjuster', 'contact_heatset_insert', 'nylon_jam_nut'):
            key = name+'_'+suffix
            hardware[key] = c.Pos(0, 0, -travel)*hardware[key]
    return printed, hardware


def alignment_and_service(c, new, p):
    require, clear, overlap = c.require, c.clear, c.overlap
    printed, hardware = local_state(c, new, {'reset': 0, 'boot': 0})
    board_bottom = p['floor']+p['solder_clearance']
    board_top = board_bottom+p['pcb_thickness']
    rim = board_top+p['component_clearance']
    measurements, assembly_paths = {}, {}
    xcyl = lambda r, length, x, y, z: c.Pos(x, y, z)*c.Rot(Y=90)*c.cyl(r, length)
    for name, direction in (('reset', -1), ('boot', 1)):
        data = new['buttons'][name]
        bp = data['params']
        tx = -p['pcb_width']/2+p['button_inset_from_left_pcb_edge']
        ty = -p['pcb_length']/2+p[name+'_button_from_bottom']
        require(abs(bp['tip_x']-tx) < 1e-7 and abs(bp['tip_y']-ty) < 1e-7,
                'Contact axis does not follow actual PCB edge datums', button=name)
        require(bp['collar_relief_direction'] == direction, 'Collar flat faces wrong switch')
        for suffix in ('nylon_adjuster', 'contact_heatset_insert', 'nylon_jam_nut'):
            center = hardware[name+'_'+suffix].bounding_box().center()
            require(abs(center.X-tx) < 1e-7 and abs(center.Y-ty) < 1e-7,
                    'Contact hardware is not concentric with measured XY', button=name, hardware=suffix)
        a, face = bp['arm_bottom_z'], bp['mounting_face_x']
        slider = printed[name+'_slider']
        floor_z = a-.8
        flat = bp['collar_flat_offset']
        require(flat-1.7 >= 1.2-1e-7, 'Low collar ligament too thin')
        # Direct polymer probes on both sides of the actual clipped boundary.
        inside = c.box(.2, .05, .2, tx, ty+direction*(flat-.05), floor_z+.1)
        outside = c.box(.2, .05, .2, tx, ty+direction*(flat+.05), floor_z+.1)
        require(abs(overlap(inside, slider)-c.volume(inside)) < 1e-7,
                'Relieved collar loses its specified ligament', button=name)
        require(overlap(outside, slider) < 1e-7, 'Low collar flat was not cut', button=name)
        ring = c.cyl(bp['contact_insert_pilot_diameter']/2-.02, .1, tx, ty, floor_z+.1)
        ring -= c.cyl(1.72, .2, tx, ty, floor_z+.05)
        require(abs(overlap(ring, slider)-c.volume(ring)) < 1e-6,
                'Heatset pocket floor annulus is incomplete')
        require(bp['arm_elbow_inset']-4.2 >= .2-1e-7, 'Elbow reaches into guide')
        # Full-width tongue remains at the housing Y until it clears the guide.
        tongue = c.box(.2, 8.2, .2, face-.1, bp['housing_y'], a+1)
        require(abs(overlap(tongue, slider)-c.volume(tongue)) < 1e-6,
                'Guide tongue is not straight at the mounting face')
        head_top = hardware[name+'_nylon_adjuster'].bounding_box().max.Z
        measurements[name] = {'tip_local_xy_mm': [tx, ty],
                              'actual_pcb_left_inset_mm': tx+p['pcb_width']/2,
                              'actual_pcb_bottom_distance_mm': ty+p['pcb_length']/2,
                              'housing_y_mm': bp['housing_y'],
                              'collar_center_to_flat_mm': flat,
                              'collar_ligament_beside_clearance_hole_mm': flat-1.7,
                              'rounded_elbow_to_guide_face_mm': bp['arm_elbow_inset']-4.2,
                              'contact_head_to_lid_underside_at_rest_mm': rim-head_top,
                              'switch_height_above_pcb_mm_provisional': bp['switch_top_z']-board_top}

        frame = printed[name+'_frame']
        keeper = printed[name+'_rear_keeper']
        own_moving = {key: printed[key] for key in data['moving_names']}
        # Stops checked on final extended-pad geometry, not only base module.
        stops = {}
        for label, dz in (('upper', .05), ('lower', -bp['stroke']-.05)):
            hit = max(overlap(c.Pos(0, 0, dz)*shape, frame+keeper) for shape in own_moving.values())
            require(hit > 1e-5, 'Mechanical end stop missing', button=name, stop=label)
            stops[label] = {'overtravel_local_z_mm': dz, 'interference_mm3': hit}

        # Assemble before fitting the nylon contact screw and its jam nut.
        moving = own_moving | {name+'_'+suffix: hardware[name+'_'+suffix]
                              for suffix in ('moving_magnet', 'contact_heatset_insert')}
        excluded = set(moving) | {name+'_rear_keeper', name+'_nylon_adjuster', name+'_nylon_jam_nut',
                                  name+'_mount_screw_1', name+'_mount_screw_2', 'lid', 'desk_bracket'}
        fixed = {key: shape for key, shape in (printed | hardware).items()
                 if key not in excluded and not key.startswith('lid_') and not key.startswith('bracket_')}
        top_offsets = [i*.5 for i in range(71)]
        for dz in top_offsets:
            for key, shape in moving.items():
                clear(c.Pos(0, 0, dz)*shape, fixed,
                      f'{name} loaded-slider top insertion blocked at {dz:g} mm: {key}')

        # The external rear cover slides along +X onto the frame, before bolts.
        rear_fixed = {key: shape for key, shape in (printed | hardware).items()
                      if key not in (name+'_rear_keeper', name+'_mount_screw_1', name+'_mount_screw_2',
                                     'lid', 'desk_bracket') and not key.startswith('lid_')}
        rear_offsets = [i*.5 for i in range(71)]
        for dx in rear_offsets:
            clear(c.Pos(-dx, 0, 0)*keeper, rear_fixed,
                  f'{name} rear-keeper insertion blocked at {-dx:g} mm')
        captures = []
        for travel in (0, .4, .8):
            pp, hh = local_state(c, new, {name: travel})
            small = pp[name+'_moving_magnet_keeper']
            escape = c.Pos(-.5, 0, 0)*small
            cover_hit = overlap(escape, keeper)
            require(cover_hit > 1e-5, 'Tiny moving keeper can escape completed housing', button=name)
            captures.append({'travel_mm': travel, 'rear_escape_shift_mm': .5,
                             'cover_interference_mm3': cover_hit})
            for suffix in ('fixed_magnet', 'moving_magnet'):
                for axis, delta in (('rear', (-.5, 0, 0)), ('front', (.5, 0, 0)),
                                    ('side', (0, .4, 0)), ('up', (0, 0, .3)), ('down', (0, 0, -.3))):
                    hit = max(overlap(c.Pos(*delta)*hh[name+'_'+suffix], shape)
                              for key, shape in pp.items() if key.startswith(name+'_'))
                    require(hit > 1e-5, 'Magnet escape sample lacks a printed stop',
                            button=name, magnet=suffix, direction=axis, travel=travel)
        assembly_paths[name] = {'upper_and_lower_stops': stops,
                                'loaded_slider_top_insertion_offsets_local_z_mm': top_offsets,
                                'loaded_slider_items': list(moving),
                                'slider_insertion_contact_screw_and_jam_nut_removed': True,
                                'slider_insertion_lid_and_rear_keeper_removed': True,
                                'other_cartridge_remains_installed': True,
                                'rear_cover_insertion_offsets_local_x_mm': [-v for v in rear_offsets],
                                'tiny_magnet_keeper_retention_samples': captures,
                                'magnet_escape_samples': 'Five directions at three button travels blocked by completed housing',
                                'status': 'clear'}

    # Below the arms, the interior plug envelope and outside cable route differ.
    tx = new['buttons']['reset']['params']['tip_x']
    face = new['buttons']['reset']['params']['mounting_face_x']
    mid_y = sum(new['buttons'][name]['params']['tip_y'] for name in ('reset', 'boot'))/2
    plug_z = board_top+p['board_vertical_play']+2+.1
    xlo = face+.25
    plug = c.box(tx-xlo, 8, 6, (tx+xlo)/2, mid_y, plug_z)
    exterior_x = face-30
    broad = c.box(tx-exterior_x, 8, 6, (tx+exterior_x)/2, mid_y, plug_z)
    cable = xcyl(1.75, tx-exterior_x, exterior_x, mid_y, plug_z+1.75)
    state_reports = []
    for reset, boot in product((0, .4, .8), repeat=2):
        travels = {'reset': reset, 'boot': boot}
        pp, hh = local_state(c, new, travels)
        all_shapes = pp | hh
        plug_blocked = {key: overlap(plug, shape) for key, shape in all_shapes.items()
                        if overlap(plug, shape) > 1e-5}
        require(set(plug_blocked) == {'pcb_clamp_left_front_screw'},
                'Provisional interior USB negative control changed', blockers=plug_blocked)
        clear(cable, all_shapes, 'Provisional 3.5 mm USB cable approach blocked')
        blocked = {key: overlap(broad, shape) for key, shape in all_shapes.items()
                   if overlap(broad, shape) > 1e-5}
        require(any(key.startswith('boot_') for key in blocked),
                'Known wide connector approach negative control did not detect BOOT housing')
        service = []
        for name in ('reset', 'boot'):
            bp = new['buttons'][name]['params']
            sx, sy = bp['tip_x'], bp['tip_y']
            switch = c.cyl(2, 1, sx, sy, bp['switch_top_z']-1)
            clear(switch, {key: shape for key, shape in all_shapes.items()
                           if key != name+'_nylon_adjuster'}, 'Rigid mechanism intersects provisional switch')
            head_z = hh[name+'_nylon_adjuster'].bounding_box().max.Z
            driver = c.cyl(1.5, 15, sx, sy, head_z+.05)
            clear(driver, {key: shape for key, shape in all_shapes.items() if key not in ('lid', 'desk_bracket')},
                  'Contact screwdriver access blocked with lid removed')
            rear = bp['mounting_face_x']-14.2
            for dy in (-3, 3):
                mount_driver = xcyl(2, 30, rear-33.05, bp['housing_y']+dy, bp['mount_hole_z'])
                clear(mount_driver, all_shapes, 'Cartridge mounting screwdriver access blocked')
            service.append({'button': name, 'contact_driver_diameter_mm': 3,
                            'contact_driver_lid_removed': True, 'mount_driver_diameter_mm': 4})
        state_reports.append({'travel_mm': travels, 'usb_inboard_8x6_plug_clear': False,
                              'usb_inboard_plug_blockers_mm3': plug_blocked,
                              'provisional_3_5mm_cable_clear': True,
                              'wide_connector_approach_blockers_mm3': blocked,
                              'button_driver_access': service, 'provisional_switch_rigid_clearance': 'clear'})
    return {'measured_axis_checks': measurements,
            'contact_axis_pitch_mm': measurements['reset']['tip_local_xy_mm'][1]-measurements['boot']['tip_local_xy_mm'][1],
            'assembly_and_retention_paths': assembly_paths,
            'usb_provisional_envelopes': {'interior_plug_width_height_mm': [8, 6],
                                         'interior_plug_x_range_mm': [xlo, tx], 'center_y_mm': mid_y,
                                         'plug_local_z_range_mm': [plug_z, plug_z+6],
                                         'outside_cable_diameter_mm': 3.5,
                                         'cable_x_range_mm': [exterior_x, tx],
                                         'outside_cable_lateral_margin_to_boot_housing_mm': .25,
                                         'interior_8x6_plug_envelope': 'blocked by left-front PCB clamp screw head; actual plug must be tested',
                                         'wide_plug_insertion_with_cartridges_installed': 'also blocked by BOOT housing; installing before cartridges does not remove the clamp-screw conflict',
                                         'physical_usb_jack_plug_length_diameter_and_bend_route': 'unmeasured'},
            'independent_state_service_checks': state_reports}


def preserved_geometry(c, new, old):
    changed = {'reset_slider', 'boot_slider'}
    require = c.require
    require(set(new['parts']) == set(old['parts']), 'Printed inventory changed')
    kept = []
    for key, shape in new['parts'].items():
        require(shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0,
                'Part is not a single valid connected solid', part=key)
        require(abs(shape.bounding_box().min.Z) < 1e-7, 'Print is not seated at Z0', part=key)
        if key in changed:
            require(abs(shape.volume-old['parts'][key].volume) > 1, 'Expected replacement slider did not change')
        else:
            c.same(shape, old['parts'][key], key+' printed geometry preserved from012')
            c.same(new['assembly'][key], old['assembly'][key], key+' installed pose preserved from012')
            kept.append(key)
    kept_hardware = []
    for key, shape in new['hardware'].items():
        if any(key.endswith('_'+suffix) for suffix in ('nylon_adjuster', 'contact_heatset_insert', 'nylon_jam_nut')):
            continue
        c.same(shape, old['hardware'][key], key+' preserved from012')
        kept_hardware.append(key)
    require(len(kept) == 13 and len(kept_hardware) == 28, 'Unexpected preserved inventory')
    for key in ('cable_retention_local', 'cable_retention_stock_local', 'cable_retention_tunnel_local',
                'cable_retention_groove_cutter_local'):
        c.same(new[key], old[key], 'Concave cable feature preserved')
    for key, shape in new['cable_retention_references_local'].items():
        c.same(shape, old['cable_retention_references_local'][key], key+' cable reference preserved')
        c.clear(shape, new['case_local_assembly'], key+' cable reference hits measured button assembly')
    return {'unchanged_printed_parts': kept, 'changed_printed_parts': sorted(changed),
            'unchanged_hardware_proxies': kept_hardware, 'contact_hardware_xy_changed': True,
            'concave_cable_feature_and_reference_geometry_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--nominal-only', action='store_true', help='Diagnostic run; does not validate the parameter variant')
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    helper = Path(__file__).with_name('check-cable-retention.py')
    c = load(helper, 'measured_alignment_geometry_helpers')
    before, previous = c.hashes(source), c.hashes(baseline)
    p = json.loads((source/'parameters.json').read_text())
    c.require(p['pcb_width'] == 49 and p['pcb_length'] == 70 and p['pcb_thickness'] == 1,
              'Measured board dimensions changed')
    c.require(p['reset_button_from_bottom'] == 30 and p['boot_button_from_bottom'] == 16
              and p['button_inset_from_left_pcb_edge'] == 3.3, 'Measured switch datums not integrated')
    old = load(baseline/'model.py', 'preserved012_for_measured_buttons').build(
        json.loads((baseline/'parameters.json').read_text()))
    scenarios = [('nominal_measured_axes', p)]
    if not args.nominal_only:
        scenarios.append(('variant_inset3_5_reset30_2_boot15_8', p | {
            'button_inset_from_left_pcb_edge': 3.5,
            'reset_button_from_bottom': 30.2, 'boot_button_from_bottom': 15.8}))
    reports = []
    for label, params in scenarios:
        new, report = check_model(source, c, params, label)
        print(label+': exact axes and cartridge assembly/service paths', flush=True)
        report['alignment_and_service'] = alignment_and_service(c, new, params)
        report['parameter_overrides'] = {key: value for key, value in params.items() if p[key] != value}
        report['baseline_comparison'] = preserved_geometry(c, new, old)
        reports.append(report)
    c.require(c.hashes(source) == before and c.hashes(baseline) == previous, 'Input source changed during checks')
    result = {'status': 'passed', 'source_hashes': before, 'baseline_hashes': previous,
              'checker_sha256': c.sha(Path(__file__)), 'geometry_helper_sha256': c.sha(helper),
              'scenarios': reports, 'parameter_variant_validated': not args.nominal_only,
              'physical_fit_tested': False,
              'limitations': ['Finite sampled digital paths do not prove all continuous motion or real print fit.',
                              'Measured XY coordinates are integrated; actual switch height, operating travel and board seating need calibration.',
                              'USB plug dimensions and wire routing remain unmeasured. The broad straight approach is blocked by BOOT housing; the inboard 8x6 envelope also hits the left-front PCB clamp screw head. The 3.5 mm cable probe is separate.',
                              'Magnet return force, electrical/RF effects, contact force and mechanical strength were not tested.',
                              'Export reimport and the quick-fit coupon are checked by the shared build and separate coupon validation.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': 'passed', 'scenarios': len(reports), 'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
