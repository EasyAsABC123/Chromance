"""Independent lid-to-body heat-set validation against preserved revision005."""
import argparse
import hashlib
import importlib.util
import json
from math import cos, pi, sin
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import fdm_cad.build
import numpy as np
import trimesh
from build123d import Align, Box, Compound, Cylinder, Pos


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes(root):
    # Only the actual CAD inputs: render/build helpers may be prepared in parallel.
    names = ("model.py", "base_model.py", "button_module.py", "mounting.py", "parameters.json", "params.json")
    return {name: sha(root/name) for name in names if (root/name).is_file()}


def params_at(root):
    for name in ("parameters.json", "params.json"):
        if (root/name).exists():
            return json.loads((root/name).read_text())
    raise FileNotFoundError(f"No parameter file in {root}")


def volume(shape):
    if shape is None:
        return 0.0
    if hasattr(shape, "volume"):
        return abs(float(shape.volume))
    return sum(volume(item) for item in shape)


def normalize(shape):
    return shape if hasattr(shape, "bounding_box") else Compound(list(shape))


def overlap(a, b):
    a, b = normalize(a), normalize(b)
    aa, bb = a.bounding_box(), b.bounding_box()
    if any(min(tuple(aa.max)[i], tuple(bb.max)[i])-max(tuple(aa.min)[i], tuple(bb.min)[i]) <= 1e-8
           for i in range(3)):
        return 0.0
    return volume(a.intersect(b))


def require(ok, message, **data):
    if not ok:
        raise AssertionError({"check": message, **data})


def cyl(r, h, x=0, y=0, z=0):
    return Pos(x, y, z)*Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def box(w, d, h, x=0, y=0, z=0):
    return Pos(x, y, z)*Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


_meshes = {}


def mesh(shape):
    cached = _meshes.get(id(shape))
    if cached is not None and cached[0] is shape:
        return cached[1]
    vertices, faces = shape.tessellate(.01, .1)
    result = trimesh.Trimesh(vertices=[list(v) for v in vertices], faces=faces, process=True)
    require(result.is_volume, "Comparison mesh is not a closed volume")
    _meshes[id(shape)] = (shape, result)
    return result


def same(a, b, message):
    require(abs(volume(a)-volume(b)) <= 1e-5, message+": volume", a=volume(a), b=volume(b))
    aa, bb = mesh(a), mesh(b)
    if (aa.vertices.shape == bb.vertices.shape and aa.faces.shape == bb.faces.shape
            and np.allclose(aa.vertices, bb.vertices, atol=1e-7, rtol=0)
            and np.array_equal(aa.faces, bb.faces)):
        return
    # Avoid the OCC coincident-slider Boolean failure observed in prior reviews.
    left = trimesh.boolean.difference([aa, bb], engine="manifold")
    right = trimesh.boolean.difference([bb, aa], engine="manifold")
    dv = [0 if len(s.faces) == 0 else abs(float(s.volume)) for s in (left, right)]
    require(max(dv) <= .001, message+": geometry", differences_mm3=dv)


def clear(shape, parts, label):
    hits = {name: overlap(shape, part) for name, part in parts.items()}
    require(max(hits.values(), default=0) <= 1e-5, label, overlaps_mm3=hits)
    return hits


def validate_case(module, params, old, label):
    print(f"{label}: build", flush=True)
    p = module.DEFAULTS | params
    new = module.build(params)
    require(set(new["parts"]) == set(old["parts"]) and len(new["parts"]) == 15,
            "Printed part inventory changed")
    preserved = []
    for name, shape in new["parts"].items():
        require(shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0,
                "Invalid printable solid", name=name)
        require(abs(shape.bounding_box().min.Z) <= 1e-6, "Printable part is off bed", name=name)
        if name != "body":
            same(shape, old["parts"][name], name+" print geometry")
            same(new["assembly"][name], old["assembly"][name], name+" world geometry")
            preserved.append(name)
    transform = new["mount_transform"]
    for point in ((0, 0, 0), (1, 2, 3)):
        np.testing.assert_allclose(list((transform*Pos(*point)).position),
                                   list((old["mount_transform"]*Pos(*point)).position), atol=1e-8)
    local_body = new["case_local_assembly"]["body"]
    old_body = old["case_local_assembly"]["body"]
    same(new["parts"]["body"], local_body, "Body print orientation")
    same(new["assembly"]["body"], transform*local_body, "Body world transform")
    rim = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]+p["component_clearance"]
    cw = p["pcb_width"]+2*p["side_margin"]
    cl = p["pcb_length"]+2*p["end_margin"]
    centers = [(sx*(cw/2-4), sy*(cl/2-4)) for sx in (-1, 1) for sy in (-1, 1)]
    pilot = p["lid_insert_pilot_diameter"]
    depth = p["lid_insert_bore_depth"]
    insert_od, insert_length = p["lid_insert_outer_diameter"], p["lid_insert_length"]
    insert_bottom, pilot_bottom = rim-insert_length, rim-depth
    bearing = rim+p["lid_thickness"]
    tip = bearing-p["lid_screw_length"]
    engagement = min(insert_length, p["lid_screw_length"]-p["lid_thickness"])
    require(abs(engagement-insert_length) <= 1e-8, "Lid screw does not engage full insert")
    require(tip-pilot_bottom >= .4-1e-8, "Lid screw lacks bottom clearance")
    require(4.4-insert_od/2 >= 2.0-1e-8, "Lid insert wall too thin")
    print(f"{label}: intended post geometry and restored nut slots", flush=True)

    # Independently reconstruct the intended feature replacement from old005:
    # restore the full four original cylinders, then drill the new round bores.
    expected = old_body
    allowed = None
    for x, y in centers:
        expected = expected+cyl(4.4, rim-p["floor"], x, y, p["floor"])
        region = box(8.82, 8.82, rim-21.9+.1, x, y, 21.9)
        allowed = region if allowed is None else allowed+region
    for x, y in centers:
        expected = expected-cyl(pilot/2, depth+.1, x, y, pilot_bottom)
    expected_differences = [volume(local_body.cut(expected)), volume(expected.cut(local_body))]
    require(max(expected_differences) <= 1e-4, "Body differs from independent round-post reconstruction",
            differences_mm3=expected_differences)
    outside_new, outside_old = local_body.cut(allowed), old_body.cut(allowed)
    outside_differences = [volume(outside_new.cut(outside_old)), volume(outside_old.cut(outside_new))]
    require(max(outside_differences) <= 1e-4, "Body changed outside four lid-post zones",
            differences_mm3=outside_differences)
    probes = []
    for x, y in centers:
        inward_y = y-(4 if y > 0 else -4)
        points = {"old_side_entry": (x, inward_y, rim-4.4),
                  "old_hex_wing": (x+2.5, y, rim-4.4),
                  "old_deep_screw_bore": (x, y, rim-9),
                  "blind_bottom": (x, y, pilot_bottom-.05)}
        for name, point in points.items():
            require(local_body.is_inside(point), "Required restored polymer absent", probe=name, point=point)
            if name != "blind_bottom":
                require(not old_body.is_inside(point), "Restoration probe did not sample an old void",
                        probe=name, point=point)
        clear(cyl(pilot/2-.01, depth-.02, x, y, pilot_bottom+.01), {"body": local_body},
              "Round pilot bore is obstructed")
        for angle in range(0, 360, 30):
            a = angle*pi/180
            require(local_body.is_inside((x+4.35*cos(a), y+4.35*sin(a), rim-2)),
                    "Original outer post cylinder is missing", angle=angle)
        probes.append({"center_xy_mm": [x, y], "restored_polymer_probes": points,
                       "pilot_bottom_z_mm": pilot_bottom, "radial_wall_to_insert_mm": 4.4-insert_od/2})

    print(f"{label}: lid closure, hardware and tool access", flush=True)
    clear(new["assembly"]["body"], {n: s for n, s in new["assembly"].items() if n != "body"},
          "Modified body collides with assembled print parts")
    # The original lid and skirt already passed geometry equality above.
    displacement = pi/4*(insert_od**2-pilot**2)*insert_length
    extra_names = set(new["hardware"])-set(old["hardware"])
    require(len(extra_names) == 8 and set(old["hardware"]) <= set(new["hardware"]),
            "Expected exactly eight added lid hardware proxies")
    require(set(new["lid_insert_names"]) | set(new["lid_screw_names"]) == extra_names,
            "Lid hardware names are inconsistent")
    for name, shape in old["hardware"].items():
        same(new["hardware"][name], shape, name+" unchanged hardware")
    expected_pairs = {(e["hardware"], e["printed"]): e["nominal_displaced_envelope_volume_mm3"]
                      for e in new["expected_hardware_intersections"]}
    new_pairs = {(name, "body") for name in new["lid_insert_names"]}
    require({pair for pair in expected_pairs if pair[0] in extra_names} == new_pairs,
            "New hardware overlap allowlist is incorrect")
    hardware_print_hits = []
    for name, shape in new["hardware"].items():
        # Existing18 unchanged proxies only need their collisions with the changed
        # body reconsidered; new8 proxies are checked against all15 print parts.
        against = new["assembly"] if name in extra_names else {"body": new["assembly"]["body"]}
        for host, part in against.items():
            hit = overlap(shape, part)
            expected_hit = displacement if (name, host) in new_pairs else expected_pairs.get((name, host), 0)
            require(abs(hit-expected_hit) <= 1e-5, "Unexpected hardware/print collision",
                    hardware=name, printed=host, overlap_mm3=hit, expected_mm3=expected_hit)
            if hit > 1e-5:
                hardware_print_hits.append({"hardware": name, "printed": host, "volume_mm3": hit})
    for name in extra_names:
        clear(new["hardware"][name], {n: s for n, s in new["hardware"].items() if n != name},
              "New lid hardware collides with hardware")
    mounts = []
    for index, (x, y) in enumerate(centers, 1):
        insert = cyl(insert_od/2, insert_length, x, y, insert_bottom)
        insert -= cyl(1.51, insert_length+.2, x, y, insert_bottom-.1)
        screw = cyl(1.5, p["lid_screw_length"], x, y, tip)+cyl(2.75, 3, x, y, bearing)
        same(new["lid_hardware_local"][f"lid_insert_{index}"], insert, "Independent insert proxy")
        same(new["lid_hardware_local"][f"lid_screw_{index}"], screw, "Independent screw proxy")
        same(new["hardware"][f"lid_insert_{index}"], transform*insert, "World insert placement")
        same(new["hardware"][f"lid_screw_{index}"], transform*screw, "World screw placement")
        driver = transform*cyl(3, 30, x, y, bearing+3+.01)
        driver_hits = clear(driver, new["assembly"] | new["hardware"], "Mounted driver approach blocked")
        iron = transform*cyl(4, 25, x, y, rim+.01)
        without_lid = {n: s for n, s in new["assembly"].items() if n != "lid"}
        without_lid.update({n: s for n, s in new["hardware"].items() if n not in new["lid_screw_names"]})
        iron_hits = clear(iron, without_lid, "Insert tool approach with lid removed is blocked")
        mounts.append({"center_local_xy_mm": [x, y], "insert_z_mm": [insert_bottom, rim],
                       "pilot_bottom_z_mm": pilot_bottom, "screw_tip_z_mm": tip,
                       "thread_engagement_mm": engagement, "bottom_margin_mm": tip-pilot_bottom,
                       "head_bearing_world_xyz_mm": list((transform*Pos(x, y, bearing)).position),
                       "driver_max_overlap_mm3": max(driver_hits.values()),
                       "iron_max_overlap_mm3": max(iron_hits.values())})
    print(f"{label}: PASS", flush=True)
    return {"status": "pass", "part_count": len(new["parts"]), "unchanged_print_parts": preserved,
            "existing_hardware_count": len(old["hardware"]), "total_hardware_count": len(new["hardware"]),
            "body_reconstruction_differences_mm3": expected_differences,
            "body_outside_four_posts_differences_mm3": outside_differences,
            "restored_post_probes": probes, "lid_mounts": mounts,
            "intentional_new_overlap_each_mm3": displacement,
            "observed_hardware_print_overlaps": hardware_print_hits,
            "lid_fastener_measurements": new["measurements"]["lid_fasteners"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", choices=("all", "nominal", "pilot_4_1"), default="all")
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    params = params_at(source)
    before, baseline_before = hashes(source), hashes(baseline)
    report = {"status": "running", "checker_sha256": sha(__file__), "source": str(source),
              "baseline": str(baseline), "source_hashes": before, "baseline_hashes": baseline_before,
              "scenarios": {}, "limits": [
                  "This compatibility revision retains the archived PCB and button geometry; measured49x70x1 board-fit changes are separate.",
                  "Tools are straight6 mm driver and8 mm insert-tool envelopes, not a model of the user's exact tools.",
                  "Threads, insert retention strength, printer tolerances and actual screw length tolerances are not physically validated.",
                  "No button-motion or desk-installation sweep was repeated: fourteen print parts and all existing hardware were compared with005."]}
    try:
        old_module = load(baseline/"model.py", "preserved005")
        new_module = load(source/"model.py", "candidate006")
        require(sha(source/"button_module.py") == sha(baseline/"button_module.py")
                and sha(source/"mounting.py") == sha(baseline/"mounting.py"), "Untouched dependency source changed")
        print("Building preserved005 reference", flush=True)
        old = old_module.build({k: v for k, v in params.items() if k in old_module.DEFAULTS})
        for label in ("nominal", "pilot_4_1"):
            if args.scenario not in ("all", label):
                continue
            variant = dict(params)
            if label == "pilot_4_1":
                variant["lid_insert_pilot_diameter"] = 4.1
            report["scenarios"][label] = validate_case(new_module, variant, old, label)
        try:
            new_module.build(params | {"lid_screw_length": 10.0})
        except ValueError as exc:
            require("clearance" in str(exc) or "bottom" in str(exc), "M3x10 rejected for unrelated reason", error=str(exc))
            report["m3x10_negative_control"] = {"status": "rejected", "reason": str(exc)}
        else:
            raise AssertionError("M3x10 negative control was accepted")
        require(hashes(source) == before, "Candidate source changed during review")
        require(hashes(baseline) == baseline_before, "Preserved baseline changed during review")
        report["status"] = "pass"
    except Exception as exc:
        report["status"] = "fail"
        report["error"] = str(exc)
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+"\n")


if __name__ == "__main__":
    main()
