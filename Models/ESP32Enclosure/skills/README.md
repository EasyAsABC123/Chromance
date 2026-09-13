# Skills and supporting 3D workflow

On Justin's host, the global skills under `~/.codex/skills/` link to their maintained
sources in `~/github/cad-models/skills/` and apply across projects. This directory
publishes portable adaptations with the same modeling preferences and validation
requirements. Runtime discovery and commands are adapted to the workbench included
in this repository.
The maintained source skill hashes and the portable adaptations are recorded in
[provenance.json](provenance.json). Installing a skill supplies instructions;
the Python runtime is a separate dependency.

Both skills require quick, versioned test-print artifacts for every new design or
geometry revision, with measurement/pass criteria and recorded physical results
feeding back into the full model.

The cable-retention preference is a **concave cylindrical groove cut into a
supported block**, with an accessible zip-tie passage below it. Keep cable diameter
separate from provisional groove clearance, and verify threading, seating, lid
clearance and jacket condition with a quick print.

| Resource | Purpose |
| --- | --- |
| [FDM CAD skill](fdm-cad/SKILL.md) | Parametric engineering parts and enclosures with build123d, manufacturing decisions, STEP/3MF exports and geometry validation |
| [FDM mesh-editing skill](fdm-mesh-edit/SKILL.md) | Existing STL/3MF inspection and repeatable edits using Trimesh and Manifold; preserve units, scene placement and original inputs |
| [Workbench setup and rebuild instructions](../README.md#rebuild) | Locked Python environment, repeatable generation and validation commands |
| [Shared CAD builder](../src/fdm_cad/build.py) and [preview renderer](../src/fdm_cad/preview.py) | Source snapshots, solid/mesh checks, exports and previews rendered from actual geometry |
| [Mesh inspection and validation helpers](../src/fdm_cad/geometry.py) | Units, mesh scene handling, dimensions, topology and geometric comparisons |
| [FreeCAD inspection script](../scripts/check-freecad.py) | Independent STEP read-back and imported `.FCStd` inspection documents |
| [Fusion export helper](../fusion/README.md) | Run inside Fusion to convert the STEP assembly and parts to native `.f3d` archives and reopen them for checks; conversion has not yet been run here |
| [Latest enclosure source](../revisions/012-easier-board-fit/model.py) and [parameters](../revisions/012-easier-board-fit/parameters.json) | Revision 012 retains the measured 49 × 70 × 1 mm PCB, adds 0.5 mm total fit width, and extends lower shelves and upper clamps by 0.5 mm over the board edges |
| [Current board-fit test 007](../fit-tests/007-board-easier-fit/) | Exact retention section and matching heat-set clamps; check the added width, deeper capture and unchanged 1.2 mm vertical slot |
| [Concave cable-fit test 006](../fit-tests/006-cable-cradle/) | Actual body and lid sections with an Ø8.4 mm groove for the measured Ø8 mm cable; this geometry remains compatible with revision 012 |
| [Current board-fit checks](../scripts/check-eased-board-fit.py) | Width and capture geometry, board-placement checks, exact board-coupon STEP comparison and cable-test 006 reuse |
| [Current mechanism checks](../scripts/check-eased-retention-mechanisms.py) | Nominal/variant tool access, screw engagement, sampled bracket/button paths and unchanged cable geometry |
| [Concave-cradle checks](../scripts/check-concave-cradle.py) | Revision 011's actual cylindrical subtraction, cable seating, tie passage and layer-support proof retained by revision 012 |
| [Recorded measurements](../measurements/) | User measurements, datum definitions and distinctions between confirmed dimensions and remaining assumptions |
| [Earlier revision checks](../scripts/) | Preserved reviews for the flipped mount, lid/PCB heat sets and corner bosses; each script documents its revision scope |

The measured **49 × 70 × 1 mm** PCB is integrated into the full enclosure. The
separate 52 mm measurement describes the populated ESP32 span. Button alignment
remains provisional: the measured **14 mm button spacing** still needs integration.
Current print-fit results remain pending; digital checks do not establish physical fit.

The enclosure itself is authored with the FDM CAD skill. The mesh skill supports
mesh-only inputs and modifications; it is not a replacement for the CAD source.
FreeCAD and Fusion are supporting workflows, not additional skills in this package.
Imported STEP/F3D/FCStd geometry does not recreate the Python model's parametric
feature history.

Keep each skill folder intact when installing it in an agent environment. Set
`FDM_CAD_HOME` to the absolute path of `Models/ESP32Enclosure` in your checkout so
both skills can find the bundled runtime from any working directory. See the
[package README](../README.md) to install the locked dependencies with `uv`.
