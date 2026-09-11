# Native Fusion archives

The `ExportEnclosure` script imports the preserved STEP files into Autodesk
Fusion, writes native `.f3d` archives, reopens them, and compares solid counts,
volumes and bounding coordinates with the CAD validation report.
The default is **009-cable-retention**, which adds a rounded cable support and
zip-tie passage to the body. All fourteen other printed parts and existing
fasteners remain unchanged from revision 008.
It retains the earlier PCB/button layout; the corrected 49 mm board and measured
button spacing are documented in the separate [fit test](../fit-tests/002-board-fit-heatsets/).

**Native conversion has not been run yet.** The development host is Linux with
no Fusion runtime available. Python syntax and input planning can be checked
here; successful native export and reopening must be confirmed inside Fusion.

## Run in Fusion

1. Clone/download this repository onto the Windows or Mac machine running Fusion.
   Keep the complete `Models/ESP32Enclosure` folder together.
2. Open Fusion's **Scripts and Add-Ins** dialog. Add/link the existing script
   folder `Models/ESP32Enclosure/fusion/ExportEnclosure` and run **ExportEnclosure**.
   In versions with the green **+** button, use it to locate the script folder.
3. Fusion imports and exports each file. A final message gives the output folder
   under `fusion/exports/009-cable-retention-<timestamp>-<suffix>/`.
4. Check `fusion-validation.json` has `"status": "passed"`. The bundle contains
   one assembly `.f3d` plus 15 individual part `.f3d` files. Open the assembly
   archive in Fusion to inspect it. A failed run retains a failure report and
   any completed files in its own folder.

Each run creates a new folder. The script closes only its temporary import
documents and restores the previously active document. It does not call cloud
Save As or modify the source STEP files. Fusion still requires its normal
installation, account and runtime access.

For another preserved version, edit `REVISION` near the top of the script to
`001-generic`, `002-console`, `003-buttons`, `004-heatsets`,
`005-downward-buttons`, `006-lid-heatsets`, `007-pcb-heatsets` or
`008-corner-bosses`. The exported part count follows
that revision's report. Output folders are Git-ignored while conversion is being
checked; a passed bundle can be copied into a versioned `fusion/native/` folder.

## What the files contain

The assembly retains the separate STEP solids at their assembled positions.
The individual archives use the separately exported print orientations and
their part filenames/body names. Assembly component labels come from STEP and
may be generic. Hardware proxies are excluded.

This conversion does **not** reconstruct the build123d parameters, sketches,
constraints, fillets or boolean operations as a Fusion feature timeline. You
can use Fusion's direct-edit tools and add new features to the imported solids.
The Python source remains the editable parametric master. A full native Fusion
feature tree would require rebuilding the design using Fusion's own features.

The script uses a 0.05 mm bound tolerance and 0.1% volume tolerance, including
Fusion's internal centimeter-to-millimeter conversion and its VeryHigh physical
property calculation accuracy. Read-back checks detect
missing solids, scale/position errors and major translation differences; they
are not proof of identical topology or physical fit. `preciseBoundingBox` requires
a Fusion release from March 2024 or later.

## Local input check

From `Models/ESP32Enclosure`, ordinary Python can check the source/report files:

```bash
python fusion/ExportEnclosure/ExportEnclosure.py --check-inputs
```

This command does not export F3D and does not validate the Fusion runtime.
No build123d packages need to be installed into Fusion's Python interpreter.

## Autodesk references

- [Import STEP options](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ImportManager_createSTEPImportOptions.htm)
- [Import into a new document](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ImportManager_importToNewDocument.htm)
- [Native archive export](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportManager_createFusionArchiveExportOptions.htm?guid=GUID-2DF9786A-A0F8-4A66-9123-FAF48210FAB6)
- [Native archive import](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ImportManager_createFusionArchiveImportOptions.htm)
- [Managing scripts](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm)
