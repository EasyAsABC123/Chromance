# Revision 014 design and validation

The [measurement record](../../measurements/2026-09-13-usb-connector.json) preserves
the user's A–F reply and clarification. Diagram B originally meant top height;
the user's B=6 instead meant thickness. The normalized top is 9+6=15 mm above
the perfboard. Raw values and normalized dimensions remain separate in the
source metadata and [measurement guide](../../measurements/usb-connector-guide/README.md).

## Reference geometry

With PCB left X−24.5, bottom Y−35 and top Z10, the outboard plug box is
X−44.5…−24.5, Y−17…−7, Z19…25. A=10 and thickness=6 apply uniformly along the
20 mm projection, conservatively including the unmeasured taper/strain relief.
The box excludes geometry inboard of the PCB left edge. The Ø3.5 flexible cable
starts at X−44.5, with an assumed center at Z22; its actual axis and route were
not measured. The separate Ø8 cable cradle is unchanged.

The stationary relief expands the box by 0.2 mm on every face. Slider reliefs
also account for the full 0.8 mm downward stroke and extend below the slider
bottom, allowing vertical installation around the seated plug. The BOOT rail
cut opens upward to eliminate a residual thin lip. Direct Boolean comparisons
confirm only both sliders and the BOOT frame change from 013.

Minimum continuous material around the contact insert envelope is 1.284690 mm
at clearance0.20 and 1.216390 mm at0.25. The source enforces the allowed clearance
range and minimum1.2 mm wall. Rear/lower guide bearings and magnet geometry are checked against their uncut
source shapes. Stop positions and travel are retained; overtravel remains
blocked despite a slightly smaller BOOT lower-stop contact area. These are geometric requirements,
not physical strength ratings.

## Rebuild

From `Models/ESP32Enclosure`:

```bash
uv sync --locked
uv run --locked python revisions/014-usb-clearance/build-revision.py --output builds/check014
uv run --locked python builds/check014/render-details.py builds/check014
uv run --locked python scripts/check-measured-usb-clearance.py \
  --source builds/check014 --baseline revisions/013-measured-buttons \
  --output builds/check014/usb-validation.json
uv run --locked python assembly-guides/014-buttons/render-guide.py \
  --source builds/check014 --output builds/check014-guide
```

The output must be fresh. For a variant, edit a copy of `parameters.json` and
pass `--params` to the build script. Keep the model, base, button module,
mounting module and build/render helpers together. The seven inputs are frozen
in [source-files.json](source-files.json). Follow
[test009](../../fit-tests/009-usb-clearance/README.md) to regenerate its exact
production replacements and complete open jig.

## Validation scope

The shared build checks all15 valid print solids, intended assembly interference,
watertight meshes, production orientation, and STEP/3MF read-back. Independent
FreeCAD reopening checks the15 parts and assembly; its FCStd contains imported
solids without a native feature history. Fusion can import STEP; native F3D
conversion still requires running the [Fusion helper](../../fusion/README.md)
inside Fusion.

The targeted [checker](../../scripts/check-measured-usb-clearance.py) evaluates
nominal0.20 and variant0.25 clearance. Each checks nine independent button
states, twelve unchanged printed pieces, all34 unchanged hardware proxies,
measured plug clearance, guide/boss material, travel stops, keeper and magnet
retention, and staged frame/slider/keeper installation with the plug present.
Finite samples do not prove continuous swept-volume clearance.

Coupled board/plug placements are evaluated at X−0.65/0/+0.65,
Y−0.4/0/+0.4 and Z0/+0.2 for all nine button-state combinations:162 samples
per scenario. Conservative envelope contacts remain in144 samples per scenario;
all centered-XY samples clear. Nominal worst contact volumes are25.1132 mm³ at
the BOOT slider,6.77119 at the RESET slider and2.646 at the BOOT frame. These
are unresolved envelope contacts, not a passing physical fit at all board
positions or proof that the actual tapered connector fails.

Use the quick print to check the real plug profile, board placement, switch
alignment and travel, return force, support removal and insert fit. Contact
adjustment must release switches at rest and actuate them before the printed
stops, without hitting the lid. Physical fit, fatigue, material behavior and
mounting capacity remain unverified.
