"""Check eased PCB retention mechanisms and unchanged concave cable geometry.

Adapted from check-flipped-mount.py without its old-baseline assertions. These
are finite digital motion samples, not a continuous collision proof or a check
of the still-pending measured button alignment, finger ergonomics or loads.
"""
import argparse
import importlib.util
import json
from math import pi
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
    for travel in (0, .4, .8):
        printed = dict(new["assembly"])
        hardware = new["hardware"] | independent_screws
        state_expected = dict(expected)
        buttons = {}
        for name in ("reset", "boot"):
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
                        travel=travel, pieces=[name, other_name])
        interactions = []
        for name, shape in hardware.items():
            for part_name, part in printed.items():
                hit = overlap(shape, part)
                nominal = state_expected.get((name, part_name), 0)
                require(abs(hit-nominal) <= 1e-5, "Unexpected hardware/printed collision during stroke",
                        travel=travel, hardware=name, printed=part_name, actual=hit, expected=nominal)
                if nominal:
                    interactions.append({"hardware": name, "printed": part_name, "expected_displacement_mm3": hit})
        items = list(hardware.items())
        for index, (name, shape) in enumerate(items):
            for other_name, other in items[index+1:]:
                require(overlap(shape, other) <= 1e-5, "Hardware collision during stroke",
                        travel=travel, hardware=[name, other_name])
        states.append({"travel_mm": travel, "buttons": buttons,
                       "expected_heatset_interactions": interactions, "unexpected_collisions": []})
        print(f"{label}: travel{travel:g} mm passed", flush=True)
    require(c.hashes(source) == before, "Source changed during validation")
    report = {"status": "passed", "scenario": label, "source_hashes": before, "checker_sha256": c.sha(Path(__file__)),
              "helper_checker_sha256": c.sha(helper_path), "printed_part_count": len(new["parts"]),
              "exported_hardware_count": len(new["hardware"]), "additional_independent_bracket_screws": 4,
              "mounting_access": mounting, "desk_screw_axis_access": desk_access,
              "sampled_case_installation": insertion, "button_states": states,
              "scope": "Finite digital mechanism samples for independent board-fit width; full retention and STEP coupon identity are checked separately.",
              "limitations": ["Installation is sampled at the listed offsets, not a continuous swept-volume proof.",
                              "Both buttons are sampled at0,0.4,0.8 mm travel; intermediate physical motion is untested.",
                              "Physical switch alignment remains unresolved: measured14 mm spacing has not been integrated.",
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


def cable_reuse(c, new, previous_cable, prior_report, p):
    require, clear = c.require, c.clear
    saddle, stock, tunnel, groove, region, refs, info = previous_cable
    expected = {"cable_retention_local": saddle, "cable_retention_stock_local": stock,
                "cable_retention_tunnel_local": tunnel, "cable_retention_groove_cutter_local": groove,
                "cable_retention_change_region_local": region}
    for key, shape in expected.items():
        c.same(new[key], shape, key+" unchanged from011")
    for name, shape in refs.items():
        c.same(new["cable_retention_references_local"][name], shape, name+" cable reference unchanged from011")
        clear(shape, new["case_local_assembly"], name+" hits current enclosure or extended clamps")
    stable_fields = ("cradle_groove_diameter_mm", "cradle_radial_clearance_mm", "cradle_width_mm",
                     "cradle_floor_above_tunnel_mm", "cradle_groove_bottom_local_z_mm",
                     "cable_axis_local_xz_mm", "tie_head_center_local_xyz_mm",
                     "tie_and_head_top_to_lid_plane_mm", "coupon_bounds_local_mm")
    actual = new["measurements"]["cable_retention"]
    for key in stable_fields:
        require(actual[key] == info[key], "Cable measurement changed", field=key)
    layers = prior_report["scenarios"][0]["layer_review"]
    require(layers["maximum_excess_area_mm2"] < 1e-5, "Prior cable layer proof failed")
    return {"status": "passed", "finished_cradle_stock_and_cutters_identical_to011": True,
            "cable_tie_head_references_identical_to011": True,
            "all_references_clear_current_assembled_parts": True,
            "minimum_lid_clearance_mm": actual["tie_and_head_top_to_lid_plane_mm"],
            "retained_nominal_layer_count": layers["layer_count"],
            "retained_layer_height_mm": layers["layer_height_mm"],
            "new_layer_sweep_performed": False,
            "coupon006_export_crop_identity": "Checked separately by check-eased-board-fit.py against reopened STEP files."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    helper_path = Path(__file__).with_name("check-cable-retention.py")
    c = load(helper_path, "eased_mechanism_geometry_helpers")
    before = c.hashes(source)
    p = json.loads((source/"parameters.json").read_text())
    c.require(p["pcb_width"] == 49 and p["board_fit_width_extra"] == .5 and p["board_edge_overlap"] == 1.3,
              "Expected measured49 mm board,0.5 mm total fit allowance and1.3 mm overlap")
    prior = load(baseline/"model.py", "preserved011_cable_geometry")
    old_p = prior.DEFAULTS | json.loads((baseline/"parameters.json").read_text())
    old_rim = old_p["floor"]+old_p["solder_clearance"]+old_p["pcb_thickness"]+old_p["component_clearance"]
    previous_cable = prior._cable_saddle(old_p, old_p["pcb_length"]/2+old_p["end_margin"],
                                       old_rim-old_p["end_cable_height"], old_rim)
    prior_path = baseline/"cable-validation.json"
    prior_report = json.loads(prior_path.read_text())
    c.require(prior_report["status"] == "passed" and prior_report["source_hashes"] == c.hashes(baseline),
              "Prior layer report does not match preserved011 sources")
    scenarios = [("nominal_extra0_5_overlap1_3", p),
                 ("variant_extra0_8_overlap1_4", p | {"board_fit_width_extra": .8, "board_edge_overlap": 1.4})]
    reports = []
    for label, params in scenarios:
        new, report = check_model(source, c, params, label)
        report["parameter_overrides"] = {k: value for k, value in params.items() if p[k] != value}
        report["board_retention"] = new["measurements"]["board_retention"]
        c.require(abs(report["board_retention"]["capture_slot_height_mm"]-1.2) < 1e-7,
                  "Vertical capture slot changed")
        c.require(abs(new["buttons"]["reset"]["params"]["tip_x"]-(-p["pcb_width"]/2+p["button_inset_from_left_pcb_edge"])) < 1e-7,
                  "Button tip followed structural allowance instead of measured PCB")
        report["cable_reuse"] = cable_reuse(c, new, previous_cable, prior_report, params)
        reports.append(report)
    c.require(c.hashes(source) == before, "Source changed during validation")
    result = {"status": "passed", "source_hashes": before, "baseline_hashes": c.hashes(baseline),
              "checker_sha256": c.sha(Path(__file__)), "helper_checker_sha256": c.sha(helper_path),
              "retained_cable_layer_report_sha256": c.sha(prior_path), "scenarios": reports,
              "physical_fit_tested": False,
              "scope": "Nominal and allowance/overlap variant sampled mechanism paths, PCB tool service, and unchanged concave cable geometry. Full board poses and coupon STEP crops are checked separately."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"status": "passed", "scenarios": len(reports), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
