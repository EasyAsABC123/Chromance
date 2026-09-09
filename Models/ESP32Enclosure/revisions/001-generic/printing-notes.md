# Printing and assembly notes

Model geometry in millimeters; no slicer profile or physical testing applied.

- Initial material candidate: unfilled PETG for a room-temperature electronics housing and bracket; confirm actual board temperature and printer capabilities before choosing a print profile. No load rating is assigned.
- PETG material reference: https://help.prusa3d.com/article/petg_2059 . Orientation/support design reference: https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135 .
- Generic reference-image prototype; 52x70 mm PCB outline is provisional, not a calibrated measurement.
- User estimates populated electronics at 52x70x15 mm; whether 15 mm is overall stack or above-board height is unconfirmed.
- Current clearances: 6 mm below PCB and 22 mm above it; default 22 mm upper allowance uses estimated 15 mm plus 7 mm for wiring.
- PCB thickness 1.6 mm and underside solder clearance remain conservative assumptions.
- Assumption: enclosure contains only low-voltage board/wiring; existing external power supply is excluded.
- Verify all board dimensions, solder protrusions, connector positions and edge-clamp clearances before printing.
- No board-hole pattern is assumed. Four removable clamps overlap 0.8 mm of PCB edge at Y=+/-17 mm.
- Side shoulders and low end stops allow 0.4 mm nominal board movement per direction; verify bare-edge clearance.
- PCB clamp vertical play is 0.2 mm; lid locating clearance is 0.3 mm per side.
- Open-edge left-side access and +Y cable notch admit prewired electronics; they are generous placeholders.
- Default hardware: 8 M3x10 mm screws (4 lid, 4 bracket), 4 M3x8 mm screws (PCB clamps), 12 standard M3 hex nuts.
- M3 nut nominal AF 5.5 mm/height 2.4 mm; current printable pockets AF 5.8 mm/height 2.7 mm.
- Desk holes are 4.5 mm clearance. Choose desk screw type/length only after desk material and thickness are known.
- Body prints floor-down. Lid exterior face and bracket desk-contact face print on the bed. Clamps print flat.
- No modeled supports. Short bridges over nut pockets and mounting flanges need slicer review; support must not fill pockets.
- Physical fit, strength, thermal behavior and RF performance remain unvalidated.
