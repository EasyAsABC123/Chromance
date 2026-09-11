---
name: fdm-cad
description: Create or modify parametric engineering parts, enclosures, and mounts for FDM printing using build123d, with editable source, validated STEP/3MF exports, and actual geometry previews. Use for CAD solids and new mechanical designs; route existing STL/3MF mesh edits to fdm-mesh-edit.
---

# FDM engineering CAD

Use build123d as the primary authoring tool. Preserve existing CadQuery or OpenSCAD source when adapting it is practical. Use FreeCAD when the user needs native sketches, constraints, or a `.FCStd` feature tree; opening STEP in FreeCAD does not recover the original parametric history. For mesh-only inputs, use `fdm-mesh-edit` if available, or inspect and edit them with Trimesh and explicit `engine="manifold"` Booleans while retaining originals, units, scene transforms, and an operation script.

## Runtime and repeatability

Locate the runtime using an explicit user-provided path, then `FDM_CAD_HOME`, then the current repository's `Models/ESP32Enclosure` directory or an existing `cad-models` checkout. The runtime directory contains `pyproject.toml`, `uv.lock`, and `src/fdm_cad`. Inspect its `README.md`, dependencies, existing model, and CLI help before extending it. The runtime is local to that checkout; installing this skill does not install the CAD packages.

For the portable runtime published in Chromance, set the actual checkout path and use:

```bash
FDM_CAD_HOME=/path/to/Chromance/Models/ESP32Enclosure
uv sync --locked --project "$FDM_CAD_HOME"
uv run --locked --project "$FDM_CAD_HOME" python -m fdm_cad build --model <model.py> --params <params.json> --output <dir>
```

Resolve the model, parameter, and output paths explicitly so builds do not depend on the working directory. Use the project's locked dependencies. If the runtime is missing, establish the local project from its maintained source and lockfile before claiming a successful build. For an archived enclosure revision with helper modules, prefer its `build-revision.py` entry point, which snapshots the required sources and hashes. Choose a fresh output directory to preserve existing revisions.

Each model is an ordinary Python module exposing `build(params: dict) -> dict`. Return:

- `parts`: named build123d `Shape` objects positioned for printing, with their lowest point at Z=0.
- `assembly`: named positioned `Shape` objects representing the assembled product.
- `measurements`: a dictionary of useful dimensions in millimeters and other clearly labeled quantities.
- `notes`: a list recording design decisions, limitations, and manufacturing guidance.

Keep dimensions, fit allowances, and manufacturing choices in the parameter file. Preserve required source assets alongside the model; do not leave required inputs solely in temporary attachment paths. Separate preview-only device envelopes from printable parts. Give separately printed supports and hardware alternatives unambiguous names.

The build retains `model.py` and `parameters.json`, writes per-part STEP/3MF into `parts/`, and produces `assembly.step`, `print-layout.3mf`, `preview.png`, `print-layout.png`, `validation.json`, and `printing-notes.md`. Preserve additional imported local modules and assets yourself when the model depends on them; a single-module snapshot cannot capture those dependencies.

## Design decisions

Start with available evidence and make a useful initial model. Record consequential missing measurements as provisional parameters; ask only when an unresolved requirement prevents meaningful progress. A ruler in a perspective photograph provides an estimate, not a verified fit. Distinguish observed features from inferred dimensions and chosen allowances.

For enclosures, resolve the board envelope, underside solder clearance, component and cable height, connector access including plug bodies and bend space, board retention, lid access, and ventilation needs. Preserve antenna keepout where relevant. A generic starting enclosure may reserve adjustable space before exact hole and port coordinates are known.

Choose the design around its load path and manufacturing conditions:

- Establish supported mass, load direction, fastener arrangement, vibration or repeated loads, service temperature, environment, and printer/material constraints when relevant.
- Choose material for the application. Use current manufacturer data or primary technical sources for temperature, chemical compatibility, and other specific performance claims. Record uncertainty instead of assigning a universal strength or material rating.
- Evaluate the proposed print orientation against layer adhesion, mounting loads, surface quality, accuracy, and support removal. Strength is affected by geometry, material, orientation, and slicing; infill percentage alone is not a design justification.
- Choose wall thickness, ribs, fillets, fasteners/inserts, and part splits deliberately. For desk mounts consider pullout, bending at bracket roots, access to screws, desk clearance, and positive retention of the enclosure.
- Prefer support-free geometry when it suits the part. Otherwise name the support strategy: slicer-generated, modeled sacrificial, or a separate printed support. Verify removal access and protect mating/visible surfaces. Keep modeled supports separately identifiable.
- Make mating clearance and hole compensation adjustable. Identify critical fits for the quick iterative test prints; do not present printer-dependent allowances as measured facts.

## Quick iterative test prints

Always create a small, quick test-print artifact for each new design or geometry revision to check assumptions and fits before recommending a full print. Include it in the deliverables instead of merely suggesting a future coupon.

Derive the test from the same model parameters and interface geometry as the full part. For an enclosure, select the relevant board-retention frame, connector/button section, lid joint, insert boss, or desk-mount interface; include mating pieces when needed.

- Minimize print time and material with local sections, open frames, or partial-height parts. Preserve true scale, interface spacing, critical wall thickness/stiffness, insertion paths, and tool access so the simplification still tests the intended behavior. Use clearly labeled clearance variants when a fit allowance is uncertain.
- Match the intended final print orientation, material, nozzle, layer height, and support strategy where established; record provisional settings otherwise. A coupon cannot establish whole-part strength, warping, or interfaces it omits. Only report time/material estimates from an actual slicer profile, with its settings identified.
- Save versioned test files under `fit-tests/<revision>/` with their source/parameters or operation script, printable 3MF (STL when appropriate), and an actual geometry preview. Include a short checklist of assumptions tested, nominal dimensions, what to measure or try, and pass/fail criteria. Link directly to the test print in the handoff.
- Record reported measurements, fit problems, and printer/material/settings with the tested revision. Apply corrections to both the full model and test geometry, then generate the next small test. Mark each assumption as provisional, physically tested, or unresolved; geometry checks alone do not verify physical fit. Digital work can finish with the test files delivered and physical results pending.

## Validation and handoff

Run the shared build and inspect its report and actual exported geometry. Check valid solids, intended part count, bounding dimensions, cavity/connector clearances, assembly interference, and watertight print meshes. Inspect the generated previews with an image viewer; illustrated concepts are not proof of the CAD geometry.

Regenerate a meaningful parameter variant when establishing or changing a parametric feature, and check that the expected dimensions and clearances change correctly. Reopen STEP and 3MF to verify units, geometry, and object count. Use appropriate geometric tolerances for tessellated mesh comparisons. Do not silently heal geometry that changes intended openings or topology.

Deliver editable Python source, parameters, required inputs, STEP, model 3MF, actual geometry previews, and a concise report. A model 3MF carries printable geometry; it is not a slicer project with verified printer, filament, support, or process settings. Create a slicer-specific project only when those settings are established.

State intended material, printing orientation, support strategy, assembly hardware, critical fits, and unverified dimensions. Geometry validation is not physical strength or fit validation. Deliver the quick test prints with their physical validation status; describe additional load tests when they would resolve a real uncertainty.
