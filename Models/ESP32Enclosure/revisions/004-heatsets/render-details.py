"""Render actual printable geometry and a labeled cartridge section.

Run with a frozen revision directory. Hardware is excluded from print exports.
"""
from pathlib import Path
import json
import sys

from fdm_cad.build import load_model, print_layout
from fdm_cad import preview
from build123d import Align, Box, Compound, Pos, export_step


def compound(items):
    return Compound(children=list(items))


def group(parts, include_lid=True, include_bracket=True):
    grouped = {"body": parts["body"]}
    if include_lid:
        grouped["lid"] = parts["lid"]
    if include_bracket:
        grouped["desk_bracket"] = parts["desk_bracket"]
    grouped["cartridge_frames_and_keepers"] = compound(
        v for k,v in parts.items() if k.startswith(("reset_", "boot_")) and not k.endswith("_slider"))
    grouped["EN_RESET_paddle"] = parts["reset_slider"]
    grouped["BOOT_paddle"] = parts["boot_slider"]
    clamps = [v for k,v in parts.items() if k.startswith("pcb_clamp_")]
    if clamps:
        grouped["PCB_clamps"] = compound(clamps)
    return grouped


def palette(parts):
    colors = {"body":"#59606e", "lid":"#9aa5b5", "desk_bracket":"#454c56",
              "cartridge_frames_and_keepers":"#49505b", "EN_RESET_paddle":"#55aaba",
              "BOOT_paddle":"#e2a750", "PCB_clamps":"#6c91a1"}
    preview.PALETTE = [colors.get(k,"#85939f") for k in parts]


def show(parts, path, title, subtitle, elevation=28, azimuth=-145):
    palette(parts)
    preview.render(parts, path, title=title, subtitle=subtitle, elevation=elevation, azimuth=azimuth)


def mechanism(model, revision):
    info = model["buttons"]["reset"]
    p = info["params"]
    center_y = p["housing_y"]
    section = Pos(-25, center_y-60, 0)*Box(150, 120, 60,
              align=(Align.CENTER, Align.CENTER, Align.MIN))
    parts = model["assembly"]
    hw = model["hardware"]
    # A second local section exposes the insert at the offset contact boss.
    # This cut is illustrative only; printable solids retain the complete boss.
    contact_cut = Pos(p["tip_x"], p["tip_y"]+6, 0)*Box(9.2, 12, 40,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))
    shapes = {
        "guide_and_keeper_sections": compound((parts["reset_frame"] & section,
                                               parts["reset_rear_keeper"] & section,
                                               parts["reset_moving_magnet_keeper"] & section)),
        "moving_paddle_section": (parts["reset_slider"] & section) - contact_cut,
        "fixed_magnet": hw["reset_fixed_magnet"],
        "moving_magnet": hw["reset_moving_magnet"],
        "nylon_contact_screw_and_jam_nut": compound(v for k,v in hw.items() if k.startswith("reset_nylon")),
        "M3x5_heatset_insert": hw["reset_contact_heatset_insert"],
    }
    z = p["switch_top_z"]
    shapes["provisional_switch_body"] = Pos(p["tip_x"],p["tip_y"],z-2.0)*Box(
        6,6,1.2,align=(Align.CENTER,Align.CENTER,Align.MIN))
    shapes["provisional_switch_button"] = Pos(p["tip_x"],p["tip_y"],z-.8)*Box(
        2.8,2.8,.8,align=(Align.CENTER,Align.CENTER,Align.MIN))
    preview.PALETTE = ["#657181", "#55aaba", "#bb6c5c", "#e2a750", "#c1c6c9", "#c39745", "#474d56", "#9babc0"]
    preview.render(shapes, revision/"button-mechanism.png", title="External button / magnetic return section",
                   subtitle=f"M3 × {p['contact_insert_length']:g} mm heat-set insert · {p['stroke']:g} mm travel · switch position and return force unverified",
                   elevation=18, azimuth=145)


def main():
    revision = Path(sys.argv[1]).resolve()
    model = load_model(revision/"model.py",json.loads((revision/"parameters.json").read_text()))
    parts = model["assembly"]
    show(group(parts, include_bracket=False), revision/"console-buttons.png",
         "ESP32 / heat-set button enclosure",
         "Revision 004 · EN/RESET in blue · BOOT in amber · bracket omitted for visibility")
    show(group(parts), revision/"preview.png", "ESP32 / external buttons and desk bracket",
         "All 15 printed parts assembled · magnet-return cartridges · provisional button alignment")
    show(group(parts), revision/"under-desk.png", "ESP32 / button access while mounted",
         "View from below desk · reach the exposed pads from the side and press toward the enclosure floor",
         elevation=-14,azimuth=-145)
    show(group(parts,include_lid=False,include_bracket=False), revision/"interior.png",
         "ESP32 / actuator arms and board retention",
         "Arms reach over clamp hardware · nylon contact screws and real electronics omitted",
         elevation=52,azimuth=-145)
    exploded = {name: (Pos(0,0,24)*shape if name == "lid" else
                      Pos(0,0,48)*shape if name == "desk_bracket" else shape)
                for name,shape in parts.items()}
    show(group(exploded), revision/"exploded.png", "ESP32 / external-button enclosure assembly",
         "Lid and bracket lifted for illustration · envelope below describes this exploded view", elevation=30)
    show(group(print_layout(model["parts"])), revision/"print-layout.png",
         "ESP32 / 15 individually printable parts",
         "Geometry layout only · inspect local supports for cartridge sliders in your slicer", elevation=52,azimuth=-65)
    mechanism(model,revision)
    export_step(compound(model["hardware"].values()), revision/"hardware-reference.step")


if __name__ == "__main__":
    main()
