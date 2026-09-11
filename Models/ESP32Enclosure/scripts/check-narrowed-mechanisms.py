"""Sample bracket installation and button motion for the narrowed enclosure.

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    helper_path = Path(__file__).with_name("check-cable-retention.py")
    c = load(helper_path, "mechanism_geometry_helpers")
    require, overlap, clear = c.require, c.overlap, c.clear
    before = c.hashes(source)
    p = json.loads((source/"parameters.json").read_text())
    print("Build final narrowed enclosure", flush=True)
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
    ow = p["pcb_width"]+2*p["side_margin"]+2*p["wall"]
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
        print(f"Travel{travel:g} mm passed", flush=True)
    require(c.hashes(source) == before, "Source changed during validation")
    report = {"status": "passed", "source_hashes": before, "checker_sha256": c.sha(Path(__file__)),
              "helper_checker_sha256": c.sha(helper_path), "printed_part_count": len(new["parts"]),
              "exported_hardware_count": len(new["hardware"]), "additional_independent_bracket_screws": 4,
              "mounting_access": mounting, "desk_screw_axis_access": desk_access,
              "sampled_case_installation": insertion, "button_states": states,
              "scope": "Finite digital samples for the final narrowed enclosure; no comparison to older printed geometry.",
              "limitations": ["Installation is sampled at the listed offsets, not a continuous swept-volume proof.",
                              "Both buttons are sampled at0,0.4,0.8 mm travel; intermediate physical motion is untested.",
                              "Physical switch alignment remains unresolved: measured14 mm spacing has not been integrated.",
                              "Centered finger cylinders are clearance probes, not validated ergonomics.",
                              "No load rating, magnetic return force, real tool fit, insert installation or printer verification.",
                              "Cartridge mounting screws are included in the34 proxies; four cartridge insert proxies and actual desk screws are omitted."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "passed", "installation_samples": len(insertion),
                      "button_states": len(states), "report": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
