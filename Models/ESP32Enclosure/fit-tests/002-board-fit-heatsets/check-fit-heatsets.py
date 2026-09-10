"""Independent review of the outboard heat-set PCB retention fit print."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import fdm_cad.build
import numpy as np
from build123d import Align, Box, Compound, Cylinder, Pos, import_step


def load(path, name):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def box(w, d, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl(r, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def volume(shape):
    if shape is None:
        return 0.0
    if hasattr(shape, "volume"):
        return abs(float(shape.volume))
    return sum(volume(item) for item in shape)


def overlap(a, b):
    if not hasattr(a, "bounding_box"):
        return sum(overlap(item, b) for item in a)
    if not hasattr(b, "bounding_box"):
        return sum(overlap(a, item) for item in b)
    aa, bb = a.bounding_box(), b.bounding_box()
    if any(min(tuple(aa.max)[i], tuple(bb.max)[i])
           - max(tuple(aa.min)[i], tuple(bb.min)[i]) <= 1e-8 for i in range(3)):
        return 0.0
    return volume(a.intersect(b))


def require(condition, message, **evidence):
    if not condition:
        raise AssertionError({"check": message, **evidence})


def clear(a, shapes, message):
    hits = {name: overlap(a, shape) for name, shape in shapes.items()}
    require(max(hits.values(), default=0) <= 1e-5, message, overlaps_mm3=hits)
    return hits


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes(root):
    root = Path(root).resolve()
    return {str(path.relative_to(root)): sha(path)
            for path in sorted(root.rglob("*"))
            if path.is_file() and (path.suffix == ".py" or path.name in {"parameters.json", "params.json"})
            and "__pycache__" not in path.parts}


def params_at(root):
    for name in ("parameters.json", "params.json"):
        path = Path(root) / name
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError(f"No parameters.json or params.json in {root}")


def check_board_fit(assembly, tray, *, width, length, thickness, bottom, floor,
                    lateral_play, vertical_play, overlap_depth, clamp_y):
    """Independent PCB proxies; dimensions come from parameters, not CAD metadata."""
    cases = []
    for dx in (-lateral_play, 0.0, lateral_play):
        for dy in (-lateral_play, 0.0, lateral_play):
            for dz in (0.0, vertical_play / 2, vertical_play):
                pcb = box(width, length, thickness, dx, dy, bottom + dz)
                hits = clear(pcb, assembly, "PCB fouls at allowed play position")
                cases.append({"translation_xyz_mm": [dx, dy, dz],
                              "maximum_overlap_mm3": max(hits.values())})

    overtravel = []
    for axis in ("X", "Y", "Z"):
        for sign in (-1, 1):
            x = sign * (lateral_play + .05) if axis == "X" else 0
            y = sign * (lateral_play + .05) if axis == "Y" else 0
            z = bottom + (vertical_play + .05 if sign > 0 else -.05) if axis == "Z" else bottom
            pcb = box(width, length, thickness, x, y, z)
            hits = {name: overlap(pcb, solid) for name, solid in assembly.items()}
            require(max(hits.values()) > 1e-4, "Deliberate overtravel was not detected", axis=axis,
                    sign=sign, overlaps_mm3=hits)
            overtravel.append({"axis": axis, "sign": sign, "overlaps_mm3": hits})

    contacts = []
    # Probe 0.01 mm into each mating surface to distinguish support from empty space.
    for sx in (-1, 1):
        for sy in (-1, 1):
            for dx in (-lateral_play, 0.0, lateral_play):
                for dy in (-lateral_play, 0.0, lateral_play):
                    cx = sx * (width / 2 - overlap_depth / 2)
                    strip = box(overlap_depth, 8, .01, cx, sy * clamp_y, bottom - .01)
                    pcb_xy = box(width, length, .01, dx, dy, bottom - .01)
                    contact = strip.intersect(pcb_xy)
                    if not hasattr(contact, "bounding_box"):
                        contact = Compound(list(contact))
                    area = volume(contact) / .01
                    require(area >= (overlap_depth-lateral_play)*8 - 1e-5,
                            "Support area lost within allowed play", area_mm2=area)
                    require(abs(overlap(contact, tray)-volume(contact)) <= 1e-5,
                            "Missing production support ledge", sx=sx, sy=sy, dx=dx, dy=dy)
                    ceiling = Pos(0, 0, thickness + vertical_play + .01) * contact
                    clamps = {n: s for n, s in assembly.items() if "clamp" in n}
                    upper_contact = sum(overlap(ceiling, solid) for solid in clamps.values())
                    require(abs(upper_contact-volume(contact)) <= 1e-5,
                            "Missing clamp overlap", sx=sx, sy=sy, dx=dx, dy=dy)
                    contacts.append({"side_xy": [sx, sy], "pcb_translation_xy_mm": [dx, dy],
                                     "contact_area_each_face_mm2": area})

    # The central field excludes the two narrow edge strips occupied by ledges.
    # It proves the declared underside height against actual solid geometry.
    solder_clearance = bottom - floor
    solder_envelope = box(width-2*overlap_depth, length, solder_clearance, z=floor)
    solder_hit = overlap(solder_envelope, tray)
    require(solder_hit <= 1e-5, "Central underside clearance is obstructed", overlap_mm3=solder_hit)

    installation = []
    for rise in (0, .05, .2, .5, 1, 2, 4, 8, 15):
        pcb = box(width, length, thickness, z=bottom+rise)
        hit = overlap(pcb, tray)
        require(hit <= 1e-5, "Unclamped PCB vertical insertion blocked", rise_mm=rise, overlap_mm3=hit)
        installation.append({"rise_mm": rise, "overlap_mm3": hit})

    oversize_width = width+2*lateral_play+.05
    hit = overlap(box(oversize_width, length, thickness, z=bottom), tray)
    require(hit > 1e-4, "Oversize-width control was not detected", overlap_mm3=hit)
    oversize_length = length+2*lateral_play+.05
    length_hit = overlap(box(width, oversize_length, thickness, z=bottom), tray)
    require(length_hit > 1e-4, "Oversize-length control was not detected", overlap_mm3=length_hit)

    # At the positive lateral stop, left board edge = locating opening/2 - actual width.
    loss_width = width-overlap_depth+lateral_play
    undersize_width = loss_width-.1
    shift = (width+2*lateral_play-undersize_width)/2
    narrow = box(undersize_width, length, .01, shift, 0, bottom-.01)
    left_strip = box(overlap_depth, 8, .01, -width/2+overlap_depth/2, clamp_y, bottom-.01)
    require(overlap(narrow, left_strip) <= 1e-5, "Undersize retention-loss control failed")
    return {"allowed_play_positions": cases, "stop_overtravel_controls": overtravel,
            "central_solder_envelope": {"xyz_mm": [width-2*overlap_depth, length, solder_clearance],
                                         "overlap_mm3": solder_hit,
                                         "excluded_region": f"The {overlap_depth:g} mm nominal edge strips include intentional support contacts"},
            "support_and_clamp_contacts": contacts, "sampled_vertical_insertion": installation,
            "oversize_width_control": {"width_mm": oversize_width, "overlap_mm3": hit},
            "oversize_length_control": {"length_mm": oversize_length, "overlap_mm3": length_hit},
            "undersize_retention_loss": {"zero_opposite_overlap_width_mm": loss_width,
                                         "tested_width_mm": undersize_width,
                                         "tested_translation_x_mm": shift}}


def check_hardware(assembly, tray, hardware, *, centers, clamp_top, clamp_thickness,
                   insert_length, insert_od, pilot_diameter, pilot_depth, screw_length):
    insert_top = clamp_top-clamp_thickness
    insert_bottom = insert_top-insert_length
    bore_bottom = insert_top-pilot_depth
    screw_tip = clamp_top-screw_length
    engagement = min(insert_length, screw_length-clamp_thickness)
    require(engagement >= 3.5, "Insufficient nominal insert engagement", engagement_mm=engagement)
    require(screw_tip-bore_bottom >= .5, "Screw can bottom out", margin_mm=screw_tip-bore_bottom)
    displacement = np.pi*(insert_od**2-pilot_diameter**2)/4*insert_length
    insert_results = []
    independent = {}
    for index, (x, y) in enumerate(centers, 1):
        insert = cyl(insert_od/2, insert_length, x, y, insert_bottom)
        insert -= cyl(1.5, insert_length+.2, x, y, insert_bottom-.1)
        screw = cyl(1.5, screw_length, x, y, screw_tip)+cyl(2.75, 3, x, y, clamp_top)
        independent[f"insert_{index}"] = insert
        independent[f"screw_{index}"] = screw
        hits = clear(screw, assembly, "M3 screw collides with printed part")
        host_overlap = overlap(insert, tray)
        require(abs(host_overlap-displacement) <= 1e-5, "Unexpected insert/host displacement",
                center_xy_mm=[x, y], measured_mm3=host_overlap, expected_mm3=displacement)
        other_prints = {name: shape for name, shape in assembly.items() if shape is not tray}
        clear(insert, other_prints, "Insert collides with another printed part")
        require(tray.is_inside((x, y, bore_bottom-.05)), "Blind pilot has no closed floor")
        pilot_check = cyl(pilot_diameter/2-.01, pilot_depth-.02, x, y, bore_bottom+.01)
        require(overlap(pilot_check, tray) <= 1e-5, "Insert pilot is obstructed")
        # A straight 6 mm diameter access envelope starts above the modeled head.
        driver = cyl(3, 25, x, y, clamp_top+3+.01)
        clear(driver, assembly, "Clamp screwdriver access blocked")
        insert_results.append({"center_xy_mm": [x, y], "insert_bounds_z_mm": [insert_bottom, insert_top],
                               "screw_tip_z_mm": screw_tip, "bore_bottom_z_mm": bore_bottom,
                               "engagement_mm": engagement, "bottom_margin_mm": screw_tip-bore_bottom,
                               "insert_host_overlap_mm3": host_overlap,
                               "screw_print_overlaps_mm3": hits})

    # Independently establish which source proxies are inserts rather than trusting names.
    recognized = {}
    for name, solid in hardware.items():
        bb = solid.bounding_box()
        possible = [key for key, ref in independent.items()
                    if np.allclose(list(bb.min), list(ref.bounding_box().min), atol=1e-6)
                    and np.allclose(list(bb.max), list(ref.bounding_box().max), atol=1e-6)
                    and abs(volume(solid)-volume(ref)) < 1e-5]
        require(len(possible) == 1, "Unknown or incorrectly sized hardware proxy", name=name, matches=possible)
        require(possible[0] not in recognized, "Duplicate hardware proxy", name=name)
        recognized[possible[0]] = name
    require(set(recognized) == set(independent), "Missing hardware proxies", recognized=recognized)
    names = list(hardware)
    for i, name in enumerate(names):
        clear(hardware[name], {other: hardware[other] for other in names[i+1:]},
              "Hardware proxies intersect")

    old_screw_tip = clamp_top-8
    require(old_screw_tip <= bore_bottom+1e-7,
            "M3x8 negative control unexpectedly has bottom clearance")
    return {"mounts": insert_results, "recognized_source_proxies": recognized,
            "m3x8_negative_control": {"tip_z_mm": old_screw_tip,
                                      "bottom_margin_mm": old_screw_tip-bore_bottom}}


def check_preservation(tray, original, p):
    height = tray.bounding_box().max.Z
    clip = box(200, 200, height+1, z=-1)
    original = original.intersect(clip)
    if not hasattr(original, "bounding_box"):
        original = Compound(list(original))
    require(np.allclose(list(tray.bounding_box().min), list(original.bounding_box().min), atol=1e-6)
            and np.allclose(list(tray.bounding_box().max), list(original.bounding_box().max), atol=1e-6),
            "Original lower-body outside dimensions changed")
    floor_clip = box(200, 200, p["floor"]-1e-4)
    a = tray.intersect(floor_clip)
    b = original.intersect(floor_clip)
    if not hasattr(a, "bounding_box"):
        a = Compound(list(a))
    if not hasattr(b, "bounding_box"):
        b = Compound(list(b))
    floor_added, floor_removed = volume(a.cut(b)), volume(b.cut(a))
    require(max(floor_added, floor_removed) <= 1e-5, "Original floor or tie slots changed",
            added_mm3=floor_added, removed_mm3=floor_removed)

    # Independently bounded feature changes: exactly four retention islands.
    # This does not trust the author's declared edit regions; end stops remain
    # outside this mask and must preserve their original geometry.
    x_inner = min(52/2-.8, p["pcb_width"]/2-p["board_edge_overlap"])-.05
    x_outer = max(34, p["pcb_width"]/2+p["clamp_screw_offset_from_pcb_edge"]
                  +p["clamp_boss_diameter"]/2)+.05
    width = x_outer-x_inner
    y_radius = max(4, p["clamp_boss_diameter"]/2)+.05
    allowed = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            region = box(width, 2*y_radius, height, sx*(x_inner+x_outer)/2,
                         sy*p["clamp_y"], p["floor"])
            allowed = region if allowed is None else allowed+region
    new_outside = tray.cut(allowed)
    old_outside = original.cut(allowed)
    added = volume(new_outside.cut(old_outside))
    removed = volume(old_outside.cut(new_outside))
    require(max(added, removed) <= 1e-4, "Geometry changed outside retention edit regions",
            added_mm3=added, removed_mm3=removed)
    return {"floor_added_mm3": floor_added, "floor_removed_mm3": floor_removed,
            "outside_retention_added_mm3": added, "outside_retention_removed_mm3": removed,
            "original_outer_bounds_mm": [list(original.bounding_box().min), list(original.bounding_box().max)]}


def check_case(source, baseline, params, label):
    print(f"{label}: building candidate", flush=True)
    module = load(source/"model.py", "heatset_fit_candidate_"+label)
    base = load(source/"base_model.py", "heatset_fit_base_"+label)
    p = base.DEFAULTS | params.get("enclosure", {})
    result = module.build(params)
    assembly, parts = result["assembly"], result["parts"]
    require(set(assembly) == set(parts) and len(parts) == 5, "Expected tray and four clamps")
    tray = assembly["board_fit_tray"]
    for name, shape in parts.items():
        require(shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0,
                "Invalid printable solid", name=name)
        require(abs(shape.bounding_box().min.Z) <= 1e-6, "Part is not on print bed", name=name)
    names = list(assembly)
    for i, name in enumerate(names):
        clear(assembly[name], {other: assembly[other] for other in names[i+1:]},
              "Printed assembly parts intersect")

    bottom = p["floor"]+p["solder_clearance"]
    board_top = bottom+p["pcb_thickness"]
    bearing = board_top+p["board_vertical_play"]+p["clamp_thickness"]
    require(abs(tray.bounding_box().max.Z-bearing-params.get("extra_height_above_clamps", 0)) <= 1e-6,
            "Unexpected tray height")
    centers = [(sx*(p["pcb_width"]/2+p["clamp_screw_offset_from_pcb_edge"]), sy*p["clamp_y"])
               for sx in (-1, 1) for sy in (-1, 1)]
    require((p["clamp_boss_diameter"]-p["clamp_insert_outer_diameter"])/2 >= 2,
            "Insufficient radial boss wall")
    require(p["clamp_screw_offset_from_pcb_edge"]-p["clamp_boss_diameter"]/2 >= p["board_lateral_play"]-1e-8,
            "Boss encroaches on PCB play envelope")
    print(f"{label}: board fit and stop controls", flush=True)
    fit = check_board_fit(assembly, tray, width=p["pcb_width"], length=p["pcb_length"],
                          thickness=p["pcb_thickness"], bottom=bottom, floor=p["floor"],
                          lateral_play=p["board_lateral_play"], vertical_play=p["board_vertical_play"],
                          overlap_depth=p["board_edge_overlap"], clamp_y=p["clamp_y"])
    print(f"{label}: hardware", flush=True)
    hardware = check_hardware(assembly, tray, result["hardware"], centers=centers,
                              clamp_top=bearing, clamp_thickness=p["clamp_thickness"],
                              insert_length=p["clamp_insert_length"], insert_od=p["clamp_insert_outer_diameter"],
                              pilot_diameter=p["clamp_insert_pilot_diameter"],
                              pilot_depth=p["clamp_insert_bore_depth"], screw_length=p["clamp_screw_length"])
    actual_allowed = {(name, "board_fit_tray") for key, name in hardware["recognized_source_proxies"].items()
                      if key.startswith("insert_")}
    declared = result["expected_hardware_intersections"]
    require({(entry["hardware"], entry["printed_part"]) for entry in declared} == actual_allowed
            and len(declared) == 4, "Insert overlap allowlist is incorrect")
    for entry in declared:
        require(abs(entry["expected_volume_mm3"]-overlap(result["hardware"][entry["hardware"]], tray)) < 1e-5,
                "Declared insert displacement does not match geometry")

    print(f"{label}: original-shell preservation", flush=True)
    if label == "nominal":
        original = import_step(baseline/"parts"/"body.step")
    else:
        original_base = load(baseline/"base_model.py", "original_console_"+label)
        op = {key: p[key] for key in original_base.DEFAULTS}
        op["pcb_width"] = p["component_reference_width"]
        op["pcb_thickness"] = p["shell_reference_pcb_thickness"]
        original_result = original_base.build_console(op)
        mounts = load(baseline/"mounting.py", "original_mounts_"+label)
        original, _ = mounts.add_mounts(original_result["assembly"]["body"],
                                        -original_result["measurements"]["main_shell_xy"][0]/2-3.6,
                                        [4, -21])
    preservation = check_preservation(tray, original, p)
    print(f"{label}: PASS", flush=True)
    return {"status": "pass", "pcb_xyz_mm": [p["pcb_width"], p["pcb_length"], p["pcb_thickness"]],
            "cavity_xy_mm": [p["component_reference_width"]+2*p["side_margin"],
                             p["pcb_length"]+2*p["end_margin"]],
            "tray_height_mm": tray.bounding_box().max.Z,
            "board_fit": fit, "hardware": hardware, "preservation": preservation,
            "source_measurements": result["measurements"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", choices=("all", "nominal", "wider_longer"), default="all")
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    params = params_at(source)
    source_before = source_hashes(source)
    report = {"status": "running", "source": str(source), "baseline": str(baseline),
              "checker_sha256": sha(__file__),
              "source_hashes": source_before,
              "baseline_hashes": {"base_model.py": sha(baseline/"base_model.py"),
                                  "mounting.py": sha(baseline/"mounting.py"),
                                  "parts/body.step": sha(baseline/"parts"/"body.step")},
              "scenarios": {}, "limits": [
                  "CAD fit checks only; printed fit, insert retention strength and actual solder/component envelopes remain untested.",
                  "The existing 0.2 mm vertical PCB play remains; this test does not validate or recalibrate actuators.",
                  "PCB installation is checked at stated sampled heights with clamps removed; tools use a straight 6 mm diameter envelope.",
                  "The 52 mm populated span is an annotation with unmeasured alignment and height; there is no populated electronics collision model.",
                  "Hardware proxies omit threads; their overlap checks are geometric and do not establish tightening torque."]}
    try:
        for name in ("nominal", "wider_longer"):
            if args.scenario not in ("all", name):
                continue
            candidate_params = json.loads(json.dumps(params))
            if name == "wider_longer":
                candidate_params.setdefault("enclosure", {}).update(pcb_width=50.0, pcb_length=74.0)
            report["scenarios"][name] = check_case(source, baseline, candidate_params, name)
        require(source_hashes(source) == source_before, "Source files changed during validation")
        report["status"] = "pass"
    except Exception as exc:
        report["status"] = "fail"
        report["error"] = str(exc)
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+"\n")


if __name__ == "__main__":
    main()
