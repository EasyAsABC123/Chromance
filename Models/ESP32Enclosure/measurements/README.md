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

The archived 52 mm retention has inner ledge faces at X ±25.2. It therefore leaves
0.7 mm gaps to the corrected substrate edges and cannot capture the centered board.
The existing 68 mm-wide main cavity can still reserve the 52 mm populated span;
shrinking the outer case is unnecessary for this retention correction.

The measured button spacing also needs a later actuator layout change: the current
4 mm housing offsets produce only 22 mm housing separation, below the 24 mm guard,
and place BOOT too close to a mounting gusset. Those guards must remain in place
until a revised mechanism is modeled and checked. The board-fit coupon omits the
actuators and cannot validate their positions or travel.

## Cable at the end opening

[2026-09-11-cable.json](2026-09-11-cable.json) records the user's **8 mm outside
diameter** measurement. Revision 010 and fit test 004 use this value for the cable
reference and lid-clearance check. The tie's width, thickness and head dimensions
remain provisional; physical retention and bend clearance have not been tested.

The existing revision 009 support can accommodate this cable in the model. The
new measurement changes the clearance assessment without requiring a different
printed support. The legacy `cable_diameter_provisional` input name is retained
for compatibility; its default value is now the user-supplied 8 mm measurement.
