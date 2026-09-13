# Revision 013 design and validation

The [measurement record](../../measurements/2026-09-12-button-alignment.json)
applies the earlier confirmed board-edge dimensions. No additional physical
measurement was inferred. The old coupled switch/housing offsets could not
accept the measured spacing while satisfying housing separation and gusset
clearance. The revised parameters express switch positions from the PCB bottom
edge and exterior housing positions independently.

The new straight tongue and rounded elbow keep the arm bend out of the guide.
The contact collar's flat is independently constrained to at least 2.9 mm
from its center, retaining 1.2 mm beside the 3.4 mm through-hole. It no longer
uses a formula that would cut through the collar at larger housing offsets.
Full upper insert geometry and the existing guided travel/retaining mechanisms
are preserved. No change to the PCB fit allowance or cable retention is included.

## Rebuild

From `Models/ESP32Enclosure`, with the package's locked Python environment:

```bash
uv sync --locked
uv run --locked python revisions/013-measured-buttons/build-revision.py --output builds/check013
uv run --locked python builds/check013/render-details.py builds/check013
uv run --locked python scripts/check-measured-button-alignment.py \
  --source builds/check013 --baseline revisions/012-easier-board-fit \
  --output builds/check013/mechanism-validation.json
```

The builder requires a fresh output directory. Edit a copy of `parameters.json`
and pass `--params` to build a variant. Keep the model, base, button module,
mounting module and build/render helpers together. [Source hashes](source-files.json)
identify all seven frozen inputs. Follow the quick test's
[instructions](../../fit-tests/008-button-alignment/README.md) to rebuild its
complete jig and two-slider subset.

The shared exporter validates each solid and mesh, reopens STEP and 3MF,
checks assembly interference and reports dimensions and units. FreeCAD separately
reopens all fifteen STEP parts and the assembly; `inspection.FCStd` contains
imported geometry, not a recovered feature tree. Native Fusion conversion uses
the existing [Fusion-side helper](../../fusion/README.md).

## Targeted checks

The mechanism checker compares all thirteen retained printed parts with 012,
checks measured contact axes and evaluates a parameter variant. It samples
independent button positions, cartridge assembly, keeper retention, printed
travel stops, fastener/tool access, USB envelopes and mounting paths. Input
hashes and exact samples are recorded in its report. Finite motion samples do
not constitute a continuous collision proof.

PCB registration still has clearance, and the actual switches' height, travel
and force are unknown. USB probes are explicitly provisional and distinguish
the inboard plug from the narrower cable passing the housings. The provisional
8 × 6 mm inboard plug box overlaps the left-front PCB clamp screw head; the
broad exterior approach is also blocked. Those are recorded obstructions, not
passing connector-fit claims. Physical button
fit, magnetic return, connector fit, material behavior and strength remain
unverified. Use the small production-geometry test before relying on the full
assembly.
