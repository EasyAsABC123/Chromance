# Heat-set button contacts — revision 004

Revision 004 preserves the approved console enclosure and magnetic-return paddles,
replacing each actuator's captive nylon nut with an **M3×5 mm heat-set insert**.
Each contact uses an **M3×12 nylon screw and one nylon jam nut**. The original
shell nuts and the separate cartridge mounting inserts are unchanged.

The complete assembly is 116.8 × 95.2 × 43.2 mm with 15 printable parts. The
body, lid, bracket, four PCB clamps, cartridge frames and keepers retain the
revision 003 geometry. Only the two contact sliders change. Revisions 001–003
are preserved separately.

## Contact insert and screw

The insert is provisionally modeled at Ø4.6 × 5 mm. Its pilot is Ø4.0 mm,
5.4 mm deep, with a Ø3.4 mm screw passage through the remaining floor. The
distal boss is Ø9 mm and retains a 1.0 mm annular floor below the pilot and
2.2 mm radial material outside the assumed insert diameter. The lowest boss
corner facing the USB plug is relieved to retain the previous connector corridor.

The insert installs flush with the boss top at Z=24.8 mm. A 12 mm nylon screw
puts the default tip at Z=16.6 mm and the head top at Z=31.6 mm, leaving
0.4 mm beneath the lid, assuming a 3 mm screw-head height and 2.4 mm nut thickness.
The jam nut locks the adjusted contact above the boss.
The nominal downward adjustment available before the screw head meets that
nut is 1.4 mm. These values assume the modeled head and nut dimensions; inspect
the actual hardware before assembly. A switch top at Z=15 mm with the same
screw is also checked as a parameter variant.

`button_contact_insert_outer_diameter`, `button_contact_insert_pilot_diameter`
and `button_contact_insert_length` control the insert. M3×5 alone does not specify
the knurl diameter or recommended pilot. Confirm these using the actual insert
drawing and a coupon in the intended material. The brass insert proxy intentionally
overlaps the undersized pilot: the checks allow only the computed displacement
volume between each insert and its own slider, not other hardware collisions.

## Operation and provisional fit

Press the exposed paddle toward the enclosure floor. Two captive Ø4 × 2 mm
axially magnetized discs face like poles toward each other to return the paddle.
A keyed guide and separate rear keeper constrain movement and provide rigid stops.

Default travel is 0.8 mm, idle contact gap 0.6 mm, and modeled switch depression
0.2 mm. Magnet face separation is 3.6 mm at rest and 2.8 mm when pressed. Actual
switch force/travel and magnetic return are unmeasured. Adjust the tip and stop
so the switch releases fully and cannot take excessive finger load.

The board is provisionally 52 × 70 × 1.6 mm with its upper face at Z=10 mm.
Photo-estimated contact centers are X=-23 mm, EN Y=0 mm, BOOT Y=-17 mm; default
switch-top Z is 16 mm. Housing centers at Y=+4 and -21 mm reserve an 11 mm USB
corridor. The checked interior plug envelope is 11 mm wide × 6 mm tall,
Z=12.3..18.3 mm. Confirm real USB/DC plug bodies, wire routing, board-edge
clamp clearance and button locations; perspective photos do not establish fit.

## Hardware

| Item | Quantity | Assumption |
| --- | ---: | --- |
| Shell/bracket M3×10 screws | 8 | Original design |
| PCB-clamp M3×8 screws | 4 | Original design |
| Shell/bracket/clamp M3 hex nuts | 12 | Original design; AF 5.5 mm, height 2.4 mm |
| Desk screws | 4 | Select for actual desk material and thickness |
| Cartridge M3×18 socket screws | 4 | Head Ø≤5.5 mm, no washer |
| Cartridge M3×4 heat-set inserts | 4 | Nominal OD4.6 mm; pilot Ø4.0 × 4.4 mm |
| **Contact M3×5 heat-set inserts** | **2** | **Provisional OD4.6 mm; pilot Ø4.0 × 5.4 mm** |
| **Nylon M3×12 contact screws** | **2** | **Adjustable nonmetal contact tips** |
| Nylon M3 jam nuts | 2 | One above each contact boss |
| Axially magnetized disc magnets | 4 | Ø4 × 2 mm; return force to test |

The M3×18 mounting screws grip 14.2 mm of plastic and engage the separate
4 mm body inserts by 3.8 mm. Those blind mounting pilots leave 1.6 mm of material
before the enclosure cavity. Do not substitute the longer 5 mm contact inserts
into those unchanged shallow mounting holes.

## Assembly and service

1. Heat-set the four short body inserts and the two 5 mm slider contact inserts
   before installing electronics or magnets. Keep each insert flush and square;
   let it cool before applying screw load. Keep the through passage clear.
2. Install the PCB retention hardware and board before attaching the cartridges.
3. With the rear keeper removed, place the fixed magnet in the frame pocket and
   the moving magnet plus its small keeper in the slider, with like poles facing.
4. Drop the slider vertically into the open-top guide in its final XY position.
   Its offset arm does not feed through the guide from the rear.
5. Fit the rear keeper and secure the cartridge with two M3×18 screws. The rear
   keeper closes the fixed magnet's feed channel and captures the slider lug;
   the frame guide retains the moving magnet's small keeper.
6. Thread the jam nut onto the nylon contact screw, fit the screw into the insert,
   set tip height against the real switch, lock the jam nut and check full release,
   travel stops and repeated return. Check screw-head clearance, then fit the lid
   and mount the enclosure on the desk bracket.

Remove the obstructing cartridge before later PCB-clamp service: the BOOT arm
crosses the left-front clamp screwdriver approach. Contact adjustment needs
access to the enclosure interior.

## FDM and validation limits

Unfilled PETG remains the initial candidate. Body prints floor-down; lid exterior
and bracket desk-contact face go on the bed. Cartridge frames/rear keepers print
on their outer sides. Slider stepped arms require local removable slicer support;
keep support off guides and magnet seats. Small magnet keepers print flat.
Review shell bridges and test insert/guide fits before committing the full set.

All previews come from the CAD geometry. Printable STEP/3MF exports omit hardware.
`hardware-reference.step` contains simplified cartridge hardware without threads;
the original shell hardware and electronics are omitted. The 3MF files do not
contain a verified slicer profile. The package README contains portable rebuild
commands; never overwrite a preserved revision.

Geometry validation does not establish physical fit, load capacity, heat behavior,
RF compatibility or magnetic return. No physical printing has been performed.
Magnets remain outside the pictured USB/button side, opposite the antenna;
finished-device radio testing is still needed. See the existing
[Espressif antenna guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html)
and [K&J guidance on repelling magnets](https://www.kjmagnetics.com/blog/repelling-magnets).
