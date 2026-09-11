"""Independent short corner-boss and matching lid validation against revision007."""
import argparse
import hashlib
import importlib.util
import json
from math import cos, floor, pi, radians, sin, tan
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


def section_rectangle(xmin,ymin,xmax,ymax):
    return manifold.CrossSection.square((xmax-xmin,ymax-ymin)).translate((xmin,ymin))


def layer_review(body,p,corners,rim,base,root):
    tm=mesh(body)
    solid=manifold.Manifold(manifold.Mesh(np.asarray(tm.vertices,dtype=np.float32),
                                        np.asarray(tm.faces,dtype=np.uint32)))
    require(str(solid.status()).endswith("NoError"),"Slice manifold is invalid",status=str(solid.status()))
    height=.2
    slope=tan(radians(p["lid_corner_support_angle"]))
    advance=height/slope
    tolerance=.003
    start=max(.1, floor((root-.4)/height)*height+.1)
    heights=np.arange(start,rim-.05,height)
    projection,embedded=p["lid_corner_projection"],p["lid_corner_wall_overlap"]
    records=[]
    previous=solid.slice(float(heights[0]-height))
    for z in heights:
        current=solid.slice(float(z))
        allowed=previous.offset(advance+tolerance,circular_segments=128)
        for sx,sy,wx,wy in corners:
            xs=sorted((wx-sx*projection,wx+sx*embedded))
            ys=sorted((wy-sy*projection,wy+sy*embedded))
            mask=section_rectangle(xs[0],ys[0],xs[1],ys[1])
            local=current^mask
            excessive=(local-allowed).area()
            require(excessive<=1e-5,"Corner layer exceeds Euclidean overhang allowance",
                    z=float(z),corner=[sx,sy],area_mm2=excessive,allowed_advance_mm=advance+tolerance)
            islands=local.decompose()
            require(len(islands)==1,"Floating or disconnected corner slice",z=float(z),corner=[sx,sy],count=len(islands))
            x_wall=section_rectangle(min(wx,wx+sx*embedded),ys[0],max(wx,wx+sx*embedded),ys[1])
            y_wall=section_rectangle(xs[0],min(wy,wy+sy*embedded),xs[1],max(wy,wy+sy*embedded))
            roots=[(local^x_wall).area(),(local^y_wall).area()]
            require(min(roots)>=embedded*(projection+embedded)-1e-4,
                    "Corner layer lacks continuous material at both wall roots",z=float(z),areas_mm2=roots)
            void=mask-local
            if z<base-.05 and void.area()>1e-5:
                require(len(void.decompose())==1,"Enclosed pocket below support",z=float(z))
                ix=wx-sx*projection;iy=wy-sy*projection
                x_open=section_rectangle(min(ix,ix+sx*.02),ys[0],max(ix,ix+sx*.02),ys[1])
                y_open=section_rectangle(xs[0],min(iy,iy+sy*.02),xs[1],max(iy,iy+sy*.02))
                require((void^x_open).area()>1e-5 and (void^y_open).area()>1e-5,
                        "Underside void does not open to main cavity",z=float(z))
            if z>base+.05:
                expected_contours=2 if z>rim-p["lid_insert_bore_depth"]+.05 else 1
                if abs(z-(rim-p["lid_insert_bore_depth"]))>.05:
                    require(local.num_contour()==expected_contours,"Residual corner pinhole or gap",
                            z=float(z),contours=local.num_contour(),expected=expected_contours)
            records.append({"z_mm":float(z),"corner":[sx,sy],"excess_area_mm2":excessive,
                            "connected_regions":len(islands),"wall_root_areas_mm2":roots})
        previous=current
    # Sensitivity control: an outward-growing square corner needs sqrt(2)*h,
    # so the same Euclidean test must detect the familiar diagonal error.
    a=section_rectangle(0,0,10,10)
    b=section_rectangle(-height,-height,10+height,10+height)
    negative=(b-a.offset(height+tolerance,circular_segments=128)).area()
    require(negative>.01,"Diagonal overhang negative control failed",excess_area_mm2=negative)
    return {"layer_height_mm":height,"allowed_horizontal_advance_mm":advance,
            "geometric_tolerance_mm":tolerance,"layer_count":len(heights),"corner_slice_count":len(records),
            "maximum_excess_area_mm2":max(r["excess_area_mm2"] for r in records),
            "diagonal_square_growth_negative_control_area_mm2":negative,"slices":records}


def check_case(module,params,old,label):
    print(label+": build and preserved geometry",flush=True)
    p=module.DEFAULTS | params
    new=module.build(params)
    require(set(new["parts"])==set(old["parts"]) and len(new["parts"])==15,"Print inventory changed")
    preserved=[]
    for name,shape in new["parts"].items():
        require(shape.is_valid and len(shape.solids())==1 and shape.volume>0,"Invalid print solid",name=name)
        require(abs(shape.bounding_box().min.Z)<1e-6,"Print part is off bed",name=name)
        if name not in {"body","lid"}:
            same(shape,old["parts"][name],name+" unchanged print")
            same(new["assembly"][name],old["assembly"][name],name+" unchanged world placement")
            preserved.append(name)
    require(set(new["hardware"])==set(old["hardware"]) and len(new["hardware"])==34,"Hardware inventory changed")
    for name,shape in old["hardware"].items():same(new["hardware"][name],shape,name+" unchanged hardware")
    t=new["mount_transform"]
    for xyz in ((0,0,0),(1,2,3)):
        np.testing.assert_allclose(list((t*Pos(*xyz)).position),list((old["mount_transform"]*Pos(*xyz)).position),atol=1e-8)
    body=new["case_local_assembly"]["body"];lid=new["case_local_assembly"]["lid"]
    original=old["case_local_assembly"]["body"];old_lid=old["case_local_assembly"]["lid"]
    cw=p["pcb_width"]+2*p["side_margin"];cl=p["pcb_length"]+2*p["end_margin"]
    board_bottom=p["floor"]+p["solder_clearance"]
    board_top=board_bottom+p["pcb_thickness"]
    rim=board_top+p["component_clearance"]
    projection=p["lid_corner_projection"];embedded=p["lid_corner_wall_overlap"]
    base=rim-p["lid_corner_pad_height"]
    root=base-projection*tan(radians(p["lid_corner_support_angle"]))
    corners=[(sx,sy,sx*cw/2,sy*cl/2) for sx in (-1,1) for sy in (-1,1)]
    width=projection+embedded;center=(embedded-projection)/2
    # Independently construct the support as the union of two halfspace-clipped
    # blocks. This differs from the author's extruded profile construction.
    block=box(width,width,rim-root,center,center,root)
    slope=tan(radians(p["lid_corner_support_angle"]))
    x_half=split(block,Plane(origin=(0,0,root),z_dir=(slope,0,1)),keep=Keep.TOP)
    y_half=split(block,Plane(origin=(0,0,root),z_dir=(0,slope,1)),keep=Keep.TOP)
    canonical=x_half+y_half
    canonical-=cyl(p["lid_insert_pilot_diameter"]/2,p["lid_insert_bore_depth"]+.1,-4,-4,rim-p["lid_insert_bore_depth"])
    cavity=box(cw,cl,rim-p["floor"],z=p["floor"])
    expected=original;allowed=None;trimmed=old_lid;trim_allowed=None
    for sx,sy,wx,wy in corners:
        old_post=cyl(4.4,rim-p["floor"],sx*(cw/2-4),sy*(cl/2-4),p["floor"])
        expected=expected-normalize(old_post.intersect(cavity))
    for sx,sy,wx,wy in corners:
        rotation={(1,1):0,(-1,1):90,(-1,-1):180,(1,-1):270}[(sx,sy)]
        placement=Pos(wx,wy,0)*Rot(Z=rotation)
        expected+=placement*canonical
        zone=placement*box(width+.02,width+.02,rim-p["floor"]+.02,center,center,p["floor"])
        allowed=zone if allowed is None else allowed+zone
        trim=placement*box(width+2*p["lid_fit_clearance"],width+2*p["lid_fit_clearance"],
                          p["lid_skirt_depth"],center,center,rim-p["lid_skirt_depth"])
        trimmed-=trim
        trim_allowed=trim if trim_allowed is None else trim_allowed+trim
    print(label+": exact corner changes, gap fill and lid compatibility",flush=True)
    body_diffs=[volume(body.cut(expected)),volume(expected.cut(body))]
    require(max(body_diffs)<1e-4,"Body differs from independent wall-supported reconstruction",differences_mm3=body_diffs)
    outside_a,outside_b=body.cut(allowed),original.cut(allowed)
    outside=[volume(outside_a.cut(outside_b)),volume(outside_b.cut(outside_a))]
    require(max(outside)<1e-4,"Body changed outside four corners",differences_mm3=outside)
    same(lid,trimmed,"Only four skirt trims change the lid")
    lid_plate=box(cw+20,cl+20,p["lid_thickness"]+.1,z=rim)
    same(normalize(lid.intersect(lid_plate)),normalize(old_lid.intersect(lid_plate)),"Lid plate/exterior/screw holes unchanged")
    rotated=Rot(X=180)*lid
    same(new["parts"]["lid"],Pos(0,0,-rotated.bounding_box().min.Z)*rotated,"Lid print orientation")
    same(new["parts"]["body"],body,"Body print orientation")
    same(new["assembly"]["body"],t*body,"Body mounted orientation")
    same(new["assembly"]["lid"],t*lid,"Lid mounted orientation")
    old_lid_hit=overlap(old_lid,body)
    require(old_lid_hit>.001,"Old-lid incompatibility negative control failed")
    require(overlap(lid,body)<1e-5,"New lid does not fully seat")
    floor_clip=box(cw+40,cl+40,p["floor"]-.0001)
    same(normalize(body.intersect(floor_clip)),normalize(original.intersect(floor_clip)),"Original floor unchanged")
    gap_probes=[]
    for sx,sy,wx,wy in corners:
        cx,cy=wx-sx*4,wy-sy*4
        for z in (base+.1,rim-3,rim-.1):
            point=(wx-sx*.2,wy-sy*.2,z)
            require(body.is_inside(point) and not original.is_inside(point),"Former corner gap is not closed",point=point)
        # Full bore floor, not just a center-point thickness measurement.
        floor_disc=cyl(p["lid_insert_pilot_diameter"]/2,2,cx,cy,rim-p["lid_insert_bore_depth"]-2)
        require(abs(overlap(floor_disc,body)-volume(floor_disc))<1e-5,"Less than2 mm material under blind bore")
        clear(cyl(p["lid_insert_pilot_diameter"]/2-.01,p["lid_insert_bore_depth"]-.02,cx,cy,rim-p["lid_insert_bore_depth"]+.01),
              {"body":body},"Pilot obstructed")
        require(not body.is_inside((cx,cy,p["floor"]+.2)),"Old floor-standing column remains")
        gap_probes.append({"corner":[sx,sy],"closed_gap_xy_mm":[wx-sx*.2,wy-sy*.2],
                           "pilot_floor_mm":p["lid_corner_pad_height"]-p["lid_insert_bore_depth"],
                           "minimum_insert_wall_mm":projection-4-p["lid_insert_outer_diameter"]/2})
    print(label+": hardware, PCB/connector space and affected button motion",flush=True)
    for name in ("body","lid"):
        clear(new["assembly"][name],{n:s for n,s in new["assembly"].items() if n!=name},"Changed print part collides")
    expected_hits={(e["hardware"],e["printed"]):e["nominal_displaced_envelope_volume_mm3"] for e in new["expected_hardware_intersections"]}
    for name,hw in new["hardware"].items():
        for host in ("body","lid"):
            hit=overlap(hw,new["assembly"][host])
            require(abs(hit-expected_hits.get((name,host),0))<1e-5,"Hardware collides with changed print",hardware=name,host=host,hit_mm3=hit)
    # The square corners approach PCB ends; test the whole vertical electronics
    # envelope for added material at all permitted XY translations.
    added=normalize(body.cut(original));envelope_rows=[]
    for dx in (-.4,0,.4):
        for dy in (-.4,0,.4):
            env=box(p["pcb_width"],p["pcb_length"],rim-p["floor"],dx,dy,p["floor"])
            hit=overlap(env,added)
            require(hit<1e-5,"Corner addition intrudes into PCB/component envelope",dx=dx,dy=dy,hit_mm3=hit)
            envelope_rows.append({"xy_translation_mm":[dx,dy],"added_material_overlap_mm3":hit})
    motion=[]
    for name,data in new["buttons"].items():
        for travel in (0,p["button_stroke"]/2,p["button_stroke"]):
            hits=[]
            for moving in data["moving_names"]:
                shape=(new["assembly"]|new["hardware"])[moving]
                checked=clear(Pos(0,0,travel)*shape,{"body":new["assembly"]["body"],"lid":new["assembly"]["lid"]},"Corner/lid touches moving button")
                hits.extend(checked.values())
            motion.append({"button":name,"travel_mm":travel,"max_overlap_mm3":max(hits)})
    # Actual end opening and mounting ears are outside the independently bounded
    # corner edits; confirm lid and PCB tool axes with the revised body as well.
    tool_hits=[]
    for sx,sy,wx,wy in corners:
        x,y=wx-sx*4,wy-sy*4
        driver=t*cyl(3,30,x,y,rim+p["lid_thickness"]+3+.01)
        hits=clear(driver,new["assembly"]|new["hardware"],"Mounted lid driver blocked")
        tool_hits.append(max(hits.values()))
    for sx in (-1,1):
        for sy in (-1,1):
            x=sx*(p["pcb_width"]/2+p["pcb_clamp_screw_offset_from_edge"]);y=sy*p["clamp_y"]
            clamp_z=board_top+p["board_vertical_play"]
            probe=t*cyl(3,rim-clamp_z+.1,x,y,clamp_z+.01)
            require(overlap(probe,new["assembly"]["body"])<1e-5,"PCB insert-tool wall clearance changed")
    print(label+": finite-layer support including diagonals",flush=True)
    layers=layer_review(body,p,corners,rim,base,root)
    old_total=sum(volume(s) for s in old["parts"].values());new_total=sum(volume(s) for s in new["parts"].values())
    volumes={"old_body_mm3":volume(original),"new_body_mm3":volume(body),"body_saved_mm3":volume(original)-volume(body),
             "body_saved_percent":100*(volume(original)-volume(body))/volume(original),
             "old_lid_mm3":volume(old_lid),"new_lid_mm3":volume(lid),"old_total_print_mm3":old_total,"new_total_print_mm3":new_total,
             "total_saved_mm3":old_total-new_total,"total_saved_percent":100*(old_total-new_total)/old_total}
    print(label+": PASS",flush=True)
    return {"status":"pass","preserved_print_parts":preserved,"unchanged_hardware_count":len(new["hardware"]),
            "body_reconstruction_difference_mm3":body_diffs,"body_outside_corner_difference_mm3":outside,
            "old_lid_interference_mm3":old_lid_hit,"new_lid_interference_mm3":overlap(lid,body),"corner_probes":gap_probes,
            "component_envelope_checks":envelope_rows,"sampled_button_motion":motion,"lid_driver_max_overlap_mm3":max(tool_hits),
            "layer_support":layers,"volumes":volumes,"source_corner_measurements":new["measurements"]["corner_bosses"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--scenario",choices=("all","nominal","steeper_taller"),default="all")
    args=parser.parse_args()
    source,baseline=args.source.resolve(),args.baseline.resolve()
    params=params_at(source)
    before,old_before=hashes(source),hashes(baseline)
    report={"status":"running","checker_sha256":sha(__file__),"source":str(source),"baseline":str(baseline),
            "source_hashes":before,"baseline_hashes":old_before,"scenarios":{},
            "limits":["Finite-layer checks sample the actual tessellated body at 0.2 mm layer height with 0.003 mm geometric allowance; they do not predict physical bridging, cooling, strength or print time.",
                      "PCB remains the archived 52 x 70 x 1.6 mm layout. Actual connectors, overhangs, wiring and the separately measured 49 mm board are unvalidated.",
                      "Preserved PCB service requires the lid and BOOT cartridge removed, with a 6 mm narrow tool reaching 21.8 mm to the rim; actual tools remain unmeasured.",
                      "Threads, heat-set fit, torque, thermal behavior, actuator calibration and physical printing remain untested."]}
    try:
        old_module=load(baseline/"model.py","baseline007")
        module=load(source/"model.py","candidate008")
        require(sha(source/"button_module.py")==sha(baseline/"button_module.py")
                and sha(source/"mounting.py")==sha(baseline/"mounting.py"),"Unchanged source dependencies differ")
        print("Building preserved 007 reference",flush=True)
        old=old_module.build({k:v for k,v in params.items() if k in old_module.DEFAULTS})
        for label in ("nominal","steeper_taller"):
            if args.scenario not in ("all",label):continue
            case=dict(params)
            if label=="steeper_taller":case.update(lid_corner_pad_height=8.5,lid_corner_support_angle=50.0)
            report["scenarios"][label]=check_case(module,case,old,label)
        try:module.build(params | {"lid_corner_pad_height":7.5})
        except ValueError as exc:
            require("floor" in str(exc).lower(),"Thin pad rejected for unrelated reason",error=str(exc))
            report["thin_pad_negative_control"]={"status":"rejected","reason":str(exc)}
        else:raise AssertionError("7.5 mm pad accepted despite less than 2 mm blind-bore floor")
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
