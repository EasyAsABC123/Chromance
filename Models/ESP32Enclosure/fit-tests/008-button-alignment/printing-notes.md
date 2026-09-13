# Printing and assembly notes

Model geometry in millimeters; no slicer profile or physical testing applied.

- For an existing revision012 assembly or test007 frame, start with the two new sliders after the archived reuse comparison passes. sliders-only.3mf contains only these two production parts.
- For a new setup, print the thirteen-part layout: low frame, four clamps and both four-piece button cartridges. All interfaces and button print orientations are exact revision013 geometry.
- Keep100% scale and use the intended final filament, nozzle, layer height and compensation. Sliders retain their production pad-face-down orientation and need local support under the elevated arms/guides; protect sliding and magnet-fit surfaces.
- Hardware: four M3x5 PCB inserts and four M3x6 clamp screws; four short M3x4 cartridge inserts and four M3x18 mounting screws; two M3x5 contact inserts, two M3x12 nylon adjusters, two nylon jam nuts and four4x2 mm magnets. Actual insert OD/pilot fit remains provisional.
- Heat-set before fitting the PCB or magnets. Install the board and its clamps before the cartridges. Do not substitute M3x8 PCB screws or metal contact screws.
- The frame uses the same low crop and central floor window as test007. It does not check central underside solder clearance, full-height walls, lid/tool access or case stiffness.
- Place the49x70x1 mm board on the ledges atZ9; align by equal side/end gaps before checking the nominal measured tip centers. The board can move+/-0.65 mm inX and+/-0.4 mm inY, so verify contact at its movement limits too.
- Switch XY is measured; switch height/travel remain provisional. Back the nylon tips away first, then adjust with the real board. Confirm both switches release at rest and that the printed stops act before damaging switch overtravel.
- Place like magnet poles facing each other. Check smooth return and repeatable hard stops through the entire stroke; magnetic force and actual sliding fit need physical testing.
- After a first bench check, support the board while inverting the jig and test press-up operation with the PCB seated against its clamps. Its0.2 mm vertical play changes the effective idle gap.
- Fit the actual USB plug and route the actual wiring during travel checks. The shortened frame cannot establish every full-shell connector clearance; the preserved production interface and any digital probe are not a substitute for the real plug.
- At published defaults the provisional8x6 mm plug box conflicts with the left-front PCB clamp screw head, and its straight outer approach conflicts with the BOOT frame. Plugging in before cartridge assembly only addresses the outer approach, not the clamp-head conflict; the actual plug must be checked.
- The omitted lid inner face is localZ32. Measure the adjusted contact head against that plane or close the real lid during the two-slider trial; no fictitious component height or extra printed gauge is included.
