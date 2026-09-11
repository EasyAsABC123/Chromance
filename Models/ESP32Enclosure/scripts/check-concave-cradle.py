"""Independent checks for an actual cylindrical cable groove and its tie passage."""
import argparse
import importlib.util
import json
from math import pi, sqrt
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def check_case(c, author, params, old, label):
    require, same, overlap, clear = c.require, c.same, c.overlap, c.clear
    p = author.DEFAULTS | params
    print(label+": build and compare non-cradle geometry to dimension-adjusted010", flush=True)
    new = author.build(params)
    inventory = c.preserve_inventory(new, old)
    body = new["case_local_assembly"]["body"]
    original = old["case_local_assembly"]["body"]
    reference = old["cable_retention_reference_body_local"]
    same(reference, new["cable_retention_reference_body_local"], "Unchanged body before cable feature")
    end_y = p["pcb_length"]/2+p["end_margin"]
    rim = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]+p["component_clearance"]
    sill = rim-p["end_cable_height"]
    projection = p["cable_saddle_projection"]
    start_y, stop_y = end_y-projection, end_y+p["cable_saddle_wall_overlap"]
    root = sill-projection
    tie_y = (start_y+end_y)/2
    tie_w, tie_t = p["zip_tie_width_provisional"], p["zip_tie_thickness_provisional"]
    slot_w = tie_w+2*p["zip_tie_slot_side_clearance"]
    slot_floor = sill-p["zip_tie_slot_floor_below_sill"]
    slot_eave = slot_floor+tie_t+2*p["zip_tie_slot_vertical_clearance"]
    slot_apex = slot_eave+slot_w/2
    diameter = p["cable_diameter_provisional"]
    radius = diameter/2+p["cable_cradle_radial_clearance"]
    half_width = radius+p["cable_cradle_side_wall"]
    groove_bottom = slot_apex+p["cable_cradle_floor_above_tunnel"]
    groove_z = groove_bottom+radius
    cable_z = groove_bottom+diameter/2
    print(label+": independent block, ramp, cylindrical subtraction and passage", flush=True)
    # Independent halfspace construction of the wall root and tunnel roof,
    # compared with the author's extruded profiles.
    block = c.box(2*half_width, stop_y-start_y, sill-root,
                  y=(start_y+stop_y)/2, z=root)
    ramp = c.split(block, c.Plane(origin=(0, end_y, root), z_dir=(0, 1, 1)), keep=c.Keep.TOP)
    upper = c.box(2*half_width, stop_y-start_y, groove_z-sill,
                  y=(start_y+stop_y)/2, z=sill)
    stock = ramp+upper
    groove = c.Pos(0, (start_y+stop_y)/2, groove_z)*c.Rot(X=90)*c.Cylinder(
        radius, stop_y-start_y+2, align=(c.Align.CENTER, c.Align.CENTER, c.Align.CENTER))
    passage = c.box(2*half_width+4, slot_w, slot_apex-slot_floor,
                    y=tie_y, z=slot_floor)
    passage = c.split(passage, c.Plane(origin=(0, tie_y, slot_apex), z_dir=(0, 1, 1)), keep=c.Keep.BOTTOM)
    passage = c.split(passage, c.Plane(origin=(0, tie_y, slot_apex), z_dir=(0, -1, 1)), keep=c.Keep.BOTTOM)
    feature = stock-groove-passage
    same(stock, new["cable_retention_stock_local"], "Independent rectangular cradle stock")
    same(feature, new["cable_retention_local"], "Independent concave cradle reconstruction")
    same(groove, new["cable_retention_groove_cutter_local"], "Independent axial cylinder cutter")
    require(feature.is_valid and len(feature.solids()) == 1, "Cradle is not one connected solid")
    require(overlap(feature, groove) < 1e-5, "Cylinder volume remains inside cradle")
    cut_volume = overlap(stock, groove)
    analytic_half_cylinder = pi*radius**2*(stop_y-start_y)/2
    require(abs(cut_volume-analytic_half_cylinder) < 1e-5,
            "Groove is not the intended half-cylinder subtraction", actual=cut_volume, expected=analytic_half_cylinder)
    expected_body = reference+feature
    differences = [c.volume(body.cut(expected_body)), c.volume(expected_body.cut(body))]
    require(max(differences) < 1e-4, "Body differs from independent cradle replacement", differences_mm3=differences)
    allowed = c.box(2*half_width+.2, stop_y-start_y+.2, groove_z-root+.2,
                    y=(start_y+stop_y)/2, z=root-.1)
    outside_a, outside_b = body.cut(allowed), original.cut(allowed)
    outside = [c.volume(outside_a.cut(outside_b)), c.volume(outside_b.cut(outside_a))]
    require(max(outside) < 1e-4, "Body changed outside cradle region", differences_mm3=outside)
    bond = overlap(stock, reference)
    require(bond > 10, "Cradle lacks a substantial volumetric wall connection")
    # Probes prove concavity: across the lower cylindrical arc, plastic lies
    # immediately below and the groove opening lies immediately above.
    arc_probes = []
    for fraction in (0, .5, .8, .95):
        x = fraction*radius
        surface_z = groove_z-sqrt(radius**2-x**2)
        below = c.box(.04, .2, .04, x, start_y+.7, surface_z-.12)
        above = c.box(.04, .2, .04, x, start_y+.7, surface_z+.08)
        solid_fraction = overlap(below, body)/below.volume
        void_overlap = overlap(above, body)
        require(solid_fraction > .999 and void_overlap < 1e-7,
                "Groove does not follow concave circular arc", x=x, solid_fraction=solid_fraction, void_mm3=void_overlap)
        arc_probes.append({"x_mm": x, "arc_z_mm": surface_z,
                           "below_material_fraction": solid_fraction, "above_overlap_mm3": void_overlap})
    for sign in (-1, 1):
        shoulder = c.box(.2, .2, .2, sign*(radius+p["cable_cradle_side_wall"]/2),
                         start_y+.7, groove_z-.3)
        require(overlap(shoulder, body)/shoulder.volume > .999, "Groove side wall missing")
    require(groove_bottom-slot_apex >= 2-1e-8, "Less than2 mm floor between groove and tunnel")
    print(label+": seated cable, threading and open-lid access", flush=True)
    refs = new["cable_retention_references_local"]
    cable_end = end_y+p["wall"]+6
    expected_cable = c.Pos(0, (start_y+cable_end)/2, cable_z)*c.Rot(X=90)*c.Cylinder(
        diameter/2, cable_end-start_y, align=(c.Align.CENTER, c.Align.CENTER, c.Align.CENTER))
    same(expected_cable, refs["cable"], "Cable seated on true concave groove bottom")
    require(abs(refs["cable"].bounding_box().min.Z-groove_bottom) < 1e-7, "Cable floats above groove floor")
    for name, shape in refs.items():
        require(shape.is_valid and len(shape.solids()) == 1, "Invalid routing reference", name=name)
        clear(shape, new["case_local_assembly"], name+" intersects an assembled print")
    thread_tool = c.box(2*half_width+16, tie_w, tie_t, y=tie_y,
                        z=slot_floor+p["zip_tie_slot_vertical_clearance"])
    clear(thread_tool, new["case_local_assembly"], "Tie tail cannot traverse tunnel")
    open_parts = {name: shape for name, shape in new["case_local_assembly"].items() if name != "lid"}
    # The sweep below the cable axis is its seated circular profile; a box from
    # groove bottom would falsely intersect every functioning concave seat.
    insertion = expected_cable+c.box(diameter, cable_end-start_y, rim+5-cable_z,
                                     y=(start_y+cable_end)/2, z=cable_z)
    clear(insertion, open_parts, "Cable cannot be laid through open groove mouth")
    hb = refs["zip_tie_head"].bounding_box()
    head_access = c.box(hb.size.X, hb.size.Y, rim+5-hb.min.Z,
                        (hb.min.X+hb.max.X)/2, (hb.min.Y+hb.max.Y)/2, hb.min.Z)
    clear(head_access, open_parts, "Tie head cannot be reached above shoulder")
    require(overlap(refs["zip_tie_head"], refs["zip_tie_route"]) > .01, "Head disconnected from tie route")
    require(overlap(refs["zip_tie_head"], refs["cable"]) < 1e-5
            and overlap(refs["zip_tie_route"], refs["cable"]) < 1e-5, "Tie or head intersects cable")
    lid_gap = rim-max(refs[name].bounding_box().max.Z for name in ("cable", "zip_tie_route", "zip_tie_head"))
    require(lid_gap >= 2-1e-8, "Less than2 mm lid clearance")
    require(hb.min.Z-groove_z >= .5-1e-8, "Tie head crowds cradle shoulder")
    require(hb.max.X <= p["end_cable_width"]/2-.5+1e-8, "Head exceeds cable exit width reserve")
    pcb_keepout = c.box(p["pcb_width"]+.6, p["pcb_length"]+.6, rim-p["floor"]-.2, z=p["floor"]+.2)
    require(overlap(feature, pcb_keepout) < 1e-5, "Cradle enters PCB/component envelope")
    for name, shape in refs.items():
        require(overlap(shape, pcb_keepout) < 1e-5, "Cable routing enters component envelope", name=name)
    clear(new["mount_transform"]*feature, new["hardware"], "Cradle interferes with hardware")
    lowered = overlap(c.Pos(0, 0, -.2)*refs["cable"], body)
    square_negative = overlap(c.box(diameter, stop_y-start_y, diameter/2,
                                    y=(start_y+stop_y)/2, z=groove_bottom), body)
    require(lowered > .1 and square_negative > 1,
            "Concavity/contact negative controls failed", lowered_mm3=lowered, square_mm3=square_negative)
    print(label+": actual layers across ramp, tie roof and concave groove", flush=True)
    layers = c.layer_review(body, (-half_width-.1, start_y-.1, half_width+.1, stop_y+.1), root, groove_z)
    return {"status": "passed", "scenario": label,
            "unchanged_nonbody_parts_relative_to_dimension_adjusted010": inventory["preserved_print_parts"],
            "unchanged_hardware_count_relative_to_dimension_adjusted010": inventory["preserved_hardware_count"],
            "body_difference_from_independent_reconstruction_mm3": differences,
            "body_change_outside_cradle_region_mm3": outside,
            "cradle_groove_diameter_mm": 2*radius, "measured_cable_diameter_mm": diameter,
            "groove_cylinder_subtraction_mm3": cut_volume, "arc_probes": arc_probes,
            "cradle_width_mm": 2*half_width, "cradle_floor_above_tunnel_mm": groove_bottom-slot_apex,
            "cradle_wall_stock_overlap_mm3": bond, "cradle_raw_volume_mm3": float(feature.volume),
            "new_body_volume_mm3": float(body.volume), "previous_body_volume_mm3": float(original.volume),
            "cable_seated_axis_z_mm": cable_z, "groove_bottom_z_mm": groove_bottom,
            "head_bottom_to_shoulder_mm": hb.min.Z-groove_z, "minimum_lid_clearance_mm": lid_gap,
            "negative_controls_mm3": {"cable_lowered_0_2mm": lowered, "square_in_concave_groove": square_negative},
            "layer_review": layers,
            "limitations": ["Actual tie feeding, bending, tightening, cable-jacket safety and pull retention require physical coupon results.",
                            "Groove radial clearance is provisional despite the measured8 mm cable diameter.",
                            "Comparison isolates cradle geometry by rebuilding010 with the same PCB dimensional corrections; it does not claim all other parts match published010."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--prior-checker", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    helper_path = (args.prior_checker or baseline.parent.parent/"scripts/check-cable-retention.py").resolve()
    c = load(helper_path, "independent_cradle_geometry_helpers")
    before = c.hashes(source)
    p = json.loads((source/"parameters.json").read_text())
    old_p = json.loads((baseline/"parameters.json").read_text())
    author = load(source/"model.py", "concave_cradle_under_review")
    previous = load(baseline/"model.py", "previous_convex_support")
    print("Build frozen convex reference010", flush=True)
    # Isolate the cradle change from the separately reviewed PCB width/thickness
    # correction. These overrides are reported explicitly, never presented as
    # unchanged printed geometry versus the originally published010 artifacts.
    adjusted = old_p | {k: p[k] for k in ("pcb_width", "pcb_thickness", "solder_clearance")}
    old = previous.build(adjusted)
    results = [check_case(c, author, p, old, "nominal_8mm_cable")]
    variant = p | {"cable_cradle_radial_clearance": .3}
    results.append(check_case(c, author, variant, old, "variant_0_3mm_radial_clearance"))
    c.require(abs(results[1]["cradle_groove_diameter_mm"]-results[0]["cradle_groove_diameter_mm"]-.2) < 1e-7,
              "Clearance variant did not enlarge the groove by0.2 mm diameter")
    c.require(results[1]["groove_cylinder_subtraction_mm3"] > results[0]["groove_cylinder_subtraction_mm3"],
              "Clearance variant did not enlarge cylindrical subtraction")
    c.require(c.hashes(source) == before, "Source changed during review")
    report = {"status": "passed", "source_hashes": before, "baseline_hashes": c.hashes(baseline),
              "checker_sha256": c.sha(Path(__file__)), "helper_checker_sha256": c.sha(helper_path),
              "baseline_parameter_overrides": {k: {"published010": old_p[k], "comparison": adjusted[k]}
                                               for k in adjusted if adjusted[k] != old_p[k]},
              "scenarios": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "passed", "report": str(args.output), "scenarios": len(results)}, indent=2))


if __name__ == "__main__":
    main()
