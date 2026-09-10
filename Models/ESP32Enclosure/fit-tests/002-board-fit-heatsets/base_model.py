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
    "pcb_width": 49.0, "pcb_length": 70.0, "pcb_thickness": 1.0,
    "component_reference_width": 52.0, "shell_reference_pcb_thickness": 1.6,
    "clamp_boss_diameter": 9.2, "clamp_screw_offset_from_pcb_edge": 5.1,
    "clamp_insert_outer_diameter": 4.6, "clamp_insert_length": 5.0,
    "clamp_insert_pilot_diameter": 4.0, "clamp_insert_bore_depth": 6.0,
    "clamp_screw_length": 6.0, "clamp_thickness": 2.0,
    "board_lateral_play": 0.4,
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
    cw, cl = p["component_reference_width"] + 2 * p["side_margin"], bl + 2 * p["end_margin"]
    ow, ol = cw + 2 * wall, cl + 2 * wall
    board_bottom = floor + p["solder_clearance"]
    board_top = board_bottom + p["pcb_thickness"]
    shell_reference_top = board_bottom + p["shell_reference_pcb_thickness"]
    h = shell_reference_top + p["component_clearance"]
    access_z = shell_reference_top + p["left_access_start_above_pcb"]
    hole_r = p["m3_clearance"] / 2
    nut_af, nut_h = p["m3_nut_across_flats"], p["m3_nut_pocket_height"]
    lug_y = ol / 2 - 11
    lug_x = ow / 2 + 6
    post_x, post_y = cw / 2 - 4, cl / 2 - 4
    lid_points = [(sx * post_x, sy * post_y) for sx in (-1, 1) for sy in (-1, 1)]
    mount_points = [(sx * lug_x, sy * lug_y) for sx in (-1, 1) for sy in (-1, 1)]
    clamp_x = bw / 2 + p["clamp_screw_offset_from_pcb_edge"]
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

    # Low end stops constrain longitudinal motion without reaching components.
    for sy in (-1, 1):
        body += _box(12, 2, board_bottom + p["shell_reference_pcb_thickness"] / 2 - floor,
                     0, sy * (bl / 2 + 1 + p["board_lateral_play"]), floor)

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
        body -= Pos(cw/2 - 0.5, y, shell_reference_top + 10.5) * extrude(slot, amount=wall + 1)

    # Tie anchors flank cable exit. Holes carry a small zip tie through the floor.
    for sx in (-1, 1):
        for dy in (-2.5, 2.5):
            body -= _box(1.8, 3.2, floor + 1,
                         sx * (p["end_cable_width"] / 2 + 3), bl / 2 + dy, -0.5)

    # Updated quick-fit retention. These features replace the former 52 mm
    # shelves, raised shoulders and hex-nut cuts at their source. Add after the
    # wall openings so the complete cylindrical insert boss remains supported.
    clamp_z = board_top + p["board_vertical_play"]
    clamp_inner = bw / 2 - p["board_edge_overlap"]
    clamp_outer = cw / 2 - 0.3
    clamp_width = clamp_outer - clamp_inner
    clamp_center = (clamp_inner + clamp_outer) / 2
    boss_radius = p["clamp_boss_diameter"] / 2
    insert_radius = p["clamp_insert_outer_diameter"] / 2
    pilot_radius = p["clamp_insert_pilot_diameter"] / 2
    bore_bottom = clamp_z - p["clamp_insert_bore_depth"]
    screw_tip = clamp_z + p["clamp_thickness"] - p["clamp_screw_length"]
    insert_bottom = clamp_z - p["clamp_insert_length"]
    shoulder_inner = bw / 2 + p["board_lateral_play"]
    if bw > p["component_reference_width"]:
        raise ValueError("PCB width exceeds reserved component/cavity reference width")
    if not 0.2 <= p["board_lateral_play"] <= 0.5:
        raise ValueError("Board lateral play must be 0.2..0.5 mm per side")
    if not 0.1 <= p["board_vertical_play"] <= 0.4:
        raise ValueError("Board vertical play must be 0.1..0.4 mm")
    if p["board_edge_overlap"] <= p["board_lateral_play"]:
        raise ValueError("PCB edge overlap must exceed maximum lateral play")
    if clamp_x - boss_radius < shoulder_inner - 1e-7:
        raise ValueError("Insert boss intrudes into the allowed PCB movement envelope")
    if clamp_x + boss_radius > ow / 2 - 0.1:
        raise ValueError("Insert boss would change the outer shell footprint")
    if boss_radius - insert_radius < 2:
        raise ValueError("Insert needs at least 2 mm radial polymer")
    if not 3.8 <= p["clamp_insert_pilot_diameter"] <= 4.2:
        raise ValueError("Provisional M3 insert pilot must be 3.8..4.2 mm")
    if p["clamp_insert_outer_diameter"] <= p["clamp_insert_pilot_diameter"]:
        raise ValueError("Heat-set insert must exceed pilot diameter")
    if p["clamp_insert_bore_depth"] < p["clamp_insert_length"] + 0.4:
        raise ValueError("Blind pilot needs at least 0.4 mm below the insert")
    if bore_bottom < floor + 0.8:
        raise ValueError("Insert pilot must leave the floor and 0.8 mm above it intact")
    if screw_tip < bore_bottom + 0.4:
        raise ValueError("Clamp screw bottoms or leaves less than 0.4 mm tip clearance")
    engagement = clamp_z - max(screw_tip, insert_bottom)
    if engagement < 3:
        raise ValueError("Clamp screw needs at least 3 mm engagement in its insert")
    if clamp_x + 2.75 > cw / 2 - 0.3:
        raise ValueError("M3 socket head would approach the side wall")
    if clamp_outer - clamp_x - hole_r < 1.5:
        raise ValueError("Clamp requires 1.5 mm ligament outboard of its screw hole")
    clamps = {}
    retention_regions = []
    clamp_centers = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * clamp_x, sy * clamp_y
            body += _box(clamp_width, 8, board_bottom - floor,
                         sx * clamp_center, y, floor)
            # This shoulder controls 0.2 mm vertical and 0.4 mm lateral play.
            body += _box(clamp_outer - shoulder_inner, 8, clamp_z - floor,
                         sx * (clamp_outer + shoulder_inner) / 2, y, floor)
            body += _cylinder(boss_radius, clamp_z - floor, x, y, floor)
            body -= _cylinder(pilot_radius, p["clamp_insert_bore_depth"] + 0.1,
                              x, y, bore_bottom)
            clamp = _box(clamp_width, 8, p["clamp_thickness"],
                         sx * clamp_center, y, clamp_z)
            clamp -= _cylinder(hole_r, p["clamp_thickness"] + 1, x, y, clamp_z - 0.5)
            name = f"pcb_clamp_{'left' if sx < 0 else 'right'}_{'front' if sy < 0 else 'rear'}"
            clamps[name] = clamp
            clamp_centers.append([x, y])
            # Broad comparison-only region also encloses the old52 mm features.
            retention_regions.append(_box(14, 11, clamp_z-floor+2.5,
                                           sx * 30, y, floor))

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
        "title": "Modified 005 shell source for heat-set PCB fit test",
        "retention_regions": retention_regions,
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
            "clamp_screw_centers_xy": clamp_centers,
            "clamp_underside_z": clamp_z,
            "clamp_insert_bore_bottom_z": bore_bottom,
            "clamp_insert_bottom_z": insert_bottom,
            "clamp_screw_tip_z": screw_tip,
            "clamp_thread_engagement": engagement,
        },
        "notes": [
            "Source adapted from revision005 base_model.py; only the quick-fit wrapper is a deliverable.",
            "PCB retention replaces the old shelves/shoulders/nut slots with insert bosses, ledges and removable clamps.",
            "The original shell width and shell feature heights use separate 52 mm/1.6 mm references; actual PCB parameters are49x70x1.",
            "The unused full console lid and bracket returned here are source context, not revised production models.",
        ],
    }
