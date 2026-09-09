# External ESP32 button paddles — design inputs

The user approved revision 002's angles/curves and requested external access to
the ESP32 buttons, suggesting magnets as a return spring. The working direction
is two guided paddles, EN/RESET and BOOT, each with two captive repelling magnets.
Both previous revisions remain preserved.

## Evidence and assumptions

- User-estimated perfboard outline: 52 × 70 mm, populated height about 15 mm.
- The supplied photograph shows EN and BOOT at the USB end of the ESP32 board.
- Provisional button centers relative to the perfboard center: X approximately
  -23 mm; EN Y approximately 0 mm, BOOT Y approximately -17 mm. These are visual
  estimates, not calibrated dimensions.
- Button tops, travel and force are unmeasured. The first CAD mechanism must
  expose adjustable contact height and explicit provisional XY parameters.
- Existing perfboard top is Z=10 mm in assembly coordinates. A provisional
  switch top Z=16 mm is a mechanism layout assumption, not inferred accuracy.
- The left-front PCB clamp sits near BOOT's estimated Y coordinate. The actuator
  arm must clear the clamp and its installed M3 screw head before descending to
  the switch.
- Buttons press toward -Z. The desk lies toward +Z. External pads must be
  reachable from the side while the enclosure remains bolted to the desk.
- Button behavior beyond EN/RESET depends on the user's firmware; this is a
  mechanical interface and does not change ESP32 firmware or wiring.

## Magnetic return and antenna

Repelling magnets need a mechanical guide because they tend to slide or rotate
out of alignment. Source: [K&J Magnetics, Repelling Magnet Forces](https://www.kjmagnetics.com/blog/repelling-magnets).
Magnet grade, separation and alignment determine the force; a cavity dimension
alone is not a validated spring-force specification.

Place new magnets and mechanism hardware outside the USB/button side, opposite
the photo's ESP32 antenna end. Espressif recommends at least 15 mm antenna
clearance within the enclosure and testing the finished product's radio range
and throughput. Source: [ESP32 hardware design guidelines](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board).

This placement reduces proximity of new metal to the antenna; it does not prove
radio compatibility or validate the existing perfboard/antenna arrangement.
Neither magnets nor screws should contact live electronics. Use a nylon contact
screw/tip and adjust it for a released gap, with travel limited independently of
the delicate board-mounted switch.

## Validation target

Check all printable parts as individual valid solids and watertight meshes;
verify neutral-format exports. Sweep the paddles from released to pressed,
checking enclosure, lid, clamp hardware and mutual interference. Inspect the
magnet capture and assembly paths, guide clearance and positive travel stops.
Retain source, auxiliary modules, parameters, a meaningful parameter variant,
hardware list and an actual-geometry mechanism preview.

Physical checks still needed before printing a fitted part: measure button
locations/heights/travel; calibrate tip extension with no idle preload; confirm
return force and release, wiring clearance, print fit and radio performance.
