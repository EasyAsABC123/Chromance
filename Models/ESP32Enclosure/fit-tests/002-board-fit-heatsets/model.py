"""Quick PCB edge-retention test; derived from 005, no actuator assembly.

Coordinates are the case print frame: board centered in XY, terminals +Y,
USB/buttons -X, tray floor Z0. The 52 mm ESP span is an annotation, not a
component solid or a verified placement. Full published enclosures are intact.
"""
import importlib.util
from math import isfinite, pi
from pathlib import Path

from build123d import Align, Box, Cylinder, Edge, Pos


def local_module(filename):
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def box(w, d, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cylinder(r, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def build(params):
    unknown = set(params) - {"enclosure", "extra_height_above_clamps", "button_centers_from_edges"}
    if unknown:
        raise ValueError(f"Unknown fit-test parameters: {sorted(unknown)}")
    base = local_module("base_model.py")
    p = base.DEFAULTS | params.get("enclosure", {})
    extra = params.get("extra_height_above_clamps", 0.0)
    if isinstance(extra, bool) or not isinstance(extra, (int, float)) or not isfinite(extra) or not 0 <= extra <= 2:
        raise ValueError("extra_height_above_clamps must be0..2 mm")
    full = base.build_console(p)
    mounting = local_module("mounting.py")
    ow, ol = full["measurements"]["main_shell_xy"]
    body, unused_lateral_pilots = mounting.add_mounts(full["assembly"]["body"], -ow/2-3.6, [4.0, -21.0])
    full["assembly"]["body"] = body
    full["parts"]["body"] = body
    clamp_names = [n for n in full["assembly"] if n.startswith("pcb_clamp_")]
    board_bottom = p["floor"] + p["solder_clearance"]
    board_top = board_bottom + p["pcb_thickness"]
    clamp_z = board_top + p["board_vertical_play"]
    height = clamp_z + p["clamp_thickness"] + extra
    bounds = body.bounding_box()
    cutter = box(bounds.size.X+2, bounds.size.Y+2, height+1,
                 (bounds.min.X+bounds.max.X)/2, (bounds.min.Y+bounds.max.Y)/2, -1)
    clipped = body.intersect(cutter)
    if clipped is None or len(clipped.solids()) != 1:
        raise ValueError("Fit tray must be one connected solid")
    tray = clipped.solids()[0]
    assembly = {"board_fit_tray": tray, **{n: full["assembly"][n] for n in clamp_names}}
    parts = {"board_fit_tray": tray, **{n: full["parts"][n] for n in clamp_names}}
    for name, shape in parts.items():
        if not shape.is_valid or len(shape.solids()) != 1 or shape.volume <= 0:
            raise ValueError(f"{name} is not one valid connected solid")
        if abs(shape.bounding_box().min.Z) > 1e-5:
            raise ValueError(f"{name} is not on the print bed")
    centers = full["measurements"]["clamp_screw_centers_xy"]
    insert_bottom = clamp_z-p["clamp_insert_length"]
    bore_bottom = clamp_z-p["clamp_insert_bore_depth"]
    bearing_z = clamp_z+p["clamp_thickness"]
    screw_tip = bearing_z-p["clamp_screw_length"]
    hardware, expected = {}, []
    for name, (x, y) in zip(clamp_names, centers):
        insert_name, screw_name = name+"_insert", name+"_screw"
        hardware[insert_name] = cylinder(p["clamp_insert_outer_diameter"]/2, p["clamp_insert_length"], x,y,insert_bottom)
        hardware[insert_name] -= cylinder(1.5,p["clamp_insert_length"]+.2,x,y,insert_bottom-.1)
        hardware[screw_name] = cylinder(1.5,p["clamp_screw_length"],x,y,screw_tip) + cylinder(2.75,3,x,y,bearing_z)
        expected.append({"hardware":insert_name, "printed_part":"board_fit_tray",
                         "reason":"Intentional heat-set displacement of undersized pilot only",
                         "expected_volume_mm3":pi/4*(p["clamp_insert_outer_diameter"]**2-p["clamp_insert_pilot_diameter"]**2)*p["clamp_insert_length"]})
    button_dims = params.get("button_centers_from_edges", {
        "upper_reset": {"from_left":3.3,"from_bottom":30.0},
        "lower_boot": {"from_left":3.3,"from_bottom":16.0}})
    button_xy = {}
    for name, dims in button_dims.items():
        if set(dims) != {"from_left","from_bottom"} or any(
                isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) for v in dims.values()):
            raise ValueError("Button reference dimensions need finite from_left/from_bottom values")
        if not 0 < dims["from_left"] < p["pcb_width"] or not 0 < dims["from_bottom"] < p["pcb_length"]:
            raise ValueError("Button reference lies outside the PCB")
        button_xy[name] = [-p["pcb_width"]/2+dims["from_left"],-p["pcb_length"]/2+dims["from_bottom"]]
    volume = sum(float(s.volume) for s in parts.values())
    return {
        "title":"ESP32 board fit / heat-set clamps",
        "parts":parts, "assembly":assembly,
        "hardware":hardware, "expected_hardware_intersections":expected,
        "reference_pcb":box(p["pcb_width"],p["pcb_length"],p["pcb_thickness"],z=board_bottom),
        "reference_esp_span":Edge.make_line((-p["component_reference_width"]/2,0,board_top),
                                             (p["component_reference_width"]/2,0,board_top)),
        "source_result":full, "clip_volume":cutter,
        "modified_retention_regions":full["retention_regions"],
        "measurements":{
            "units":"mm", "source_revision":"005-downward-buttons; retention source replaced for this fit test",
            "coordinate_system":"Case print frame: floorZ0, USB-X, terminals+Y; this test has no desk transform",
            "pcb_assumed_xyz_mm":[p["pcb_width"],p["pcb_length"],p["pcb_thickness"]],
            "pcb_dimension_status":"Defaults 49x70x1 mm are user supplied; parameter overrides are unmeasured variants. This fit test has not been physically tested.",
            "cavity_xy_mm":full["measurements"]["cavity_xy"],
            "main_shell_xy_mm":[ow,ol],"tray_xyz_mm":list(tray.bounding_box().size),
            "tray_height_mm":height,"board_bottom_z_mm":board_bottom,"board_top_z_mm":board_top,
            "floor_thickness_mm":p["floor"],"underside_clearance_mm":p["solder_clearance"],
            "board_locating_opening_xy_mm":[p["pcb_width"]+2*p["board_lateral_play"],p["pcb_length"]+2*p["board_lateral_play"]],
            "nominal_board_play_per_side_mm":p["board_lateral_play"],
            "nominal_bare_edge_overlap_mm":p["board_edge_overlap"],
            "minimum_edge_overlap_at_lateral_stop_mm":p["board_edge_overlap"]-p["board_lateral_play"],
            "board_slot_height_mm":p["pcb_thickness"]+p["board_vertical_play"],
            "nominal_vertical_play_mm":p["board_vertical_play"],
            "retention_y_centers_mm":[-p["clamp_y"],p["clamp_y"]],"retention_y_width_mm":8,
            "clamp_screw_centers_xy_mm":centers,"clamp_underside_z_mm":clamp_z,
            "clamp_thickness_mm":p["clamp_thickness"],"clamp_head_bearing_z_mm":bearing_z,
            "clamp_boss_diameter_mm":p["clamp_boss_diameter"],
            "clamp_insert_outer_diameter_mm":p["clamp_insert_outer_diameter"],
            "clamp_insert_length_mm":p["clamp_insert_length"],
            "clamp_insert_pilot_diameter_mm":p["clamp_insert_pilot_diameter"],
            "clamp_insert_bore_depth_mm":p["clamp_insert_bore_depth"],
            "clamp_insert_bottom_z_mm":insert_bottom,"clamp_insert_bore_bottom_z_mm":bore_bottom,
            "minimum_boss_radial_polymer_mm":(p["clamp_boss_diameter"]-p["clamp_insert_outer_diameter"])/2,
            "polymer_below_blind_pilot_mm":bore_bottom,
            "polymer_above_floor_below_blind_pilot_mm":bore_bottom-p["floor"],
            "clamp_screw_length_mm":p["clamp_screw_length"],"clamp_screw_tip_z_mm":screw_tip,
            "clamp_insert_thread_engagement_mm":clamp_z-max(screw_tip,insert_bottom),
            "clamp_screw_tip_to_bore_bottom_mm":screw_tip-bore_bottom,
            "left_access_sill_z_mm":board_bottom+p["shell_reference_pcb_thickness"]+p["left_access_start_above_pcb"],
            "unused_cartridge_pilot_centers_xyz_mm":unused_lateral_pilots,
            "esp_span_reference":{"width_mm":p["component_reference_width"],"cad_display":"Centered width line at PCB top, an annotation only; no height or component length modeled","alignment_status":"Provisional; sketch suggests right overhang, exact left/right split unmeasured"},
            "button_centers_from_edges_mm":button_dims,"button_reference_centers_xy_mm":button_xy,
            "button_reference_status":"Coordinates recorded only; actuator geometry intentionally absent",
            "test_cad_volume_cm3":volume/1000,"physical_fit_tested":False,
        },
        "notes":[
            "Quick board-fit test only. Published revisions001..005 and the previous fit test remain unchanged.",
            f"Use one tray and four clamps. Actual PCB {p['pcb_width']:g}x{p['pcb_length']:g}x{p['pcb_thickness']:g} mm is centered in the existing {full['measurements']['cavity_xy'][0]:g} mm-wide cavity.",
            f"Four removable edge clamps use M3x{p['clamp_screw_length']:g} socket screws and four M3x{p['clamp_insert_length']:g} heat-set inserts; no screw passes through the PCB.",
            f"Insert OD{p['clamp_insert_outer_diameter']:g} mm and pilot diameter{p['clamp_insert_pilot_diameter']:g} mm remain provisional. Confirm against the purchased insert and filament before installation.",
            f"Blind pilot depth {p['clamp_insert_bore_depth']:g} mm, insert engagement {clamp_z-max(screw_tip,insert_bottom):g} mm and screw-tip margin {screw_tip-bore_bottom:g} mm. With the default dimensions, M3x8 screws bottom and must not be substituted.",
            "Print tray floor-down and clamps flat, with scale100% in millimeters. No modeled supports; review the four empty lateral pilot bridges in the slicer.",
            "Install the four vertical heat-set inserts flush before placing the PCB. The four horizontal cartridge pilot bores are retained reference features and stay empty.",
            "Place the unpowered board on the four ledges, then tighten clamps gently onto the printed shoulders. Do not clamp conductors or components, and do not force a warped board flat.",
            f"Support/clamp strips are8 mm wide at Y+/-{p['clamp_y']:g}; nominal bare-edge overlap{p['board_edge_overlap']:g} mm with lateralplay+/-{p['board_lateral_play']:g} and verticalplay{p['board_vertical_play']:g} mm. Bare edge availability remains unverified.",
            "The52 mm ESP span is a separate width reference, not the PCB substrate. Actual overhang split and component height at each clamp remain unknown; check with the physical assembly.",
            f"Underside solder allowance remains{p['solder_clearance']:g} mm. The sketch's12 mm side dimension has unconfirmed endpoints and is not used as a height.",
            "Measured button XY coordinates are stored without button bodies or actuators. This test does not validate button linkage, upper connector/wire clearance, lid fit or desk mounting.",
            "Physical fit/strength and slicer settings remain untested. Use the intended enclosure filament and printer compensation so the fit trial transfers.",
        ],
    }
