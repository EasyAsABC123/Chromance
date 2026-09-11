# Design decisions and repeatable validation

The [fit correction record](../../measurements/2026-09-11-retention-fit.json)
records the user's reported 3 mm shelf-spacing error and explicit request to
narrow the full enclosure by 3 mm total. The original tested file was not
identified. No absolute printed dimensions or slicer settings were supplied,
so no printer shrinkage compensation is inferred.

The width parameter changes from 52 to 49 mm. PCB thickness changes from 1.6 to
the confirmed 1 mm; solder clearance changes from 6 to 6.6 mm so PCB top Z10 and
rim Z32 stay fixed. The retained button housing offsets and Y coordinates are
still provisional: measured Y−5/−19 and X−21.2 need a separate mechanism layout.
The existing collision guards are retained. All earlier revision files remain intact.

The cable feature is independently reconstructed as a supporting block minus
an actual cylinder and tie tunnel. The checker probes both sides of the curved
seat surface, verifies the cylindrical cut volume, 2 mm web and side walls,
seated cable, straight tie threading, cable insertion, head access and lid
clearance. A meaningful Ø8.6 mm groove variant is also built and checked. Across
nominal and variant, 157 sampled 0.2 mm layers meet the local growth check. This
is a geometric support check, not an actual sliced print profile.

For isolating the cable change, the checker rebuilds revision 010 with the same
49/1/6.6 PCB overrides and verifies equality outside the cable region. That
comparison does not claim compatibility with the original published 010 body.
A separate width check reopens the actual published 010/011 STEP files, verifies
3 mm reductions in body/lid/bracket, and confirms the other twelve shapes match
after position normalization. Independent probes locate the shelf/shoulder/clamp
faces; 18 bare-board positions sample nominal XY and vertical play without collision.

The board coupon is the exact exported full-body STEP cropped at Z12.2 mm, with
a 44 × 66 mm central floor window and all four full clamps. Comparison against
independently reopened STEP geometry gives zero added/missing volume. Its open
center omits central underside collision checking and full-shell stiffness.
The cable coupon similarly compares against the actual body/lid STEP crop.

The shared builder verifies all 15 solids, assembly interference, print Z0,
watertight 3MF meshes and STEP/3MF reopening. FreeCAD independently reopens and
checks the parts and assembly, then saves/reopens `inspection.FCStd`. This file
contains imported solids, without the Python model's parametric feature history.
The hardware STEP contains 34 simplified proxies, including cartridge mounting
screws; cartridge insert proxies, body-to-bracket screws and desk screws are
omitted. The mechanism checker adds independent body-to-bracket screw references.

From `Models/ESP32Enclosure`, use fresh output directories:

```bash
uv sync --locked
uv run --locked python revisions/011-fit-and-cable-cradle/build-revision.py --output builds/rev011
uv run --locked python builds/rev011/render-details.py builds/rev011
uv run --locked python fit-tests/005-board-width/build-test.py --output builds/board005
uv run --locked python builds/board005/render-test.py builds/board005
uv run --locked python fit-tests/006-cable-cradle/build-test.py --output builds/cable006
uv run --locked python builds/cable006/render-test.py builds/cable006
uv run --locked python scripts/check-board-width.py --full builds/rev011 \
  --baseline revisions/010-8mm-cable --test builds/board005 --output builds/rev011/width-validation.json
uv run --locked python scripts/check-concave-cradle.py --source builds/rev011 \
  --baseline revisions/010-8mm-cable --output builds/rev011/cable-validation.json
uv run --locked python scripts/check-narrowed-mechanisms.py --source builds/rev011 \
  --output builds/rev011/mechanism-validation.json
uv run --locked python scripts/check-measured-cable-fit.py --full builds/rev011 \
  --test builds/cable006 --output builds/cable006/fit-validation.json
```

The source snapshot/hash manifests make each build and coupon reproducible.
Physical results belong in each test's `fit-results.json`, with the printed
source hash, measured gap/fit observations and printer/material/settings. Further
corrections should create a new revision and new targeted test, retaining this one.
