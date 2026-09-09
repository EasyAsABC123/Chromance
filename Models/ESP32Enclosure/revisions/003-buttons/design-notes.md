# Console enclosure with external buttons — revision 003

Revision 003 retains the user's approved console styling and adds two removable
magnetic-return cartridges for EN/RESET and BOOT. Original revision 001 and
approved revision 002, including their ZIP archives, remain unchanged.

The complete printed assembly remains **116.8 × 95.2 × 43.2 mm**. It comprises
15 printable parts: the body, lid, desk bracket, four PCB clamps and four parts
for each button cartridge. The blue/amber render colors distinguish the paddles;
they do not assign filament or imply illuminated buttons.

## Operation and alignment

Reach the exposed paddle from the side under the desk and press toward the
enclosure floor. The paddle and rigid contact arm move down together. Two captive
4 × 2 mm magnets face like poles toward one another; a rectangular guide prevents
lateral movement. Front/shoulder stops limit downward travel; the rear keeper
captures the slider lug and provides the upper stop.

Default paddle travel is 0.8 mm with 0.6 mm idle gap above the provisional switch,
leaving 0.2 mm modeled switch depression. These are CAD settings, not the travel
or force rating of the unidentified switch. Measure the switch and set the tip
and stop so it fully releases at rest and cannot be overpressed.

Button centers are photo estimates: X=-23 mm, EN Y=0 and BOOT Y=-17 mm relative to
the 52 × 70 mm perfboard center. Switch top Z=16 mm is a provisional mechanism
layout, with the perfboard top at Z=10 mm. The original conservative PCB/wiring
clearances and separate external PSU assumption remain in force.

XY positions, switch height, guide clearance, stroke and nylon contact-screw
length are parameters. Default M3×10 contact screws have only 0.2 mm downward
adjustment before the head meets the jam nut. A lower switch can use a longer
nylon screw: the checked example uses switch top Z=15 mm and M3×12, with its head
below the lid. The model rejects nylon hardware that collides with the lid or
PCB clamps. Confirm actual screw/head dimensions and full nut engagement.

Housing centers are offset to Y=+4 and -21 mm. Their 11 mm gap reserves USB access
below the moving arms; the default arm bottom at full press is Z=18.4 mm. Actual
plug bodies, bend space, solder joints and wires are not captured by the photos
accurately enough to declare physical clearance.

## Additional hardware

The original shell hardware remains 8 M3×10 screws, 4 M3×8 screws, 12 M3 hex nuts
and four desk screws chosen for the actual desk.

| New item | Quantity | Model assumption |
| --- | ---: | --- |
| Axially magnetized disc magnets | 4 | Ø4 × 2 mm; grade/return force to be tested |
| M3 socket screws | 4 | 18 mm under-head length, head Ø≤5.5 mm, no washer |
| Short M3 heat-set inserts | 4 | 4 mm long, nominal outside diameter 4.6 mm |
| Nylon M3 contact screws | 2 | Default 10 mm; parameter supports 8/10/12 mm |
| Nylon M3 nuts | 4 | One captive nut and one jam nut per contact |

Cartridge screws grip 14.2 mm of plastic before entering the inserts by 3.8 mm.
The blind insert holes are provisionally Ø4.0 × 4.4 mm, leaving 1.6 mm of material
before the cavity. Confirm the insert pilot with its drawing and a fit coupon;
an insert's knurled outside diameter is not its pilot diameter. The
[Ruthex short M3 insert](https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck)
is the reference for the 4 mm length.

## Assembly and service

1. Install heat-set inserts while the body is empty. Fit PCB retention hardware
   and board before attaching the button cartridges.
2. With each rear keeper removed, feed the fixed magnet into the frame's rear
   pocket. Load the moving magnet and its small rectangular keeper into the slider.
3. Drop the slider into the open-top guide from above in its final XY position.
   Fit the nylon contact hardware with the assembly accessible.
4. Fit the rear keeper and bolt the cartridge to the body with two M3×18 screws.
   The keeper closes the fixed magnet pocket and captures the moving magnet
   keeper and slider lug. Neither magnet relies on adhesive or a snap fit.
5. Calibrate the nylon contact against the measured switch and lock the jam nut.
   Check full release, travel stops and repeated return before fitting the lid.
6. Fit the lid and bolt the housing to the desk bracket. For later PCB-clamp
   service, remove the obstructing cartridge first; BOOT's arm crosses the
   left-front clamp's screwdriver path. Remove the housing for contact adjustment.

## FDM and magnetic considerations

Unfilled PETG remains the provisional material candidate. Print the body
floor-down, lid exterior-down and bracket desk-contact-face down. Cartridge
frames and rear keepers print on their outer sides; their stepped slider arms
need local removable supports in the supplied orientation. Keep support scars
away from guide and magnet seats. The small magnet keepers print flat.
Check guide fit and insert pilots on coupons before committing the enclosure.

The magnets have 3.6 mm nominal face separation at rest and 2.8 mm at the default
stop. Their grade and the printed guide friction determine whether return is
reliable; this has not been measured. Mechanical guidance is needed because
repelling magnets tend to move out of alignment. [K&J Magnetics](https://www.kjmagnetics.com/blog/repelling-magnets)

New magnets sit outside the USB/button side, opposite the antenna pictured on the
ESP32. Espressif recommends at least 15 mm antenna clearance in the product and
testing the finished enclosure's radio range and throughput. This model does
not establish RF compatibility or validate the existing antenna/perfboard layout.
[Espressif hardware guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html)

## Rebuild and files

Run from the workbench root, using a fresh output directory:

```bash
uv run --locked python models/esp32-desk-enclosure/styles/console-buttons/build-revision.py \
  --output models/esp32-desk-enclosure/revisions/004-buttons
uv run --locked python models/esp32-desk-enclosure/revisions/004-buttons/render-details.py \
  models/esp32-desk-enclosure/revisions/004-buttons
freecad-python scripts/check-freecad.py models/esp32-desk-enclosure/revisions/004-buttons
```

The builder freezes `model.py`, `button_module.py`, `mounting.py`, rendering/build
helpers and parameters, then records their SHA256 hashes. Preserve all of them
together. Editable STEP solids open in Fusion; Python remains the parametric
master and is not converted to a Fusion feature timeline.

`assembly.step` contains the 15 printed solids. `hardware-reference.step` contains
the cartridge magnets, mounting screws and nylon contact hardware at the
corresponding positions, without threads; original shell hardware is omitted.
Neither that hardware nor the illustrative switch in the cutaway is included in
`print-layout.3mf`. The 3MF is model geometry without a tested slicer profile.

Digital geometry and motion checks do not establish physical fit, mounting
strength, switch life, heat behavior or magnetic return. No physical printing
has been performed.

Retained verification scripts:

```bash
uv run --locked python models/esp32-desk-enclosure/styles/console-buttons/check-cartridges.py
uv run --locked python models/esp32-desk-enclosure/styles/console-buttons/check-integration.py \
  --model-dir models/esp32-desk-enclosure/styles/console-buttons \
  --baseline models/esp32-desk-enclosure/revisions/002-console/model.py \
  --preserved-root . --output /tmp/button-integration-review.json
```

Final validation passed STEP/3MF read-back, FreeCAD reopening, 18 cartridge motion
states, 54 top-loading poses and 768 independent integration checks across four
configurations. The actual rendered geometry was visually inspected. These
checks include positive stops, magnet retention, assembly paths, hardware access,
a larger board, changed stroke/guide clearance and lower switches with longer
contact screws. Report files are retained in the revision directory.
