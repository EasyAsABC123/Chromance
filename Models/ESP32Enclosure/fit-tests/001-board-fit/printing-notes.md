# Printing and assembly notes

Model geometry in millimeters; no slicer profile or physical testing applied.

- Board-fit coupon only; the production revision005 model remains unchanged.
- The tray is an exact low-height intersection of the production body. Four PCB clamps are unchanged production parts.
- Print one tray and four clamps, floor-down/flat as exported. Tray height 12.2 mm; keep scale at 100% in millimeters.
- Use the intended enclosure filament and XY compensation so the fit result transfers. A PLA bench trial can check layout but does not validate PETG tolerances.
- Suggested starting slice: 0.4 mm nozzle, 0.2 mm layers, 3 perimeters, 4 top/bottom layers, 15% infill. These are untested settings, not a supplied slicer profile or time estimate.
- No modeled supports; begin with supports off and inspect the short nut-pocket bridges and horizontal cartridge pilot bores in the slicer.
- Hardware for retention test: four M3x8 screws and four standard M3 hex nuts (assumed AF5.5, height2.4 mm). No inserts or magnets are needed for this test; PCB clamp retention still uses its original hex nuts.
- With power disconnected, load the four PCB-clamp nuts into their -Y side-entry pockets, place the board component-side up, then install the clamps. Tighten only to the printed shoulders; do not force the board flat.
- Check that the board sits on all four ledges without rocking, solder touching the floor, or clamping components/conductors at the board edges.
- Nominal PCB 52x70x1.6 mm, locating opening 52.8x70.8 mm, slot height 1.8 mm.
- The USB/button side is the long open -X edge with two external cartridge pads. The terminal/cable end is +Y, identifiable by the four small zip-tie slots in the floor.
- Test lower connector clearance with actual plugs. This shortened tray cannot validate the full connector corridor, cable exit, upper components/wires, lid, button alignment/travel or desk mount.
- After checking the clamps, hold the assembly over a padded surface and turn it over gently to check retention in the eventual mounted orientation.
- Both PCB faces need bare material at the support/clamp strips. Nominal overlap 0.8 mm falls to 0.4 mm at the opposite lateral stop, while the near strip contacts up to 1.2 mm of the board edge.
- The 0.2 mm vertical board play also changes actuator clearance after inversion. Calibrate contacts with the retained board resting against its clamps in the mounted orientation; otherwise the provisional geometric switch depression can increase from 0.2 to 0.4 mm. This coupon does not test actuators or actual switch travel.
- Record the actual PCB width/length/thickness, maximum underside protrusion, any fouling location and the amount of looseness before revising the enclosure parameters.
