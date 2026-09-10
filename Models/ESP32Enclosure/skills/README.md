# Skills and supporting 3D workflow

These are portable adaptations of the two local skills used for this CAD workflow.
The engineering and validation instructions are retained; runtime discovery and
commands now point to the copy of the workbench included in this repository.
The original skill hashes and the small set of adaptations are recorded in
[provenance.json](provenance.json). Installing a skill supplies instructions;
the Python runtime is a separate dependency.

| Resource | Purpose |
| --- | --- |
| [FDM CAD skill](fdm-cad/SKILL.md) | Parametric engineering parts and enclosures with build123d, manufacturing decisions, STEP/3MF exports and geometry validation |
| [FDM mesh-editing skill](fdm-mesh-edit/SKILL.md) | Existing STL/3MF inspection and repeatable edits using Trimesh and Manifold; preserve units, scene placement and original inputs |
| [Workbench setup and rebuild instructions](../README.md#rebuild) | Locked Python environment, repeatable generation and validation commands |
| [Shared CAD builder](../src/fdm_cad/build.py) and [preview renderer](../src/fdm_cad/preview.py) | Source snapshots, solid/mesh checks, exports and previews rendered from actual geometry |
| [Mesh inspection and validation helpers](../src/fdm_cad/geometry.py) | Units, mesh scene handling, dimensions, topology and geometric comparisons |
| [FreeCAD inspection script](../scripts/check-freecad.py) | Independent STEP read-back and imported `.FCStd` inspection documents |
| [Fusion export helper](../fusion/README.md) | Run inside Fusion to convert the STEP assembly and parts to native `.f3d` archives and reopen them for checks; conversion has not yet been run here |
| [Latest enclosure source](../revisions/005-downward-buttons/model.py) and [parameters](../revisions/005-downward-buttons/parameters.json) | Editable revision 005 model, with earlier revisions retained |
| [Board-fit test](../fit-tests/001-board-fit/) | Short production-derived tray, original clamps, printable 3MF and a physical-fit checklist |
| [Mount and button integration checks](../scripts/check-flipped-mount.py) | Clearances, button travel, hardware engagement and sampled enclosure installation/removal positions |

The enclosure itself is authored with the FDM CAD skill. The mesh skill supports
mesh-only inputs and modifications; it is not a replacement for the CAD source.
FreeCAD and Fusion are supporting workflows, not additional skills in this package.
Imported STEP/F3D/FCStd geometry does not recreate the Python model's parametric
feature history.

Keep each skill folder intact when installing it in an agent environment. Set
`FDM_CAD_HOME` to the absolute path of `Models/ESP32Enclosure` in your checkout so
both skills can find the bundled runtime from any working directory. See the
[package README](../README.md) to install the locked dependencies with `uv`.
