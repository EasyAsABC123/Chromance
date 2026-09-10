"""Independent geometry review of revision 005's orientation and replacement mount."""
import argparse
import hashlib
import importlib.util
import json
from math import sqrt
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import fdm_cad.build
import numpy as np
import trimesh
from build123d import Align, Box, Cylinder, Pos, RegularPolygon, Rot, extrude


def load(path, name):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def volume(shape):
    if shape is None:
        return 0.0
    if hasattr(shape, 'volume'):
        return float(shape.volume)
    return sum(float(item.volume) for item in shape)


def overlap(a, b):
    aa, bb = a.bounding_box(), b.bounding_box()
    if any(min(tuple(aa.max)[i], tuple(bb.max)[i])
           - max(tuple(aa.min)[i], tuple(bb.min)[i]) <= 1e-8 for i in range(3)):
        return 0.0
    return volume(a.intersect(b))


_meshes = {}


def mesh(shape):
    cached = _meshes.get(id(shape))
    if cached is not None and cached[0] is shape:
        return cached[1]
    vertices, faces = shape.tessellate(0.01, 0.1)
    result = trimesh.Trimesh(vertices=[list(v) for v in vertices], faces=faces, process=True)
    assert result.is_volume, 'Validation tessellation must be a watertight consistently wound volume'
    _meshes[id(shape)] = (shape, result)
    return result


def mesh_difference(a, b):
    result = trimesh.boolean.difference([mesh(a), mesh(b)], engine='manifold')
    return result, 0.0 if len(result.faces) == 0 else abs(float(result.volume))


def same(a, b, label):
    assert abs(volume(a)-volume(b)) <= 1e-5, (label, 'volume changed')
    aa, bb = mesh(a), mesh(b)
    if (aa.vertices.shape == bb.vertices.shape and aa.faces.shape == bb.faces.shape
            and np.allclose(aa.vertices, bb.vertices, atol=1e-7, rtol=0)
            and np.array_equal(aa.faces, bb.faces)):
        return
    # OCC incorrectly reports empty common geometry for two regenerated,
    # byte-identically tessellated BOOT sliders. Use the independent mesh engine
    # for coincident-shape comparison rather than trusting that CAD Boolean.
    _, left = mesh_difference(a, b)
    _, right = mesh_difference(b, a)
    assert left <= 0.001 and right <= 0.001, (label, 'shape changed', left, right)


def cyl(radius, height, x, y, z):
    return Pos(x, y, z) * Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def check(params, source_module, baseline_module, button_module, label):
    base_keys = set(baseline_module.DEFAULTS) | set(baseline_module.BUTTON_DEFAULTS)
    base_params = {key: value for key, value in params.items() if key in base_keys}
    old = baseline_module.build(base_params)
    new = source_module.build(params)
    p = baseline_module.DEFAULTS | baseline_module.BUTTON_DEFAULTS | base_params
    gap = params.get('desk_gap_above_case_floor', 2.0)
    pcb_bottom = p['floor']+p['solder_clearance']
    pcb_top = pcb_bottom+p['pcb_thickness']
    shell_height = pcb_top+p['component_clearance']
    plate_bottom = shell_height+p['bracket_clearance_above_body']
    desk_z = plate_bottom+p['bracket_plate_thickness']
    translation_z = plate_bottom-gap
    transform = Pos(0, 0, translation_z)*Rot(X=180)
    point = lambda xyz: [xyz[0], -xyz[1], translation_z-xyz[2]]
    assert set(new['parts']) == set(old['parts'])
    assert len(new['parts']) == 15
    changed_names = {'desk_bracket', 'reset_slider', 'boot_slider'}
    for name, solid in new['parts'].items():
        assert solid.is_valid and len(solid.solids()) == 1 and solid.volume > 0, name
        assert abs(solid.bounding_box().min.Z) < 1e-6, (name, 'not on print bed')
        if name not in changed_names:
            same(solid, old['parts'][name], f'{name} print part')
            same(new['assembly'][name], transform*old['assembly'][name], f'{name} rigid transform')
    pad_extensions = {}
    for name in ('reset', 'boot'):
        original = transform*old['assembly'][f'{name}_slider']
        extended = new['assembly'][f'{name}_slider']
        _, missing = mesh_difference(original, extended)
        assert missing <= 0.001, (name, 'extension removed original slider material', missing)
        added, added_volume = mesh_difference(extended, original)
        assert added_volume > 0
        bp = old['buttons'][name]['params']
        cx, cy = bp['mounting_face_x']-7.1, -bp['housing_y']
        top_local = bp['arm_bottom_z']+7.8
        extension = (translation_z-top_local)-extended.bounding_box().min.Z
        assert abs(extension-7) < 1e-6, (name, 'expected seven millimeter pad extension')
        allowed_min = [cx-4.4, cy-6, translation_z-top_local-extension]
        allowed_max = [cx+4.4, cy+6, translation_z-top_local+0.6]
        assert np.all(added.bounds[0] >= np.array(allowed_min)-0.001)
        assert np.all(added.bounds[1] <= np.array(allowed_max)+0.001)
        same(new['parts'][f'{name}_slider'],
             source_module._base._on_bed(Rot(Y=180)*(transform.inverse()*extended)),
             f'{name} slider print orientation')
        pad_extensions[name] = extension
    for name, solid in old['hardware'].items():
        same(new['hardware'][name], transform*solid, f'{name} hardware transform')

    body, bracket = new['assembly']['body'], new['assembly']['desk_bracket']
    assert abs(bracket.bounding_box().max.Z-desk_z) < 1e-6
    assert abs(body.bounding_box().max.Z-translation_z) < 1e-6
    assert abs(plate_bottom-body.bounding_box().max.Z-gap) < 1e-6
    assert all(s.bounding_box().max.Z <= desk_z+1e-6 for s in new['assembly'].values())
    same(new['parts']['desk_bracket'],
         Pos(0, 0, desk_z)*Rot(X=180)*bracket, 'bracket printing orientation')
    # Body/cover/clamps retain their wall thicknesses because they are exact
    # rigid transforms above. Verify the new H plate thickness at its center.
    for offset in (0.1, p['bracket_plate_thickness']-0.1):
        assert bracket.is_inside((0, 0, plate_bottom+offset))
    assert not bracket.is_inside((0, 0, plate_bottom-0.05))

    # Board placement is a geometric transform; no new connector or PCB claims.
    pcb = Pos(0, 0, pcb_bottom)*Box(p['pcb_width'], p['pcb_length'], p['pcb_thickness'],
                                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    world_pcb = transform*pcb
    assert all(overlap(world_pcb, solid) <= 1e-5 for solid in new['assembly'].values())

    mounting = []
    review_mount_hardware = {}
    insert_length = p['button_contact_insert_length']
    insert_od = p['button_contact_insert_outer_diameter']
    pilot_diameter = p['button_contact_insert_pilot_diameter']
    new_insert_keys = sorted(set(new['hardware'])-set(old['hardware']))
    assert len(new_insert_keys) == 4, new_insert_keys
    bracket_insert_overlap = np.pi*(insert_od**2-pilot_diameter**2)/4*insert_length
    interface_z = translation_z-(shell_height-5)
    ear_bottom_z = translation_z-shell_height
    ow, ol = old['measurements']['main_shell_xy']
    for index, (x, source_y) in enumerate(old['measurements']['body_mount_centers_xy']):
        y = -source_y
        screw = cyl(1.5, 10, x, y, ear_bottom_z)+cyl(2.75, 3, x, y, ear_bottom_z-3)
        assert all(overlap(screw, solid) <= 1e-5 for solid in new['assembly'].values()), (x, y, 'mount screw collision')
        review_mount_hardware[f'independent_body_mount_screw_{index+1}'] = screw
        matches = [(key, solid) for key, solid in new['hardware'].items() if key in new_insert_keys
                   and abs(solid.bounding_box().center().X-x) < 1e-6
                   and abs(solid.bounding_box().center().Y-y) < 1e-6]
        assert len(matches) == 1, (x, y, 'missing bracket insert')
        key, insert = matches[0]
        assert abs(insert.bounding_box().min.Z-interface_z) < 1e-6
        assert abs(insert.bounding_box().max.Z-interface_z-insert_length) < 1e-6
        assert abs(overlap(insert, bracket)-bracket_insert_overlap) < 1e-5
        assert abs(ear_bottom_z+10-interface_z-insert_length) < 1e-6
        assert not bracket.is_inside((x, y, interface_z+insert_length+0.3))
        assert bracket.is_inside((x, y, interface_z+insert_length+0.5))
        driver = cyl(3, 30, x, y, ear_bottom_z-3-30.02)
        assert all(overlap(driver, solid) <= 1e-5 for solid in new['assembly'].values()), (x, y, 'M3 driver blocked')
        # Sidewall is measured against the provisional insert envelope, while
        # point probes check actual material outside the smaller printed pilot.
        inner = ow/2+p['belt_projection']+params.get('bracket_belt_clearance', 0.6)
        minimum_wall = min(abs(x)-inner-insert_od/2,
                           params.get('bracket_leg_width_y', 8.6)/2-insert_od/2)
        assert minimum_wall >= 1.8, (x, y, 'insufficient insert boss wall')
        assert bracket.is_inside((x, y+pilot_diameter/2+0.1, interface_z+3))
        mounting.append({'center_world_xy_mm': [x, y], 'screw_shank_mm': 10,
                         'ear_thickness_mm': 5, 'insert_engagement_mm': insert_length,
                         'insert_envelope_minimum_wall_mm': minimum_wall,
                         'driver_radius_mm': 3, 'access': 'clear'})
    for x, source_y in old['measurements']['desk_screw_centers_xy']:
        # The new bracket remains in original world coordinates; the set of
        # symmetric +/-Y desk holes is invariant under the enclosure flip.
        access = cyl(p['desk_screw_clearance']/2-0.05, 40, x, source_y, plate_bottom-40)
        assert all(overlap(access, solid) <= 1e-5 for solid in new['assembly'].values()), (x, source_y, 'desk screw access blocked')

    insertion = []
    case_parts = {name: solid for name, solid in new['assembly'].items() if name != 'desk_bracket'}
    for downward_shift in (0, 0.25, 1, 2, 4, 6, 8, 10, 12, 16, 20, 25, 30, 40, 50):
        for name, solid in case_parts.items():
            assert overlap(Pos(0, 0, -downward_shift)*solid, bracket) <= 1e-5, (downward_shift, name, 'vertical installation blocked')
        for name, solid in old['hardware'].items():
            assert overlap(Pos(0, 0, -downward_shift)*new['hardware'][name], bracket) <= 1e-5, (downward_shift, name, 'hardware installation blocked')
        insertion.append({'case_offset_z_mm': -downward_shift, 'status': 'clear'})

    states = []
    for travel in (0, p['button_stroke']/2, p['button_stroke']):
        printed = dict(new['assembly'])
        hardware = new['hardware'] | review_mount_hardware
        expected_interactions = {(key, 'desk_bracket'): bracket_insert_overlap for key in new_insert_keys}
        button_report = {}
        for name in ('reset', 'boot'):
            original_button = old['buttons'][name]
            local_params = original_button['params'] | {'travel': travel}
            local = button_module.make_button(local_params, name)
            for moving_name in original_button['moving_names']:
                printed[moving_name] = Pos(0, 0, travel)*new['assembly'][moving_name]
                if not moving_name.endswith('_slider'):
                    same(printed[moving_name], transform*local['assembly'][moving_name], f'{moving_name} upward motion')
            for suffix in ('moving_magnet', 'nylon_adjuster', 'contact_heatset_insert', 'nylon_jam_nut'):
                key = f'{name}_{suffix}'
                hardware[key] = Pos(0, 0, travel)*new['hardware'][key]
                same(hardware[key], transform*local['hardware'][key], f'{key} upward motion')
            for item in local['expected_hardware_intersections']:
                expected_interactions[item['hardware'], item['printed']] = item['nominal_displaced_envelope_volume_mm3']

            source_pad = [local_params['mounting_face_x']-7.1, local_params['housing_y'],
                          local_params['arm_bottom_z']+7.8+pad_extensions[name]-travel]
            px, py, pz = point(source_pad)
            slider = printed[f'{name}_slider']
            assert slider.is_inside((px, py, pz+0.05)) and not slider.is_inside((px, py, pz-0.05))
            finger = cyl(6, 30, px, py, pz-30.02)
            assert all(overlap(finger, solid) <= 1e-5 for solid in printed.values()), (name, travel, 'finger approach blocked')
            assert all(overlap(finger, solid) <= 1e-5 for solid in hardware.values()), (name, travel, 'finger approach blocked by hardware')
            centered_large = cyl(10, 20, px, py, pz-20.05)
            centered_large_hits = {
                key: hit for key, solid in printed.items()
                if (hit := overlap(centered_large, solid)) > 1e-5
            }
            assert not centered_large_hits, (name, travel, centered_large_hits)
            assert all(overlap(centered_large, solid) <= 1e-5 for solid in hardware.values()), (name, travel, '20 mm centered finger approach blocked by hardware')
            fixed = hardware[f'{name}_fixed_magnet'].bounding_box()
            moving = hardware[f'{name}_moving_magnet'].bounding_box()
            magnet_gap = fixed.min.Z-moving.max.Z
            assert abs(magnet_gap-(3.6-travel)) < 1e-6
            tip_z = hardware[f'{name}_nylon_adjuster'].bounding_box().max.Z
            switch_z = point([local_params['tip_x'], local_params['tip_y'], local_params['switch_top_z']])[2]
            contact_gap = switch_z-tip_z
            expected_gap = p['button_stroke']-p['modeled_switch_depression']-travel
            assert abs(contact_gap-expected_gap) < 1e-6
            button_report[name] = {'pad_face_world_xyz_mm': [px, py, pz],
                                   'press_direction_world': [0, 0, 1],
                                   'finger_approach_diameter_mm': 12,
                                   'centered_20mm_finger_obstructions_mm3': centered_large_hits,
                                   'usable_20mm_finger_contact_point_world_mm': [px, py, pz],
                                   'usable_20mm_finger_approach': 'clear',
                                   'switch_face_world_z_mm': switch_z,
                                   'contact_gap_mm': contact_gap, 'magnet_face_gap_mm': magnet_gap}

        pairs = list(printed.items())
        for index, (name, solid) in enumerate(pairs):
            for other_name, other in pairs[index+1:]:
                assert overlap(solid, other) <= 1e-5, (travel, name, other_name, 'printed collision')
        interactions = []
        for name, solid in hardware.items():
            for other_name, other in printed.items():
                hit = overlap(solid, other)
                expected = expected_interactions.get((name, other_name), 0)
                assert abs(hit-expected) <= 1e-5, (travel, name, other_name, hit, expected)
                if expected:
                    interactions.append({'hardware': name, 'printed': other_name, 'polymer_displacement_mm3': hit})
        hardware_items = list(hardware.items())
        for index, (name, solid) in enumerate(hardware_items):
            for other_name, other in hardware_items[index+1:]:
                assert overlap(solid, other) <= 1e-5, (travel, name, other_name, 'hardware collision')
        states.append({'travel_mm': travel, 'buttons': button_report,
                       'expected_heatset_interactions': interactions, 'unexpected_collisions': []})
        print(json.dumps({'scenario': label, 'travel_mm': travel, 'status': 'passed'}), flush=True)

    return {'scenario': label, 'status': 'passed', 'desk_plane_world_z_mm': desk_z,
            'case_floor_to_bracket_plate_gap_mm': gap,
            'point_transform': ['x', '-y', f'{translation_z}-z'],
            'unchanged_printed_parts': sorted(set(old['parts'])-changed_names),
            'slider_pad_extension_mm': pad_extensions,
            'mounting_access': mounting, 'vertical_installation_sweep': insertion, 'states': states,
            'pcb_world_bounds_mm': [list(world_pcb.bounding_box().min), list(world_pcb.bounding_box().max)],
            'physical_strength_or_support_profile_tested': False,
            'print_notes': 'Twelve preserved parts retain exact print geometry. Extended sliders retain their rotation but need taller local arm supports. Straight replacement bracket prints desk-contact face down; blind insert pilots open at the leg tops in print orientation.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True, help='Revision 005 source directory')
    parser.add_argument('--baseline', type=Path, required=True, help='Preserved revision 004 directory')
    parser.add_argument('--output', type=Path, required=True, help='Validation report to write')
    parser.add_argument('--scenario', choices=['all', 'nominal', 'larger_mount_gap', 'larger_board'], default='all')
    args = parser.parse_args()
    baseline = load(args.baseline/'model.py', 'preserved004')
    current = load(args.source/'model.py', 'downward005')
    buttons = load(args.baseline/'button_module.py', 'preserved004_buttons')
    for new_name, old_name in [('base_model.py', 'model.py'), ('button_module.py', 'button_module.py'), ('mounting.py', 'mounting.py')]:
        assert (args.source/new_name).read_bytes() == (args.baseline/old_name).read_bytes(), (new_name, '004 source changed')
    param_path = args.source/'params.json'
    if not param_path.exists():
        param_path = args.source/'parameters.json'
    params = json.loads(param_path.read_text())
    scenarios = [('nominal', params),
                 ('larger_mount_gap', params | {'desk_gap_above_case_floor': 4.0}),
                 ('larger_board', params | {'pcb_width': params['pcb_width']+4, 'pcb_length': params['pcb_length']+8})]
    if args.scenario != 'all':
        scenarios = [(label, values) for label, values in scenarios if label == args.scenario]
    reports = [check(p, current, baseline, buttons, label) for label, p in scenarios]
    output = {'status': 'passed', 'scenarios': reports,
              'source_hashes': {name: hashlib.sha256((args.source/name).read_bytes()).hexdigest()
                                for name in ('model.py', 'base_model.py', 'button_module.py', 'mounting.py')},
              'scope': 'Rigid-body orientation, replacement bracket, access and motion geometry; no physical load, insert-fit, magnetic-force or printer validation.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({'status': 'passed', 'scenarios': len(reports), 'output': str(args.output)}), flush=True)


if __name__ == '__main__':
    main()
