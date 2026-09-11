"""Independent PCB-clamp heat-set validation against preserved revision006."""
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


def check_geometry(new, old, p):
    changed = {"body"} | {n for n in old["parts"] if n.startswith("pcb_clamp_")}
    require(set(new["parts"]) == set(old["parts"]) and len(new["parts"]) == 15,
            "Printed inventory changed")
    preserved = []
    for name, shape in new["parts"].items():
        require(shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0,
                "Invalid print solid", name=name)
        require(abs(shape.bounding_box().min.Z) <= 1e-6, "Part is off print bed", name=name)
        if name not in changed:
            same(shape, old["parts"][name], name+" unchanged print")
            same(new["assembly"][name], old["assembly"][name], name+" unchanged world placement")
            preserved.append(name)
    t = new["mount_transform"]
    for xyz in ((0, 0, 0), (1, 2, 3)):
        np.testing.assert_allclose(list((t*Pos(*xyz)).position),
                                   list((old["mount_transform"]*Pos(*xyz)).position), atol=1e-8)
    body = new["case_local_assembly"]["body"]
    original = old["case_local_assembly"]["body"]
    bottom = p["floor"]+p["solder_clearance"]
    top = bottom+p["pcb_thickness"]
    clamp_z = top+p["board_vertical_play"]
    inner, outer = p["pcb_width"]/2-p["board_edge_overlap"], p["pcb_width"]/2+8
    shoulder = p["pcb_width"]/2+.4
    old_x = p["pcb_width"]/2+4.5
    new_x = p["pcb_width"]/2+p["pcb_clamp_screw_offset_from_edge"]
    boss_r = p["pcb_clamp_boss_diameter"]/2
    pilot = p["pcb_insert_pilot_diameter"]
    bore_bottom = clamp_z-p["pcb_insert_bore_depth"]
    centers = [(sx*new_x, sy*p["clamp_y"]) for sx in (-1, 1) for sy in (-1, 1)]
    expected = original
    allowed = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            y = sy*p["clamp_y"]
            expected += box(outer-inner, 8, bottom-p["floor"], sx*(inner+outer)/2, y, p["floor"])
            expected += box(outer-shoulder, 8, clamp_z-p["floor"], sx*(outer+shoulder)/2, y, p["floor"])
            region = box(new_x+boss_r-inner+.2, 2*max(4,boss_r)+.2, clamp_z-p["floor"]+.2,
                         sx*(inner+new_x+boss_r)/2, y, p["floor"])
            allowed = region if allowed is None else allowed+region
            name = f"pcb_clamp_{'left' if sx < 0 else 'right'}_{'front' if sy < 0 else 'rear'}"
            clamp = box(outer-inner, 8, 2, sx*(inner+outer)/2, y, clamp_z)
            clamp -= cyl(p["m3_clearance"]/2, 3, sx*new_x, y, clamp_z-.5)
            same(new["case_local_assembly"][name], clamp, name+" only bore moved")
            same(new["parts"][name], Pos(0, 0, -clamp_z)*clamp, name+" print orientation")
            same(new["assembly"][name], t*clamp, name+" world placement")
    # Original ledges/shoulders were cut by the left access. Reapply that cut
    # before adding complete reinforced bosses, just as the intended topology requires.
    shell_width = p["pcb_width"]+2*p["side_margin"]+2*p["wall"]
    rim = top+p["component_clearance"]
    access_z = top+p["left_access_start_above_pcb"]
    expected -= box(p["wall"]+1, p["left_access_length"], rim+2,
                    -shell_width/2+p["wall"]/2, 0, access_z)
    # The preserved cartridge pads were added after that window in006, so keep
    # their upper0.3 mm caps when restoring only the older retention features.
    expected += original
    for x, y in centers:
        expected += cyl(boss_r, clamp_z-p["floor"], x, y, p["floor"])
        expected -= cyl(pilot/2, p["pcb_insert_bore_depth"]+.1, x, y, bore_bottom)
    diff = [volume(body.cut(expected)), volume(expected.cut(body))]
    require(max(diff) <= 1e-4, "Body differs from independently reconstructed reinforcement", differences_mm3=diff)
    outside_a, outside_b = body.cut(allowed), original.cut(allowed)
    outside = [volume(outside_a.cut(outside_b)), volume(outside_b.cut(outside_a))]
    require(max(outside) <= 1e-4, "Body changed outside four PCB supports", differences_mm3=outside)
    same(new["parts"]["body"], body, "Body print placement")
    same(new["assembly"]["body"], t*body, "Body world placement")
    for name in changed:
        clear(new["assembly"][name], {n: s for n, s in new["assembly"].items() if n != name},
              "Changed print part collides at rest")
    # Probe complete annular material, especially the upper outboard left sector
    # that would be missing if bosses were added before the access-window cut.
    probes = []
    for x, y in centers:
        sx = 1 if x > 0 else -1
        old_center = sx*old_x
        restored = {"side_entry": (old_center, y-3.8, bottom-2),
                    "hex_wing": (old_center-sx*2.6, y, bottom-2),
                    "old_bottom_screw_bore": (old_center, y, p["floor"]+.1)}
        for label, point in restored.items():
            require(not original.is_inside(point), "Restoration probe was not inside old void", probe=label)
            require(body.is_inside(point), "PCB nut void was not filled", probe=label, point=point)
        clear(cyl(pilot/2-.01, p["pcb_insert_bore_depth"]-.02, x, y, bore_bottom+.01),
              {"body": body}, "PCB pilot is obstructed")
        require(body.is_inside((x,y,bore_bottom-.05)), "PCB blind bore floor is missing")
        for z in (clamp_z-.05, clamp_z-p["pcb_insert_length"]+.05):
            annulus = cyl(boss_r-.01, .01, x, y, z-.005)
            annulus -= cyl(p["pcb_insert_outer_diameter"]/2+.01, .03, x, y, z-.015)
            require(abs(overlap(annulus,body)-volume(annulus)) < 1e-5,
                    "Reinforcement lacks a complete annular wall", center=[x,y], z=z)
        probes.append({"center_local_xy_mm":[x,y],"restored_voids":restored,
                       "minimum_radial_wall_mm":boss_r-p["pcb_insert_outer_diameter"]/2})
    require(boss_r-p["pcb_insert_outer_diameter"]/2 >= 2-1e-8, "Post wall below2 mm")

    # Added polymer must not newly intrude into solder/component space over the
    # full PCB XY envelope, including its permitted lateral play.
    added = normalize(body.cut(original))
    additions_clearance = []
    for dx in (-.4, 0, .4):
        for dy in (-.4, 0, .4):
            envelope = box(p["pcb_width"], p["pcb_length"], rim-p["floor"], dx, dy, p["floor"])
            hit = overlap(added, envelope)
            require(hit <= 1e-5, "New polymer intrudes into PCB/component/solder envelope", dx=dx,dy=dy,overlap_mm3=hit)
            additions_clearance.append({"xy_translation_mm":[dx,dy],"overlap_mm3":hit})
    play = []
    for dx in (-.4,0,.4):
        for dy in (-.4,0,.4):
            for dz in (0,p["board_vertical_play"]/2,p["board_vertical_play"]):
                pcb = t*box(p["pcb_width"],p["pcb_length"],p["pcb_thickness"],dx,dy,bottom+dz)
                hits = clear(pcb,new["assembly"] | new["hardware"],"PCB play pose collides")
                play.append({"local_translation_xyz_mm":[dx,dy,dz],"max_overlap_mm3":max(hits.values())})
    return {"preserved_print_parts":preserved,"body_reconstruction_difference_mm3":diff,
            "body_outside_supports_difference_mm3":outside,"post_probes":probes,
            "added_material_clearance":additions_clearance,"pcb_play_positions":play}, changed, centers


def check_hardware_and_service(new, old, p, changed, centers):
    t = new["mount_transform"]
    clamp_z = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]+p["board_vertical_play"]
    rim = p["floor"]+p["solder_clearance"]+p["pcb_thickness"]+p["component_clearance"]
    bearing = clamp_z+2
    tip = bearing-p["pcb_clamp_screw_length"]
    bore_bottom = clamp_z-p["pcb_insert_bore_depth"]
    insert_bottom = clamp_z-p["pcb_insert_length"]
    engagement = clamp_z-max(tip,insert_bottom)
    require(engagement >= 3, "Insufficient PCB insert engagement")
    require(tip-bore_bottom >= .4-1e-8, "PCB screw can bottom")
    extra = set(new["hardware"])-set(old["hardware"])
    require(len(extra)==8 and set(old["hardware"]) <= set(new["hardware"]), "Hardware inventory changed unexpectedly")
    require(set(new["pcb_insert_names"]) | set(new["pcb_screw_names"]) == extra, "PCB hardware identifiers mismatch")
    for name, part in old["hardware"].items():
        same(part,new["hardware"][name],name+" unchanged existing hardware")
    displacement = pi/4*(p["pcb_insert_outer_diameter"]**2-p["pcb_insert_pilot_diameter"]**2)*p["pcb_insert_length"]
    expected = {(e["hardware"],e["printed"]):e["nominal_displaced_envelope_volume_mm3"]
                for e in new["expected_hardware_intersections"]}
    new_pairs = {(name,"body") for name in new["pcb_insert_names"]}
    require({pair for pair in expected if pair[0] in extra} == new_pairs, "Unexpected new overlap allowlist")
    observed=[]
    for name, hw in new["hardware"].items():
        against = new["assembly"] if name in extra else {n:new["assembly"][n] for n in changed}
        for part_name, part in against.items():
            hit=overlap(hw,part)
            intended=displacement if (name,part_name) in new_pairs else expected.get((name,part_name),0)
            require(abs(hit-intended)<1e-5,"Unexpected hardware/print interference",hardware=name,
                    printed=part_name,overlap_mm3=hit,expected_mm3=intended)
            if hit>1e-5:observed.append({"hardware":name,"printed":part_name,"volume_mm3":hit})
    for name in extra:
        clear(new["hardware"][name],{n:s for n,s in new["hardware"].items() if n!=name},
              "PCB hardware collides with hardware")
    service={n:s for n,s in new["assembly"].items() if n!="lid" and not n.startswith("boot_")}
    service.update({n:s for n,s in new["hardware"].items()
                    if not n.startswith("boot_") and n not in new["lid_screw_names"]})
    iron_service={n:s for n,s in service.items() if not n.startswith("pcb_clamp_")}
    tool_rows=[]
    for x,y in centers:
        side="left" if x<0 else "right"
        end="front" if y<0 else "rear"
        name=f"pcb_clamp_{side}_{end}"
        insert=cyl(p["pcb_insert_outer_diameter"]/2,p["pcb_insert_length"],x,y,insert_bottom)
        insert-=cyl(1.51,p["pcb_insert_length"]+.2,x,y,insert_bottom-.1)
        screw=cyl(1.5,p["pcb_clamp_screw_length"],x,y,tip)+cyl(2.75,3,x,y,bearing)
        same(new["pcb_hardware_local"][name+"_insert"],insert,"Independent PCB insert proxy")
        same(new["pcb_hardware_local"][name+"_screw"],screw,"Independent PCB screw proxy")
        same(new["hardware"][name+"_insert"],t*insert,"PCB insert world transform")
        same(new["hardware"][name+"_screw"],t*screw,"PCB screw world transform")
        driver=t*cyl(3,35,x,y,bearing+3+.01)
        driver_hits=clear(driver,service,"Driver blocked after lid/BOOT removal")
        narrow=t*cyl(3,rim-clamp_z+.1,x,y,clamp_z+.01)
        narrow_hits=clear(narrow,iron_service,"Narrow iron approach blocked")
        barrel=t*cyl(6,25,x,y,rim+.01)
        barrel_hits=clear(barrel,iron_service,"Wide iron barrel blocked above rim")
        wide=t*cyl(4,rim-clamp_z-.02,x,y,clamp_z+.01)
        wide_hit=overlap(wide,new["assembly"]["body"])
        if x>0:require(wide_hit>1e-4,"Wide iron negative control did not detect right wall")
        tool_rows.append({"name":name,"center_local_xy_mm":[x,y],"thread_engagement_mm":engagement,
                          "screw_tip_z_mm":tip,"bore_bottom_z_mm":bore_bottom,"bottom_margin_mm":tip-bore_bottom,
                          "driver_diameter_mm":6,"driver_max_overlap_mm3":max(driver_hits.values()),
                          "iron_narrow_diameter_mm":6,"minimum_narrow_reach_mm":rim-clamp_z,
                          "iron_narrow_max_overlap_mm3":max(narrow_hits.values()),
                          "iron_upper_barrel_diameter_mm":12,"barrel_start_local_z_mm":rim+.01,
                          "iron_upper_barrel_max_overlap_mm3":max(barrel_hits.values()),
                          "eight_mm_iron_wall_overlap_mm3":wide_hit})
    # Detect the established BOOT service obstruction rather than hiding it.
    bx=-centers[-1][0]
    by=-p["clamp_y"]
    obstructed=t*cyl(3,35,bx,by,bearing+3+.01)
    boot_hits={n:overlap(obstructed,s) for n,s in new["assembly"].items() if n.startswith("boot_")}
    require(max(boot_hits.values())>1e-4,"Expected BOOT service obstruction was not detected")
    # Only interfaces changed by007 need fresh motion checks.
    motion=[]
    targets={n:new["assembly"][n] for n in changed}
    targets.update({n:new["hardware"][n] for n in extra})
    for button,data in new["buttons"].items():
        for travel in (0,p["button_stroke"]/2,p["button_stroke"]):
            hits={}
            for name in data["moving_names"]:
                shape=(new["assembly"] | new["hardware"])[name]
                moved=Pos(0,0,travel)*shape
                checked=clear(moved,targets,"Button motion hits changed PCB joint")
                hits[name]=max(checked.values())
            motion.append({"button":button,"travel_mm":travel,"max_overlap_mm3":max(hits.values())})
    return {"old_hardware_count":len(old["hardware"]),"new_hardware_count":len(extra),
            "total_hardware_count":len(new["hardware"]),"new_insert_displacement_each_mm3":displacement,
            "observed_expected_print_overlaps":observed,"service_access":tool_rows,
            "boot_service_obstruction_mm3":boot_hits,"sampled_button_motion":motion}


def check_case(module,params,old,label):
    print(label+": build",flush=True)
    p=module.DEFAULTS | params
    new=module.build(params)
    print(label+": preservation, reinforcement and PCB clearance",flush=True)
    geometry,changed,centers=check_geometry(new,old,p)
    print(label+": hardware, tools and button travel",flush=True)
    hardware=check_hardware_and_service(new,old,p,changed,centers)
    print(label+": PASS",flush=True)
    return {"status":"pass","geometry":geometry,"hardware":hardware,
            "source_measurements":new["measurements"]["pcb_fasteners"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--scenario",choices=("all","nominal","pilot_4_1"),default="all")
    args=parser.parse_args()
    source,baseline=args.source.resolve(),args.baseline.resolve()
    params=params_at(source)
    before,old_before=hashes(source),hashes(baseline)
    report={"status":"running","checker_sha256":sha(__file__),"source":str(source),"baseline":str(baseline),
            "source_hashes":before,"baseline_hashes":old_before,"scenarios":{},
            "limits":["PCB remains the archived52x70x1.6 mm layout; the49 mm board and new button coordinates remain separate.",
                      "A6 mm iron-tip envelope needs21.8 mm narrow reach before a wider barrel may begin above the rim; actual tools are unmeasured.",
                      "BOOT cartridge and lid removal remain required for affected clamp access; heat-set installation also removes the clamps.",
                      "No new intrusion into nominal PCB/component/solder envelopes is distinct from validating the actual populated electronics.",
                      "Hardware threads, insert fit/strength, torque and physical printing remain untested."]}
    try:
        old_module=load(baseline/"model.py","baseline006")
        module=load(source/"model.py","candidate007")
        require(sha(source/"button_module.py")==sha(baseline/"button_module.py")
                and sha(source/"mounting.py")==sha(baseline/"mounting.py"),"Unchanged source dependencies differ")
        print("Building preserved006 reference",flush=True)
        old=old_module.build({k:v for k,v in params.items() if k in old_module.DEFAULTS})
        for label in ("nominal","pilot_4_1"):
            if args.scenario not in ("all",label):continue
            case=dict(params)
            if label=="pilot_4_1":case["pcb_insert_pilot_diameter"]=4.1
            report["scenarios"][label]=check_case(module,case,old,label)
        try:module.build(params | {"pcb_clamp_screw_length":8.0})
        except ValueError as exc:
            require("bottom" in str(exc) or "clearance" in str(exc),"Long screw rejected for unrelated reason",error=str(exc))
            report["m3x8_negative_control"]={"status":"rejected","reason":str(exc)}
        else:raise AssertionError("M3x8 was accepted despite blind-hole bottoming")
        text=(source/"base_model.py").read_text()
        require("_nut_slot" not in text,"Obsolete nut-pocket construction remains in base source")
        report["printed_nut_trap_inventory"]={"body":0,"four_pcb_clamps":0,"lid":0,"desk_bracket":0,
            "eight_cartridge_parts":0,"method":"Exact007 feature reconstruction removes body traps; clamps are independently reconstructed clearance-hole plates; lid/bracket/eight cartridge parts equal previously validated006 geometry. Base source has no nut-slot construction.",
            "separate_nut_hardware":"Two external nylon contact-adjuster jam nuts remain hardware proxies; they are not printed traps."}
        require(hashes(source)==before,"Candidate source changed during review")
        require(hashes(baseline)==old_before,"Preserved baseline changed during review")
        report["status"]="pass"
    except Exception as exc:
        report["status"]="fail";report["error"]=str(exc)
        raise
    finally:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":main()
