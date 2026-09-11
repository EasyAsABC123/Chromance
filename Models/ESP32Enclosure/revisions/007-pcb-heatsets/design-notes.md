# PCB-clamp heat-set joints — revision 007

The four PCB-clamp nut pockets were still present in revision 006. This revision
fills those pockets and their lower side-entry windows, adds reinforced blind
insert bosses, and moves the matching clamp holes 0.4 mm outward. The thin upper
slot is intentional clearance for the PCB edge and remains open.

Reprint **one body and four PCB clamps** using `replacement-parts.3mf`, or the
individual files in `parts/`. Use this matching set: the earlier clamp holes no
longer line up with the new body. The lid, bracket and eight button parts retain
their geometry and assembly positions from revision 006. All archives are preserved.

## PCB joint dimensions

| Feature | Nominal geometry |
| --- | --- |
| Insert | M3 thread, 5 mm length, provisional OD4.6 mm |
| Pilot | Ø4.0 mm × 6.0 mm blind depth |
| Reinforced boss | Ø8.8 mm; 2.1 mm radial polymer around the insert envelope |
| Screw centers | Local X±30.9, Y±17 mm; moved 0.4 mm outward |
| Clamp | 2 mm thick, Ø3.4 mm clearance hole |
| Screw | M3×6 socket screw, head Ø5.5 × 3 mm or smaller, no washer |
| Insert engagement | 4 mm |
| Screw tip to bore bottom | 2 mm |
| Preserved board slot | 1.8 mm high for the archived 1.6 mm PCB plus 0.2 mm play |

Coordinates above are the body print frame: floor Z0, PCB bottom Z8.4/top Z10,
clamp underside Z10.2/top Z12.2. Insert bottom is Z5.2 and pilot bottom Z4.2.
The board-edge supports and locating shoulders remain in their original positions.
The reinforced bosses keep continuous material around the inserts, including
where the left connector opening previously cut into the tops of the mounts.

M3×5 does not specify the insert's outside diameter. Check your purchased insert
and filament, then adjust `pcb_insert_outer_diameter` and
`pcb_insert_pilot_diameter` if needed. The model rejects insufficient engagement,
post material or blind-tip clearance. **M3×8 PCB screws reach the blind bore
bottom and must be replaced with M3×6.** Actual screw-length and printing tolerances
remain untested; the geometric margins are nominal dimensions.

## Printing and assembly

1. Print the body floor-down and the clamps flat, at 100% scale in millimeters.
   Unfilled PETG remains the initial material candidate. The insert pilots open
   upward. No supports are modeled; inspect the unchanged short shell and
   horizontal cartridge-hole bridges in the slicer.
2. With the lid, PCB and cartridges removed, heat-set the four PCB inserts flush
   with the clamp shoulders and let them cool. The right-side wall limits tool
   diameter: the validated approach uses a **Ø6 mm narrow shaft with at least
   21.8 mm reach** before a wider barrel can clear the open rim. Confirm your
   installation tool fits; a straight Ø8 mm tool does not clear that wall.
3. Seat the board on the ledges, keeping solder joints and components clear.
   Fit the four new clamps and M3×6 screws. The clamps seat on printed shoulders;
   they should capture the edge without squeezing the PCB or its components.
4. Refit the button cartridges and lid. Existing BOOT-cartridge removal is still
   needed to reach the left-front clamp during service. A Ø6 mm screwdriver
   approach is modeled; the right wall leaves only 0.1 mm nominal lateral margin.
5. Mount with the lid facing downward and press the exposed paddles upward.
   Check that the contacts release at rest and the board is captured before use.

Insert pullout strength, installation torque, physical print fit, return force,
RF behavior and mounting load capacity have not been tested. The actual component
and connector envelopes also remain unverified.

## Complete fastener inventory

| Joint | Hardware |
| --- | --- |
| PCB clamps — changed | 4 M3×5 inserts + 4 M3×6 socket screws |
| Lid — retained from 006 | 4 M3×5 inserts + 4 M3×8 socket screws |
| Desk bracket | 4 M3×5 inserts + 4 M3×10 screws |
| Button contacts | 2 M3×5 inserts + 2 nylon M3×12 adjusters and 2 separate nylon jam nuts |
| Cartridge mounting | 4 M3×4 inserts + 4 M3×18 socket screws |
| Bracket to desk | Screws selected for the actual desk material and thickness |

Total: **fourteen M3×5 inserts plus four M3×4 inserts**. No captive hex-nut
pockets remain in the printable parts. The contact jam nuts lock adjustment and
are exposed hardware, not nuts captured inside printed pockets. Rectangular
PCB-edge, magnet and mechanical-stop openings still serve their original purposes.

## Compatibility with the measured board

This revision retains the earlier full-model 52 × 70 × 1.6 mm PCB assumption and
button locations. Its clamps still cannot retain the measured 49 mm substrate.
Use [fit test 002](../../fit-tests/002-board-fit-heatsets/) for the
49 × 70 × 1 mm substrate; the 52 mm ESP32 span is a separate dimension. The
measured 14 mm button spacing requires a later actuator-layout change. No new
physical-fit acceptance or printer compensation is inferred from this nut fix.

## Validation and repeatability

`validation.json` covers the fifteen CAD solids, individual STEP and 3MF read-back,
units, print placement and printed-assembly interference. `replacement-validation.json`
checks the five-object replacement 3MF against its CAD bounds and volumes.
`freecad-validation.json` records independent reopening of all STEP parts and the
assembly. `inspection.FCStd` is imported geometry; Python remains the parametric
master. The Fusion helper defaults to this revision, but native F3D conversion
still requires a run inside Fusion.

The independent PCB-joint check is in `pcb-validation.json`. It checks both the
nominal Ø4.0 mm pilot and a Ø4.1 mm variant, the removal of the old nut entries,
retained board support/clearance, new hardware interference, tool approaches and
compatibility with unchanged parts. `hardware-reference.step` separately contains
34 simplified hardware proxies; threads and some other fasteners are omitted.
It is reference geometry and is excluded from the printable exports.

From `Models/ESP32Enclosure`, use a fresh output directory:

```bash
uv run --locked python revisions/007-pcb-heatsets/build-revision.py --output builds/pcb-check
uv run --locked python builds/pcb-check/render-details.py builds/pcb-check
uv run --locked python scripts/check-pcb-heatsets.py --source builds/pcb-check \
  --baseline revisions/006-lid-heatsets --output builds/pcb-check/pcb-validation.json
```

Keep the five CAD inputs and both build/render helpers together. Their hashes
are recorded in `source-files.json`; the independent report also records the CAD
source and checker hashes. Shared setup and optional FreeCAD commands are in the
[package README](../../README.md#rebuild).
