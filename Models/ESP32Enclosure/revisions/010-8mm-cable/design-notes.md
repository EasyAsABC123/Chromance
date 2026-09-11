# Measured cable update

The user supplied an **8 mm outside diameter** at the cable opening. Revision 010
uses that measurement in both the full enclosure and the quick fit test. The
input key `cable_diameter_provisional` is retained for compatibility, but its
8 mm default is user supplied. Tie width2.5 mm, thickness1 mm and head5×5×4 mm
remain unmeasured assumptions.

The rounded support stays radius4 mm and length8 mm with7 mm inward projection.
Its passage remains3.2 mm wide and1.4 mm straight height with a45° roof. The
support still has2 mm above the roof apex and0.9 mm minimum floor thickness at
the inboard eave. Its crown stays at localZ20; the8 mm cable center isZ24, and
its top isZ28. The loose tie envelope tops out atZ29.3, leaving2.7 mm to the lid
planeZ32. The tie head sits alongside the cable and clears the lid and exit.

All fifteen printed solids, their print/assembly placement, and34 existing
hardware proxies match revision009. The body volume remains46.747 cm³; the
outside assembly dimensions remain116.8×95.2×39.6 mm. No new load, strength,
print-time or filament claim follows from updating the diameter.

The independent [measurement check](cable-validation.json) verifies unchanged
printed geometry and hardware plus the8 mm cable/tie placement and insertion
paths. It references the preserved, hashed revision009 layer-support report;
unchanged printed geometry does not need a repeated layer sweep. The shared
builder and FreeCAD reopen the new exports. The quick coupon is compared with
independently reopened full-part STEP crops.

See [revision009's design notes](../009-cable-retention/design-notes.md) for the
unchanged feature dimensions, assembly hardware, orientation and support strategy.
Use the [new fit-test instructions](../../fit-tests/004-8mm-cable/README.md) to
check the actual cable and tie; physical results remain pending. The new
measurement does not resolve the separate full-board/button layout or wiring
bend-clearance questions.

From `Models/ESP32Enclosure`, rebuild into fresh directories:

```bash
uv run --locked python revisions/010-8mm-cable/build-revision.py --output builds/8mm-cable
uv run --locked python builds/8mm-cable/render-details.py builds/8mm-cable
uv run --locked python scripts/check-measured-cable.py --source builds/8mm-cable \
  --baseline revisions/009-cable-retention --output builds/8mm-cable/cable-validation.json
```
