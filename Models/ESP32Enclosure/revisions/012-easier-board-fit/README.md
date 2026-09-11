# Revision 012 — easier PCB fit and deeper shelves

This revision adds **0.5 mm total width** to the enclosure and **0.5 mm more
coverage beneath each perfboard edge**. Matching upper clamps receive the same
deeper coverage. The actual PCB remains the measured **49 × 70 × 1 mm**; the new
`board_fit_width_extra` parameter records fit allowance separately.

**[Print test 007 first — five-part 3MF](../../fit-tests/007-board-easier-fit/print-layout.3mf)**,
with [fit instructions](../../fit-tests/007-board-easier-fit/README.md). Its low
open frame and four clamps use the exact full-model shelf/shoulder/fastener
geometry. Physical results for this revision are pending.

| Dimension | Revision 011 | Revision 012 |
| --- | --- | --- |
| Main shell width, excluding belt/ears | 69.8 mm | **70.3 mm** |
| Main cavity width | 65 mm | **65.5 mm** |
| Overall printed assembly width | 113.8 mm | **114.3 mm** |
| Overall length × height | 95.2 × 39.6 mm | **95.2 × 39.6 mm** |
| Gap between locating shoulders | 49.8 mm | **50.3 mm** |
| Centered clearance at each PCB side | 0.4 mm | **0.65 mm** |
| Shelf/clamp coverage under/over each centered PCB edge | 0.8 mm | **1.3 mm** |
| Gap between inner shelf faces | 47.4 mm | **46.4 mm** |
| Minimum edge coverage at a lateral stop | 0.4 mm | **0.65 mm** |
| Vertical capture slot | 1.2 mm | **1.2 mm** |

The deeper shelf means horizontal coverage under the board, not a taller slot.
Both upper and lower contact strips must land on bare PCB, clear of solder,
traces and components. The new test checks this with the actual assembly.
Board bottom/top stay at local Z9/Z10 and the 6.6 mm underside allowance remains
a placement choice. The 52 mm populated ESP32 span is separate from substrate size.

## Matching parts

Use the revision 012 **body, lid, desk bracket, four PCB clamps and two sliders**.
The six other cartridge frame/keeper pieces match revision 011 after translation
and can be reused. Shelf/clamp outer faces and fastener centers move outward
0.25 mm on each side. Their inner faces extend 0.5 mm under the centered board,
so the clamp pieces become 0.75 mm wider in total.

The slider arms also change: the guides follow the outward-moving wall while
contact tips keep their X position relative to the actual board. The measured
button Y spacing and 3.3 mm edge inset still require a separate actuator layout;
this revision does not establish physical switch alignment.

The desk mounting pattern grows by 0.5 mm overall. Check the new bracket's hole
locations before attaching it. All fastener sizes, blind depths and engagements
remain unchanged; no captive-nut pockets are added.

- [Body 3MF](parts/body.3mf), [lid 3MF](parts/lid.3mf),
  [desk bracket 3MF](parts/desk_bracket.3mf).
- [All individual STEP/3MF parts](parts/) and [full print-layout 3MF](print-layout.3mf).
- [Assembly STEP](assembly.step) for Fusion 360 or FreeCAD; the editable master
  is [Python source](model.py), [parameters](parameters.json) and adjacent modules.
- [Interior](interior.png), [under-desk view](under-desk.png), [exploded view](exploded.png).

## Cable and printing

The concave Ø8.4 mm cradle for the measured 8 mm cable is unchanged.
**[Cable test 006 remains usable](../../fit-tests/006-cable-cradle/README.md)**:
its actual body/lid STEP crop matches this revision. No replacement cable coupon
is needed. Zip-tie size, groove clearance and actual retention remain provisional.

Print body floor-down, lid exterior-down, bracket desk-contact-face down and PCB
clamps flat. Sliders keep their existing print orientation with local removable
support beneath stepped arms. Start with supports off for cradle and corner ribs;
inspect ramps and short bridges in the slicer. No supports are modeled. Unfilled
PETG remains the initial material candidate; use intended final settings for the
coupon. These model 3MFs carry millimeter geometry without verified printer,
material or process profiles; no print time or load rating is assigned.

Retain four M3×5 inserts/M3×6 screws for PCB clamps; four M3×5/M3×8 for the lid;
four M3×5/M3×10 for bracket attachment; two M3×5 inserts with nylon M3×12 adjusters
and exposed jam nuts; and four M3×4/M3×18 cartridge joints. Insert OD4.6/pilot4.0 mm
are provisional until checked with your hardware. The PCB insert-tool path still
needs 21.8 mm of narrow reach with a modeled Ø6 mm shaft and 0.1 mm wall clearance.
Test 007 cannot check that full-height reach. Install inserts before board and
cartridges; remove BOOT for later left-front clamp service.

See [design and rebuild notes](design-notes.md), [export checks](validation.json),
[FreeCAD checks](freecad-validation.json), [retention and coupon checks](fit-validation.json)
and [mechanism/cable checks](mechanism-validation.json). Digital checks do not
establish physical fit, switch alignment, material behavior or mounting strength.
