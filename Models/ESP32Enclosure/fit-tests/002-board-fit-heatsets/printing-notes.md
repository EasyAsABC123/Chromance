# Printing and assembly notes

Model geometry in millimeters; no slicer profile or physical testing applied.

- Quick board-fit test only. Published revisions001..005 and the previous fit test remain unchanged.
- Use one tray and four clamps. Actual PCB 49x70x1 mm is centered in the existing 68 mm-wide cavity.
- Four removable edge clamps use M3x6 socket screws and four M3x5 heat-set inserts; no screw passes through the PCB.
- Insert OD4.6 mm and pilot diameter4 mm remain provisional. Confirm against the purchased insert and filament before installation.
- Blind pilot depth 6 mm, insert engagement 4 mm and screw-tip margin 2 mm. With the default dimensions, M3x8 screws bottom and must not be substituted.
- Print tray floor-down and clamps flat, with scale100% in millimeters. No modeled supports; review the four empty lateral pilot bridges in the slicer.
- Install the four vertical heat-set inserts flush before placing the PCB. The four horizontal cartridge pilot bores are retained reference features and stay empty.
- Place the unpowered board on the four ledges, then tighten clamps gently onto the printed shoulders. Do not clamp conductors or components, and do not force a warped board flat.
- Support/clamp strips are8 mm wide at Y+/-17; nominal bare-edge overlap0.8 mm with lateralplay+/-0.4 and verticalplay0.2 mm. Bare edge availability remains unverified.
- The52 mm ESP span is a separate width reference, not the PCB substrate. Actual overhang split and component height at each clamp remain unknown; check with the physical assembly.
- Underside solder allowance remains6 mm. The sketch's12 mm side dimension has unconfirmed endpoints and is not used as a height.
- Measured button XY coordinates are stored without button bodies or actuators. This test does not validate button linkage, upper connector/wire clearance, lid fit or desk mounting.
- Physical fit/strength and slicer settings remain untested. Use the intended enclosure filament and printer compensation so the fit trial transfers.
