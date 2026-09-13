# Printing and assembly notes

Model geometry in millimeters; no slicer profile or physical testing applied.

- For an existing revision013 assembly or test008/test007 frame, print the RESET slider, BOOT slider and BOOT frame after the archived reuse comparison passes. replacements-only.3mf contains these three exact production parts.
- For a new setup, print the thirteen-part layout: low frame, four clamps and both four-piece button cartridges. All interfaces and button print orientations are exact revision014 geometry.
- Keep 100% scale and use the intended final filament, nozzle, layer height and compensation. Sliders retain their production pad-face-down orientation and need local support under the elevated arms/guides; protect sliding and magnet-fit surfaces.
- Hardware: four M3x5 PCB inserts and four M3x6 clamp screws; four short M3x4 cartridge inserts and four M3x18 mounting screws; two M3x5 contact inserts, two M3x12 nylon adjusters, two nylon jam nuts and four 4x2 mm magnets. Actual insert OD/pilot fit remains provisional.
- Heat-set before fitting the PCB or magnets. Install the board and its clamps before the cartridges. Do not substitute M3x8 PCB screws or metal contact screws.
- The frame uses the same low crop and central floor window as test007. It does not check central underside solder clearance, full-height walls, lid/tool access or case stiffness.
- Place the 49x70x1 mm board on the ledges at Z9; align by equal side/end gaps before checking the nominal measured tip centers. The board can move +/-0.65 mm in X and+/-0.4 mm inY, so verify contact at its movement limits too.
- Switch XY is measured; switch height/travel remain provisional. Back the nylon tips away first, then adjust with the real board. Confirm both switches release at rest and that the printed stops act before damaging switch overtravel.
- Place like magnet poles facing each other. Check smooth return and repeatable hard stops through the entire stroke; magnetic force and actual sliding fit need physical testing.
- After a first bench check, support the board while inverting the jig and test press-up operation with the PCB seated against its clamps. Its 0.2 mm vertical play changes the effective idle gap.
- Fit the actual USB plug and route the actual wiring during travel checks. The shortened frame cannot establish every full-shell connector clearance; the preserved production interface and any digital probe are not a substitute for the real plug.
- The measured USB plug is modeled conservatively as a 10 mm wide, 6 mm thick box projecting 20 mm beyond the board edge, centered 23 mm from the bottom, with underside 9 mm above the PCB. Cable diameter is 3.5 mm. Nominal and PCB-play probe results are reported separately; do not infer physical fit at all board positions. This USB measurement does not resize the unchanged 8 mm power-cable cradle.
- The omitted lid inner face is local Z32. Measure the adjusted contact head against that plane or close the real lid during the three-part trial; no fictitious component height or extra printed gauge is included.
