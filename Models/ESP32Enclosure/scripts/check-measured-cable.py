"""Verify the measured8 mm cable on the unchanged revision009 saddle geometry.

This review validates digital envelopes only. The same-source small print is
still required to test actual cable/tie fit, feeding, tightening, and grip.
"""
import argparse
import importlib.util
import json
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
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--prior-checker", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    checker = (args.prior_checker or baseline.parent.parent/"scripts/check-cable-retention.py").resolve()
    c = load(checker, "independent_cable_geometry_helpers")
    before = c.hashes(source)
    p = json.loads((source/"parameters.json").read_text())
    old_p = json.loads((baseline/"parameters.json").read_text())
    require, same, overlap, clear = c.require, c.same, c.overlap, c.clear
    require(set(p) == set(old_p), "Parameter inventory changed")
    changes = {k: [old_p[k], p[k]] for k in p if p[k] != old_p[k]}
    require(changes == {"cable_diameter_provisional": [6.0, 8.0]},
            "Only the measured cable diameter may change", changes=changes)
    require(p["cable_saddle_radius"] == 4 and p["cable_saddle_projection"] == 7
            and p["zip_tie_width_provisional"] == 2.5 and p["zip_tie_thickness_provisional"] == 1,
            "The nominal existing saddle and tie are required")
    print("Build frozen009 and measured8 mm candidate", flush=True)
    old = load(baseline/"model.py", "old_cable_retention009").build(old_p)
    new = load(source/"model.py", "measured_cable_retention010").build(p)
    print("Compare all prints, hardware, saddle and placements", flush=True)
    inventory = c.preserve_inventory(new, old)
    same(new["parts"]["body"], old["parts"]["body"], "Body print unchanged")
    same(new["assembly"]["body"], old["assembly"]["body"], "Body world placement unchanged")
    for key in ("cable_retention_local", "cable_retention_stock_local", "cable_retention_tunnel_local",
                "cable_retention_added_local", "cable_retention_reference_body_local"):
        same(new[key], old[key], key+" unchanged")
    # Every actual print shape and world placement is unchanged, so the enclosure
    # bounding envelope and all print orientations are necessarily unchanged too.
    require(len(new["parts"]) == 15, "Expected15 printed pieces")
    body = new["case_local_assembly"]["body"]
    refs = new["cable_retention_references_local"]
    end_y = p["pcb_length"]/2+p["end_margin"]
    rim = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]+p["component_clearance"]
    sill = rim-p["end_cable_height"]
    crown = sill+p["cable_saddle_radius"]
    start_y = end_y-p["cable_saddle_projection"]
    stop_y = end_y+p["wall"]+6
    cable_z = crown+4
    tie_y = (start_y+end_y)/2
    print("Check measured8 mm cable, existing tunnel, head and open-lid insertion", flush=True)
    expected_cable = c.Pos(0, (start_y+stop_y)/2, cable_z)*c.Rot(X=90)*c.Cylinder(
        4, stop_y-start_y, align=(c.Align.CENTER, c.Align.CENTER, c.Align.CENTER))
    same(expected_cable, refs["cable"], "Measured8 mm cylinder on unchanged crown")
    cable_box = refs["cable"].bounding_box()
    require(abs(cable_box.size.X-8) < 1e-7 and abs(cable_box.size.Z-8) < 1e-7,
            "Cable reference is not8 mm diameter")
    require(abs(cable_box.min.Z-20) < 1e-7 and abs(cable_box.max.Z-28) < 1e-7,
            "Cable reference is not seated at crownZ20")
    routing_hits = {}
    for name, shape in refs.items():
        require(shape.is_valid and len(shape.solids()) == 1, "Invalid reference envelope", name=name)
        routing_hits[name] = clear(shape, new["case_local_assembly"], name+" intersects assembled parts")
    require(overlap(refs["zip_tie_head"], refs["zip_tie_route"]) > .01,
            "Tie head reference is disconnected from loop")
    require(overlap(refs["zip_tie_head"], refs["cable"]) < 1e-5
            and overlap(refs["zip_tie_route"], refs["cable"]) < 1e-5,
            "Tie references cut measured cable")
    slot_floor = sill-p["zip_tie_slot_floor_below_sill"]
    thread_tool = c.box(2*p["cable_saddle_radius"]+16, p["zip_tie_width_provisional"],
                        p["zip_tie_thickness_provisional"], y=tie_y,
                        z=slot_floor+p["zip_tie_slot_vertical_clearance"])
    threading = clear(thread_tool, new["case_local_assembly"], "Existing tunnel cannot feed the tie tail")
    open_parts = {name: shape for name, shape in new["case_local_assembly"].items() if name != "lid"}
    cable_access = c.box(8, stop_y-start_y, rim+5-crown,
                         y=(start_y+stop_y)/2, z=crown)
    insertion = clear(cable_access, open_parts, "Measured cable cannot be inserted from the open lid")
    hb = refs["zip_tie_head"].bounding_box()
    head_access = c.box(hb.size.X, hb.size.Y, rim+5-hb.min.Z,
                        (hb.min.X+hb.max.X)/2, (hb.min.Y+hb.max.Y)/2, hb.min.Z)
    head_insertion = clear(head_access, open_parts, "Tie head lacks open-lid access")
    top = max(refs[name].bounding_box().max.Z for name in ("cable", "zip_tie_route", "zip_tie_head"))
    lid_gap = rim-top
    require(abs(lid_gap-2.7) < 1e-7, "Expected2.7 mm minimum reference-to-lid clearance", clearance_mm=lid_gap)
    pcb_keepout = c.box(p["pcb_width"]+.6, p["pcb_length"]+.6,
                        rim-p["floor"]-.2, z=p["floor"]+.2)
    pcb_hits = {name: overlap(shape, pcb_keepout) for name, shape in refs.items()}
    require(max(pcb_hits.values()) < 1e-5, "Cable references enter existing assumed component envelope")
    cable_negative = overlap(c.Pos(0, 0, -.2)*refs["cable"], body)
    thread_negative = overlap(c.Pos(0, 0, -p["zip_tie_slot_vertical_clearance"]-.3)*thread_tool, body)
    require(cable_negative > .1 and thread_negative > .1, "Contact/blocked-path negative controls failed")
    # No new layer sweep: prove identical printed geometry first, then explicitly
    # retain the measured nominal layer proof for the actual same source baseline.
    prior_path = baseline/"cable-retention-validation.json"
    if not prior_path.exists():
        prior_path = baseline/"cable-validation.json"
    prior = json.loads(prior_path.read_text())
    require(prior["status"] == "passed", "Prior layer report did not pass")
    require(prior["source_hashes"] == c.hashes(baseline), "Prior layer report is not for baseline009")
    nominal_layers = prior["scenarios"][0]["layer_review"]
    require(nominal_layers["maximum_excess_area_mm2"] < 1e-5, "Prior nominal layer proof failed")
    require(c.hashes(source) == before, "Source changed during review")
    report = {
        "status": "passed", "source_hashes": before, "baseline_hashes": c.hashes(baseline),
        "checker_sha256": c.sha(Path(__file__)), "helper_checker_sha256": c.sha(checker),
        "parameter_changes": changes, "unchanged_print_count": 15,
        "unchanged_hardware_count": inventory["preserved_hardware_count"],
        "printed_geometry_envelope_unchanged": True, "saddle_geometry_unchanged": True,
        "cable_diameter_user_measured_mm": 8, "cable_axis_local_z_mm": cable_z,
        "cable_crown_contact_local_z_mm": crown, "cable_top_local_z_mm": cable_box.max.Z,
        "minimum_cable_tie_head_to_lid_mm": lid_gap, "routing_intersections_mm3": routing_hits,
        "threading_intersections_mm3": threading, "cable_insertion_intersections_mm3": insertion,
        "head_access_intersections_mm3": head_insertion, "component_envelope_intersections_mm3": pcb_hits,
        "negative_controls_mm3": {"cable_lowered_0_2mm": cable_negative,
                                  "tie_path_lowered_into_floor": thread_negative},
        "retained_layer_proof": {"report_sha256": c.sha(prior_path),
                                 "nominal_layer_count": nominal_layers["layer_count"],
                                 "layer_height_mm": nominal_layers["layer_height_mm"],
                                 "maximum_excess_area_mm2": nominal_layers["maximum_excess_area_mm2"],
                                 "reason": "All printed geometry and print orientations match baseline009 exactly."},
        "limitations": ["User measured cable diameter8 mm; no physical coupon result is yet recorded.",
                        "Tie dimensions, flexibility, tightening, jacket safety and pull retention remain unverified.",
                        "Loose rectangular tie loop is a clearance reference, not exact bent hardware.",
                        "Existing nominal52x70 board model is retained; measured49 mm layout remains separate."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "passed", "unchanged_prints": 15,
                      "unchanged_hardware": 34, "cable_mm": 8, "lid_gap_mm": lid_gap,
                      "report": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
