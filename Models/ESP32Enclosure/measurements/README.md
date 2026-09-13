# Board and cable measurements

[2026-09-10-board.json](2026-09-10-board.json) transcribes the user's dimensioned
sketch and follow-up answers. The numeric record is self-contained; the original
photo is not a build dependency. Its SHA256 identifies the source attachment.

The user printed and test-fitted the first coupon and reported a dimensional
mismatch. No measured dimensions of the printed tray were supplied, so printer
compensation has not been inferred from that report.

| Feature | Supplied measurement |
| --- | --- |
| Perfboard substrate | **49 × 70 × 1 mm** |
| ESP32 width/span | **52 mm**, separate from the substrate width |
| Upper button center | **3.3 mm from left, 30 mm from bottom** |
| Lower button center | **3.3 mm from left, 16 mm from bottom** |
| Button spacing | **14 mm** |

The user confirmed the button dimensions describe centers, and that the side-view
1 mm label is PCB thickness. The side-view 12 mm label is retained as an observation;
its endpoints do not establish an actual switch-top height or underside protrusion.
The exact division of ESP32 overhang between the two PCB edges is still unmeasured.

The PCB mounting holes are too small for the proposed direct screws, so that
approach was abandoned. Updated retention uses edge clamps with **M3×5 heat-set
inserts in the tray**, keeping the screws outside the PCB. No hole enlargement is
assumed. Insert outside diameter and pilot fit remain dependent on the actual hardware.

For a PCB centered in the cavity, its edges are X ±24.5 and Y ±35. Button centers
then map to X−21.2, Y−5 and Y−19 in the case's printing coordinates. This centering
is a design placement; it is not an additional measurement from the sketch.

Revision 011 integrates the 49 × 70 × 1 mm substrate into the full enclosure.
The user reported the locking shelves 3 mm too far apart and explicitly requested
**3 mm total reduction of the full enclosure width**; see
[the physical-feedback record](2026-09-11-retention-fit.json). The source print
was not identified and no absolute printed gap was measured, so printer
compensation has not been inferred.

The shell width reduces from 72.8 to 69.8 mm and the cavity from 68 to 65 mm.
Each retention side moves inward 1.5 mm, giving a 49.8 mm locating gap and 47.4 mm
inner ledge gap. The PCB top stays Z10, with the 1 mm substrate bottom at Z9 and
a 1.2 mm capture slot. The chosen 6.6 mm underside allowance preserves the top
datum and overall height; it is not a measured solder protrusion. New
[test 005](../fit-tests/005-board-width/README.md) checks the revised retention
using exact full-model geometry. The 52 mm populated span still needs physical
clearance checks at the clamp locations.

The old coupled 4 mm housing offsets could not directly accept the measured
button spacing: they produced only 22 mm housing separation and placed BOOT too
close to a mounting gusset. Revision 013 resolves this with independent housing
positions and dogleg arms; the housing-separation and gusset guards remain.
The board-only coupons omit the actuators and cannot validate their travel.

## Cable at the end opening

[2026-09-11-cable.json](2026-09-11-cable.json) records the user's **8 mm outside
diameter** measurement. Revision 010 and fit test 004 use this value for the cable
reference and lid-clearance check. The tie's width, thickness and head dimensions
remain provisional; physical retention and bend clearance have not been tested.

The existing revision 009 support can accommodate this cable in the model. The
new measurement changes the clearance assessment without requiring a different
printed support. The legacy `cable_diameter_provisional` input name is retained
for compatibility; its default value is now the user-supplied 8 mm measurement.

Revision 011 replaces the raised support with an actual **Ø8.4 mm cylindrical
cutout** in a block, as requested. The measured 8 mm cable seats in this concave
groove. Radial allowance 0.2 mm and zip-tie dimensions remain provisional. Use
[test 006](../fit-tests/006-cable-cradle/README.md) for the changed cable geometry;
old tests 003/004 represent the superseded convex support.

## Easier fit after revision 011

[2026-09-11-easier-fit.json](2026-09-11-easier-fit.json) records the request for
0.5 mm more width and 0.5 mm deeper shelves. No new measured print dimension was
supplied. Revision 012 keeps the measured 49 × 70 × 1 mm substrate and adds a
separate 0.5 mm total fit allowance: shoulder gap 50.3 mm, centered side clearance
0.65 mm. Shelves and matching upper clamps extend 0.5 mm farther under/over the
actual board edges, giving 1.3 mm centered coverage and 0.65 mm minimum after
lateral movement. The capture slot stays 1.2 mm high. Use
[test 007](../fit-tests/007-board-easier-fit/README.md) to check the new interfaces.

The deeper coverage is horizontal, not extra vertical slot height. Verify bare
PCB contact on both faces, actual solder/ESP32 overhang and retention when
inverted. Cable geometry is unchanged; test 006 remains representative.

## Measured button alignment in revision 013

[2026-09-12-button-alignment.json](2026-09-12-button-alignment.json) records the
integration of the already confirmed 30/16 mm bottom offsets and 3.3 mm left
inset. The exterior housings stay at local Y4 and Y−21 while the two revised
sliders reach X−21.2, Y−5/−19. The body and twelve other printed pieces retain
revision 012 geometry. Use [test 008](../fit-tests/008-button-alignment/README.md)
to check the two actuators with the actual board and USB plug. XY dimensions
are now implemented; physical alignment, switch height/travel, return force
and connector fit remain pending.

## Measured USB connector in revision 014

[2026-09-13-usb-connector.json](2026-09-13-usb-connector.json) preserves the raw
A–F reply and the user's height clarification. The
[measurement diagram](usb-connector-guide/README.md) uses the perfboard top as
its height datum. **The raw B=6 meant thickness**, although diagram B labels top
height: underside D=9 plus thickness 6 gives a **15 mm top height**.

| Feature | Confirmed value |
| --- | ---: |
| Maximum molded plug/strain-relief width, A | 10 mm |
| Plug thickness | 6 mm |
| Top above perfboard, normalized B | 15 mm |
| Outward projection past left edge, C | 20 mm |
| Underside above perfboard, D | 9 mm |
| USB center from board bottom, E | 23 mm |
| Flexible USB cable diameter, F | 3.5 mm |

The centered conservative outboard plug occupies case-local X−44.5…−24.5,
Y−17…−7 and Z19…25. The maximum width/thickness is applied over the whole
projection; taper and the inboard jack/metal geometry are unmeasured. Cable axis
height and bend route remain assumptions. This USB cable is separate from the
unchanged 8 mm cable in the end cradle.

[Revision 014](../revisions/014-usb-clearance/README.md) relieves both sliders and
the BOOT guide. [Quick test 009](../fit-tests/009-usb-clearance/README.md) checks the
actual plug and board positions before a full print. Centered CAD clearance
passes; board movement can consume the allowance, so physical fit is pending.
