# Revision 013 — measured button alignment

The two revised sliders put the contact tips at the measured ESP32 switch
centers. RESET is **30 mm from the bottom board edge**, BOOT is **16 mm**, and
both are **3.3 mm from the left edge**. The earlier 17 mm tip separation is
now **14 mm**.

**[Print only the two replacement sliders first](../../fit-tests/008-button-alignment/sliders-only.3mf)**.
Use the [fit checklist](../../fit-tests/008-button-alignment/README.md) and
[illustrated button assembly guide](../../assembly-guides/013-buttons/README.md).
The body and other twelve printed pieces are unchanged from revision 012.
For a fresh test setup, the [complete open jig](../../fit-tests/008-button-alignment/print-layout.3mf)
includes the actual board-registration frame, four clamps and both cartridges.

![Measured button axes and actual slider geometry](../../assembly-guides/013-buttons/04-button-alignment.png)

| Feature | Revision 012 | Revision 013 |
| --- | --- | --- |
| RESET center from bottom | 35 mm | **30 mm** |
| BOOT center from bottom | 18 mm | **16 mm** |
| Both centers from left edge | 3 mm | **3.3 mm** |
| Tip center separation | 17 mm | **14 mm** |
| Exterior housing centers, local Y | 4 / −21 mm | **Unchanged** |
| Overall enclosure | 114.3 × 95.2 × 39.6 mm | **Unchanged** |

The local PCB edges are X±24.5 and Y±35. The new tip axes are therefore
RESET **(−21.2, −5)** and BOOT **(−21.2, −19)**. These assume the PCB is
centered. The locating gap allows ±0.65 mm sideways and ±0.4 mm lengthwise
movement; verify alignment throughout the available board movement.

## What changed

Each arm exits its guide as a straight tongue before bending inward toward the
switch. This keeps the existing body mounting pads, frame, magnets and stops
while accommodating the larger RESET offset. The low contact collars have
flats facing each other, preserving a 1.2 mm ligament beside the M3 through-hole
and an 8.2 mm gap between those flats. The full insert bosses remain intact.

Only **reset_slider** and **boot_slider** need reprinting when upgrading from
012. Reuse its body, lid, desk bracket, four PCB clamps, two frames, two rear
keepers and two tiny moving-magnet keepers. Hardware is unchanged. Each slider
takes an M3×5 contact insert and nylon M3×12 adjuster with a nylon jam nut.
The exterior body pads still take **short M3×4 inserts**, with two M3×18 screws
per cartridge; do not substitute 5 mm inserts into their 4.4 mm blind pilots.

- [RESET slider 3MF](parts/reset_slider.3mf) and [BOOT slider 3MF](parts/boot_slider.3mf).
- [All individual STEP/3MF parts](parts/) and [full print layout](print-layout.3mf).
- [Assembly STEP](assembly.step) for Fusion 360 or FreeCAD.
- Editable [model](model.py), [parameters](parameters.json) and adjacent modules.
- [Interior](interior.png), [mounted view](under-desk.png), [exploded view](exploded.png).

## Assembly and fit limits

Install inserts before magnets/electronics. Fit the board, clamps and USB plug
before the cartridges. The BOOT arm obstructs its adjacent PCB clamp driver
path, and the retained exterior cartridge can obstruct straight USB plug
insertion. The actual jack, plug and cable remain unmeasured. The new contact
spacing does not preserve the earlier 11 mm straight inner USB corridor.

The checker distinguishes a small **8 × 6 mm inboard plug envelope** from a
**3.5 mm cable envelope** passing between the exterior housings. These are
provisional clearance probes, not measured connector dimensions. The 8 × 6 mm
plug box **intersects the left-front PCB clamp screw head by 18.858 mm³**;
a broad straight plug approach is also blocked by the exterior cartridge.
Installing the plug before the cartridge only addresses the latter. Check
actual connector dimensions and fit; a clamp or connector-access revision may
be needed. Test the real cable with both buttons through their full travel.

Set nylon tips to release both switches at rest and actuate them before the
printed stops limit movement. The assumed 0.8 mm slider stroke and 0.2 mm
switch depression do not establish the actual switch travel. Recheck the lid:
nominal head clearance is only 0.4 mm before adjustment. Follow the assembly
guide for magnet polarity and keeper order; final return force is untested.

Sliders retain their production print orientation, with finger-pad faces toward
the bed. Use local removable support beneath the stepped arms and keep guide,
magnet and insert surfaces clean. Use the intended final material/settings for
the quick test. PETG remains the initial candidate; no printer/material profile,
print-time estimate or strength rating is supplied in these geometry 3MFs.

Board retention and the concave cable cradle retain revision 012 geometry.
[Board test 007](../../fit-tests/007-board-easier-fit/README.md) and
[cable test 006](../../fit-tests/006-cable-cradle/README.md) remain representative.

See [rebuild and validation details](design-notes.md), [export checks](validation.json),
[independent FreeCAD reopening](freecad-validation.json), and
[mechanism checks](mechanism-validation.json). Digital validation implements
and checks the measured coordinates; physical fit remains pending.
