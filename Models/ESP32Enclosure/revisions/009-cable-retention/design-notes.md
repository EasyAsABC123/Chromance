# Cable retention — design and validation notes

Only the body changes from revision 008. A rounded support follows the cable's
axis just inside the end opening. The zip tie passes straight through a tunnel
under the support, then around both the support and insulated cable. The support
joins the end wall with a sloping underside; no separate printed fastener is added.
The lid and all thirteen other printed parts remain compatible.

## Nominal geometry

Coordinates below use the body print frame: floor at Z0, rim at Z32, cable exit
at +Y. When mounted beneath the desk, +Y becomes world−Y and the lid faces down.

| Feature | Nominal value |
| --- | --- |
| Rounded support | Radius 4 mm; 8 mm long along the cable |
| Support location | X±4; Y37..45; crown Z20 |
| Wall connection | 1 mm overlap; 45° underside begins at Z9 |
| Cable reference | Ø6 mm, axis at X0/Z23; diameter provisional |
| Zip-tie band reference | 2.5 mm wide × 1 mm thick; provisional |
| Zip-tie head reference | 5 × 5 × 4 mm, placed beside the cable; provisional |
| Passage | 3.2 mm wide along Y, 1.4 mm straight height, 45° roof |
| Passage height | Floor Z15; eaves Z16.4; apex Z18 |
| Strap allowance | 0.35 mm each side; 0.2 mm above and below |
| Material above tunnel apex | 2 mm at the crown |
| Minimum tunnel floor over underside | 0.9 mm at the inboard eave |
| Loose tie/head envelope to lid plane | 4.7 mm |
| Nominal support-to-PCB end gap | 2 mm; component/wiring overhang remains unmeasured |
| Body CAD volume | 46.405 → 46.747 cm³ |
| Added body CAD volume | 0.341 cm³ |

The outside assembly dimensions remain 116.8 × 95.2 × 39.6 mm. No lid holes,
corner supports, mounting ears, PCB clamps, button parts or existing hardware axes
move. The old floor tie slots remain; this new tie route stays inside the shell
and does not pass under its desk-facing back.

These are geometric dimensions, not a pull-load rating or print-time estimate.
The thin floor at the passage and the tie's contact at its mouths specifically
need checking in the [small test print](../../fit-tests/003-cable-retention/).
Tighten only enough to hold the jacket; the test should identify snagging, slipping,
strap damage, cable deformation or cracking before using the full enclosure.

## Print and installation

Print the body floor-down. The new anchor's underside and tunnel roof grow at
45°; no supports are modeled for this feature. Review the actual sliced layers
with the intended filament, nozzle and layer height. Unfilled PETG remains the
provisional enclosure material. The other parts keep their existing orientations
and support requirements.

With the lid removed, thread the free tie tail along X through the passage. Place
the insulated cable along the rounded crown, close the tie with its head beside
the cable, and keep internal slack before the electrical termination. Check lid
closure before trimming the tail. Fit and grip depend on the actual cable jacket,
tie dimensions, print settings and installation; a rigid reference cable does not
prove bend clearance for the real wiring.

All existing inserts and screws remain unchanged: fourteen M3×5 inserts, four
M3×4 cartridge inserts, M3×8 lid screws, M3×6 PCB clamp screws, M3×10 bracket screws,
M3×18 cartridge screws and the nylon contact adjusters/jam nuts. See
[revision 008](../008-corner-bosses/design-notes.md) for the existing assembly details.
Add one suitable zip tie after verifying its fit. No printed captive-nut pockets
are introduced.

## Quick fit print and validation

The test is an exact body/lid crop bounded by X±16, Y36..47.6 and Z0..34.4 in the
full model. Body section: 32 × 11.6 × 32 mm. Lid section: 32 × 10.4 × 4.4 mm in
its print orientation. Their total solid volume is
3.514 cm³. This is not a sliced filament estimate.

- Shared build: fifteen valid, connected printed solids; no assembly overlaps;
  per-part STEP/3MF read-back, units, dimensions and watertight meshes pass.
- Independent retention checker: exact body reconstruction; 0 mm³ removed and
  341.425 mm³ added; all fourteen other printed parts and
  34 existing hardware proxies remain unchanged from revision 008.
- Cable/tie checks: cable placement, straight tail threading, head access,
  lid clearance, PCB envelope and button motion remain clear in the model.
- Printing geometry: 120 sections at 0.2 mm layer spacing across nominal and
  variant supports pass the local 45° support check. The variant uses an 8 mm
  cable, 3 mm tie, radius4.5 support and 7.5 mm projection; it retains 2.2 mm
  lid clearance. These variant settings must change together; the nominal
  geometry is not automatically a fit for every cable up to 8 mm.
- Negative controls reject excessive cable/head sizes and inadequate roof
  thickness, and detect a threading probe placed below the passage.
- Coupon: two valid printable solids match independently reopened full-part
  STEP crops exactly. Its source/parameters match the full revision.
- FreeCAD 1.1.3 independently reopens the fifteen full parts and two coupon parts,
  their assemblies, and saved imported inspection documents successfully.

Physical results are pending in the test's [fit-results.json](../../fit-tests/003-cable-retention/fit-results.json).
Its cut boundaries do not represent whole-shell stiffness or rated strain relief.
The measured 49 × 70 × 1 mm board and 14 mm button spacing remain separate from
this full enclosure's older board/button layout; use the corrected board-fit test
for that retention check. Native Fusion F3D conversion still requires running the
included helper inside Fusion; STEP is the available interchange geometry.

## Rebuild

From `Models/ESP32Enclosure`, use fresh output directories:

```bash
uv run --locked python revisions/009-cable-retention/build-revision.py --output builds/cable-retention
uv run --locked python builds/cable-retention/render-details.py builds/cable-retention
uv run --locked python scripts/check-cable-retention.py --source builds/cable-retention \
  --baseline revisions/008-corner-bosses --output builds/cable-retention/cable-validation.json
```

The retained source hashes identify all five CAD inputs and both build/render
helpers. Pass `--params` to the build helper for a parameter variant. The
[fit-test guide](../../fit-tests/003-cable-retention/README.md) gives its separate
rebuild and STEP-crop comparison commands.
