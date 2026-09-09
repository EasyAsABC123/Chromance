"""Console-inspired ESP32/perfboard enclosure, separate from generic revision 001.

Assembly coordinates: board centered in XY, +Y is terminal/cable end, -X is
USB/DC access side, +Z points toward the desk. Body floor bottom is Z=0.
Parts returned by build() are individually placed on Z=0 in print orientation.
No filesystem writes or viewer calls occur on import or build.
"""
from math import isfinite, sqrt

from build123d import (
    Align, Axis, Box, Cylinder, Plane, Polygon, Pos, RegularPolygon, Rot,
    SlotOverall, chamfer, extrude, fillet,
)


DEFAULTS = {
    "pcb_width": 52.0, "pcb_length": 70.0, "pcb_thickness": 1.6,
    "solder_clearance": 6.0, "component_clearance": 22.0,
    "side_margin": 8.0, "end_margin": 9.0, "wall": 2.4, "floor": 2.4,
    "lid_thickness": 2.4, "lid_fit_clearance": 0.3, "lid_skirt_depth": 2.0,
    "left_access_length": 60.0, "left_access_start_above_pcb": -1.0,
    "end_cable_width": 24.0, "end_cable_height": 16.0, "clamp_y": 17.0,
    "board_edge_overlap": 0.8, "board_vertical_play": 0.2,
    "m3_clearance": 3.4, "m3_nut_across_flats": 5.8,
    "m3_nut_pocket_height": 2.7, "desk_screw_clearance": 4.5,
    "bracket_plate_thickness": 3.2, "bracket_clearance_above_body": 8.0,
    "corner_radius": 3.0, "edge_bevel": 0.8, "belt_projection": 1.2,
    "belt_bottom": 3.6, "belt_height": 4.8,
    "vent_angle": 25.0, "lid_vent_width": 2.6, "accent_depth": 0.4,
}


def _box(w, d, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _cylinder(r, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _rounded_box(w, d, h, radius, z=0):
    solid = _box(w, d, h, z=z)
    return fillet(solid.edges().filter_by(Axis.Z), radius)


def _nut_slot(x, y, z, af, height, entry_direction, entry_length=5.0):
    """Hexagonal M3 pocket with a radial side-loading passage.

    Hexagon flats are parallel to Y, so insertion along Y uses width AF.
    X-facing bracket slots use the rotated equivalent.
    """
    x_entry = entry_direction in ("+x", "-x")
    hexagon = RegularPolygon(af / sqrt(3), 6, rotation=0 if x_entry else 30)
    cut = Pos(x, y, z) * extrude(hexagon, amount=height)
    if x_entry:
        s = 1 if entry_direction == "+x" else -1
        cut += _box(entry_length, af, height, x + s * entry_length / 2, y, z)
    else:
        s = 1 if entry_direction == "+y" else -1
        cut += _box(af, entry_length, height, x, y + s * entry_length / 2, z)
    return cut


def _on_bed(shape):
    return Pos(0, 0, -shape.bounding_box().min.Z) * shape


def build_console(params: dict) -> dict:
    unknown = set(params) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"Unknown parameters: {sorted(unknown)}")
    p = DEFAULTS | params
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v)
           for v in p.values()):
        raise ValueError("Every parameter must be a finite number in millimeters")
    if any(v <= 0 for k, v in p.items() if k != "left_access_start_above_pcb"):
        raise ValueError("Dimensions must be positive")
    if p["wall"] < 2 or p["floor"] < 2 or p["lid_thickness"] < 2:
        raise ValueError("This screw-fastened prototype requires wall/floor/lid >= 2 mm")
    if p["pcb_width"] < 40 or p["pcb_length"] < 55:
        raise ValueError("Board is too small for this mounting layout")
    if p["side_margin"] < 8 or p["end_margin"] < 9:
        raise ValueError("Side/end margins must accommodate retention and lid hardware")
    if not 0.15 <= p["lid_fit_clearance"] <= 0.6:
        raise ValueError("Lid fit clearance must be 0.15..0.6 mm per side")
    if not 0.4 <= p["board_edge_overlap"] <= 1.2:
        raise ValueError("PCB retention overlap must be 0.4..1.2 mm")
    if not 3.2 <= p["m3_clearance"] <= 3.8:
        raise ValueError("M3 clearance must be 3.2..3.8 mm")
    if not 5.6 <= p["m3_nut_across_flats"] <= 6.0:
        raise ValueError("M3 nut pocket AF must be 5.6..6.0 mm")
    if not 2.5 <= p["m3_nut_pocket_height"] <= 3.0:
        raise ValueError("M3 nut pocket height must be 2.5..3.0 mm")
    if not 5.8 <= p["solder_clearance"] <= 10:
        raise ValueError("Solder clearance must be 5.8..10 mm for the retention nuts")
    if p["component_clearance"] < 22:
        raise ValueError("Component height is too small for this bracket and access layout")
    if p["bracket_clearance_above_body"] < p["lid_thickness"] + 4.0:
        raise ValueError("Bracket must clear lid and external screw heads")
    if p["lid_skirt_depth"] > 2.5:
        raise ValueError("Lid skirt would obstruct lid nut insertion slots")
    if not 1.5 <= p["corner_radius"] <= 3.0:
        raise ValueError("Corner radius must stay 1.5..3 mm to protect the square cavity")
    if not 0.4 <= p["edge_bevel"] <= 0.8 or p["edge_bevel"] >= p["corner_radius"]:
        raise ValueError("Exterior bevel must stay 0.4..0.8 mm and below corner radius")
    if not 0.6 <= p["belt_projection"] <= 1.5:
        raise ValueError("Belt projection must stay 0.6..1.5 mm")
    if p["belt_height"] <= 2 * p["belt_projection"] or p["belt_bottom"] < p["floor"]:
        raise ValueError("Belt needs a straight center and must start above the floor")
    if not 15 <= p["vent_angle"] <= 30 or not 2.2 <= p["lid_vent_width"] <= 3:
        raise ValueError("Vent angle/width must stay 15..30 degrees / 2.2..3 mm")
    if not 0.2 <= p["accent_depth"] <= 0.4 or p["lid_thickness"] - p["accent_depth"] < 2:
        raise ValueError("Accent recess must retain at least 2 mm of lid")
    # The untouched square inner corner is the limiting wall at an outer fillet.
    if (2 ** 0.5) * p["wall"] - (2 ** 0.5 - 1) * p["corner_radius"] < 2:
        raise ValueError("Rounded corner must retain at least 2 mm of shell")

    bw, bl = p["pcb_width"], p["pcb_length"]
    wall, floor = p["wall"], p["floor"]
    cw, cl = bw + 2 * p["side_margin"], bl + 2 * p["end_margin"]
    ow, ol = cw + 2 * wall, cl + 2 * wall
    board_bottom = floor + p["solder_clearance"]
    board_top = board_bottom + p["pcb_thickness"]
    h = board_top + p["component_clearance"]
    access_z = board_top + p["left_access_start_above_pcb"]
    hole_r = p["m3_clearance"] / 2
    nut_af, nut_h = p["m3_nut_across_flats"], p["m3_nut_pocket_height"]
    lug_y = ol / 2 - 11
    lug_x = ow / 2 + 6
    post_x, post_y = cw / 2 - 4, cl / 2 - 4
    lid_points = [(sx * post_x, sy * post_y) for sx in (-1, 1) for sy in (-1, 1)]
    mount_points = [(sx * lug_x, sy * lug_y) for sx in (-1, 1) for sy in (-1, 1)]
    clamp_x = bw / 2 + 4.5
    clamp_y = p["clamp_y"]
    if clamp_y + 5 >= bl / 2 or clamp_y < 6:
        raise ValueError("Retention clamps must stay inside the board ends and separate")
    if p["left_access_length"] > cl - 16:
        raise ValueError("Left access would cut the enclosure corners")
    if p["end_cable_width"] > cw - 22 or p["end_cable_height"] >= h - floor - 3:
        raise ValueError("Cable opening must leave end-wall corners and floor intact")
    if not floor + 3 <= access_z < h - 3:
        raise ValueError("Left connector opening must leave a wall below it")
    if p["belt_bottom"] + p["belt_height"] > min(access_z, h - 17.3) - 0.4:
        raise ValueError("Belt must remain below connector access and mounting gussets")

    radius, bevel = p["corner_radius"], p["edge_bevel"]
    outer = _rounded_box(ow, ol, h, radius)
    outer = chamfer(outer.edges().group_by(Axis.Z)[0], bevel)
    b = p["belt_projection"]
    belt = _rounded_box(ow + 2*b, ol + 2*b, p["belt_height"], radius + b,
                        z=p["belt_bottom"])
    belt_edges = belt.edges().group_by(Axis.Z)
    belt = chamfer(list(belt_edges[0]) + list(belt_edges[-1]), b)
    body = (outer + belt) - _box(cw, cl, h, z=floor)

    # Lid screw posts sit beyond the PCB ends. Nuts insert from the open interior.
    for x, y in lid_points:
        body += _cylinder(4.4, h - floor, x, y, floor)
        body -= _cylinder(hole_r, 10.5, x, y, h - 10)
        body -= _nut_slot(x, y, h - 5.5, nut_af, nut_h,
                          "-y" if y > 0 else "+y")

    # Removable PCB clamps overlap only a narrow, provisional board-edge strip.
    clamp_z = board_top + p["board_vertical_play"]
    clamps = {}
    clamp_outer = bw / 2 + 8
    clamp_inner = bw / 2 - p["board_edge_overlap"]
    clamp_width = clamp_outer - clamp_inner
    clamp_center = (clamp_inner + clamp_outer) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * clamp_x, sy * clamp_y
            body += _box(clamp_width, 8, board_bottom - floor,
                         sx * clamp_center, y, floor)
            # A shoulder gives repeatable vertical clearance without crushing PCB.
            shoulder_inner = bw / 2 + 0.4
            body += _box(clamp_outer - shoulder_inner, 8, clamp_z - floor,
                         sx * (clamp_outer + shoulder_inner) / 2, y, floor)
            body -= _cylinder(hole_r, clamp_z - floor + 0.4, x, y, floor)
            body -= _nut_slot(x, y, board_bottom - 3.5, nut_af, nut_h, "-y", 4.2)
            clamp = _box(clamp_width, 8, 2, sx * clamp_center, y, clamp_z)
            clamp -= _cylinder(hole_r, 3, x, y, clamp_z - 0.5)
            name = f"pcb_clamp_{'left' if sx < 0 else 'right'}_{'front' if sy < 0 else 'rear'}"
            clamps[name] = clamp

    # Low end stops constrain longitudinal motion without reaching components.
    for sy in (-1, 1):
        body += _box(12, 2, board_bottom + p["pcb_thickness"] / 2 - floor,
                     0, sy * (bl / 2 + 1.4), floor)

    # Four bolted mounting ears. Two 45-degree ribs support each raised flange.
    for x, y in mount_points:
        sx = 1 if x > 0 else -1
        inner, outer = sx * (ow / 2 - 0.3), sx * (ow / 2 + 12)
        body += _box(12.3, 14, 5, sx * (ow / 2 + 5.85), y, h - 5)
        for dy in (-5.8, 5.8):
            profile = Plane.XZ * Polygon(
                (inner, h - 17.3), (outer, h - 5), (inner, h - 5), align=None
            )
            body += Pos(0, y + dy, 0) * extrude(profile, amount=1.2, both=True)
        body -= _cylinder(hole_r, 6, x, y, h - 5.5)

    # Open-edge cutouts admit prewired electronics. They intentionally stay generic.
    left_cut = _box(wall + 1.0, p["left_access_length"], h + 2,
                    -ow / 2 + wall / 2, 0, access_z)
    end_cut = _box(p["end_cable_width"], wall + 1.0, p["end_cable_height"] + 2,
                   0, ol / 2 - wall / 2, h - p["end_cable_height"])
    body -= left_cut
    body -= end_cut

    # Seven short diagonal slots on the visible right wall. Each rounded roof
    # is a small local bridge; preserve the gussets at the ends of this wall.
    for y in (-17.4, -11.6, -5.8, 0, 5.8, 11.6, 17.4):
        slot = Plane.YZ * SlotOverall(9.0, 2.4, rotation=90-p["vent_angle"])
        body -= Pos(cw/2 - 0.5, y, board_top + 10.5) * extrude(slot, amount=wall + 1)

    # Tie anchors flank cable exit. Holes carry a small zip tie through the floor.
    for sx in (-1, 1):
        for dy in (-2.5, 2.5):
            body -= _box(1.8, 3.2, floor + 1,
                         sx * (p["end_cable_width"] / 2 + 3), bl / 2 + dy, -0.5)

    # Lid printed with exterior face on bed; downward locating skirt prints upward.
    lid_t = p["lid_thickness"]
    lid = _rounded_box(ow, ol, lid_t, radius, z=h)
    lid = chamfer(lid.edges().group_by(Axis.Z)[-1], bevel)
    skirt_w, skirt_l = cw - 2 * p["lid_fit_clearance"], cl - 2 * p["lid_fit_clearance"]
    skirt_depth = p["lid_skirt_depth"]
    skirt = _box(skirt_w, skirt_l, skirt_depth, z=h - skirt_depth)
    skirt -= _box(skirt_w - 2.4, skirt_l - 2.4, skirt_depth + 1, z=h - skirt_depth - 0.5)
    for x, y in lid_points:
        skirt -= _cylinder(4.8, skirt_depth + 1, x, y, h - skirt_depth - 0.5)
    # Keep locating lips clear of both access openings and attached wires.
    skirt -= _box(wall + 4, p["left_access_length"] + 0.6, skirt_depth + 1,
                   -cw / 2, 0, h - skirt_depth - 0.5)
    skirt -= _box(p["end_cable_width"] + 0.6, wall + 4, skirt_depth + 1,
                   0, cl / 2, h - skirt_depth - 0.5)
    lid += skirt
    for x, y in lid_points:
        lid -= _cylinder(hole_r, lid_t + 1, x, y, h - 0.5)
    # Parallel diagonal vents and twin narrow recessed rails recall console
    # panel detailing while leaving the exterior face flat for printing.
    for y in range(-24, 25, 6):
        slot = SlotOverall(29, p["lid_vent_width"], rotation=-p["vent_angle"])
        lid -= Pos(4, y, h - 0.5) * extrude(slot, amount=lid_t + 1)
    for x in (-23, -20):
        groove = SlotOverall(45, 0.8, rotation=90)
        lid -= Pos(x, 0, h + lid_t - p["accent_depth"]) * extrude(groove, amount=p["accent_depth"] + 0.5)

    # H-shaped under-desk bracket. Install it first; body screws install from below.
    bracket_z = h + p["bracket_clearance_above_body"]
    plate_t = p["bracket_plate_thickness"]
    bracket = _box(10, 2 * lug_y + 14, plate_t, z=bracket_z)
    for y in (-lug_y, lug_y):
        bracket += _box(ow + 44, 14, plate_t, 0, y, bracket_z)
    for x, y in mount_points:
        bracket += _box(12, 14, bracket_z - h, x, y, h)
        bracket -= _cylinder(hole_r, bracket_z - h + plate_t + 1, x, y, h - 0.5)
        bracket -= _nut_slot(x, y, h + 2.0, nut_af, nut_h,
                            "+x" if x > 0 else "-x", 6.2)
    desk_holes = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (ow / 2 + 17), sy * lug_y
            desk_holes.append([x, y])
            bracket -= _cylinder(p["desk_screw_clearance"] / 2,
                                 plate_t + 1, x, y, bracket_z - 0.5)

    assembly = {"body": body, "lid": lid, "desk_bracket": bracket, **clamps}
    parts = {name: _on_bed(Rot(X=180) * part if name in ("lid", "desk_bracket") else part)
             for name, part in assembly.items()}
    for name, part in parts.items():
        if not part.is_valid or len(part.solids()) != 1 or part.volume <= 0:
            raise ValueError(f"Generated part {name} is not one valid connected solid")
    return {
        "title": "ESP32 / console-inspired enclosure · revision 002",
        "parts": parts,
        "assembly": assembly,
        "measurements": {
            "units": "mm", "pcb_assumed": [bw, bl, p["pcb_thickness"]],
            "pcb_bottom_z": board_bottom, "pcb_top_z": board_top,
            "cavity_xy": [cw, cl], "body_outer_without_ears": [ow + 2*b, ol + 2*b, h],
            "main_shell_xy": [ow, ol],
            "body_outer_with_ears": [ow + 24, ol + 2*b, h],
            "overall_assembled": [ow + 44, ol + 2*b, bracket_z + plate_t],
            "style": {"corner_fillet_radius": radius, "external_edge_chamfer": bevel,
                      "belt_projection": b, "belt_z_range": [p["belt_bottom"], p["belt_bottom"]+p["belt_height"]],
                      "corner_wall_min_above_base_bevel": sqrt(2)*wall-(sqrt(2)-1)*radius,
                      "lid_vent_angle_degrees": p["vent_angle"], "lid_vent_count": 9,
                      "side_vent_count": 7, "accent_recess_depth": p["accent_depth"]},
            "lid_top_z": h + lid_t,
            "desk_contact_z": bracket_z + plate_t,
            "left_access_yz": [p["left_access_length"], h - access_z],
            "end_cable_access_xz": [p["end_cable_width"], p["end_cable_height"]],
            "desk_screw_centers_xy": desk_holes,
            "body_mount_centers_xy": [list(pt) for pt in mount_points],
            "lid_screw_centers_xy": [list(pt) for pt in lid_points],
            "m3_nut_pocket_af": nut_af,
            "m3_nut_pocket_height": nut_h,
            "pcb_edge_overlap": p["board_edge_overlap"],
            "pcb_vertical_play": p["board_vertical_play"],
        },
        "notes": [
            "Revision 002 is a separate console-inspired styling variant; generic revision 001 is preserved unchanged.",
            f"Styling: R{radius:g} mm outer vertical corners; {bevel:g} mm bottom-body/top-lid 45-degree chamfers; {b:g} mm projecting lower belt with 45-degree transitions.",
            "The cavity, PCB retention, lid skirt, all screw centers, bracket and assembly heights retain the generic interface. Belt adds 2.4 mm overall length at default settings.",
            f"Main walls remain {wall:g} mm; outer corner rounding leaves {sqrt(2)*wall-(sqrt(2)-1)*radius:.2f} mm minimum diagonal shell above the base chamfer. Bevels locally narrow the bed-contact perimeter.",
            "Nine diagonal lid slots and seven side slots are functional openings; thermal performance has not been measured.",
            f"Two 0.8 mm-wide decorative lid channels are recessed {p['accent_depth']:g} mm and retain at least 2 mm lid thickness. Their short roof spans print above the exterior face on the bed.",
            "Side-slot rounded roofs add approximately 3 mm local bridge spans. Review these and the existing nut-pocket bridges in the slicer; no additional modeled supports are included.",
            "Initial material candidate: unfilled PETG for a room-temperature electronics housing and bracket; confirm actual board temperature and printer capabilities before choosing a print profile. No load rating is assigned.",
            "PETG material reference: https://help.prusa3d.com/article/petg_2059 . Orientation/support design reference: https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135 .",
            f"Generic reference-image prototype; {bw:g}x{bl:g} mm PCB outline is provisional, not a calibrated measurement.",
            "User estimates populated electronics at 52x70x15 mm; whether 15 mm is overall stack or above-board height is unconfirmed.",
            f"Current clearances: {p['solder_clearance']:g} mm below PCB and {p['component_clearance']:g} mm above it; default 22 mm upper allowance uses estimated 15 mm plus 7 mm for wiring.",
            f"PCB thickness {p['pcb_thickness']:g} mm and underside solder clearance remain conservative assumptions.",
            "Assumption: enclosure contains only low-voltage board/wiring; existing external power supply is excluded.",
            "Verify all board dimensions, solder protrusions, connector positions and edge-clamp clearances before printing.",
            f"No board-hole pattern is assumed. Four removable clamps overlap {p['board_edge_overlap']:g} mm of PCB edge at Y=+/-{clamp_y:g} mm.",
            "Side shoulders and low end stops allow 0.4 mm nominal board movement per direction; verify bare-edge clearance.",
            f"PCB clamp vertical play is {p['board_vertical_play']:g} mm; lid locating clearance is {p['lid_fit_clearance']:g} mm per side.",
            "Open-edge left-side access and +Y cable notch admit prewired electronics; they are generous placeholders.",
            "Default hardware: 8 M3x10 mm screws (4 lid, 4 bracket), 4 M3x8 mm screws (PCB clamps), 12 standard M3 hex nuts.",
            f"M3 nut nominal AF 5.5 mm/height 2.4 mm; current printable pockets AF {nut_af:g} mm/height {nut_h:g} mm.",
            f"Desk holes are {p['desk_screw_clearance']:g} mm clearance. Choose desk screw type/length only after desk material and thickness are known.",
            "Body prints floor-down. Lid exterior face and bracket desk-contact face print on the bed. Clamps print flat.",
            "No modeled supports. Short bridges over nut pockets and mounting flanges need slicer review; support must not fill pockets.",
            "Physical fit, strength, thermal behavior and RF performance remain unvalidated.",
        ],
    }


BUTTON_DEFAULTS = {
    "reset_button_y": 0.0, "boot_button_y": -17.0,
    "button_inset_from_left_pcb_edge": 3.0,
    "reset_switch_height_above_pcb": 6.0, "boot_switch_height_above_pcb": 6.0,
    "reset_contact_screw_length": 10.0, "boot_contact_screw_length": 10.0,
    "button_housing_y_offset": 4.0, "button_stroke": 0.8,
    "button_guide_clearance": 0.3, "modeled_switch_depression": 0.2,
    "button_arm_height_above_pcb": 9.2,
    "button_insert_pilot_diameter": 4.0, "button_insert_bore_depth": 4.4,
}


def _local_module(filename):
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def build(params: dict) -> dict:
    """Approved console shell plus replaceable external magnetic button paddles.

    The button_module.py and mounting.py files are required source dependencies.
    Use build-revision.py to freeze all three before exporting a new revision.
    Hardware proxies are returned separately and never included in print meshes.
    """
    unknown = set(params) - set(DEFAULTS) - set(BUTTON_DEFAULTS)
    if unknown:
        raise ValueError(f"Unknown parameters: {sorted(unknown)}")
    p = DEFAULTS | BUTTON_DEFAULTS | params
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v)
           for v in p.values()):
        raise ValueError("Every model parameter must be a finite number")
    result = build_console({k: p[k] for k in DEFAULTS})
    button_module = _local_module("button_module.py")
    mounting = _local_module("mounting.py")
    ow, ol = result["measurements"]["main_shell_xy"]
    board_top = result["measurements"]["pcb_top_z"]
    face_x = -ow/2 - 3.6
    tip_x = -p["pcb_width"]/2 + p["button_inset_from_left_pcb_edge"]
    if not 2 <= p["button_inset_from_left_pcb_edge"] <= 5:
        raise ValueError("Button inset must stay 2..5 mm from the PCB left edge")
    if not 0 <= p["button_housing_y_offset"] <= 4:
        raise ValueError("Cartridge Y offset must stay 0..4 mm")
    centers = [p["reset_button_y"]+p["button_housing_y_offset"],
               p["boot_button_y"]-p["button_housing_y_offset"]]
    if centers[0]-centers[1] < 24:
        raise ValueError("Button cartridges must leave at least 10 mm between housings")
    for y in centers:
        if abs(y)+7 > ol/2-18.2:
            raise ValueError("Button cartridge would approach a mounting gusset")
    body, mount_centers = mounting.add_mounts(
        result["assembly"]["body"], face_x, centers,
        pilot_diameter=p["button_insert_pilot_diameter"],
        bore_depth=p["button_insert_bore_depth"])
    result["assembly"]["body"] = body
    result["parts"]["body"] = _on_bed(body)
    result["hardware"] = {}
    result["buttons"] = {}
    for name, center, tip_y, switch_h, screw_length in (
        ("reset", centers[0], p["reset_button_y"], p["reset_switch_height_above_pcb"], p["reset_contact_screw_length"]),
        ("boot", centers[1], p["boot_button_y"], p["boot_switch_height_above_pcb"], p["boot_contact_screw_length"]),
    ):
        bp = {"mounting_face_x": face_x, "housing_y": center,
              "tip_x": tip_x, "tip_y": tip_y, "switch_top_z": board_top+switch_h,
              "arm_bottom_z": board_top+p["button_arm_height_above_pcb"],
              "stroke": p["button_stroke"], "guide_clearance": p["button_guide_clearance"],
              "switch_depression": p["modeled_switch_depression"],
              "contact_screw_length": screw_length,
              "mount_hole_y_spacing": 6.0, "mount_hole_z": 5.0}
        button = button_module.make_button(bp, name)
        result["parts"].update(button["parts"])
        result["assembly"].update(button["assembly"])
        result["hardware"].update(button["hardware"])
        result["buttons"][name] = {"params": bp, "moving_names": button["moving_names"],
                                   "measurements": button["measurements"]}
    for name, part in result["parts"].items():
        if not part.is_valid or len(part.solids()) != 1 or part.volume <= 0:
            raise ValueError(f"Generated part {name} is not one valid connected solid")
    for hardware_name, hardware in result["hardware"].items():
        if "_nylon" not in hardware_name:
            continue
        for host_name, host in result["assembly"].items():
            if host_name.startswith(("reset_", "boot_")):
                continue
            common = hardware.intersect(host)
            overlap = 0.0 if common is None else (
                float(common.volume) if hasattr(common, "volume") else
                sum(float(s.volume) for s in common))
            if overlap > 0.001:
                raise ValueError(f"{hardware_name} collides with {host_name}; adjust switch height/screw length")
    boxes = [s.bounding_box() for s in result["assembly"].values()]
    bounds_min = [min(tuple(b.min)[i] for b in boxes) for i in range(3)]
    bounds_max = [max(tuple(b.max)[i] for b in boxes) for i in range(3)]
    result["measurements"]["overall_assembled"] = [hi-lo for lo, hi in zip(bounds_min, bounds_max)]
    result["measurements"]["body_outer_without_ears"] = [ow/2+p["belt_projection"]-face_x,
        ol+2*p["belt_projection"], result["measurements"]["body_outer_without_ears"][2]]
    result["measurements"]["button_mount_centers_xyz"] = mount_centers
    result["measurements"]["buttons"] = {name: b["measurements"] for name, b in result["buttons"].items()}
    result["title"] = "ESP32 / console enclosure with external buttons · revision 003"
    result["notes"] = [n for n in result["notes"] if not n.startswith("Revision 002")]
    result["notes"].extend([
        "Revision 003 adds removable EN/RESET and BOOT cartridges to the approved revision 002 console styling. Both prior revisions are preserved.",
        "The button locations and height are provisional photo/layout estimates, not measured fit. Adjust XY parameters and nylon tip height before fitting to the real electronics.",
        "Button housings are offset to reserve an 11 mm USB corridor at default dimensions; actual USB plug, DC plug, wiring and switch envelopes remain unverified.",
        "Two captive 4x2 mm axially magnetized discs per button face like poles together. A keyed guide and rigid travel stops constrain the paddle; return force and friction require physical testing.",
        f"Additional hardware: four M3x18 socket screws (head diameter<=5.5 mm), four short M3 heat-set inserts (nominal length4 / OD4.6 mm), four 4x2 mm magnets, one nylon M3x{p['reset_contact_screw_length']:g} EN contact screw, one nylon M3x{p['boot_contact_screw_length']:g} BOOT contact screw and four nylon M3 nuts. No mounting washers are assumed.",
        f"Provisional insert pilots: {p['button_insert_pilot_diameter']:g} mm diameter x {p['button_insert_bore_depth']:g} mm blind depth. Confirm with the insert drawing and a material-specific coupon; OD4.6 mm is not the pilot diameter.",
        "The model's hardware proxies are excluded from printable parts and print-layout.3mf. They are simplified illustrations without threads or magnetic simulation.",
        f"Paddle stroke {p['button_stroke']:g} mm; idle contact gap {p['button_stroke']-p['modeled_switch_depression']:g} mm; modeled switch depression {p['modeled_switch_depression']:g} mm. Actual switch travel is unknown; calibrate the stop and tip so the switch is released at rest and never carries excess finger load.",
        "The nylon contact tip is calibrated while the enclosure is accessible, then locked with its jam nut. The external pad is pressed toward the enclosure floor while mounted under the desk.",
        "Install PCB clamps before attaching the cartridges. The BOOT arm overlaps the left-front clamp's screwdriver approach, so remove that cartridge for later clamp service.",
        "Contact screw length is configurable. Default10 mm screws have limited downward adjustment; use an appropriate longer nylon screw for a lower measured switch and recheck its head against the lid. Do not extend a screw past full captive-nut engagement.",
        "Cartridge frames and rear keepers print on their outer sides; sliders need local removable support under their stepped arms. Keep support scars away from guide and magnet-fit faces. The small moving-magnet keepers print flat.",
        "Magnets are placed outside the USB/button side, opposite the pictured antenna. Espressif recommends at least15 mm antenna clearance and final-product radio testing: https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html . Existing antenna/perfboard performance is not established by this model.",
        "Magnet guidance: https://www.kjmagnetics.com/blog/repelling-magnets . Short insert reference: https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck .",
        "Preserve button_module.py and mounting.py alongside model.py. Use build-revision.py for builds that snapshot all required source files.",
    ])
    return result
