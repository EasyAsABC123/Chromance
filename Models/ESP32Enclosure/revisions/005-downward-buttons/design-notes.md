# Downward-facing buttons — revision 005

The enclosure mounts with its lid facing the floor and its button faces exposed
below the cartridges. Press a paddle **upward toward the desk**. The complete
enclosure, PCB and cartridge mechanism turn together, so each contact still
presses its switch in the correct direction. Revisions 001–004 remain preserved.

**Three printed parts change: the desk bracket and the two sliders.** The
sliders' finger pads extend 7 mm farther outward, bringing the downward-facing
surfaces below the mounting ears throughout their travel. The internal guide,
magnet seats, stops and heat-set contact geometry retain revision 004 dimensions.
The body, lid, PCB clamps and cartridge frames/keepers are reusable. Turning a
cartridge alone would reverse its motion and misalign its contact; this revision
changes the complete case mounting orientation.

The new bracket reaches around the inverted case. Its straight legs clear the
original mounting ribs and projecting trim during installation as well as in the
final position. Four M3×5 heat-set inserts replace its former captive hex nuts.
The desk surface and green upward arrows in
`under-desk.png` show the intended installation and finger movement; they are
illustrations and are excluded from printable exports.

## Mounting and service

1. Fit four M3×5 heat-set inserts into the empty bracket from its lower mating
   faces. Keep them flush and let them cool. Install the bracket onto the desk
   with screws selected for its material and thickness, with the enclosure detached.
2. Assemble the electronics and cartridges using revision 004's hardware and
   contact-adjustment procedure. The M3×5 insert outside diameter and pilot remain
   provisional: nominal OD4.6 mm, pilot Ø4.0 mm. The four separate cartridge
   mounting inserts are still 4 mm long. There are now six M3×5 inserts total:
   four in the desk bracket and two in the contact sliders. Eight shell/clamp
   hex nuts remain; the four original bracket hex nuts are no longer used.
3. Lift the enclosure vertically into the bracket with its lid facing downward.
   Secure its four mounting ears upward using the existing M3×10 screws; each
   passes through the 5 mm ear and engages the 5 mm bracket insert. Keep wires
   clear of the bracket and secure the cable
   strain relief. The printed clamps retain the PCB in the inverted installation.
4. Confirm that both paddles release their switches at rest and return freely after
   an upward press. The existing 0.8 mm travel, 0.6 mm idle gap and 0.2 mm modeled
   switch depression are unchanged; actual switch travel and force need checking.
5. Check the lid and all mounting screws before use. Remove the obstructing BOOT
   cartridge before servicing the left-front PCB clamp, as in revision 004.

The separate external power supply remains outside this enclosure. Button
coordinates, PCB outline, connector envelopes and wiring clearances are still
photo-based assumptions. No physical printing or load testing has been performed.

## Printing

The replacement bracket prints with its desk-contact face on the bed, leaving
its insert pilots open upward. No supports are modeled. The extended sliders
retain the previous print orientation but raise their arms farther above the
bed, so provide local removable support beneath the arms. Keep guide and magnet
surfaces free of support scars. The other twelve parts retain their geometry
and print orientation; already printed parts that fit can be reused.

Unfilled PETG remains the initial material candidate. The longer bracket legs
change the mounting load path; geometry checks do not establish a load rating.
Material, layer bonding, fasteners and the actual desk must be assessed before
relying on the mount. Magnet return and finished-device RF behavior remain
unverified physically.

## Source and coordinates

`base_model.py`, `button_module.py` and `mounting.py` preserve revision 004's
parametric enclosure mechanism. The new `model.py` builds it, applies the mounting
transform, extends the external pad faces, and substitutes the new bracket.
Retain these files with the parameters
and build/render helpers; use `build-revision.py` to freeze them into a new build.

Cartridge parameter coordinates remain in the original local frame so contact
and stroke settings retain their meaning. Mounted coordinates and the upward
press direction are reported separately. The STEP assembly shows the mounted
orientation; individual STEP/3MF files retain their print orientations.

The Fusion export helper can convert these STEP files inside Fusion. Native
`.f3d` export has not been executed on the Linux development host, and STEP
conversion does not recreate a Fusion feature timeline.

## Digital checks

All fifteen parts passed CAD validity, STEP/3MF read-back and independent FreeCAD
reopening. The mounting checks passed the default dimensions, a 4 mm gap above
the case floor, and a 56 × 78 mm board variant. Both centered 20 mm fingertip
envelopes clear the assembly at rest, half travel and full travel. The case's
vertical installation path was checked up to 50 mm below its mounted position.

At default dimensions, the pads are 1.2 mm below the mounting-ear underside at
full press. Bracket legs leave 0.6 mm around the projecting trim and 0.3 mm beside
the original gussets. The bracket inserts retain 1.9 mm of material inboard and
2.0 mm along Y; M3×10 screws have 5 mm nominal engagement and 0.4 mm tip clearance.
These are modeled dimensions and envelopes, not measured print or hand fit.
