"""Local cartridge attachment pads; intended to be retained with model source."""
from build123d import Align, Cylinder, Pos, RectangleRounded, Rot, extrude


def add_mounts(body, face_x, housing_centers_y, *, hole_z=5.0,
               hole_y_offset=3.0, pilot_diameter=4.0, bore_depth=4.4):
    """Join bed-supported pads and blind bores outside the existing cavity.

    face_x = original shell -X outside face minus 3.6 mm. The pad overlaps
    1.0 mm into that wall, including 0.2 mm across its bottom chamfer footprint.
    Nominal inserts: M3 short, length4 / outside diameter4.6 mm.
    Pilot fit is printer/material dependent and must be tested before fitting.
    """
    if not 3.8 <= pilot_diameter <= 4.2 or not 4.2 <= bore_depth <= 4.5:
        raise ValueError("Pilot hole/depth must stay 3.8..4.2 / 4.2..4.5 mm")
    centers = []
    for y in housing_centers_y:
        pad = Pos(face_x+2.3, y, 0) * extrude(RectangleRounded(4.6, 14.0, 0.8), amount=9.3)
        body += pad
        for dy in (-hole_y_offset, hole_y_offset):
            yy = y + dy
            hole = Pos(face_x-0.01, yy, hole_z) * Rot(Y=90) * Cylinder(
                pilot_diameter/2, bore_depth+0.01,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
            body -= hole
            centers.append([face_x, yy, hole_z])
    return body, centers
