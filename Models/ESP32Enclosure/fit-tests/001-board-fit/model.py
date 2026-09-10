"""Small board-fit tray cut from the frozen revision005 production enclosure.

The production print coordinates are used: floor down, terminals toward +Y,
USB/buttons toward -X. This bench-test orientation differs from desk mounting.
"""
import importlib.util
from math import isfinite
from pathlib import Path

from build123d import Align, Box, Pos


def source_module():
    path = Path(__file__).resolve().parent / "enclosure" / "model.py"
    spec = importlib.util.spec_from_file_location("fit_source_enclosure", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def box(w, d, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def build(params):
    unknown = set(params) - {"enclosure", "extra_height_above_clamps"}
    if unknown:
        raise ValueError(f"Unknown fit-test parameters: {sorted(unknown)}")
    source = source_module()
    p = source.DEFAULTS | params.get("enclosure", {})
    extra = params.get("extra_height_above_clamps", 0.0)
    if isinstance(extra, bool) or not isinstance(extra, (int, float)) or not isfinite(extra) or not 0 <= extra <= 2:
        raise ValueError("extra_height_above_clamps must be 0..2 mm")
    full = source.build(p)
    local = full["case_local_assembly"]
    board_bottom = p["floor"] + p["solder_clearance"]
    board_top = board_bottom + p["pcb_thickness"]
    clamp_names = [name for name in local if name.startswith("pcb_clamp_")]
    if len(clamp_names) != 4:
        raise ValueError("Expected four production PCB clamps")
    height = max(local[name].bounding_box().max.Z for name in clamp_names) + extra
    bounds = local["body"].bounding_box()
    cutter = box(bounds.size.X + 2, bounds.size.Y + 2, height + 1,
                 (bounds.min.X + bounds.max.X)/2,
                 (bounds.min.Y + bounds.max.Y)/2, -1)
    clipped = local["body"].intersect(cutter)
    if clipped is None or len(clipped.solids()) != 1:
        raise ValueError("Clipped production body must remain one valid solid")
    tray = clipped.solids()[0]
    if not tray.is_valid:
        raise ValueError("Clipped production body is invalid")
    assembly = {"board_fit_tray": tray, **{name: local[name] for name in clamp_names}}
    parts = {"board_fit_tray": tray, **{name: full["parts"][name] for name in clamp_names}}
    volume = sum(float(s.volume) for s in parts.values())
    full_volume = sum(float(s.volume) for s in full["parts"].values())
    body_and_clamps_volume = float(local["body"].volume) + sum(float(local[n].volume) for n in clamp_names)
    nominal = box(p["pcb_width"], p["pcb_length"], p["pcb_thickness"], z=board_bottom)
    return {
        "title": "ESP32 board-fit test / 005",
        "parts": parts,
        "assembly": assembly,
        "reference_pcb": nominal,
        "source_result": full,
        "clip_volume": cutter,
        "measurements": {
            "units": "mm", "source_revision": "005-downward-buttons",
            "coordinate_system": "Case print coordinates: floor Z0, USB -X, terminal end +Y",
            "pcb_assumed_xyz_mm": [p["pcb_width"], p["pcb_length"], p["pcb_thickness"]],
            "tray_xyz_mm": list(tray.bounding_box().size),
            "tray_height_mm": height,
            "board_bottom_z_mm": board_bottom, "board_top_z_mm": board_top,
            "floor_thickness_mm": p["floor"], "underside_clearance_mm": p["solder_clearance"],
            "board_locating_opening_xy_mm": [p["pcb_width"] + .8, p["pcb_length"] + .8],
            "nominal_board_play_per_side_mm": .4,
            "nominal_bare_edge_overlap_mm": p["board_edge_overlap"],
            "minimum_edge_overlap_at_lateral_stop_mm": p["board_edge_overlap"] - .4,
            "board_slot_height_mm": p["pcb_thickness"] + p["board_vertical_play"],
            "nominal_vertical_play_mm": p["board_vertical_play"],
            "retention_y_centers_mm": [-p["clamp_y"], p["clamp_y"]],
            "retention_y_width_mm": 8.0,
            "left_access_sill_z_mm": board_top + p["left_access_start_above_pcb"],
            "test_cad_volume_cm3": volume / 1000,
            "full_15_part_cad_volume_cm3": full_volume / 1000,
            "cad_volume_reduction_vs_full_set_percent": 100 * (1 - volume / full_volume),
            "cad_volume_reduction_vs_body_and_clamps_percent": 100 * (1 - volume / body_and_clamps_volume),
            "physical_fit_tested": False,
        },
        "notes": [
            "Board-fit coupon only; the production revision005 model remains unchanged.",
            "The tray is an exact low-height intersection of the production body. Four PCB clamps are unchanged production parts.",
            f"Print one tray and four clamps, floor-down/flat as exported. Tray height {height:g} mm; keep scale at 100% in millimeters.",
            "Use the intended enclosure filament and XY compensation so the fit result transfers. A PLA bench trial can check layout but does not validate PETG tolerances.",
            "Suggested starting slice: 0.4 mm nozzle, 0.2 mm layers, 3 perimeters, 4 top/bottom layers, 15% infill. These are untested settings, not a supplied slicer profile or time estimate.",
            "No modeled supports; begin with supports off and inspect the short nut-pocket bridges and horizontal cartridge pilot bores in the slicer.",
            "Hardware for retention test: four M3x8 screws and four standard M3 hex nuts (assumed AF5.5, height2.4 mm). No inserts or magnets are needed for this test; PCB clamp retention still uses its original hex nuts.",
            "With power disconnected, load the four PCB-clamp nuts into their -Y side-entry pockets, place the board component-side up, then install the clamps. Tighten only to the printed shoulders; do not force the board flat.",
            "Check that the board sits on all four ledges without rocking, solder touching the floor, or clamping components/conductors at the board edges.",
            f"Nominal PCB {p['pcb_width']:g}x{p['pcb_length']:g}x{p['pcb_thickness']:g} mm, locating opening {p['pcb_width']+.8:g}x{p['pcb_length']+.8:g} mm, slot height {p['pcb_thickness']+p['board_vertical_play']:g} mm.",
            "The USB/button side is the long open -X edge with two external cartridge pads. The terminal/cable end is +Y, identifiable by the four small zip-tie slots in the floor.",
            "Test lower connector clearance with actual plugs. This shortened tray cannot validate the full connector corridor, cable exit, upper components/wires, lid, button alignment/travel or desk mount.",
            "After checking the clamps, hold the assembly over a padded surface and turn it over gently to check retention in the eventual mounted orientation.",
            "Both PCB faces need bare material at the support/clamp strips. Nominal overlap 0.8 mm falls to 0.4 mm at the opposite lateral stop, while the near strip contacts up to 1.2 mm of the board edge.",
            "The 0.2 mm vertical board play also changes actuator clearance after inversion. Calibrate contacts with the retained board resting against its clamps in the mounted orientation; otherwise the provisional geometric switch depression can increase from 0.2 to 0.4 mm. This coupon does not test actuators or actual switch travel.",
            "Record the actual PCB width/length/thickness, maximum underside protrusion, any fouling location and the amount of looseness before revising the enclosure parameters.",
        ],
    }
