"""Render revision006 and a section through its lid heat-set joint.

Desk, direction arrows, hardware and switch proxies are illustration only.
"""
from pathlib import Path
import json
import sys

from fdm_cad.build import load_model, print_layout
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
        "existing_lid_section": model["case_local_assembly"]["lid"] & half,
        "M3x5_insert_section": model["lid_hardware_local"]["lid_insert_1"] & half,
        "M3x8_lid_screw": model["lid_hardware_local"]["lid_screw_1"],
    }
    preview.PALETTE = ["#59606e", "#9aa5b5", "#c39745", "#bac5cd"]
    preview.render(shapes, revision/"lid-joint.png",
                   title="Lid joint / M3 × 5 heat-set insert",
                   subtitle="Revision 006 · four joints · M3 × 8 screws · Ø4 × 6 mm blind pilots · simplified hardware",
                   elevation=15, azimuth=-75)


def main():
    revision = Path(sys.argv[1]).resolve()
    model = load_model(revision/"model.py", json.loads((revision/"parameters.json").read_text()))
    parts = model["assembly"]
    show(group(parts), revision/"preview.png", "ESP32 / downward-facing buttons",
         "Revision 006 · lid uses M3 × 5 heat-set inserts · EN/RESET in blue · BOOT in amber")
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
         "Lid removed downward · four round blind insert bores replace the lid nut slots", elevation=-48)
    exploded = {name: (Pos(0, 0, -24)*shape if name == "lid" else
                      Pos(0, 0, 30)*shape if name == "desk_bracket" else shape)
                for name, shape in parts.items()}
    show(group(exploded), revision/"exploded.png", "ESP32 / revised desk mounting",
         "Lid moved down and bracket moved up for illustration · electronics remain captured", elevation=-25)
    show(group(print_layout(model["parts"])), revision/"print-layout.png", "ESP32 / 15 printable parts",
         "Only the body changes from revision 005 · reuse the lid and other 13 parts",
         elevation=52, azimuth=-65)
    lid_joint(model, revision)
    mechanism(model, revision)
    export_step(compound(model["hardware"].values()), revision/"hardware-reference.step")


if __name__ == "__main__":
    main()
