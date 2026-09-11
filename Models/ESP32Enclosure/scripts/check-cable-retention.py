"""Independent bounded geometry review for revision009 cable retention.

Digital geometry checks do not establish physical fit, cable-jacket safety,
material strength, or a strain-relief pull rating.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import fdm_cad.build
import numpy as np
import trimesh
import manifold3d as manifold
from build123d import Align, Box, Compound, Cylinder, Keep, Plane, Pos, Rot, split


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes(root):
    return {name: sha(root/name) for name in
            ("model.py", "base_model.py", "button_module.py", "mounting.py", "parameters.json")
            if (root/name).is_file()}


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
    left = trimesh.boolean.difference([aa, bb], engine="manifold")
    right = trimesh.boolean.difference([bb, aa], engine="manifold")
    dv = [0 if len(s.faces) == 0 else abs(float(s.volume)) for s in (left, right)]
    require(max(dv) <= .001, message+": geometry", differences_mm3=dv)


def clear(shape, parts, label):
    hits = {name: overlap(shape, part) for name, part in parts.items()}
    require(max(hits.values(), default=0) <= 1e-5, label, overlaps_mm3=hits)
    return hits


def section_rectangle(xmin, ymin, xmax, ymax):
    return manifold.CrossSection.square((xmax-xmin, ymax-ymin)).translate((xmin, ymin))


def preserve_inventory(new, old):
    require(set(new["parts"]) == set(old["parts"]) and len(new["parts"]) == 15,
            "Print inventory changed")
    preserved = []
    for name, shape in new["parts"].items():
        require(shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0,
                "Invalid print solid", name=name)
        require(abs(shape.bounding_box().min.Z) < 1e-6, "Print part is off bed", name=name)
        if name != "body":
            same(shape, old["parts"][name], name+" unchanged print")
            same(new["assembly"][name], old["assembly"][name], name+" unchanged world placement")
            preserved.append(name)
    require(set(new["hardware"]) == set(old["hardware"]) and len(new["hardware"]) == 34,
            "Hardware inventory changed")
    for name, shape in old["hardware"].items():
        same(new["hardware"][name], shape, name+" unchanged hardware")
    t = new["mount_transform"]
    for xyz in ((0, 0, 0), (1, 2, 3)):
        np.testing.assert_allclose(list((t*Pos(*xyz)).position),
                                   list((old["mount_transform"]*Pos(*xyz)).position), atol=1e-8)
    body = new["case_local_assembly"]["body"]
    same(new["parts"]["body"], body, "Body print orientation")
    same(new["assembly"]["body"], t*body, "Body mounted orientation")
    clear(body, {name: shape for name, shape in new["case_local_assembly"].items() if name != "body"},
          "New body intersects existing assembled print parts")
    return {"preserved_print_parts": preserved, "preserved_hardware_count": len(new["hardware"])}


def layer_review(body, xy_bounds, z_bottom, z_top):
    """Evaluate actual mesh sections against Euclidean preceding-layer support.

    This local check covers the new cable support, not all legacy print features.
    The rounded crown must shrink upward and the tunnel roof must grow within the
    same allowance as the 45-degree root ramp.
    """
    tm = mesh(body)
    solid = manifold.Manifold(manifold.Mesh(np.asarray(tm.vertices, dtype=np.float32),
                                            np.asarray(tm.faces, dtype=np.uint32)))
    require(str(solid.status()).endswith("NoError"), "Slice manifold is invalid")
    height, allowance, tolerance = .2, .2, .004
    start = np.floor((z_bottom-.3)/height)*height+.1
    heights = np.arange(start, z_top+.05, height)
    region = section_rectangle(*xy_bounds)
    records = []
    previous = solid.slice(float(start-height))
    for z in heights:
        current = solid.slice(float(z))
        local = current ^ region
        unsupported = local-previous.offset(allowance+tolerance, circular_segments=128)
        area = unsupported.area()
        require(area < 1e-5, "Cable support layer exceeds 45-degree support allowance",
                z_mm=float(z), unsupported_area_mm2=area)
        regions = local.decompose()
        # A tunnel can divide a single layer into two supported banks. The
        # previous-layer coverage above determines whether either starts floating;
        # a two-dimensional island count cannot establish three-dimensional
        # connectivity through the floor below the tunnel.
        records.append({"z_mm": float(z), "excess_area_mm2": area,
                        "connected_regions": len(regions)})
        previous = current
    # A deliberately floating patch must fail this exact same area test.
    prior = section_rectangle(0, 0, 2, 2)
    floating = section_rectangle(3, 0, 4, 1)
    negative = (floating-prior.offset(allowance+tolerance)).area()
    require(negative > .5, "Layer support negative control failed")
    return {"layer_height_mm": height, "allowed_horizontal_advance_mm": allowance,
            "tessellation_allowance_mm": tolerance, "layer_count": len(records),
            "maximum_excess_area_mm2": max(r["excess_area_mm2"] for r in records),
            "floating_patch_negative_control_mm2": negative, "slices": records}


def check_case(module, params, old, label):
    print(label+": build and preserved interfaces", flush=True)
    p = module.DEFAULTS | params
    new = module.build(params)
    inventory = preserve_inventory(new, old)
    body = new["case_local_assembly"]["body"]
    original = old["case_local_assembly"]["body"]
    radius = p["cable_saddle_radius"]
    projection = p["cable_saddle_projection"]
    embedded = p["cable_saddle_wall_overlap"]
    end_y = p["pcb_length"]/2+p["end_margin"]
    rim = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]+p["component_clearance"]
    sill = rim-p["end_cable_height"]
    crown, root = sill+radius, sill-projection
    start_y, stop_y = end_y-projection, end_y+embedded
    tie_y = (start_y+end_y)/2
    tie_w, tie_t = p["zip_tie_width_provisional"], p["zip_tie_thickness_provisional"]
    gap_y, gap_z = p["zip_tie_slot_side_clearance"], p["zip_tie_slot_vertical_clearance"]
    slot_w = tie_w+2*gap_y
    slot_floor = sill-p["zip_tie_slot_floor_below_sill"]
    slot_eave = slot_floor+tie_t+2*gap_z
    slot_apex = slot_eave+slot_w/2
    cable_d = p["cable_diameter_provisional"]
    cable_z = crown+cable_d/2

    print(label+": independent halfspace reconstruction", flush=True)
    # Author extrudes a polygon. Independently clip a rectangular block with the
    # 45-degree underside halfspace; its lower face limits the embedded wall leg.
    block = box(2*radius, stop_y-start_y, sill-root,
                y=(start_y+stop_y)/2, z=root)
    wedge = split(block, Plane(origin=(0, end_y, root), z_dir=(0, 1, 1)), keep=Keep.TOP)
    tube = Pos(0, (start_y+stop_y)/2, sill)*Rot(X=90)*Cylinder(
        radius, stop_y-start_y, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    cap = normalize(tube.intersect(box(2*radius+.2, stop_y-start_y+.2, radius+.1,
                                      y=(start_y+stop_y)/2, z=sill)))
    stock = wedge+cap
    passage = box(2*radius+4, slot_w, slot_apex-slot_floor,
                  y=tie_y, z=slot_floor)
    passage = split(passage, Plane(origin=(0, tie_y, slot_apex), z_dir=(0, 1, 1)), keep=Keep.BOTTOM)
    passage = split(passage, Plane(origin=(0, tie_y, slot_apex), z_dir=(0, -1, 1)), keep=Keep.BOTTOM)
    feature = stock-passage
    same(feature, new["cable_retention_local"], "Independent saddle and tunnel reconstruction")
    same(stock, new["cable_retention_stock_local"], "Independent support stock reconstruction")
    same(original, new["cable_retention_reference_body_local"], "Baseline body reference")
    expected = original+feature
    differences = [volume(body.cut(expected)), volume(expected.cut(body))]
    require(max(differences) < 1e-4, "Body differs from independent reconstruction", differences_mm3=differences)
    added = normalize(body.cut(original))
    removed = volume(original.cut(body))
    require(removed < 1e-4, "Existing body material removed", removed_mm3=removed)
    require(added.volume > 100, "Support adds no useful body geometry")
    same(added, new["cable_retention_added_local"], "Declared added material")
    allowed = box(2*radius+.2, stop_y-start_y+.2, crown-root+.2,
                  y=(start_y+stop_y)/2, z=root-.1)
    require(volume(added.cut(allowed)) < 1e-5, "Body changed outside bounded cable support")
    require(feature.is_valid and len(feature.solids()) == 1, "Cable saddle is disconnected")
    bond = overlap(stock, original)
    require(bond > 10, "Saddle lacks volumetric wall connection", volume_mm3=bond)
    np.testing.assert_allclose(list(body.bounding_box().min), list(original.bounding_box().min), atol=1e-7)
    np.testing.assert_allclose(list(body.bounding_box().max), list(original.bounding_box().max), atol=1e-7)

    print(label+": routing, insertion, hardware and component envelopes", flush=True)
    refs = new["cable_retention_references_local"]
    require(set(refs) == {"cable", "zip_tie_route", "zip_tie_head", "zip_tie_straight_threading_segment"},
            "Missing routing geometry")
    for name, shape in refs.items():
        require(shape.is_valid and len(shape.solids()) == 1, "Invalid reference envelope", name=name)
        clear(shape, new["case_local_assembly"], name+" collides with an assembled print part")
    # An independently sized strip traverses beyond both tunnel mouths, proving
    # that a free tie tail can be fed in X before closing the loop. The head is
    # deliberately not required to pass through this small band-only tunnel.
    thread_tool = box(2*radius+16, tie_w, tie_t, y=tie_y, z=slot_floor+gap_z)
    clear(thread_tool, new["case_local_assembly"], "Straight tie threading path blocked")
    blocked_thread = overlap(Pos(0, 0, -gap_z-.3)*thread_tool, body)
    require(blocked_thread > .1, "Too-low threading negative control failed", overlap_mm3=blocked_thread)
    expected_cable = Pos(0, (start_y+end_y+p["wall"]+6)/2, cable_z)*Rot(X=90)*Cylinder(
        cable_d/2, end_y+p["wall"]+6-start_y,
        align=(Align.CENTER, Align.CENTER, Align.CENTER))
    same(expected_cable, refs["cable"], "Cable diameter, crown contact and exit direction")
    require(overlap(Pos(0, 0, -.2)*refs["cable"], body) > .1,
            "Cable saddle contact negative control failed")
    require(abs(refs["cable"].bounding_box().min.Z-crown) < 1e-7,
            "Cable does not sit on crown")
    other_open = {name: shape for name, shape in new["case_local_assembly"].items() if name != "lid"}
    cable_access = box(cable_d, end_y+p["wall"]+6-start_y, rim+5-crown,
                       y=(start_y+end_y+p["wall"]+6)/2, z=crown)
    clear(cable_access, other_open, "Cable cannot be laid from the open lid onto the saddle")
    hb = refs["zip_tie_head"].bounding_box()
    head_access = box(hb.size.X, hb.size.Y, rim+5-hb.min.Z,
                      (hb.min.X+hb.max.X)/2, (hb.min.Y+hb.max.Y)/2, hb.min.Z)
    clear(head_access, other_open, "Tie head lacks access through open lid")
    require(overlap(refs["zip_tie_head"], refs["zip_tie_route"]) > .01,
            "Tie head envelope is disconnected from loop envelope")
    require(overlap(refs["zip_tie_route"], refs["cable"]) < 1e-5, "Loose tie route cuts cable")
    require(overlap(refs["zip_tie_head"], refs["cable"]) < 1e-5, "Tie head cuts cable")
    pcb_keepout = box(p["pcb_width"]+.6, p["pcb_length"]+.6,
                      rim-p["floor"]-.2, z=p["floor"]+.2)
    require(overlap(added, pcb_keepout) < 1e-5, "Support enters existing assumed PCB/component envelope")
    hardware_hits = clear(new["mount_transform"]*added, new["hardware"], "New support hits existing hardware")
    button_hits = {}
    for name in ("reset", "boot"):
        for distance in (0, p["button_stroke"]/2, p["button_stroke"]):
            slider = Pos(0, 0, -distance)*new["case_local_assembly"][name+"_slider"]
            hit = overlap(added, slider)
            require(hit < 1e-5, "New support obstructs button travel", button=name, stroke=distance)
            button_hits[f"{name}_{distance:g}"] = hit
    require(crown-slot_apex >= 2-1e-8, "Less than2 mm above tunnel center apex")
    minimum_floor = slot_floor-(sill-projection/2+slot_w/2)
    require(minimum_floor >= .8-1e-8, "Tunnel inboard floor too thin")
    top = max(refs[name].bounding_box().max.Z for name in ("cable", "zip_tie_route", "zip_tie_head"))
    require(rim-top >= 2-1e-8, "Cable/tie/head too close to lid")
    require(refs["zip_tie_head"].bounding_box().max.X <= p["end_cable_width"]/2-.5+1e-8,
            "Tie head exceeds exit width reserve")
    print(label+": actual mesh layers around support and tunnel", flush=True)
    layers = layer_review(body, (-radius-.1, start_y-.1, radius+.1, stop_y+.1), root, crown)
    return {"scenario": label, "status": "passed", **inventory,
            "independent_body_difference_mm3": differences, "removed_body_volume_mm3": removed,
            "added_body_volume_mm3": float(added.volume), "wall_stock_bond_mm3": bond,
            "cable_diameter_mm": cable_d, "tie_band_width_mm": tie_w, "tie_band_thickness_mm": tie_t,
            "tunnel_width_mm": slot_w, "tunnel_center_roof_material_mm": crown-slot_apex,
            "minimum_tunnel_inboard_floor_mm": minimum_floor, "envelope_to_lid_mm": rim-top,
            "low_thread_negative_control_overlap_mm3": blocked_thread,
            "new_material_hardware_overlaps_mm3": hardware_hits,
            "button_stroke_overlaps_mm3": button_hits, "layer_review": layers,
            "limitations": ["Digital geometry only; physical cable/tie fit pending.",
                            "Tie loop is a loose assembly envelope, not a bent hardware model.",
                            "No pull rating, jacket damage limit, material strength, or print-time claim.",
                            "Existing nominal52x70 board model retained; measured49 mm layout not integrated."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    before = hashes(source)
    module = load(source/"model.py", "cable_retention_under_review")
    previous = load(baseline/"model.py", "cable_retention_baseline")
    p = json.loads((source/"parameters.json").read_text())
    old_p = json.loads((baseline/"parameters.json").read_text())
    require({k: v for k, v in p.items() if k in old_p} == old_p,
            "Existing parameter values changed")
    print("Build frozen baseline008", flush=True)
    old = previous.build(old_p)
    results = [check_case(module, p, old, "nominal_6mm_cable_2_5mm_tie")]
    variant = p | {"cable_diameter_provisional": 8.0, "zip_tie_width_provisional": 3.0,
                   "cable_saddle_radius": 4.5, "cable_saddle_projection": 7.5}
    results.append(check_case(module, variant, old, "variant_8mm_cable_3mm_tie_radius4_5_projection7_5"))
    require(results[1]["added_body_volume_mm3"] > results[0]["added_body_volume_mm3"],
            "Radius variant did not enlarge support")
    require(results[1]["tunnel_width_mm"] > results[0]["tunnel_width_mm"],
            "Tie width variant did not enlarge tunnel")
    negatives = {}
    # Exercise validation without paying to rebuild the whole existing enclosure.
    end_y = p["pcb_length"]/2+p["end_margin"]
    rim = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]+p["component_clearance"]
    for name, overrides in {"oversize_cable": {"cable_diameter_provisional": 9},
                            "thin_tunnel_roof": {"cable_saddle_radius": 3.5},
                            "head_exceeds_exit": {"zip_tie_head_width_provisional": 9}}.items():
        try:
            module._cable_saddle(module.DEFAULTS | p | overrides, end_y, rim-p["end_cable_height"], rim)
        except ValueError as error:
            negatives[name] = str(error)
        else:
            raise AssertionError("Invalid parameter case accepted: "+name)
    require(hashes(source) == before, "Source changed during review")
    report = {"status": "passed", "source_hashes": before, "baseline_hashes": hashes(baseline),
              "checker_sha256": sha(Path(__file__)), "scenarios": results,
              "invalid_parameter_checks": negatives}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": report["status"], "report": str(args.output),
                      "scenarios": len(results), "layers": sum(r["layer_review"]["layer_count"] for r in results)}, indent=2))


if __name__ == "__main__":
    main()
