"""Mechanically guided magnetic-return ESP32 actuator cartridge, millimeters.

Slider and tip move together in -Z. Magnets and fasteners are hardware only.
The slider top-loads with the -X keeper removed; the keeper captures its stop lug.
"""
from math import atan2, degrees, isfinite, sqrt
from build123d import Align, Axis, Box, Cylinder, Polygon, Pos, RegularPolygon, Rot, chamfer, extrude


DEFAULTS = {
    "mounting_face_x": -40.0, "housing_y": 4.0,
    "tip_x": -23.0, "tip_y": 0.0, "switch_top_z": 16.0,
    "arm_bottom_z": 19.2, "stroke": 0.8, "guide_clearance": 0.3,
    "switch_depression": 0.2, "travel": 0.0,
    "contact_screw_length": 12.0,
    "contact_insert_outer_diameter": 4.6,
    "contact_insert_pilot_diameter": 4.0,
    "contact_insert_length": 5.0,
    "mount_hole_y_spacing": 6.0, "mount_hole_z": 5.0,
}


def box(w, d, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl(r, h, x=0, y=0, z=0):
    return Pos(x, y, z) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def x_cyl(r, length, x, y, z):
    return Pos(x, y, z) * Rot(0, 90, 0) * Cylinder(
        r, length, align=(Align.CENTER, Align.CENTER, Align.MIN))


def on_bed(shape):
    return Pos(0, 0, -shape.bounding_box().min.Z) * shape


def make_button(params=None, name="button"):
    """Return printed parts, assembly, hardware, mount cutters, and dimensions.

    `travel` translates every moving part down from rest. `arm_bottom_z` shifts
    the whole sliding guide/magnet section while base mounting holes stay fixed.
    Mount screw axes are +X; rear keeper is the screw-head bearing surface.
    """
    supplied = params or {}
    unknown = set(supplied) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"Unknown button parameters: {sorted(unknown)}")
    p = DEFAULTS | supplied
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(v)
           for v in p.values()):
        raise ValueError("Button dimensions must be finite numbers")
    if not 0.6 <= p["stroke"] <= 1.0:
        raise ValueError("Button stroke must be 0.6..1.0 mm")
    if not 0 <= p["travel"] <= p["stroke"]:
        raise ValueError("Travel must be between rest and the mechanical stop")
    if not 0.2 <= p["guide_clearance"] <= 0.4:
        raise ValueError("Guide clearance must be 0.2..0.4 mm per side")
    if not 0 < p["switch_depression"] <= 0.2:
        raise ValueError("Unmeasured switch depression is bounded to 0.2 mm")
    if p["contact_screw_length"] not in (8.0, 10.0, 12.0):
        raise ValueError("Nylon contact screw length must be 8, 10, or 12 mm")
    if not 4.0 <= p["contact_insert_length"] <= 6.0:
        raise ValueError("Contact insert length must be 4..6 mm for this boss")
    if not 3.4 < p["contact_insert_pilot_diameter"] < p["contact_insert_outer_diameter"]:
        raise ValueError("Insert pilot must exceed M3 clearance and remain below insert outer diameter")
    if 9.0-p["contact_insert_outer_diameter"] < 2.4:
        raise ValueError("Contact insert envelope must retain at least 1.2 mm radial boss material")
    if abs(p["tip_y"] - p["housing_y"]) > 4.0:
        raise ValueError("Tip Y offset must stay within +/-4 mm")
    if not 18.8 <= p["arm_bottom_z"] <= 20.2:
        raise ValueError("This cartridge accommodates arm bottom Z=18.8..20.2")

    face, y, tx, ty = p["mounting_face_x"], p["housing_y"], p["tip_x"], p["tip_y"]
    stroke, gap = p["stroke"], p["guide_clearance"]
    a = p["arm_bottom_z"]
    dz = a - 19.2
    rear, inner_rear, inner_front = face-14.2, face-11.8, face-2.4
    sx0, sx1 = inner_rear+gap, inner_front-gap
    slider_width, slider_y_width = sx1-sx0, 8.6-2*gap
    mx, slider_center = face-7.2, (sx0+sx1)/2
    guide_floor, slider_bottom = 11.2+dz, 13.0+dz
    slider_top = a+4.8
    pad_bottom, pad_top = slider_top, slider_top+3.0
    if tx <= inner_front+10:
        raise ValueError("Tip must remain at least 10 mm inside the front guide")

    # Open-top U frame: top-load slider at final XY with rear keeper removed.
    frame = box(11.8, 14, a+6.4-2.4, (inner_rear+face)/2, y, 2.4)
    frame -= box(9.5, 8.6, 30, inner_rear+4.65, y, guide_floor)
    # Open the arm channel upward so the diagonal tip never has to pass through
    # a narrow front window. Its sill remains the primary lower travel stop.
    frame -= box(12.2, 11.2, 30, face-5.9, y, a-stroke)
    # Pads above side rails contact at the same lower travel limit.
    for sign in (-1, 1):
        frame -= box(9.5, 3.0, 20, inner_rear+4.65,
                     y+sign*5.8, pad_bottom-stroke)

    # Two horizontal M3 mounting bolts also retain the rear keeper.
    mounting_centers = []
    for dy in (-p["mount_hole_y_spacing"]/2, p["mount_hole_y_spacing"]/2):
        mounting_centers.append((face, y+dy, p["mount_hole_z"]))
        frame -= x_cyl(1.7, 15, rear-0.2, y+dy, p["mount_hole_z"])

    # Fixed 4x2 magnet in a side-loading 4.3 mm square pocket. Rear keeper's
    # tongue closes its feed channel, leaving no adhesive-dependent retention.
    fixed_bottom = 8.2+dz
    frame -= box(mx+2.15-inner_rear+0.2, 4.3, 2.2,
                 (mx+2.15+inner_rear-0.2)/2, y, fixed_bottom)
    keeper = box(2.4, 14, a+4.0-2.4, rear+1.2, y, 2.4)
    keeper += box(mx-2.15-inner_rear+0.05, 4.1, 2.0,
                  (inner_rear+mx-2.15-0.05)/2, y, fixed_bottom+0.1)
    for _, hy, hz in mounting_centers:
        keeper -= x_cyl(1.7, 3.0, rear-0.2, hy, hz)

    # Slider rectangular key prevents magnet repulsion from translating sideways.
    slider = box(slider_width, slider_y_width, slider_top-slider_bottom,
                 slider_center, y, slider_bottom)
    slider += box(slider_width, 12.0, 3.0, slider_center, y, pad_bottom)
    # Soften only the exposed upper perimeter; keep bottom stop shoulders flat.
    slider = chamfer(slider.edges().group_by(Axis.Z)[-1], 0.5)
    # Rigid arm: diagonal footprint changes Y at the distal contact while its
    # underside stays above clamp screw heads across the PCB edge.
    angle = degrees(atan2(ty-y, tx-mx))
    length = ((tx-mx)**2+(ty-y)**2)**0.5
    arm = Pos((mx+tx)/2, (y+ty)/2, a) * Rot(0, 0, angle) * Box(
        length+0.5, 8.4, 4.8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    arm += cyl(4.5, 4.8, tx, ty, a)
    slider += arm

    # Rear stop lug is captured once the keeper is bolted to the base.
    lug_z, lug_h = a+0.8, 2.0
    slider += box(sx0-rear-0.2, 6.0, lug_h, (sx0+rear+0.2)/2, y, lug_z)
    keeper -= box(3.0, 6.6, lug_h+stroke, rear+1.2, y, lug_z-stroke)

    moving_pocket_bottom = slider_bottom+0.8
    slider -= box(mx+2.15-sx0+0.2, 4.3, 2.2,
                  (mx+2.15+sx0-0.2)/2, y, moving_pocket_bottom)
    magnet_keeper = box(mx-2.15-sx0-0.1, 4.1, 2.0,
                        (sx0+mx-2.15)/2, y, moving_pocket_bottom+0.1)

    # M3x5 heatset at the distal contact only. The arm/guide interface is unchanged.
    # Boss is locally deeper; pilot has 0.4 mm axial relief below the insert and
    # a 1.0 mm floor around the M3 through-hole. Knurls displace pilot material.
    insert_length = p["contact_insert_length"]
    insert_od = p["contact_insert_outer_diameter"]
    pilot_diameter = p["contact_insert_pilot_diameter"]
    boss_bottom = a-0.8
    boss_top = max(a+4.8, boss_bottom+insert_length+1.4)
    pocket_depth = insert_length+0.4
    insert_bottom = boss_top-insert_length
    slider += cyl(4.5, boss_top-boss_bottom, tx, ty, boss_bottom)
    slider -= cyl(1.7, boss_top-boss_bottom+1, tx, ty, boss_bottom-0.5)
    slider -= cyl(pilot_diameter/2, pocket_depth+0.2,
                  tx, ty, boss_top-pocket_depth)
    # Relieve only the low collar toward the inner USB approach. The 14 mm
    # cartridge edge defines that corridor; allow 0.1 mm at its boundary. With
    # +/-4 mm tip offset this clips at tip Y +/-2.9, leaving 1.2 mm around the
    # M3 through-hole. The insert/pilot region above the arm bottom is untouched.
    tip_y_offset = ty-y
    collar_relief_direction = 0 if abs(tip_y_offset)<1e-9 else (1 if tip_y_offset>0 else -1)
    collar_limit = 7.0-abs(tip_y_offset)-0.1
    if collar_relief_direction:
        collar_edge_y = ty+collar_relief_direction*collar_limit
        slider -= box(9.2, 20, a-boss_bottom+0.1, tx,
                      collar_edge_y+collar_relief_direction*10, boss_bottom-0.1)

    idle_gap = stroke-p["switch_depression"]
    tip_bottom = p["switch_top_z"]+idle_gap
    if not tip_bottom < boss_bottom-0.3:
        raise ValueError("Switch/contact height leaves no adjustable tip below contact boss")
    screw_length = p["contact_screw_length"]
    jam_top = boss_top+2.4
    minimum_tip = jam_top-screw_length
    if tip_bottom < minimum_tip-1e-7:
        raise ValueError("Contact screw head would intersect jam nut; choose a longer nylon screw")
    if tip_bottom > insert_bottom+1e-7:
        raise ValueError("Contact screw does not span the full insert thread height")
    # Simplified hardware proxies: geometry only, not thread or magnetic analysis.
    nylon_screw = cyl(1.5, screw_length, tx, ty, tip_bottom)
    nylon_screw += cyl(2.75, 3, tx, ty, tip_bottom+screw_length)
    contact_insert = cyl(insert_od/2, insert_length, tx, ty, insert_bottom)
    contact_insert -= cyl(1.51, insert_length+0.2, tx, ty, insert_bottom-0.1)
    jam_nut = Pos(tx, ty, boss_top) * extrude(RegularPolygon(5.5/sqrt(3), 6), amount=2.4)
    jam_nut -= cyl(1.51, 3, tx, ty, boss_top-0.1)
    fixed_magnet = cyl(2, 2, mx, y, fixed_bottom+0.1)
    moving_magnet = cyl(2, 2, mx, y, moving_pocket_bottom+0.1)
    hardware = {
        "fixed_magnet": fixed_magnet, "moving_magnet": moving_magnet,
        "nylon_adjuster": nylon_screw, "contact_heatset_insert": contact_insert,
        "nylon_jam_nut": jam_nut,
    }
    for i, (_, hy, hz) in enumerate(mounting_centers):
        screw = x_cyl(1.5, 18, rear, hy, hz)
        screw += x_cyl(2.75, 3.0, rear-3.0, hy, hz)
        hardware[f"mount_screw_{i+1}"] = screw

    assembled = {"frame": frame, "slider": slider, "rear_keeper": keeper,
                 "moving_magnet_keeper": magnet_keeper}
    moving_names = ("slider", "moving_magnet_keeper")
    for key in moving_names:
        assembled[key] = Pos(0, 0, -p["travel"]) * assembled[key]
    for key in ("moving_magnet", "nylon_adjuster", "contact_heatset_insert", "nylon_jam_nut"):
        hardware[key] = Pos(0, 0, -p["travel"]) * hardware[key]

    # Place the beam on its broad flat side for XY filament paths along its arm.
    # Guide/rear keeper print on their outer -X sides; small magnet plug is flat.
    parts = {
        "frame": on_bed(Rot(0, -90, 0)*frame),
        "slider": on_bed(Rot(0, 180, 0)*slider),
        "rear_keeper": on_bed(Rot(0, -90, 0)*keeper),
        "moving_magnet_keeper": on_bed(magnet_keeper),
    }
    # Native printing orientation for slider has a stepped arm: local supports
    # may be required; keep guide and magnet fit surfaces free of support scars.
    prefix = lambda values: {f"{name}_{key}": value for key, value in values.items()}
    return {
        "parts": prefix(parts), "assembly": prefix(assembled),
        "hardware": prefix(hardware),
        "expected_hardware_intersections": [{
            "hardware": f"{name}_contact_heatset_insert",
            "printed": f"{name}_slider",
            "reason": "Heatset knurl envelope intentionally displaces polymer in the smaller pilot; printed CAD is pre-installation geometry.",
            "nominal_displaced_envelope_volume_mm3": 3.141592653589793*(insert_od**2-pilot_diameter**2)/4*insert_length,
        }],
        "moving_names": [f"{name}_{key}" for key in moving_names],
        "mounting_centers": mounting_centers,
        "measurements": {
            "mounting_face_x_mm": face, "rear_head_bearing_x_mm": rear,
            "housing_y_mm": y, "housing_width_y_mm": 14.0,
            "mount_screw_centers_xyz_mm": mounting_centers,
            "mount_screw_grip_mm": 14.2, "m3x18_insert_engagement_mm": 3.8,
            "guide_clearance_per_side_mm": gap, "stroke_mm": stroke,
            "travel_mm": p["travel"], "tip_center_xy_mm": [tx, ty],
            "switch_top_z_provisional_mm": p["switch_top_z"],
            "idle_tip_gap_mm": idle_gap,
            "contact_screw_length_mm": screw_length,
            "contact_head_top_z_at_rest_mm": tip_bottom+screw_length+3,
            "minimum_contact_tip_z_with_jam_nut_at_rest_mm": minimum_tip,
            "contact_downward_adjustment_margin_mm": tip_bottom-minimum_tip,
            "full_insert_engagement_tip_z_range_at_rest_mm": [minimum_tip, insert_bottom],
            "contact_insert_outer_diameter_provisional_mm": insert_od,
            "contact_insert_pilot_diameter_provisional_mm": pilot_diameter,
            "contact_insert_length_mm": insert_length,
            "contact_insert_pocket_depth_mm": pocket_depth,
            "contact_boss_bottom_z_at_rest_mm": boss_bottom,
            "contact_boss_top_z_at_rest_mm": boss_top,
            "contact_boss_height_mm": boss_top-boss_bottom,
            "contact_boss_floor_mm": boss_top-pocket_depth-boss_bottom,
            "contact_boss_radial_wall_to_insert_envelope_mm": (9.0-insert_od)/2,
            "contact_lower_collar_clearance_to_usb_edge_mm": 0.1,
            "contact_lower_collar_relief_direction_y": collar_relief_direction,
            "contact_lower_collar_minimum_ligament_to_through_hole_mm": min(4.5,collar_limit)-1.7,
            "jam_nut_thread_height_mm": 2.4,
            "maximum_modeled_switch_depression_mm": p["switch_depression"],
            "magnet_face_gap_at_rest_mm": moving_pocket_bottom+0.1-(fixed_bottom+2.1),
            "magnet_face_gap_at_stop_mm": moving_pocket_bottom+0.1-(fixed_bottom+2.1)-stroke,
        },
        "notes": [
            f"Four printed parts; two 4x2 axially magnetized discs, two M3x18 socket screws, one M3x{insert_length:g} heatset insert, one nylon M3x{screw_length:g} contact screw and one nylon M3 jam nut per button.",
            "Mounting screws bear on rear keeper at X=face-14.2; head OD<=5.5 mm, no washer assumed. Body M3 inserts are separate.",
            "Heatset the contact insert from +Z into the slider boss before fitting electronics or magnets; keep it flush and verify the passage remains clear. Insert fixed magnet through open rear of frame. Insert moving magnet and rectangular keeper into slider. With rear keeper removed, lower bare slider from +Z at final XY into the open-top guide. Fit rear keeper, bolt cartridge to body, then install nylon adjuster and jam nut. Guide captures moving magnet keeper throughout stroke.",
            "Orient like magnet poles toward each other. Return force, friction, magnetic influence and switch operation require physical validation; no RF claim.",
            "Adjust nylon tip with enclosure accessible; lock jam nut. Default 0.6 mm idle gap and 0.8 mm motion model 0.2 mm switch depression only; actual switch location/travel are unmeasured.",
            f"At rest, this screw reaches tip Z>={minimum_tip:g} mm before its head contacts the jam nut; downward adjustment margin is {tip_bottom-minimum_tip:g} mm. The {insert_length:g} mm insert and 2.4 mm jam nut have full nominal shaft coverage for tip Z={minimum_tip:g}..{insert_bottom:g} mm; the tip must also remain below the boss and preserve the measured switch gap. Threads are not modeled. Use a nylon contact screw; do not substitute a bare metal tip over the PCB.",
            f"Heatset outer diameter {insert_od:g} mm and pilot {pilot_diameter:g} mm are provisional pending the actual M3x5 insert dimensions. Pocket depth is {pocket_depth:g} mm and floor is {boss_top-pocket_depth-boss_bottom:g} mm. The insert envelope intentionally overlaps the smaller pilot by polymer-displacement volume; this expected host interaction is reported separately from unexpected collisions.",
            "Only the collar below the arm is relieved toward the USB corridor, providing 0.1 mm clearance at the cartridge's inner Y edge while retaining at least 1.2 mm around the M3 passage. The upper insert boss and material directly below the pilot remain intact.",
            "Front arm sill and pad shoulders provide lower stops; the rear keeper lug window provides upper retention and an additional lower stop. Never use switch bottoming-out as the travel stop.",
            "Check 0.3 mm per-side sliding clearance with a small coupon. Print arm with continuous filament along its span; use local removable supports if needed, away from guide/magnet fits.",
            "Removing both mounting screws releases rear keeper and makes magnets serviceable. Keep small magnets contained during assembly and servicing.",
        ],
    }


def build(params):
    """Standalone shared-runtime build contract, one EN cartridge by default."""
    result = make_button(params, "button")
    return {key: result[key] for key in ("parts", "assembly", "measurements", "notes")}
