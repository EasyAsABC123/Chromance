# Lid heat-set joints — revision 006

Four M3×5 heat-set inserts replace the lid's captive M3 nuts. The new body has
round blind pilots with continuous material around them; the former hex pockets
and side entries are absent. All fourteen other printed solids, their print
orientations and their assembly positions match revision 005. The existing lid
can be reused. Revision 005 and both archived board-fit tests are unchanged.

## Lid joint

| Feature | Nominal geometry |
| --- | --- |
| Insert | M3 thread, 5 mm long, provisional 4.6 mm outside diameter |
| Printed pilot | Ø4.0 mm, 6.0 mm deep from the open body rim |
| Body post | Ø8.8 mm; 2.1 mm radial polymer outside the insert envelope |
| Lid | Existing 2.4 mm lid with Ø3.4 mm clearance holes |
| Lid screw | M3×8 socket head, no washer; reference head Ø5.5 × 3 mm |
| Screw projection below lid | 5.6 mm |
| Nominal insert engagement | Full 5.0 mm insert length |
| Screw tip to blind bore bottom | 0.4 mm |

M3×5 specifies thread and length, not outside diameter. The insert OD and pilot
are provisional until the purchased insert and filament are checked. Adjust
`lid_insert_outer_diameter` and `lid_insert_pilot_diameter` together as needed.
The model limits the pilot and post-wall dimensions and rejects screws that
bottom. **M3×10 lid screws from revision 005 must be replaced with M3×8.** The
0.4 mm tip margin is nominal; actual screw length and insert installation depth
must also fit. Threads and knurling are omitted from the hardware proxies.

1. Print the replacement body floor-down with the insert openings upward.
   Keep the existing lid and other printed parts that fit. Inspect the slicer's
   short shell bridges; no supports are modeled for this change.
2. With the lid removed, install four inserts from the open rim. Set their ends
   flush with the rim and let them cool. Installing on the bench before fitting
   electronics gives the clearest access.
3. Seat the lid skirt and fit four M3×8 screws through the existing clearance
   holes. The lid must seat before the screws reach the bore bottoms.
4. Mounted under the desk, the lid faces downward and the screws are reached
   upward from below. Support the enclosure/electronics when servicing it.

The intended material remains unfilled PETG, pending a printed insert-fit check.
Geometry validation does not establish insert pullout strength, torque limits,
finished print fit or a load rating.

## Other fasteners and compatibility

| Joint | Revision 006 hardware |
| --- | --- |
| Lid to body — changed | 4 M3×5 heat-set inserts + 4 M3×8 socket screws |
| Body to desk bracket — unchanged | 4 M3×5 heat-set inserts + 4 M3×10 screws |
| Actuator contacts — unchanged | 2 M3×5 heat-set inserts + 2 M3×12 nylon adjusters and nylon jam nuts |
| Cartridge mounting — unchanged | 4 short M3×4 heat-set inserts; existing cartridge screws |
| PCB edge clamps — archived full-model layout | 4 M3×8 screws and 4 M3 hex nuts |
| Bracket to desk | Select screws for the actual desk material and thickness |

There are **ten M3×5 inserts plus four M3×4 inserts** in this full revision.
The separate [corrected board-fit test](../../fit-tests/002-board-fit-heatsets/)
uses four M3×5 inserts and **M3×6** clamp screws. Those clamp screws are a different
length from this revision's lid screws.

The full model retains revision 005's earlier 52 mm PCB-retention assumption and
button coordinates. Its clamps cannot retain the measured 49 mm substrate; use
the corrected fit test for that check. Integrating the measured 49 × 70 × 1 mm
board, 52 mm ESP32 span and 14 mm button spacing still needs a full actuator-layout
revision. This hardware fix does not claim that integration or a physical fit.
Button motion, magnet return, mounting geometry and support requirements for the
unchanged parts remain as documented in [revision 005](../005-downward-buttons/design-notes.md).

## Files and validation

`parts/body.3mf` is the replacement print geometry. `assembly.step` contains the
fifteen printable solids in the mounted orientation; each individual STEP/3MF is
in its print orientation. `hardware-reference.step` separately contains 26
simplified hardware proxies, including the four new inserts and four lid screws.
It is an illustration of selected hardware, not a complete hardware BOM or a
printable assembly. `lid-joint.png` sections the actual CAD post, lid and insert.

The shared build checks each solid, STEP and 3MF read-back, mesh closure, units,
print placement and printed-assembly interference. Independent FreeCAD inspection
reopens all STEP parts and the assembly. `inspection.FCStd` contains imported
geometry; editable parameters remain in Python. The Fusion helper now defaults
to this revision, but native F3D conversion still requires a run inside Fusion.

`lid-validation.json` records independent nominal and Ø4.1 mm pilot scenarios:

- All fourteen other printed parts and all eighteen existing hardware proxies
  match revision 005 in geometry and placement.
- Body changes are confined to the four lid posts. The former hex pockets,
  radial entries and deeper screw-hole portions are filled with polymer; the
  remaining voids match the new round blind bores.
- Printed solids do not intersect. All eight new hardware proxies clear the
  other printed parts and hardware, except the four explicitly allowed insert
  envelopes that displace polymer in their own pilots.
- Nominal screw engagement, blind-tip clearance, radial post material and tool
  approach clearances pass. The tool probes use a Ø6 mm driver from below and a
  Ø8 mm insert-tool approach with the lid removed; larger tools are not covered.
- A longer M3×10 lid screw is rejected for bottoming. The Ø4.1 mm pilot variant
  changes the bores while preserving the other parts and joint clearances.

These checks cover the lid fastener change. Existing button travel and desk
installation checks are in revision 005's reports; they were not rerun because
the relevant part geometry and transforms are unchanged.

From `Models/ESP32Enclosure`, regenerate into a fresh directory:

```bash
uv run --locked python revisions/006-lid-heatsets/build-revision.py --output builds/lid-check
uv run --locked python builds/lid-check/render-details.py builds/lid-check
uv run --locked python scripts/check-lid-heatsets.py --source builds/lid-check \
  --baseline revisions/005-downward-buttons --output builds/lid-check/lid-validation.json
```

Keep all five CAD inputs and both build/render helpers together. `source-files.json`
records their hashes, and the lid report records the independently checked source
and checker hashes. The shared runtime and optional FreeCAD commands are described
in the [package README](../../README.md#rebuild).
