# Printing and assembly notes

Model geometry in millimeters; no slicer profile or physical testing applied.

- Print one frame and four clamps at 100% scale. Interfaces are exact revision011 body/clamp geometry, cropped at clamp-top height, with a central floor window to reduce material.
- Body frame floor-down and clamps flat match the final orientation. Use the intended final material/nozzle/layer height/compensation; these geometry 3MF files contain no verified slicer profile.
- Use four M3x5 heat-set inserts and four M3x6 socket screws. OD4.6/pilot4.0 mm are provisional. Install flush before placing the board; do not substitute M3x8 screws, which bottom in the blind pilots.
- Place the unpowered 49x70x1 mm PCB on all four shelves. Check that shelves and clamps touch bare board only, with no solder/component contact. Tighten clamps onto their printed shoulders without bending the board.
- Measure the 49.8 mm locating gap and 47.4 mm gap between inner ledge faces at both front/rear pairs. Capture slot is 1.2 mm high, leaving 0.2 mm nominal vertical play for the 1 mm board.
- Support the board while turning the assembled frame over; it must stay captured without rocking or slipping off the ledges. Verify the actual 52 mm populated span clears the clamps.
- Start with supports off and inspect short horizontal pilot roofs in the slicer. The center window omits underside collision checking there; check protrusions against the 6.6 mm allowance separately.
- This short open frame cannot establish full shell stiffness/warping, long heat-set tool reach, button alignment, lid or mount fit, or load capacity. Physical results remain pending.
