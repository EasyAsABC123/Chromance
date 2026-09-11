"""Render revision008 with short, closed corner mounts for the lid.

Desk, direction arrows, hardware and switch proxies are illustration only.
"""
from pathlib import Path
import json
import math
import numpy as np
import sys

from fdm_cad.build import load_model, print_layout, export_mesh
from fdm_cad.geometry import mesh_inspect, load_mesh_instances
from fdm_cad import preview
from build123d import Align, Box, Compound, Cone, Cylinder, Pos, export_step


def compound(items):
    return Compound(children=list(items))


def box(w, d, h, x=0, y=0, z=0):
    return Pos(x, y, z)*Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def group(parts, lid=True, bracket=True):
    grouped = {"body": parts["body"]}
    if lid:
        grouped["lid"] = parts["lid"]
    if bracket:
        grouped["desk_bracket"] = parts["desk_bracket"]
    grouped["guides_keepers_and_PCB_clamps"] = compound(
        v for k, v in parts.items() if k.startswith("pcb_clamp_") or
        (k.startswith(("reset_", "boot_")) and not k.endswith("_slider")))
    grouped["EN_RESET_paddle"] = parts["reset_slider"]
    grouped["BOOT_paddle"] = parts["boot_slider"]
    return grouped


def show(parts, path, title, subtitle, elevation=-25, azimuth=-145):
    colors = {"body": "#59606e", "lid": "#9aa5b5", "desk_bracket": "#454c56",
              "guides_keepers_and_PCB_clamps": "#49505b", "EN_RESET_paddle": "#55aaba",
              "BOOT_paddle": "#e2a750", "desk_reference": "#b89976",
              "press_upward": "#78b88a"}
    preview.PALETTE = [colors.get(k, "#85939f") for k in parts]
    preview.render(parts, path, title=title, subtitle=subtitle,
                   elevation=elevation, azimuth=azimuth)


def upward_arrow(x, y, pad_z):
    return (Pos(x, y, pad_z-19)*Cylinder(0.9, 11, align=(Align.CENTER, Align.CENTER, Align.MIN))
            + Pos(x, y, pad_z-8)*Cone(2.5, 0, 6, align=(Align.CENTER, Align.CENTER, Align.MIN)))


def mechanism(model, revision):
    p = model["buttons"]["reset"]["params"]  # Preserved cartridge-local coordinates.
    transform = model["mount_transform"]
    section = transform*box(150, 120, 60, -25, p["housing_y"]-60)
    contact_cut = transform*box(9.2, 12, 40, p["tip_x"], p["tip_y"]+6)
    parts, hw = model["assembly"], model["hardware"]
    shapes = {
        "guide_and_keeper_sections": compound(parts[n] & section for n in
            ("reset_frame", "reset_rear_keeper", "reset_moving_magnet_keeper")),
        "moving_paddle_section": (parts["reset_slider"] & section)-contact_cut,
        "fixed_magnet": hw["reset_fixed_magnet"],
        "moving_magnet": hw["reset_moving_magnet"],
        "nylon_contact_screw_and_jam_nut": compound(v for k, v in hw.items() if k.startswith("reset_nylon")),
        "M3x5_heatset_insert": hw["reset_contact_heatset_insert"],
        "provisional_switch_body": transform*box(6, 6, 1.2, p["tip_x"], p["tip_y"], p["switch_top_z"]-2),
        "provisional_switch_button": transform*box(2.8, 2.8, .8, p["tip_x"], p["tip_y"], p["switch_top_z"]-.8),
    }
    preview.PALETTE = ["#657181", "#55aaba", "#bb6c5c", "#e2a750", "#c1c6c9", "#c39745", "#474d56", "#9babc0"]
    preview.render(shapes, revision/"button-mechanism.png",
                   title="Button section / mounted orientation",
                   subtitle="Press the lower paddle upward · M3 × 5 mm heat-set contact · magnet return",
                   elevation=-18, azimuth=-145)


def lid_joint(model, revision):
    info = model["measurements"]["lid_fasteners"]
    x, y = info["centers_local_xy_mm"][0]
    rim = info["post_rim_local_z_mm"]
    # Actual local solids, cut through the fastener axis. No illustrative shell.
    half = box(14, 7, 18, x, y+3.5, rim-9)
    shapes = {
        # Display the post after the insert displaces polymer. Remove only the
        # simplified insert envelope to avoid overlapping cut-face pixels;
        # printed source and exports retain their undersized Ø4 pilot.
        "body_post_section": (model["case_local_assembly"]["body"] & half)
                             - model["lid_hardware_local"]["lid_insert_1"],
        "revised_lid_section": model["case_local_assembly"]["lid"] & half,
        "M3x5_insert_section": model["lid_hardware_local"]["lid_insert_1"] & half,
        "M3x8_lid_screw": model["lid_hardware_local"]["lid_screw_1"],
    }
    preview.PALETTE = ["#59606e", "#9aa5b5", "#c39745", "#bac5cd"]
    preview.render(shapes, revision/"lid-joint.png",
                   title="Lid joint / M3 × 5 heat-set insert",
                   subtitle="Revision 008 · four joints · M3 × 8 screws · Ø4 × 6 mm blind pilots · simplified hardware",
                   elevation=15, azimuth=-75)


def pcb_joint(model, revision):
    info = model["measurements"]["pcb_fasteners"]
    name = "pcb_clamp_right_front"
    x, y = info["centers_local_xy_mm"][2]
    half = box(14, 6, 17, x, y+3, 0)
    hardware = model["pcb_hardware_local"]
    insert = hardware[name+"_insert"]
    # Section the exported source solids. Display the post after local polymer
    # displacement by the hardware envelope; no change to the printable pilot.
    parts = {
        "body_post_section": (model["case_local_assembly"]["body"] & half)-insert,
        "PCB_clamp_section": model["case_local_assembly"][name] & half,
        "M3x5_insert_section": insert & half,
        "M3x6_clamp_screw": hardware[name+"_screw"],
    }
    board_edge = x-model["measurements"]["pcb_fasteners"]["screw_hole_outward_shift_from_006_mm"]-4.5
    bottom = info["board_bottom_local_z_mm"]
    thickness = info["board_top_local_z_mm"]-bottom
    parts["bare_PCB_edge_reference"] = box(4, 6, thickness, board_edge-2, y+3, bottom) & half
    preview.PALETTE = ["#59606e", "#9aa5b5", "#c39745", "#bac5cd", "#4d9c88"]
    preview.render(parts, revision/"pcb-joint.png",
                   title="PCB clamp / M3 × 5 heat-set insert",
                   subtitle="Revision 008 · M3 × 6 screw · lower nut entry filled · thin board-edge slot retained",
                   elevation=12, azimuth=-80)


def corner_detail(model, revision):
    info = model["measurements"]["corner_bosses"]
    x, y = model["measurements"]["lid_fasteners"]["centers_local_xy_mm"][-1]
    h = info["pad_top_local_z_mm"]
    # Actual body crop includes the floor, both walls, and the entire support.
    crop = box(16, 16, h+.1, x-1.7, y-1.7, 0)
    feature = model["corner_supports_local"]["corner_right_rear"] & crop
    current = model["case_local_assembly"]["body"] & crop
    old = model["reference_full_height_body_local"] & crop
    shell = current-feature
    preview.PALETTE = ["#66717e", "#55aaba"]
    preview.render({"shell_corner_section":shell, "short_corner_mount":feature},
                   revision/"corner-boss.png",
                   title="Corner lid mount / short wall supports",
                   subtitle="Revision 008 · 8 mm upper pad · 45° undersides · closed corner gap · open space below",
                   elevation=15, azimuth=-135)
    # Shift along the camera's horizontal axis to compare equal-scale CAD crops.
    left = Pos(-x, -y, 0)
    right = Pos(-x+24, -y-24, 0)
    preview.PALETTE = ["#949ca6", "#66717e", "#55aaba"]
    preview.render({"revision_007_full_height_post":left*old,
                    "revision_008_shell_corner":right*shell,
                    "revision_008_short_mount":right*feature},
                   revision/"corner-comparison.png",
                   title="Corner mounts / revision 007 → 008",
                   subtitle=f"Same-scale CAD sections · body solid volume reduced {info['body_volume_saved_percent']:.2f}% · print time not estimated",
                   elevation=15, azimuth=-135)


def replacement_set(model, revision):
    parts = {n: s for n, s in model["parts"].items()
             if n in ("body", "lid")}
    assert len(parts) == 2
    layout = print_layout(parts)
    path = revision/"replacement-parts.3mf"
    export_mesh(layout, path)
    report = mesh_inspect(path)
    assert report["instance_count"] == 2
    actual = sorted(load_mesh_instances(path), key=lambda entry: entry[1].bounds[0].tolist())
    expected = sorted(layout.items(), key=lambda entry: list(entry[1].bounding_box().min))
    for (node, mesh), (name, solid) in zip(actual, expected):
        bounds = [list(solid.bounding_box().min), list(solid.bounding_box().max)]
        assert mesh.is_volume and len(mesh.split()) == 1, name
        assert np.allclose(mesh.bounds, bounds, atol=.05, rtol=0), name
        assert math.isclose(mesh.volume, solid.volume, rel_tol=.005), name
    report.update(status="passed", printed_parts=list(parts),
                  physical_fit_tested=False, slicer_profile_applied=False,
                  note="Body and matching lid only; other thirteen revision007 parts are reusable.")
    (revision/"replacement-validation.json").write_text(json.dumps(report, indent=2)+"\n")
    preview.PALETTE = ["#59606e", "#9aa5b5"]
    preview.render(layout, revision/"replacement-parts.png",
                   title="Revision 008 / body and lid",
                   subtitle="Short corner mounts · matching lid locating lip · M3 × 5 inserts and M3 × 8 lid screws",
                   elevation=45, azimuth=-65)


def main():
    revision = Path(sys.argv[1]).resolve()
    model = load_model(revision/"model.py", json.loads((revision/"parameters.json").read_text()))
    parts = model["assembly"]
    show(group(parts), revision/"preview.png", "ESP32 / compact corner lid mounts",
         "Revision 008 · short lid mounts with sloped supports · closed corner gaps · EN/RESET in blue · BOOT in amber")
    show(group(parts, bracket=False), revision/"console-buttons.png", "ESP32 / accessible button faces",
         "Mounted orientation · press upward from below · bracket omitted for visibility")
    scene = group(parts)
    scene["desk_reference"] = box(150, 125, 6, z=model["measurements"]["desk_contact_z"])
    arrows = []
    for name, info in model["buttons"].items():
        x, y, z = info["pad_world"]["at_rest_xyz_mm"]
        arrows.append(upward_arrow(x, y, z))
    scene["press_upward"] = compound(arrows)
    show(scene, revision/"under-desk.png", "Under-desk access / press upward",
         "Brown plane = desk underside · green arrows = finger motion · reference objects are not printable",
         elevation=-18, azimuth=-145)
    show(group(parts, lid=False, bracket=False), revision/"interior.png", "ESP32 / inverted internal assembly",
         "Lid removed · short corner bosses replace the tall posts · PCB clamps retained", elevation=-48)
    exploded = {name: (Pos(0, 0, -24)*shape if name == "lid" else
                      Pos(0, 0, 30)*shape if name == "desk_bracket" else shape)
                for name, shape in parts.items()}
    show(group(exploded), revision/"exploded.png", "ESP32 / revised desk mounting",
         "Lid moved down and bracket moved up for illustration · electronics remain captured", elevation=-25)
    show(group(print_layout(model["parts"])), revision/"print-layout.png", "ESP32 / 15 printable parts",
         "Reprint the body and lid · reuse the other thirteen parts from revision 007",
         elevation=52, azimuth=-65)
    corner_detail(model, revision)
    pcb_joint(model, revision)
    replacement_set(model, revision)
    lid_joint(model, revision)
    mechanism(model, revision)
    export_step(compound(model["hardware"].values()), revision/"hardware-reference.step")


if __name__ == "__main__":
    main()
