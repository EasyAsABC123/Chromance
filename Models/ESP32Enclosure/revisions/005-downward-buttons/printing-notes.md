# Printing and assembly notes

Model geometry in millimeters; no slicer profile or physical testing applied.

- Revision005 preserves the revision004 body, lid, PCB clamps and internal M3x5 actuator geometry. The new desk bracket and two extended finger-pad sliders are the only changed print parts. Revisions001..004 remain preserved.
- The enclosure and its hardware rotate 180 degrees about X, then translate by Z=38 mm. The USB/button side stays -X; the cable end changes from +Y to -Y. World +Z points toward the desk.
- The floor faces the desk with 2 mm clearance below the bracket plate. The lid and extended paddle faces point downward: reach from below and press upward through 0.8 mm nominal travel.
- Each existing finger pad is extended 7 mm in its original local +Z direction, with 0.6 mm overlap and a new 0.5 mm top chamfer. Guide, magnets, contact insert, nylon tip and positive stops are unchanged; motion remains rigid 1:1.
- All button parameters and their original measurement fields remain in the source frame. Use mount_transform for world placement and slider_pad_extensions for the added pads; buttons[name].pad_world gives the new exposed faces and press direction.
- Desk contact remains at Z=43.2 mm and all four desk screw positions are unchanged. Straight bracket legs leave 0.6 mm belt clearance along the full insertion path and 0.3 mm clearance to the existing ear gussets.
- The new bracket uses four additional M3x5 heat-set inserts, replacing its four former captive hex nuts. Existing M3x10 screws pass upward through the flipped 5 mm ears for 5 mm nominal insert engagement and 0.4 mm blind-tip clearance. The eight lid/PCB nuts remain unchanged.
- Bracket insert OD 4.6 mm and pilot 4 mm remain provisional. Blind pilot depth is 5.4 mm; the printed legs retain 1.9 mm inboard and 2 mm Y material to the insert envelope. Verify the actual insert drawing and a printed fit coupon.
- Install the bracket inserts from the lower leg faces on the bench. Fix the bracket to the desk, raise the enclosure vertically between its legs, and fit the four M3x10 screws from below. Select desk screw penetration after measuring desk material and thickness.
- Each bracket insert intentionally displaces its own pilot. The exact insert/desk_bracket host pairs are declared separately from unexpected interference; hardware proxies are excluded from printed exports.
- The original ears and their ribs carry enclosure weight through the four M3 screws into the bracket posts and crossbars. Top gussets distribute post load. No strength or creep load rating is assigned.
- With the PCB inverted, its four removable edge clamps support board weight. Confirm the provisional 0.8 mm bare-edge overlap and retention; secure heavy cables independently.
- Print the new bracket with its desk-contact face on the bed. Print the extended sliders with their new finger-pad faces on the bed, matching the original slider rotation; the longer extensions raise the arms and guides farther from the bed, so local removable supports are needed. Protect guide and magnet fits from support scars.
- All remaining parts retain revision004 print orientation. The M3x5 contact inserts, nylon M3x12 adjusters, short M3x4 body inserts, magnets and travel stops remain unchanged at default settings. Contact adjustment requires lid access; the BOOT-side PCB clamp requires cartridge removal.
- Support the electronics when opening the downward-facing lid. Remove the enclosure for initial wiring, slider service and calibration. Do not substitute metal contact tips over the PCB.
- Current board outline 52x70 mm, PCB 1.6 mm, solder clearance 6 mm and component/wire clearance 22 mm remain provisional. Actual connectors, switch positions, magnetic force, printed fit, strength, temperature and RF behavior require physical validation.
- Retain base_model.py, button_module.py and mounting.py beside this wrapper. These exact revision004 files define the preserved source geometry; the wrapper contains the three revision005 changes.
