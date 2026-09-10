"""Check the coupon against production STEP and probe PCB/hardware fits.

Geometry tests use idealized PCB and hardware envelopes. They cannot establish
the real board's outline, populated edge clearance or printer accuracy.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from math import sqrt
from pathlib import Path

from fdm_cad.build import load_model
from fdm_cad.geometry import check_solid
from build123d import Align, Cylinder, Pos, RegularPolygon, ShapeList, extrude, import_step


def box(w, d, h, x=0, y=0, z=0):
    from build123d import Box
    return Pos(x, y, z) * Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def overlap(a, b):
    common = a.intersect(b)
    if common is None:
        return 0.0
    items = list(common) if isinstance(common, (list, tuple, ShapeList)) else [common]
    return sum(float(s.volume) for s in items)


def cylinder(r, h, x, y, z):
    return Pos(x, y, z) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def check_case(source, params, label):
    result = load_model(source / "model.py", params)
    p = params["enclosure"]
    m = result["measurements"]
    tray = result["parts"]["board_fit_tray"]
    assembled = result["assembly"]
    records = []

    def record(name, actual, requirement):
        if not requirement:
            raise AssertionError(f"{label}: {name}: {actual}")
        records.append({"name": name, "actual": actual, "passed": True})

    for name, part in result["parts"].items():
        check_solid(part, name, print_orientation=True)
    bw, bl, bt = p["pcb_width"], p["pcb_length"], p["pcb_thickness"]
    bottom = m["board_bottom_z_mm"]
    # Clamps removed for insertion. Sample approach from20 mm above seat.
    insert_results = []
    for dz in [0, .2, 1, 3, 8, 20]:
        v = overlap(box(bw, bl, bt, z=bottom + dz), tray)
        insert_results.append({"height_above_seat_mm": dz, "overlap_mm3": v})
    record("unclamped_board_vertical_insertion_samples", insert_results,
           all(v["overlap_mm3"] < .001 for v in insert_results))

    # A retained board may touch stops and move through the entire vertical slot.
    worst = 0.0
    positions = 0
    for x in [-.4, 0, .4]:
        for y in [-.4, 0, .4]:
            for dz in [0, p["board_vertical_play"]]:
                board = box(bw, bl, bt, x, y, bottom + dz)
                worst = max(worst, *(overlap(board, s) for s in assembled.values()))
                positions += 1
    record("retained_board_at_side_end_and_vertical_stops", {"samples": positions, "worst_overlap_mm3": worst}, worst < .001)

    # Positive controls: the gauge must actually reject oversize/thick boards.
    for name, board in {
        "width_beyond_locating_opening": box(bw + 1.0, bl, bt, z=bottom),
        "length_beyond_locating_opening": box(bw, bl + 1.0, bt, z=bottom),
        "thickness_beyond_clamp_slot": box(bw, bl, bt + p["board_vertical_play"] + .2, z=bottom),
    }.items():
        v = sum(overlap(board, s) for s in assembled.values())
        record(name, {"detected_overlap_mm3": v}, v > .05)

    underside = box(bw, bl, p["solder_clearance"], z=p["floor"])
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            # Exclude the intentional bare-board contact strips; no solder allowed here.
            underside -= box(p["board_edge_overlap"] + 2, 8, p["solder_clearance"] + 2,
                             sx * (bw/2 - p["board_edge_overlap"]/2 + 1),
                             sy * p["clamp_y"], p["floor"] - 1)
    v = overlap(underside, tray)
    record("six_mm_underside_envelope_excluding_contact_strips", v, v < .001)

    hardware = []
    for name, clamp in assembled.items():
        if not name.startswith("pcb_clamp_"):
            continue
        sx = -1 if "left" in name else 1
        sy = -1 if "front" in name else 1
        x, y = sx*(bw/2 + 4.5), sy*p["clamp_y"]
        head_z = clamp.bounding_box().max.Z
        shaft = cylinder(1.5, 8, x, y, head_z - 8)
        screw = shaft + cylinder(2.75, 3, x, y, head_z)
        # Nut drawn against the upper pocket face; print nut pocket remains unchanged.
        nut_top = bottom - 3.5 + p["m3_nut_pocket_height"]
        nut = Pos(x, y, nut_top - 2.4) * extrude(RegularPolygon(5.5/sqrt(3), 6, rotation=30), amount=2.4)
        nut -= cylinder(1.51, 2.6, x, y, nut_top - 2.5)
        screw_v = sum(overlap(screw, s) for s in assembled.values())
        nut_v = overlap(nut, tray)
        approach_v = max(overlap(Pos(0, offset, 0)*nut, tray) for offset in [-12, -8, -6, -4, -2, 0])
        driver = cylinder(3, 20, x, y, head_z + 3)
        driver_v = sum(overlap(driver, s) for s in assembled.values())
        h = {"clamp": name, "screw_overlap_mm3": screw_v, "nut_overlap_mm3": nut_v,
             "nut_entry_sample_worst_overlap_mm3": approach_v, "driver_overlap_mm3": driver_v,
             "tip_to_floor_mm": head_z - 8 - p["floor"],
             "nut_engagement_mm": min(nut_top, head_z) - max(nut_top - 2.4, head_z - 8)}
        hardware.append(h)
        record(name + "_hardware", h, max(screw_v, nut_v, approach_v, driver_v) < .001
               and h["tip_to_floor_mm"] > 0 and h["nut_engagement_mm"] >= 2.399)

    return result, {"scenario": label, "status": "passed", "checks": records,
                    "measurements": m, "hardware": hardware}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    params = json.loads((source / "parameters.json").read_text())
    result, nominal = check_case(source, params, "nominal")
    comparisons = []
    for name in result["parts"]:
        old_name = "body" if name == "board_fit_tray" else name
        old = import_step(baseline / "parts" / (old_name + ".step"))
        if name == "board_fit_tray":
            old = old.intersect(result["clip_volume"]).solids()[0]
        current = result["parts"][name]
        # STEP read-back and fresh CAD may have distinct face decomposition.
        lost = float((old-current).volume)
        added = float((current-old).volume)
        if max(abs(lost), abs(added)) > .001:
            raise AssertionError(f"Coupon does not match production part {name}: {lost}, {added}")
        comparisons.append({"part": name, "removed_from_expected_mm3": lost,
                            "added_to_expected_mm3": added, "passed": True})
    variant_params = deepcopy(params)
    variant_params["enclosure"].update(pcb_width=56.0, pcb_length=78.0)
    variant, variant_report = check_case(source, variant_params, "56x78mm_board")
    if variant["measurements"]["board_locating_opening_xy_mm"] != [56.8, 78.8]:
        raise AssertionError("Parameterized locating opening failed to follow board size")
    issues = [
        {"id": "bare_edges_and_lateral_retention", "status": "physical_measurement_required",
         "detail": "Nominal 0.8 mm overlap falls to 0.4 mm at the opposite stop; up to 1.2 mm bare strip is contacted on the near side. With the unchanged 52.8 mm locating opening, a 51.6 mm-wide PCB can lose the opposite supports at its lateral stop."},
        {"id": "vertical_play_changes_button_calibration", "status": "calibrate_after_retention_fit",
         "detail": "The 0.2 mm board play lets the inverted PCB settle against clamps. With unchanged contact tips, nominal idle gap 0.6 becomes 0.4 mm and geometric full-stroke depression 0.2 becomes 0.4 mm. Set/verify contacts with the actual board seated against clamps in the mounted orientation; actual switch travel remains unknown. This coupon excludes actuators."},
        {"id": "upper_geometry_omitted", "status": "not_tested_by_coupon",
         "detail": "Lid, full upper component/wiring space, full USB/DC plug corridor, end cable exit, actuator/button alignment and desk bracket are omitted. Successful coupon fit does not certify these."},
    ]
    hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(source.rglob("*.py")) if "__pycache__" not in p.parts}
    hashes["parameters.json"] = hashlib.sha256((source / "parameters.json").read_bytes()).hexdigest()
    baseline_files = [baseline / "parts" / (n + ".step") for n in
                      ["body", "pcb_clamp_left_front", "pcb_clamp_left_rear", "pcb_clamp_right_front", "pcb_clamp_right_rear"]]
    report = {"status": "passed", "physical_fit_tested": False, "units": "mm",
              "source_sha256": hashes,
              "baseline_step_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in baseline_files},
              "production_geometry_comparisons": comparisons,
              "scenarios": [nominal, variant_report], "fit_risks_and_followups": issues}
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "passed", "scenarios": 2, "production_comparisons": len(comparisons),
                      "output": str(args.output.resolve()), "fit_risks": issues}))


if __name__ == "__main__":
    main()
