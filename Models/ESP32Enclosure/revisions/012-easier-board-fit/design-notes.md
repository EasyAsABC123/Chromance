# Fit allowance and shelf coverage

The [request record](../../measurements/2026-09-11-easier-fit.json) preserves the
user's requested +0.5 mm width and +0.5 mm shelf depth. No new measured printed
dimensions or printer compensation were supplied. The implementation treats
width as total added enclosure/retention clearance and depth as additional
horizontal coverage under each centered board edge.

The measured substrate width stays 49 mm. A separate `board_fit_width_extra`
(default 0.5 mm) drives shell width, locating shoulders, clamp outer faces and
fastener X positions. The inner shelf/clamp faces are based on the actual board
edge minus `board_edge_overlap`, now 1.3 mm. This gives a 50.3 mm locating gap,
46.4 mm shelf-inner gap and 0.65 mm minimum coverage after maximum lateral play.
The 1.2 mm vertical slot, board height, case height and length stay fixed.

The parameter bounds permit 0–1 mm additional fit width and 0.4–1.5 mm nominal
edge coverage, with a separate guard requiring positive coverage after the full
lateral allowance. Nominal and a meaningful 0.8 mm extra-width / 1.4 mm coverage
variant are built and checked. The variant has a 50.6 mm locating gap and 0.6 mm
minimum coverage. Zero additional allowance and invalid/out-of-range inputs are
also exercised by the source validation script.

The independent fit checker reopens revision 011/012 STEP files. Body, lid and
bracket each widen 0.5 mm; four clamps gain 12 mm³ each and two sliders extend
their guide-to-contact arms. Six other cartridge parts match after position
normalization. It probes actual shelf/shoulder/clamp faces, verifies the full
support strips, and checks 18 bare-PCB positions in both nominal and variant.

The new quick test is a full-width lower-body crop at Z12.2 mm with a 44 × 66 mm
coupon-only floor window and four complete clamps. The window stays 1.2 mm
inboard of the nominal shelf inner edges. Reopened full-production STEP geometry
is compared with the coupon; the comparison must have zero added/missing volume
within 0.001 mm³ tolerance. The central floor is absent only in the test, so
central underside protrusions require a separate measurement against the 6.6 mm
allowance. Full warping, stiffness, upper obstructions and tool reach are omitted.

The existing cable coupon 006 is compared with the actual production body/lid
STEP crop and remains identical. The unchanged concave feature and cable/tie
references are checked against the new assembled geometry; the unchanged local
layer-support evidence is linked by hash to revision 011. No repeat layer sweep
or new cable coupon is necessary for this board-fit change.

STEP/3MF export validity, watertight meshes, print placement and assembly
interference are checked by the shared builder. FreeCAD independently reopens
all parts and assembly, then saves/reopens `inspection.FCStd`. The mechanism
checker samples bracket installation, screw/driver access, PCB insert tool
access, and button travel/finger approaches for nominal and variant. These are
sampled digital checks; measured switch alignment and physical fit remain pending.

From `Models/ESP32Enclosure`, use fresh output directories:

```bash
uv sync --locked
uv run --locked python revisions/012-easier-board-fit/build-revision.py --output builds/rev012
uv run --locked python builds/rev012/render-details.py builds/rev012
uv run --locked python fit-tests/007-board-easier-fit/build-test.py --output builds/board007
uv run --locked python builds/board007/render-test.py builds/board007
uv run --locked python scripts/check-eased-board-fit.py --full builds/rev012 \
  --baseline revisions/011-fit-and-cable-cradle --test builds/board007 --output builds/rev012/fit-validation.json
uv run --locked python scripts/check-eased-retention-mechanisms.py --source builds/rev012 \
  --baseline revisions/011-fit-and-cable-cradle --output builds/rev012/mechanism-validation.json
```

Keep all adjacent source modules/build/render helpers together. Each builder
freezes source and parameter hashes. Record actual printed measurements and
settings in test 007's result template, then apply later changes to a new full
revision and corresponding quick test. Revisions 001–011 remain preserved.

The full 3MF exposed a validator ordering bug: a CAD minimum X of approximately
−9×10⁻¹⁶ mm sorted before a different row at X0, while both exported minima were
X0. Sorting the arrays paired different parts and falsely reported a large
position error. The builder now matches complete transformed bounds one-to-one,
retaining 0.05 mm absolute tolerance and zero relative tolerance. Regression
checks exercise floating-point row reordering, ambiguous matches, missing or
duplicated instances and actual transformation/extent errors. The report records
the matching and maximum error for each part.
