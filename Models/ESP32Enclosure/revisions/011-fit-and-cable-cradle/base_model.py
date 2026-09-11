"""Revision008 base: short wall-supported corner bosses replace tall lid posts.

Assembly coordinates: board centered in XY, +Y is terminal/cable end, -X is
USB/DC access side, +Z points toward the desk. Body floor bottom is Z=0.
Parts returned by build() are individually placed on Z=0 in print orientation.
No filesystem writes or viewer calls occur on import or build.
"""
from math import isfinite, radians, sqrt, tan

from build123d import (
    Align, Axis, Box, Cylinder, Plane, Polygon, Pos, Rot,
    SlotOverall, chamfer, extrude, fillet,
)


DEFAULTS = {
    "pcb_width": 49.0, "pcb_length": 70.0, "pcb_thickness": 1.0,
    "solder_clearance": 6.6, "component_clearance": 22.0,
    "side_margin": 8.0, "end_margin": 9.0, "wall": 2.4, "floor": 2.4,
    "lid_thickness": 2.4, "lid_fit_clearance": 0.3, "lid_skirt_depth": 2.0,
    "lid_insert_outer_diameter": 4.6, "lid_insert_length": 5.0,
    "lid_insert_pilot_diameter": 4.0, "lid_insert_bore_depth": 6.0,
    "lid_screw_length": 8.0,
    "lid_corner_projection": 8.4, "lid_corner_pad_height": 8.0,
    "lid_corner_support_angle": 45.0, "lid_corner_wall_overlap": 0.4,
    "left_access_length": 60.0, "left_access_start_above_pcb": -1.0,
    "end_cable_width": 24.0, "end_cable_height": 16.0, "clamp_y": 17.0,
    "board_edge_overlap": 0.8, "board_vertical_play": 0.2,
    "m3_clearance": 3.4, "desk_screw_clearance": 4.5,
    "pcb_insert_outer_diameter": 4.6, "pcb_insert_length": 5.0,
    "pcb_insert_pilot_diameter": 4.0, "pcb_insert_bore_depth": 6.0,
    "pcb_clamp_screw_length": 6.0, "pcb_clamp_boss_diameter": 8.8,
    "pcb_clamp_screw_offset_from_edge": 4.9,
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


def _on_bed(shape):
    return Pos(0, 0, -shape.bounding_box().min.Z) * shape


def _corner_support(projection, overlap, pad_bottom, top_z, angle):
    """Canonical +X/+Y corner: inner wall faces X0/Y0, cavity X-/Y-.

    The two wedges are united, giving underside root + min(-X,-Y)*tan(angle)
    inside the cavity. Each layer grows from the nearer wall; there is no
    diagonally expanding square pyramid. The embedded strip is flat at root.
    """
    root_z = pad_bottom - projection * tan(radians(angle))
    width = projection + overlap
    center = (overlap-projection)/2
    upper = _box(width,width,top_z-pad_bottom,center,center,pad_bottom)
    profile_points = ((-projection,pad_bottom),(overlap,pad_bottom),
                      (overlap,root_z),(0,root_z))
    x_wedge = Pos(0,center,0)*extrude(Plane.XZ*Polygon(*profile_points,align=None),
                                    amount=width/2,both=True)
    y_wedge = Pos(center,0,0)*extrude(Plane.YZ*Polygon(*profile_points,align=None),
                                    amount=width/2,both=True)
    return upper+x_wedge+y_wedge, root_z


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
    if not 5.8 <= p["solder_clearance"] <= 10:
        raise ValueError("Preserved underside allowance must stay5.8..10 mm")
    if p["component_clearance"] < 22:
        raise ValueError("Component height is too small for this bracket and access layout")
    if p["bracket_clearance_above_body"] < p["lid_thickness"] + 4.0:
        raise ValueError("Bracket must clear lid and external screw heads")
    if p["lid_skirt_depth"] > 2.5:
        raise ValueError("Preserved lid skirt depth must stay at or below 2.5 mm")
    # Retain the lid's heat-set interface while changing its corner support.
    # The blind pilots remain circular; no nut pockets or side entries return.
    if not 3.8 <= p["lid_insert_pilot_diameter"] <= 4.2:
        raise ValueError("Lid insert pilot must stay 3.8..4.2 mm pending an actual insert fit test")
    if p["lid_insert_outer_diameter"] <= p["lid_insert_pilot_diameter"]:
        raise ValueError("Lid insert outside diameter must exceed the printed pilot")
    if not 8.4 <= p["lid_corner_projection"] <= p["end_margin"]-0.5:
        raise ValueError("Corner projection must retain the full insert envelope and PCB-end clearance")
    if not 0.2 <= p["lid_corner_wall_overlap"] <= min(0.8,p["wall"]-1):
        raise ValueError("Corner wall overlap must stay0.2..0.8 mm and remain inside the shell")
    if not 45 <= p["lid_corner_support_angle"] <= 55:
        raise ValueError("Corner underside angle must stay45..55 degrees above the XY plane")
    if p["lid_corner_pad_height"]-p["lid_insert_bore_depth"] < 2.0-1e-8:
        raise ValueError("Corner pad needs at least2 mm of solid floor beneath the entire pilot")
    if p["lid_corner_projection"]-4-p["lid_insert_outer_diameter"]/2 < 2.0-1e-8:
        raise ValueError("Lid insert requires at least2 mm material at the inboard pad faces")
    if p["lid_insert_bore_depth"] < p["lid_insert_length"] + 0.4:
        raise ValueError("Lid insert pilot needs at least 0.4 mm below the insert")
    lid_projection = p["lid_screw_length"] - p["lid_thickness"]
    if lid_projection < p["lid_insert_length"] - 1e-8:
        raise ValueError("Lid screw must engage the full nominal insert length")
    if p["lid_insert_bore_depth"] - lid_projection < 0.4 - 1e-8:
        raise ValueError("Lid screw bottoms or leaves less than 0.4 mm blind-tip clearance; use M3x8 at default dimensions")
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
    lug_y = ol / 2 - 11
    lug_x = ow / 2 + 6
    post_x, post_y = cw / 2 - 4, cl / 2 - 4
    lid_points = [(sx * post_x, sy * post_y) for sx in (-1, 1) for sy in (-1, 1)]
    mount_points = [(sx * lug_x, sy * lug_y) for sx in (-1, 1) for sy in (-1, 1)]
    clamp_x = bw / 2 + p["pcb_clamp_screw_offset_from_edge"]
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

    # Tall lid columns are absent. Short corner pads are joined later, after
    # wall cutouts, so their diagonal corner fill stays continuous to the rim.

    # Removable PCB clamps overlap only a narrow, provisional board-edge strip.
    clamp_z = board_top + p["board_vertical_play"]
    clamps = {}
    clamp_outer = bw / 2 + 8
    clamp_inner = bw / 2 - p["board_edge_overlap"]
    clamp_width = clamp_outer - clamp_inner
    clamp_center = (clamp_inner + clamp_outer) / 2
    boss_r = p["pcb_clamp_boss_diameter"] / 2
    insert_r = p["pcb_insert_outer_diameter"] / 2
    pilot_r = p["pcb_insert_pilot_diameter"] / 2
    bore_bottom = clamp_z - p["pcb_insert_bore_depth"]
    screw_tip = clamp_z + 2.0 - p["pcb_clamp_screw_length"]
    insert_bottom = clamp_z - p["pcb_insert_length"]
    if not 3.8 <= p["pcb_insert_pilot_diameter"] <= 4.2:
        raise ValueError("PCB insert pilot must stay3.8..4.2 mm pending actual insert fit")
    if insert_r <= pilot_r or boss_r-insert_r < 2.0-1e-8:
        raise ValueError("PCB insert needs an undersized pilot and at least2 mm radial polymer")
    if clamp_x-boss_r < bw/2+0.4-1e-8:
        raise ValueError("PCB insert boss intrudes into the retained board play envelope")
    if clamp_x+boss_r > ow/2-0.2:
        raise ValueError("PCB insert boss would alter the external shell footprint")
    if clamp_x-bw/2-0.4-insert_r < 2.0-1e-8:
        raise ValueError("PCB locating shoulder needs at least2 mm material before the insert OD")
    if p["pcb_insert_bore_depth"] < p["pcb_insert_length"]+0.4:
        raise ValueError("PCB insert pilot needs at least0.4 mm below the insert")
    if bore_bottom < floor+0.8:
        raise ValueError("PCB blind pilot must retain the floor plus0.8 mm of post")
    if screw_tip-bore_bottom < 0.4-1e-8:
        raise ValueError("PCB clamp screw bottoms or lacks0.4 mm tip clearance; use M3x6 at defaults")
    if clamp_z-max(screw_tip,insert_bottom) < 3.0:
        raise ValueError("PCB clamp screw needs at least3 mm insert engagement")
    if clamp_outer-clamp_x-hole_r < 1.3-1e-8:
        raise ValueError("PCB clamp needs at least1.3 mm outer screw-hole ligament")
    if clamp_outer-clamp_x-2.75 < 0.3-1e-8:
        raise ValueError("PCB M3 socket head needs at least0.3 mm clearance inside the clamp edge")
    pcb_points = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * clamp_x, sy * clamp_y
            body += _box(clamp_width, 8, board_bottom - floor,
                         sx * clamp_center, y, floor)
            # A shoulder gives repeatable vertical clearance without crushing PCB.
            shoulder_inner = bw / 2 + 0.4
            body += _box(clamp_outer - shoulder_inner, 8, clamp_z - floor,
                         sx * (clamp_outer + shoulder_inner) / 2, y, floor)
            clamp = _box(clamp_width, 8, 2, sx * clamp_center, y, clamp_z)
            clamp -= _cylinder(hole_r, 3, x, y, clamp_z - 0.5)
            name = f"pcb_clamp_{'left' if sx < 0 else 'right'}_{'front' if sy < 0 else 'rear'}"
            clamps[name] = clamp
            pcb_points.append([x,y])

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

    # Reinforce after the left-access cut so its upper outer sector cannot be
    # removed. The insert cylinder stops0.1 mm outside the board's allowed play;
    # the original narrow PCB capture slots and locating shoulders remain.
    for x,y in pcb_points:
        body += _cylinder(boss_r,clamp_z-floor,x,y,floor)
        body -= _cylinder(pilot_r,p["pcb_insert_bore_depth"]+0.1,x,y,bore_bottom)

    # Paired wall-supported wedges close the former circular-post corner gaps.
    # Keep an unexported legacy comparison to quantify CAD volume, not print time.
    stock_body = body
    corner_projection = p["lid_corner_projection"]
    corner_overlap = p["lid_corner_wall_overlap"]
    pad_bottom = h-p["lid_corner_pad_height"]
    canonical, corner_root = _corner_support(corner_projection,corner_overlap,
                                             pad_bottom,h,p["lid_corner_support_angle"])
    if corner_root < floor+2:
        raise ValueError("Corner supports must start at least2 mm above the floor")
    if corner_projection > cl/2-p["left_access_length"]/2-0.5:
        raise ValueError("Corner pad would obstruct the preserved left access opening")
    canonical -= _cylinder(p["lid_insert_pilot_diameter"]/2,
                            p["lid_insert_bore_depth"]+0.1,-4,-4,h-p["lid_insert_bore_depth"])
    corner_supports = {}
    corner_regions = {}
    corner_skirt_cuts = {}
    legacy_posts = {}
    legacy_body = stock_body
    for sx in (-1,1):
        for sy in (-1,1):
            name = f"corner_{'left' if sx<0 else 'right'}_{'front' if sy<0 else 'rear'}"
            rotation = {(1,1):0,(-1,1):90,(-1,-1):180,(1,-1):270}[(sx,sy)]
            placement = Pos(sx*cw/2,sy*cl/2,0)*Rot(Z=rotation)
            feature = placement*canonical
            corner_supports[name] = feature
            body += feature
            region_width = corner_projection+corner_overlap
            region_center = (corner_overlap-corner_projection)/2
            corner_regions[name] = placement*_box(region_width,region_width,h-floor,
                                                    region_center,region_center,floor)
            skirt_clearance = p["lid_fit_clearance"]
            corner_skirt_cuts[name] = placement*_box(region_width+2*skirt_clearance,
                region_width+2*skirt_clearance,p["lid_skirt_depth"]+0.2,
                region_center,region_center,h-p["lid_skirt_depth"]-0.1)
            x,y = sx*post_x,sy*post_y
            legacy = _cylinder(4.4,h-floor,x,y,floor)
            legacy -= _cylinder(p["lid_insert_pilot_diameter"]/2,
                p["lid_insert_bore_depth"]+0.1,x,y,h-p["lid_insert_bore_depth"])
            legacy_posts[name] = legacy
            legacy_body += legacy
    old_net = float(legacy_body.volume-stock_body.volume)
    new_net = float(body.volume-stock_body.volume)

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
    # The old corner gap housed small skirt segments. Trim only those segments
    # and leave the lid plate, outer profile, holes and remaining skirt intact.
    for cut in corner_skirt_cuts.values():
        skirt -= cut
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
        # This legacy source bracket is replaced by the wrapper's existing
        # heat-set bracket. It contains no nut-pocket geometry either.
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
        "corner_supports_local": corner_supports,
        "corner_regions_local": corner_regions,
        "corner_skirt_trim_regions_local": corner_skirt_cuts,
        "legacy_lid_posts_local": legacy_posts,
        "reference_full_height_body_local": legacy_body,
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
            "pcb_clamp_screw_centers_xy": pcb_points,
            "pcb_clamp_underside_z": clamp_z,
            "pcb_insert_pilot_bottom_z": bore_bottom,
            "pcb_insert_bottom_z": insert_bottom,
            "pcb_clamp_screw_tip_z": screw_tip,
            "printed_captive_nut_pocket_count": 0,
            "pcb_edge_overlap": p["board_edge_overlap"],
            "pcb_vertical_play": p["board_vertical_play"],
            "corner_bosses": {
                "count":4,"inner_wall_projection_mm":corner_projection,
                "wall_overlap_mm":corner_overlap,
                "pad_square_width_mm":corner_projection+corner_overlap,
                "pad_bottom_local_z_mm":pad_bottom,"pad_top_local_z_mm":h,
                "pad_height_mm":p["lid_corner_pad_height"],
                "wall_root_local_z_mm":corner_root,
                "underside_angle_from_xy_degrees":p["lid_corner_support_angle"],
                "underside_rule":"root + min(distance_from_X_wall,distance_from_Y_wall)*tan(angle); paired wedge union",
                "pilot_floor_thickness_mm":p["lid_corner_pad_height"]-p["lid_insert_bore_depth"],
                "minimum_inboard_material_to_insert_mm":corner_projection-4-p["lid_insert_outer_diameter"]/2,
                "lid_skirt_corner_clearance_mm":p["lid_fit_clearance"],
                "lid_skirt_trim_z_range_mm":[h-skirt_depth,h],
                "raw_old_post_feature_volume_mm3":sum(float(s.volume) for s in legacy_posts.values()),
                "raw_new_corner_feature_volume_mm3":sum(float(s.volume) for s in corner_supports.values()),
                "old_feature_net_addition_to_shell_mm3":old_net,
                "new_feature_net_addition_to_shell_mm3":new_net,
                "body_volume_saved_mm3":old_net-new_net,
                "comparison":"Same remaining body features and parameters; legacy columns replace the new corner pads in an unexported comparison only",
                "changed_print_parts":["body","lid"],"unchanged_print_part_count":13,
            },
        },
        "notes": [
            "Revision 002 is a separate console-inspired styling variant; generic revision 001 is preserved unchanged.",
            f"Styling: R{radius:g} mm outer vertical corners; {bevel:g} mm bottom-body/top-lid 45-degree chamfers; {b:g} mm projecting lower belt with 45-degree transitions.",
            "Revision008 replaces tall lid posts with short corner pads and two wall-supported underside wedges. The lid skirt is trimmed only around these pads; all hardware axes and PCB capture strips stay unchanged.",
            f"Main walls remain {wall:g} mm; outer corner rounding leaves {sqrt(2)*wall-(sqrt(2)-1)*radius:.2f} mm minimum diagonal shell above the base chamfer. Bevels locally narrow the bed-contact perimeter.",
            "Nine diagonal lid slots and seven side slots are functional openings; thermal performance has not been measured.",
            f"Two 0.8 mm-wide decorative lid channels are recessed {p['accent_depth']:g} mm and retain at least 2 mm lid thickness. Their short roof spans print above the exterior face on the bed.",
            "Side-slot rounded roofs add approximately3 mm local bridge spans; no modeled supports are included.",
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
            f"Lid hardware remains4 M3x{p['lid_screw_length']:g} screws and4 M3x{p['lid_insert_length']:g} heat-set inserts. PCB clamps now use4 M3x{p['pcb_clamp_screw_length']:g} screws and4 M3x{p['pcb_insert_length']:g} heat-set inserts; the wrapper defines the actual desk bracket hardware.",
            "All printed captive-nut pockets and their side entries are removed, including the unused legacy bracket cuts. Narrow PCB capture slots remain functional locating geometry.",
            f"Desk holes are {p['desk_screw_clearance']:g} mm clearance. Choose desk screw type/length only after desk material and thickness are known.",
            "Body prints floor-down. Lid exterior face and bracket desk-contact face print on the bed. Clamps print flat.",
            "No modeled supports. Review the retained mounting flanges and horizontal cartridge pilot bridges in the slicer.",
            "Physical fit, strength, thermal behavior and RF performance remain unvalidated.",
        ],
    }


BUTTON_DEFAULTS = {
    "reset_button_y": 0.0, "boot_button_y": -17.0,
    "button_inset_from_left_pcb_edge": 3.0,
    "reset_switch_height_above_pcb": 6.0, "boot_switch_height_above_pcb": 6.0,
    "reset_contact_screw_length": 12.0, "boot_contact_screw_length": 12.0,
    "button_contact_insert_outer_diameter": 4.6,
    "button_contact_insert_pilot_diameter": 4.0,
    "button_contact_insert_length": 5.0,
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
    # Complete the comparison body with the identical external cartridge pads.
    # This reference is excluded from every printed/exported part collection.
    result["reference_full_height_body_local"], _ = mounting.add_mounts(
        result["reference_full_height_body_local"],face_x,centers,
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
              "contact_insert_outer_diameter": p["button_contact_insert_outer_diameter"],
              "contact_insert_pilot_diameter": p["button_contact_insert_pilot_diameter"],
              "contact_insert_length": p["button_contact_insert_length"],
              "mount_hole_y_spacing": 6.0, "mount_hole_z": 5.0}
        button = button_module.make_button(bp, name)
        result["parts"].update(button["parts"])
        result["assembly"].update(button["assembly"])
        result["hardware"].update(button["hardware"])
        result["buttons"][name] = {"params": bp, "moving_names": button["moving_names"],
                                   "measurements": button["measurements"],
                                   "expected_hardware_intersections": button["expected_hardware_intersections"]}
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
    result["title"] = "ESP32 / console enclosure with M3 heat-set actuators · revision 004"
    result["notes"] = [n for n in result["notes"] if not n.startswith("Revision 002")]
    result["notes"].extend([
        "Revision 004 replaces each actuator's captive nylon nut with an M3x5 mm heat-set insert and uses an M3x12 nylon contact screw. Revisions 001, 002 and 003 are preserved.",
        "The button locations and height are provisional photo/layout estimates, not measured fit. Adjust XY parameters and nylon tip height before fitting to the real electronics.",
        "Button housings are offset to reserve an 11 mm USB corridor at default dimensions; actual USB plug, DC plug, wiring and switch envelopes remain unverified.",
        "Two captive 4x2 mm axially magnetized discs per button face like poles together. A keyed guide and rigid travel stops constrain the paddle; return force and friction require physical testing.",
        f"Additional hardware: four M3x18 socket screws (head diameter<=5.5 mm), four short M3 mounting inserts (nominal length4 / OD4.6 mm), two M3x{p['button_contact_insert_length']:g} actuator inserts (provisional OD{p['button_contact_insert_outer_diameter']:g} mm), four 4x2 mm magnets, one nylon M3x{p['reset_contact_screw_length']:g} EN contact screw, one nylon M3x{p['boot_contact_screw_length']:g} BOOT contact screw and two nylon M3 jam nuts. No mounting washers are assumed.",
        f"Provisional insert pilots: {p['button_insert_pilot_diameter']:g} mm diameter x {p['button_insert_bore_depth']:g} mm blind depth. Confirm with the insert drawing and a material-specific coupon; OD4.6 mm is not the pilot diameter.",
        "The model's hardware proxies are excluded from printable parts and print-layout.3mf. They are simplified illustrations without threads or magnetic simulation.",
        f"Paddle stroke {p['button_stroke']:g} mm; idle contact gap {p['button_stroke']-p['modeled_switch_depression']:g} mm; modeled switch depression {p['modeled_switch_depression']:g} mm. Actual switch travel is unknown; calibrate the stop and tip so the switch is released at rest and never carries excess finger load.",
        "The nylon contact tip is calibrated while the enclosure is accessible, then locked with its jam nut. The external pad is pressed toward the enclosure floor while mounted under the desk.",
        "Install PCB clamps before attaching the cartridges. The BOOT arm overlaps the left-front clamp's screwdriver approach, so remove that cartridge for later clamp service.",
        "Contact screw length is configurable; default12 mm screws suit the deeper heat-set boss. Recheck head-to-lid clearance and full insert engagement after changing switch height or screw length.",
        f"Actuator insert pilot: {p['button_contact_insert_pilot_diameter']:g} mm diameter, {p['button_contact_insert_length']+0.4:g} mm blind depth with M3 through-hole. The M3x5 designation does not specify outside diameter; OD and pilot remain provisional pending the actual insert dimensions.",
        "Actuator heat-set inserts intentionally displace the undersized plastic pilot during installation. Only each named insert/slider overlap is expected; it is recorded separately from unintended interference.",
        "Cartridge frames and rear keepers print on their outer sides; sliders need local removable support under their stepped arms. Keep support scars away from guide and magnet-fit faces. The small moving-magnet keepers print flat.",
        "Magnets are placed outside the USB/button side, opposite the pictured antenna. Espressif recommends at least15 mm antenna clearance and final-product radio testing: https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html . Existing antenna/perfboard performance is not established by this model.",
        "Magnet guidance: https://www.kjmagnetics.com/blog/repelling-magnets . Short insert reference: https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck .",
        "Preserve button_module.py and mounting.py alongside model.py. Use build-revision.py for builds that snapshot all required source files.",
    ])
    return result
