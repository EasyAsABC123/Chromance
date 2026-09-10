---
name: fdm-mesh-edit
description: Inspect and modify existing STL or 3MF meshes for FDM printing using Trimesh and Manifold, preserving originals and repeatable operation scripts. Use for mesh cuts, unions, holes, scaling, and transformations; use fdm-cad for new parametric solids or STEP-based CAD work.
---

# Repeatable FDM mesh editing

Use Trimesh for loading, inspection, transformations, and export; use `manifold3d` for solid Boolean operations through Trimesh with `engine="manifold"` explicitly. Mesh edits do not recover CAD sketches, constraints, or feature history. If editable source or STEP exists, consider modifying that source instead of the tessellated derivative.

## Runtime and inputs

Locate the runtime using an explicit user-provided path, then `FDM_CAD_HOME`, then the current repository's `Models/ESP32Enclosure` directory or an existing `cad-models` checkout. The runtime directory contains `pyproject.toml`, `uv.lock`, and `src/fdm_cad`. Inspect its README, dependencies, CLI help, and any existing mesh helpers. This is a checkout-local runtime; installing the skill does not install the Python packages. Use its locked dependencies.

For the portable runtime published in Chromance, set the actual checkout path:

```bash
FDM_CAD_HOME=/path/to/Chromance/Models/ESP32Enclosure
uv sync --locked --project "$FDM_CAD_HOME"
uv run --locked --project "$FDM_CAD_HOME" python -m fdm_cad mesh-inspect <file.3mf>
uv run --locked --project "$FDM_CAD_HOME" python -m fdm_cad mesh-inspect <file.stl> --units mm
```

The STL unit choice must reflect the source; supported choices are `mm`, `cm`, `m`, and `in`. Inspection is read-only. Use explicit input/output paths. Run a retained modification script with the same environment:

```bash
uv run --locked --project "$FDM_CAD_HOME" python <edit_script.py>
```

Preserve the original file and record its identity, source, units, dimensions, and object count before modifications. Keep required inputs with the project, not solely in temporary attachment directories. STL has no reliable unit metadata: establish scale from the user, source documentation, or a known dimension; record any provisional assumption explicitly. Honor 3MF model units and convert to millimeters once. Do not supply a conflicting unit override for declared 3MF units.

## Scene and edit discipline

Load 3MF as a scene initially. Inspect scene graph instances and transforms; do not edit only the untransformed geometry dictionary. When flattening is appropriate, copy each instantiated mesh and apply its full world transform, preserving distinct instances. Retain named objects separately when they represent printed parts. Do not silently union assemblies into one object.

Write the operations into a reproducible Python script with explicit input paths, parameters, units, coordinate frames, and output names. Keep original assembly placement distinct from the final printing orientation. Inspect both before exporting.

For a Boolean operation, operands should represent consistently wound, watertight volumes. Use an explicit engine, for example:

```python
result = trimesh.boolean.difference([body, cutter], engine="manifold")
```

Check preconditions and report failed or empty results. Do not automatically cap openings, fill holes, or discard components as generic repair: those can alter the requested part. Make repairs deliberate and record what changed. When poor mesh quality makes the edit unreliable, explain the concrete issue and choose targeted repair or parametric reconstruction according to the requested geometry.

For scaling, distinguish unit conversion from design changes: uniform scaling also changes holes, walls, fits, and mounting dimensions. For cuts and unions, verify the result where the operands meet and identify new overhangs, thin walls, or support needs. For load-bearing edits, use the same material, orientation, and load-path reasoning as `fdm-cad`; mesh validity alone says nothing about strength.

## Validation and deliverables

Compare original and edited bounding dimensions, expected object/connected-component count, watertightness, winding, and volume where defined. Verify requested measurements and preserve intentional openings. Reopen the exported result and inspect actual mesh previews; apply tolerances appropriate to tessellation rather than requiring exact CAD-volume equality.

Deliver the original inputs, operation script and parameters, dependency context, edited STL/3MF, actual geometry previews, and a concise change/validation report. Explicitly identify any unverified scale, fit, repaired topology, or strength assumption.

Treat exported 3MF as model geometry. Trimesh-based loading and export do not promise preservation of slicer profiles, modifiers, supports, painted attributes, or vendor extensions. Keep the original slicer project and report metadata that was intentionally preserved, omitted, or not inspected; avoid overwriting it with a geometry export. Do not claim a STEP export recreated editable parametric history.
