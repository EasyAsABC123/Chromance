"""Repeat cartridge geometry, contact direction, stops, and retention checks."""
import json
from pathlib import Path

import fdm_cad.build
from build123d import Pos
from button_module import make_button, box


def volume(shape):
    if shape is None:
        return 0.0
    return float(shape.volume) if hasattr(shape, "volume") else sum(float(s.volume) for s in shape)


def intersections(first, second=None):
    findings = []
    names = list(first)
    for i, name in enumerate(names):
        others = second.items() if second is not None else ((k, first[k]) for k in names[i+1:])
        for other, shape in others:
            v = volume(first[name].intersect(shape))
            if v > 1e-6:
                findings.append({"parts": [name, other], "volume_mm3": v})
    return findings


reports = []
for label, housing_y, tip_y in (("en", 4.0, 0.0), ("boot", -21.0, -17.0)):
    for stroke in (0.6, 0.8, 1.0):
        settings = {"housing_y": housing_y, "tip_y": tip_y, "stroke": stroke}
        rest = make_button(settings, label)
        for travel in (0, stroke/2, stroke):
            item = make_button(settings | {"travel": travel}, label)
            assert all(s.is_valid and len(s.solids()) == 1 for s in item["assembly"].values())
            hits = intersections(item["assembly"])
            hardware_hits = intersections(item["assembly"], item["hardware"])
            assert not hits, hits
            assert not hardware_hits, hardware_hits
            expected_bottom = 16+stroke-0.2-travel
            assert abs(item["hardware"][f"{label}_nylon_adjuster"].bounding_box().min.Z-expected_bottom) < 1e-6
            assert item["measurements"]["magnet_face_gap_at_stop_mm"] > 2.5
            reports.append({"button":label, "stroke_mm":stroke, "travel_mm":travel,
                            "printed_overlaps":hits, "hardware_overlaps":hardware_hits,
                            "tip_bottom_z_mm":expected_bottom})
        # Beyond either stop, solid interference must appear. These are geometry
        # checks of the stops; they do not prove a force or cycle-life rating.
        static = {k:s for k,s in rest["assembly"].items() if k not in rest["moving_names"]}
        moving = {k:rest["assembly"][k] for k in rest["moving_names"]}
        for displacement in (+0.05, -stroke-0.05):
            illegal = {k:Pos(0,0,displacement)*s for k,s in moving.items()}
            hits = intersections(illegal, static)
            assert hits, (label, stroke, displacement, "stop did not engage")
        # Moving magnet keeper cannot escape through the intact rear cover.
        plug = rest["assembly"][f"{label}_moving_magnet_keeper"]
        escape = Pos(-0.45,0,0)*plug
        assert volume(escape.intersect(rest["assembly"][f"{label}_rear_keeper"])) > 0.01
        # Service path: remove rear keeper, then lift the bare slider vertically
        # at its final XY. Nylon adjuster is fitted after initial installation.
        for lift in (0.0,0.25,0.5,1.0,2.0,5.0,10.0,20.0,35.0):
            lifted = Pos(0,0,lift)*rest["assembly"][f"{label}_slider"]
            assert volume(lifted.intersect(rest["assembly"][f"{label}_frame"])) < 1e-6, (label,stroke,lift)

en = make_button({}, "en")
boot = make_button({"housing_y":-21.0, "tip_y":-17.0}, "boot")
assert not intersections(en["assembly"], boot["assembly"])
# Outer cable approach remains 11 mm wide below the lowest moving arm plane.
corridor = box(32, 11, 18.39, -42.5, -8.5, 0)
assert not intersections({"usb_approach":corridor}, en["assembly"] | boot["assembly"])
lower_switch = make_button({"switch_top_z":15.0, "contact_screw_length":12.0}, "lower_switch")
assert not intersections(lower_switch["assembly"])
assert not intersections(lower_switch["assembly"], lower_switch["hardware"])
assert abs(lower_switch["hardware"]["lower_switch_nylon_adjuster"].bounding_box().max.Z-30.6) < 1e-6
assert abs(en["measurements"]["minimum_contact_tip_z_with_jam_nut_at_rest_mm"]-16.4) < 1e-6
assert abs(en["measurements"]["contact_downward_adjustment_margin_mm"]-0.2) < 1e-6
result = {"status":"passed", "states":reports, "state_count":len(reports),
          "stop_overtravel_checked_mm":0.05,
          "top_loading_lifts_checked_mm":[0.0,0.25,0.5,1.0,2.0,5.0,10.0,20.0,35.0],
          "usb_approach_width_y_mm":11.0,
          "usb_approach_upper_z_mm":18.39,
          "lower_switch_12mm_screw": {
              "switch_top_z_mm":15.0, "screw_length_mm":12.0,
              "head_top_z_mm":30.6, "hardware_overlaps":[],
              "downward_adjustment_margin_mm":lower_switch["measurements"]["contact_downward_adjustment_margin_mm"],
          },
          "physical_switch_travel_known":False,
          "magnet_force_tested":False}
Path(__file__).with_name("cartridge-motion-validation.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"status":"passed", "states":len(reports)}))
