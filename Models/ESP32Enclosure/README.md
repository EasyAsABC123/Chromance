# ESP32 desk enclosure

Parametric enclosure for the pictured ESP32/perfboard controller, with console-inspired
curves, chamfers, ventilation, an under-desk bracket and external EN/RESET and BOOT
paddles. The user's [latest measurements](measurements/) separate the
**49 × 70 × 1 mm perfboard** from the **52 mm ESP32 span**. Confirmed button centers
are 30 and 16 mm from the bottom edge, each 3.3 mm from the left edge.

**Latest full enclosure: [011 — 3 mm narrower, with a concave cable cradle](revisions/011-fit-and-cable-cradle/README.md).**
The body, lid and desk bracket are each 3 mm narrower. The retention now uses the
measured 49 × 70 × 1 mm substrate. A block with an Ø8.4 mm cylindrical cutout seats
the measured 8 mm cable, with a zip-tie passage underneath.

**Quick iterative prints:**

- [005 — board retention, five-part 3MF](fit-tests/005-board-width/print-layout.3mf)
  and [fit instructions](fit-tests/005-board-width/README.md).
- [006 — concave cable cradle and lid section, two-part 3MF](fit-tests/006-cable-cradle/print-layout.3mf)
  and [fit instructions](fit-tests/006-cable-cradle/README.md).

Both are derived from revision 011's exact CAD inputs. Print these before a full
replacement. The user reported the earlier shelves 3 mm too far apart and asked
to shrink the full case; [the correction record](measurements/2026-09-11-retention-fit.json)
preserves that feedback. Physical results for the new tests remain pending.

Replace **body, lid and desk bracket together**. Their new screw centers move
inward 1.5 mm per side, including the desk mounting pattern. The four PCB clamps
and eight button pieces match revision 010 after translating their positions and
can be reused. The completed printed assembly is **113.8 × 95.2 × 39.6 mm**.

**Button alignment remains unresolved:** the earlier actuator Y layout is still
present. The measured 14 mm spacing and 3.3 mm edge inset need a separate mechanism
revision; this width/cable update does not claim physical button alignment.
The enclosure mounts lid-down; press the exposed pads upward. Test the actual
52 mm populated span and available bare PCB edges using test 005.

The cable cradle has 2 mm side walls and 2 mm above its tie passage. The Ø8.4 mm
cut provides provisional 0.2 mm radial allowance; actual zip-tie dimensions are
still unmeasured. The seated 8 mm cable and provisional tie/head leave 2.7 mm to
the lid plane digitally. Thread with the lid open; seat the cable and snug the
tie over it. Retention force has not been tested.

![Actual concave cable cradle](revisions/011-fit-and-cable-cradle/cable-anchor.png)

## Open or print

- [Assembly STEP](revisions/011-fit-and-cable-cradle/assembly.step): 15 printable
  solids in assembly position; open/import in Fusion 360 or FreeCAD. The editable
  parametric master is Python, not a Fusion timeline.
- [Body 3MF](revisions/011-fit-and-cable-cradle/parts/body.3mf),
  [lid 3MF](revisions/011-fit-and-cable-cradle/parts/lid.3mf), and
  [desk bracket 3MF](revisions/011-fit-and-cable-cradle/parts/desk_bracket.3mf).
- [Individual STEP/3MF parts](revisions/011-fit-and-cable-cradle/parts/) and
  [full print-layout 3MF](revisions/011-fit-and-cable-cradle/print-layout.3mf).
- [Cable/tie routing](revisions/011-fit-and-cable-cradle/cable-routing.png),
  [lid clearance](revisions/011-fit-and-cable-cradle/cable-closure.png),
  [mounted view](revisions/011-fit-and-cable-cradle/under-desk.png), and
  [interior](revisions/011-fit-and-cable-cradle/interior.png).
- [Revision guide](revisions/011-fit-and-cable-cradle/README.md) and
  [design/validation notes](revisions/011-fit-and-cable-cradle/design-notes.md).

These files carry geometry in millimeters, without verified printer or filament
profiles. Reference electronics/cable/tie/desk solids are excluded from printing.
The separate hardware STEP contains 34 simplified proxies and is not a complete
fastener assembly. Physical fit, load capacity and material behavior remain untested.

For native `.f3d` files, run the included [Fusion export script](fusion/README.md)
inside Fusion on Windows or Mac. Native conversion is pending a Fusion run; it
does not recreate the Python model's feature history.

## Preserved revisions

| Revision | Design |
| --- | --- |
| [001-generic](revisions/001-generic/) | Original rectangular enclosure and desk bracket |
| [002-console](revisions/002-console/) | Approved rounded/chamfered shell, diagonal vents and recessed lid detail |
| [003-buttons](revisions/003-buttons/) | External magnetic-return paddles with captive nylon contact nuts |
| [004-heatsets](revisions/004-heatsets/) | M3×5 contact inserts, M3×12 contact screws and local USB-clearance relief |
| [005-downward-buttons](revisions/005-downward-buttons/) | Inverted case, extended finger pads and straight bracket legs with M3×5 inserts |
| [006-lid-heatsets](revisions/006-lid-heatsets/) | Four lid nut pockets replaced by M3×5 inserts and M3×8 screws; only the body changes, retaining compatibility with the other revision 005 parts |
| [007-pcb-heatsets](revisions/007-pcb-heatsets/) | Four PCB-clamp nut pockets replaced by M3×5 inserts and M3×6 screws; body and four clamps change, retaining compatibility with the other ten revision 006 parts |
| [008-corner-bosses](revisions/008-corner-bosses/) | Full-height lid posts replaced by short corner pads and 45° wall ribs, with matching lid-skirt clearance; body and lid change, retaining compatibility with the other thirteen revision 007 parts |
| [009-cable-retention](revisions/009-cable-retention/) | Rounded cable support with a zip-tie passage at the end opening; only the body changes from revision 008, accompanied by a small exact-geometry fit test |
| [010-8mm-cable](revisions/010-8mm-cable/) | Records the measured 8 mm cable, updates clearance references and the quick test; all fifteen printed parts remain unchanged from revision 009 |
| [011-fit-and-cable-cradle](revisions/011-fit-and-cable-cradle/) | Full body/lid/bracket width reduced 3 mm, measured 49 × 70 × 1 mm PCB capture, concave cylindrical cable seat and two exact-geometry fit tests |


Revisions 001–010 are preserved unchanged. The original checksum manifest covers
171 files in revisions 001–004; the lid-joint checks compare revision 006 with 005.
The PCB-clamp checks compare revision 007 with 006; the corner-boss checks compare
revision 008 with 007. The cable-retention checks compare revision 009 with 008; the measured-cable
checks confirm unchanged printed geometry and the 8 mm clearance in revision 010.
Revision 011 separately checks the width reduction, exact board/cable coupons,
concave geometry and clearance variant, button travel and bracket installation.
Its width comparison confirms twelve reusable printed shapes; both new test
prints and the full export also pass independent FreeCAD reopening.
Their archived notes/reports contain historical workstation paths and references
to ZIP bundles; use the portable commands below. ZIP duplicates and reference
photos are not required to regenerate this numerical model and are omitted.

## Rebuild

The **[published skills and workflow overview](skills/README.md)** includes portable
copies of the FDM CAD and mesh-editing skills used with this workbench, plus links
to the shared builder, mesh checks, FreeCAD inspection and Fusion export helper.

The package uses build123d/OpenCascade for CAD, Trimesh for mesh checks and CPU
rendering for previews. It includes the source utilities and `uv.lock`; no
workstation-specific CAD installation is needed for the main Python build.

From this directory, with `uv` installed:

```bash
uv sync --locked
uv run --locked python revisions/011-fit-and-cable-cradle/build-revision.py --output builds/check
uv run --locked python builds/check/render-details.py builds/check
uv run --locked python scripts/check-concave-cradle.py --source builds/check \
  --baseline revisions/010-8mm-cable --output builds/check/cable-validation.json
uv run --locked python -m pytest -q
uv run --locked python scripts/verify-archives.py
```

The lockfile selects Python 3.13 and pinned CAD/mesh dependencies. The builder
requires a **new output directory** so it cannot overwrite an archived revision.
To change dimensions, copy `revisions/011-fit-and-cable-cradle/parameters.json`, edit it, and
pass `--params your-parameters.json` with a new `--output` directory. Keep
`model.py`, `base_model.py`, `button_module.py`, `mounting.py` and the build/render helpers together;
the builder snapshots their source and hashes into every build.

`validation.json` records solid validity, STEP and 3MF read-back, mesh checks,
dimensions, print orientation and assembly interference. Validation reports in
the revision directory document the additional mechanism checks.

The revision 008 reports cover STEP/3MF read-back, independent FreeCAD inspection,
corner-pad and rib geometry, lid clearance, insert/screw fit and preservation of
the other thirteen printed parts. Revision 007 retains its PCB-joint checks and
revision 006 its lid-joint checks. Revision 005 retains its button-travel, fingertip,
bracket and case-installation checks. Archived reports record source hashes and
original test paths; the command above uses package-relative inputs. The shared workflow tests
also pass. Portability has been exercised on Linux x86_64; other platforms and
native Fusion conversion have not been tested here.

For optional independent STEP inspection, run
`scripts/check-freecad.py <fresh-build-directory>` with a Python interpreter that
can import FreeCAD and Part. It writes an imported `inspection.FCStd` and a
comparison report into that build directory. The supplied archived inspection
files were checked with FreeCAD 1.1.3; they are imported geometry, not native
sketch/feature histories. No local FreeCAD launcher or binary is bundled.

## Printing and fit

Unfilled PETG is the initial material candidate. Print the body floor-down, the
lid exterior-down and the bracket desk-contact-face down. Cartridge frames and
rear keepers print on their outer sides; sliders need local removable support
under their stepped arms. The extended pads increase the needed support height.
Keep guide and magnet seats free of support scars.
Review the short shell bridges in the slicer. No supports are modeled.
The new lid pads grow from paired 45° wall ribs; inspect that region in the slicer
along with the trimmed lid skirt. Any CAD volume reduction is a solid-geometry
comparison; print time and filament savings require a sliced comparison.

The fourteen PCB/lid/bracket/contact inserts are modeled as **5 mm long, 4.6 mm outside diameter**
with a **4.0 mm pilot**. M3×5 specifies thread and length, not outside diameter;
the diameter/pilot are provisional parameters until the actual insert is known.
Check a material-specific insert and guide-fit coupon before printing the full
set. The four cartridge mounting inserts are a different, **4 mm-long** part.
The lid pilots are **6 mm deep**. M3×8 screws through the unchanged 2.4 mm lid
give 5 mm nominal insert engagement and 0.4 mm blind-tip clearance. Install these
four inserts flush from the open body rim before fitting the lid.
The pads project 8.4 mm into the cavity and overlap each wall by 0.4 mm. They are
8 mm tall, with 2 mm of material below the blind pilots; their paired ribs start
8.4 mm below the pads. These dimensions describe the nominal geometry and do not
establish the joint's physical load capacity.
The four PCB-clamp pilots are also **6 mm deep**. Their M3×6 screws give 4 mm
nominal engagement and 2 mm blind-tip clearance. Install the inserts flush with
the boss tops before placing the PCB and clamps. These screws capture the board
edges without passing through the PCB.

The magnet return uses two captive Ø4 × 2 mm magnets per paddle, with like poles
facing. Return force, physical switch travel, connector fit, thermal behavior,
RF performance and mounting strength have not been tested. Set contact height
and travel to release the switch at rest and prevent overpressing. The model
assumes only the low-voltage controller is enclosed; the external PSU is separate.
