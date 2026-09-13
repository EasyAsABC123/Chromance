"""Independent revision014 measured USB envelope and mechanism review.

The measured dimensions bound an intentionally conservative uniform box; actual
plug taper, the inboard jack, cable-axis height and physical fits are separate.
Nominal clearance and parameter variants are checked; board-play envelope
collisions are reported explicitly as unresolved, not hidden or called a fit.
"""
import argparse
import importlib.util
import json
from itertools import product
from math import hypot
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def local_state(c, new, travels):
    printed = dict(new['case_local_assembly'])
    hardware = {key: new['mount_transform']*value for key, value in new['hardware'].items()}
    for name, travel in travels.items():
        for key in new['buttons'][name]['moving_names']:
            printed[key] = c.Pos(0, 0, -travel)*printed[key]
        for suffix in ('moving_magnet', 'nylon_adjuster', 'contact_heatset_insert', 'nylon_jam_nut'):
            key = name+'_'+suffix
            hardware[key] = c.Pos(0, 0, -travel)*hardware[key]
    return printed, hardware


def check_cartridges_without_usb(c, new, p):
    require, clear, overlap = c.require, c.clear, c.overlap
    printed, hardware = local_state(c, new, {'reset': 0, 'boot': 0})
    board_bottom = p['floor']+p['solder_clearance']
    board_top = board_bottom+p['pcb_thickness']
    rim = board_top+p['component_clearance']
    measurements, assembly_paths = {}, {}
    xcyl = lambda r, length, x, y, z: c.Pos(x, y, z)*c.Rot(Y=90)*c.cyl(r, length)
    for name, direction in (('reset', -1), ('boot', 1)):
        data = new['buttons'][name]
        bp = data['params']
        tx = -p['pcb_width']/2+p['button_inset_from_left_pcb_edge']
        ty = -p['pcb_length']/2+p[name+'_button_from_bottom']
        require(abs(bp['tip_x']-tx) < 1e-7 and abs(bp['tip_y']-ty) < 1e-7,
                'Contact axis does not follow actual PCB edge datums', button=name)
        require(bp['collar_relief_direction'] == direction, 'Collar flat faces wrong switch')
        for suffix in ('nylon_adjuster', 'contact_heatset_insert', 'nylon_jam_nut'):
            center = hardware[name+'_'+suffix].bounding_box().center()
            require(abs(center.X-tx) < 1e-7 and abs(center.Y-ty) < 1e-7,
                    'Contact hardware is not concentric with measured XY', button=name, hardware=suffix)
        a, face = bp['arm_bottom_z'], bp['mounting_face_x']
        slider = printed[name+'_slider']
        floor_z = a-.8
        flat = bp['collar_flat_offset']
        require(flat-1.7 >= 1.2-1e-7, 'Low collar ligament too thin')
        # Direct polymer probes on both sides of the actual clipped boundary.
        inside = c.box(.2, .05, .2, tx, ty+direction*(flat-.05), floor_z+.1)
        outside = c.box(.2, .05, .2, tx, ty+direction*(flat+.05), floor_z+.1)
        require(abs(overlap(inside, slider)-c.volume(inside)) < 1e-7,
                'Relieved collar loses its specified ligament', button=name)
        require(overlap(outside, slider) < 1e-7, 'Low collar flat was not cut', button=name)
        ring = c.cyl(bp['contact_insert_pilot_diameter']/2-.02, .1, tx, ty, floor_z+.1)
        ring -= c.cyl(1.72, .2, tx, ty, floor_z+.05)
        require(abs(overlap(ring, slider)-c.volume(ring)) < 1e-6,
                'Heatset pocket floor annulus is incomplete')
        require(bp['arm_elbow_inset']-4.2 >= .2-1e-7, 'Elbow reaches into guide')
        head_top = hardware[name+'_nylon_adjuster'].bounding_box().max.Z
        measurements[name] = {'tip_local_xy_mm': [tx, ty],
                              'actual_pcb_left_inset_mm': tx+p['pcb_width']/2,
                              'actual_pcb_bottom_distance_mm': ty+p['pcb_length']/2,
                              'housing_y_mm': bp['housing_y'],
                              'collar_center_to_flat_mm': flat,
                              'collar_ligament_beside_clearance_hole_mm': flat-1.7,
                              'rounded_elbow_to_guide_face_mm': bp['arm_elbow_inset']-4.2,
                              'contact_head_to_lid_underside_at_rest_mm': rim-head_top,
                              'switch_height_above_pcb_mm_provisional': bp['switch_top_z']-board_top}

        frame = printed[name+'_frame']
        keeper = printed[name+'_rear_keeper']
        own_moving = {key: printed[key] for key in data['moving_names']}
        # Stops checked on final extended-pad geometry, not only base module.
        stops = {}
        for label, dz in (('upper', .05), ('lower', -bp['stroke']-.05)):
            hit = max(overlap(c.Pos(0, 0, dz)*shape, frame+keeper) for shape in own_moving.values())
            require(hit > 1e-5, 'Mechanical end stop missing', button=name, stop=label)
            stops[label] = {'overtravel_local_z_mm': dz, 'interference_mm3': hit}

        # Assemble before fitting the nylon contact screw and its jam nut.
        moving = own_moving | {name+'_'+suffix: hardware[name+'_'+suffix]
                              for suffix in ('moving_magnet', 'contact_heatset_insert')}
        excluded = set(moving) | {name+'_rear_keeper', name+'_nylon_adjuster', name+'_nylon_jam_nut',
                                  name+'_mount_screw_1', name+'_mount_screw_2', 'lid', 'desk_bracket'}
        fixed = {key: shape for key, shape in (printed | hardware).items()
                 if key not in excluded and not key.startswith('lid_') and not key.startswith('bracket_')}
        top_offsets = [i*.5 for i in range(71)]
        for dz in top_offsets:
            for key, shape in moving.items():
                clear(c.Pos(0, 0, dz)*shape, fixed,
                      f'{name} loaded-slider top insertion blocked at {dz:g} mm: {key}')

        # The external rear cover slides along +X onto the frame, before bolts.
        rear_fixed = {key: shape for key, shape in (printed | hardware).items()
                      if key not in (name+'_rear_keeper', name+'_mount_screw_1', name+'_mount_screw_2',
                                     'lid', 'desk_bracket') and not key.startswith('lid_')}
        rear_offsets = [i*.5 for i in range(71)]
        for dx in rear_offsets:
            clear(c.Pos(-dx, 0, 0)*keeper, rear_fixed,
                  f'{name} rear-keeper insertion blocked at {-dx:g} mm')
        captures = []
        for travel in (0, .4, .8):
            pp, hh = local_state(c, new, {name: travel})
            small = pp[name+'_moving_magnet_keeper']
            escape = c.Pos(-.5, 0, 0)*small
            cover_hit = overlap(escape, keeper)
            require(cover_hit > 1e-5, 'Tiny moving keeper can escape completed housing', button=name)
            captures.append({'travel_mm': travel, 'rear_escape_shift_mm': .5,
                             'cover_interference_mm3': cover_hit})
            for suffix in ('fixed_magnet', 'moving_magnet'):
                for axis, delta in (('rear', (-.5, 0, 0)), ('front', (.5, 0, 0)),
                                    ('side', (0, .4, 0)), ('up', (0, 0, .3)), ('down', (0, 0, -.3))):
                    hit = max(overlap(c.Pos(*delta)*hh[name+'_'+suffix], shape)
                              for key, shape in pp.items() if key.startswith(name+'_'))
                    require(hit > 1e-5, 'Magnet escape sample lacks a printed stop',
                            button=name, magnet=suffix, direction=axis, travel=travel)
        assembly_paths[name] = {'upper_and_lower_stops': stops,
                                'loaded_slider_top_insertion_offsets_local_z_mm': top_offsets,
                                'loaded_slider_items': list(moving),
                                'slider_insertion_contact_screw_and_jam_nut_removed': True,
                                'slider_insertion_lid_and_rear_keeper_removed': True,
                                'other_cartridge_remains_installed': True,
                                'rear_cover_insertion_offsets_local_x_mm': [-v for v in rear_offsets],
                                'tiny_magnet_keeper_retention_samples': captures,
                                'magnet_escape_samples': 'Five directions at three button travels blocked by completed housing',
                                'status': 'clear'}

    return {"measured_axis_checks": measurements, "assembly_and_retention_paths_without_usb": assembly_paths}


def bounds(shape):
    bb = shape.bounding_box()
    return [list(bb.min), list(bb.max)]


def from_bounds(c, points):
    lo, hi = points
    return c.box(hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2],
                 (hi[0]+lo[0])/2, (hi[1]+lo[1])/2, lo[2])


def hits(c, probe, shapes):
    result = {}
    for name, shape in shapes.items():
        volume = c.overlap(probe, shape)
        if volume > 1e-5:
            result[name] = {'volume_mm3': volume,
                            'intersection_bounds_local_mm': bounds(c.normalize(probe.intersect(shape)))}
    return result


def independent_usb(c, p):
    left = -p['pcb_width']/2
    center_y = -p['pcb_length']/2+p['usb_center_from_bottom']
    top = p['floor']+p['solder_clearance']+p['pcb_thickness']
    z = top+p['usb_plug_underside_above_pcb']
    lo = [left-p['usb_plug_projection'], center_y-p['usb_plug_width']/2, z]
    hi = [left, center_y+p['usb_plug_width']/2, z+p['usb_plug_thickness']]
    gap = p['usb_fit_clearance']
    enlarged = [[v-gap for v in lo], [v+gap for v in hi]]
    sweep = [list(enlarged[0]), list(enlarged[1])]
    sweep[1][2] += p['button_stroke']
    radius = p['usb_cable_diameter']/2
    cable_z = z+p['usb_plug_thickness']/2
    cable = c.Pos(lo[0]-30, center_y, cable_z)*c.Rot(Y=90)*c.cyl(radius, 30)
    return {'bounds': [lo, hi], 'clearance_bounds': enlarged, 'sweep_bounds': sweep,
            'nominal': from_bounds(c, [lo, hi]), 'clearance': from_bounds(c, enlarged),
            'sweep': from_bounds(c, sweep), 'cable': cable,
            'provisional_cable_axis_z': cable_z}


def preservation_and_material(c, new, old, p, usb):
    require = c.require
    refs = new['usb_relief_references_local']
    c.same(refs['plug_nominal'], usb['nominal'], 'Nominal measured plug independently constructed')
    c.same(refs['plug_clearance'], usb['clearance'], 'Independent clearance envelope')
    changed = {'reset_slider', 'boot_slider', 'boot_frame'}
    preserved = []
    for name, shape in new['parts'].items():
        require(shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0,
                'Printed part is not a single valid solid', part=name)
        require(abs(shape.bounding_box().min.Z) < 1e-7, 'Printed part is not on Z0', part=name)
        if name in changed:
            require(old['parts'][name].volume-shape.volume > .01, 'Expected USB relief did not remove material', part=name)
        else:
            c.same(shape, old['parts'][name], name+' unchanged printable geometry from013')
            c.same(new['assembly'][name], old['assembly'][name], name+' unchanged installed geometry from013')
            preserved.append(name)
    require(len(preserved) == 12, 'Unexpected unchanged printed inventory')
    require(set(new['hardware']) == set(old['hardware']) and len(new['hardware']) == 34,
            'Hardware inventory changed')
    for name, shape in new['hardware'].items():
        c.same(shape, old['hardware'][name], name+' unchanged hardware from013')
    material = {}
    for name in ('reset', 'boot'):
        bp = new['buttons'][name]['params']
        c.same(refs[name+'_slider_swept_clearance_at_rest'], usb['sweep'], 'Independent operating-travel sweep')
        cut = refs[name+'_slider_relief_cutter']
        cut_bounds = bounds(cut)
        for axis in (0, 1):
            require(abs(cut_bounds[0][axis]-usb['clearance_bounds'][0][axis]) < 1e-7
                    and abs(cut_bounds[1][axis]-usb['clearance_bounds'][1][axis]) < 1e-7,
                    'Loading relief changed measured XY clearance')
        require(abs(cut_bounds[1][2]-usb['sweep_bounds'][1][2]) < 1e-7,
                'Moving relief does not include full upward stroke sweep')
        prior_slider = old['case_local_assembly'][name+'_slider']
        require(cut_bounds[0][2] < prior_slider.bounding_box().min.Z,
                'Slider relief is not open to its bottom for top loading')
        final_slider = new['case_local_assembly'][name+'_slider']
        c.same(final_slider, prior_slider-cut, name+' changes only by the USB loading relief')
        frame_cut = refs[name+'_frame_open_rail_cutter']
        prior_frame = old['case_local_assembly'][name+'_frame']
        rail_bounds = [list(usb['clearance_bounds'][0]), list(usb['clearance_bounds'][1])]
        rail_bounds[1][2] = max(rail_bounds[1][2], prior_frame.bounding_box().max.Z)+.1
        c.same(frame_cut, from_bounds(c, rail_bounds), 'Frame rail clearance opens through its top')
        final_frame = new['case_local_assembly'][name+'_frame']
        c.same(final_frame, prior_frame-frame_cut, name+' frame changes only within open rail relief')
        require(c.overlap(frame_cut, final_frame) < 1e-7, 'Thin frame lip remains above the USB relief')
        # Exact preserved rear and negative-Y bearings; the frame also retains
        # every lower bearing below the raised plug. These are material checks,
        # not a friction, deflection or strength rating.
        rear_limit = usb['clearance_bounds'][0][0]
        rear = c.box(rear_limit+100, 160, 60, (rear_limit-100)/2, 0, 0)
        lower = c.box(160, 160, usb['clearance_bounds'][0][2], 0, 0, 0)
        # Limit this probe to the guide; RESET's distal contact lies on the
        # negative-Y side too and is intentionally relieved farther inboard.
        face = bp['mounting_face_x']
        negative = c.box(face+100, bp['housing_y']+80, 60,
                         (face-100)/2, (bp['housing_y']-80)/2, 0)
        c.same(c.normalize(final_frame.intersect(rear)), c.normalize(prior_frame.intersect(rear)),
               'Stationary rear guide bearing preserved')
        c.same(c.normalize(final_frame.intersect(lower)), c.normalize(prior_frame.intersect(lower)),
               'Stationary lower guide bearing preserved')
        for region in (rear, negative):
            c.same(c.normalize(final_slider.intersect(region)), c.normalize(prior_slider.intersect(region)),
                   'Moving rear and negative-side guide bearings preserved')
        magnet_x = bp['mounting_face_x']-7.2
        seats = c.box(6, 6, 10, magnet_x, bp['housing_y'], 10)
        for final, prior in ((final_frame, prior_frame), (final_slider, prior_slider)):
            c.same(c.normalize(final.intersect(seats)), c.normalize(prior.intersect(seats)),
                   'Printed fixed and moving magnet-seat regions preserved')
        tx, ty = bp['tip_x'], bp['tip_y']
        lo, hi = usb['clearance_bounds']
        dx = max(lo[0]-tx, 0, tx-hi[0])
        dy = max(lo[1]-ty, 0, ty-hi[1])
        wall = min(4.5, hypot(dx, dy))-bp['contact_insert_outer_diameter']/2
        require(wall >= 1.2-1e-7, 'USB corner leaves insufficient insert wall', button=name, wall_mm=wall)
        hardware = new['mount_transform']*new['hardware'][name+'_contact_heatset_insert']
        z = hardware.bounding_box().min.Z+.01
        height = hardware.bounding_box().max.Z-z-.01
        # A continuous 1.2 mm polymer ring outside the actual OD envelope must
        # survive over the entire insert height, excluding only end faces.
        ring = c.cyl(bp['contact_insert_outer_diameter']/2+1.2, height, tx, ty, z)
        ring -= c.cyl(bp['contact_insert_outer_diameter']/2+.001, height+.02, tx, ty, z-.01)
        require(abs(c.overlap(ring, final_slider)-c.volume(ring)) < 1e-5,
                'Actual CAD loses the continuous minimum insert-wall ring', button=name)
        material[name] = {'minimum_insert_envelope_wall_mm': wall,
                          'continuous_1_2mm_polymer_ring_over_insert_height': True,
                          'slider_loading_relief_bounds_local_mm': cut_bounds,
                          'frame_lower_and_rear_bearings_identical': True,
                          'slider_negative_side_and_rear_bearings_identical': True,
                          'fixed_and_moving_magnet_seat_regions_identical': True,
                          'frame_rail_has_no_thin_upper_lip': True}
    return {'unchanged_printed_parts': preserved, 'changed_printed_parts': sorted(changed),
            'unchanged_hardware_proxies': list(new['hardware']), 'material_checks': material}


def with_plug_assembly_paths(c, new, usb):
    printed, hardware = local_state(c, new, {'reset': 0, 'boot': 0})
    records = {}
    offsets = sorted(set([i*.5 for i in range(81)]+[.1, .2, .4]))
    for name in ('reset', 'boot'):
        moving = {key: printed[key] for key in new['buttons'][name]['moving_names']}
        moving |= {name+'_'+suffix: hardware[name+'_'+suffix]
                   for suffix in ('moving_magnet', 'contact_heatset_insert')}
        # Plug first, bare frame from -X, loaded slider from +Z, rear cover
        # from -X, then bolts and nylon contact adjustment. The bare frame is
        # held until the rear cover and correct length bolts secure it.
        common = {key: value for key, value in (printed | hardware).items()
                  if key not in ('lid', 'desk_bracket') and not key.startswith('lid_')
                  and not key.startswith(name+'_')}
        common['clearance_expanded_plug'] = usb['clearance']
        for offset in offsets:
            c.clear(c.Pos(-offset, 0, 0)*printed[name+'_frame'], common,
                    f'{name} bare frame cannot approach with USB installed at X offset {-offset:g}')
        slider_fixed = common | {name+'_frame': printed[name+'_frame'],
                                  name+'_fixed_magnet': hardware[name+'_fixed_magnet']}
        for offset in offsets:
            for key, shape in moving.items():
                c.clear(c.Pos(0, 0, offset)*shape, slider_fixed,
                        f'{name} loaded slider cannot top-load around USB at Z offset {offset:g}: {key}')
        rear_fixed = slider_fixed | moving
        for offset in offsets:
            c.clear(c.Pos(-offset, 0, 0)*printed[name+'_rear_keeper'], rear_fixed,
                    f'{name} rear cover cannot approach with USB installed at X offset {-offset:g}')
        records[name] = {'bare_frame_offset_local_x_samples_mm': [-v for v in offsets],
                         'loaded_slider_offset_local_z_samples_mm': offsets,
                         'rear_cover_offset_local_x_samples_mm': [-v for v in offsets],
                         'plug_probe': 'Clearance-expanded measured outboard bounding box',
                         'lid_removed': True, 'nylon_contact_screw_and_jam_nut_absent_during_loading': True,
                         'bare_frame_held_until_rear_cover_bolted': True, 'status': 'clear'}
    insertion = []
    for travel in (0, .8):
        pp, hh = local_state(c, new, {'reset': travel, 'boot': travel})
        for outward in (0, .5, 1, 2, 4, 6, 8, 12, 16, 20, 30, 40):
            blocked = hits(c, c.Pos(-outward, 0, 0)*usb['nominal'], pp | hh)
            insertion.append({'both_buttons_travel_mm': travel, 'plug_offset_x_mm': -outward,
                              'intersections': blocked})
    return {'cartridge_loading_with_plug_present': records,
            'straight_plug_insertion_after_cartridges': {
                'status': 'unresolved_conservative_envelope_obstructions' if any(v['intersections'] for v in insertion) else 'sampled_clear',
                'samples': insertion,
                'interpretation': 'Box uses maximum width over the entire projection; actual taper may differ. Use the verified plug-first sequence.'}}


def usb_motion_and_board_poses(c, new, p, usb):
    nominal_records, play_records = [], []
    worst = {}
    board_bottom = p['floor']+p['solder_clearance']
    xplay = (new['measurements']['board_retention']['shoulder_gap_mm']-p['pcb_width'])/2
    c.require(abs(xplay-.65) < 1e-7 and p['board_vertical_play'] == .2, 'Board play datum changed')
    axes = [(-xplay, 0, xplay), (-.4, 0, .4), (0, p['board_vertical_play'])]
    for reset, boot in product((0, .4, .8), repeat=2):
        travels = {'reset': reset, 'boot': boot}
        pp, hh = local_state(c, new, travels)
        shapes = pp | hh
        c.clear(usb['nominal'], shapes, 'Measured nominal outboard plug box intersects mechanism')
        c.clear(usb['clearance'], shapes, 'Specified clearance envelope intersects mechanism')
        c.clear(usb['cable'], shapes, 'Provisional centered straight cable envelope intersects mechanism')
        driver_records = []
        for name in ('reset', 'boot'):
            bp = new['buttons'][name]['params']
            sx, sy = bp['tip_x'], bp['tip_y']
            switch = c.cyl(2, 1, sx, sy, bp['switch_top_z']-1)
            c.clear(switch, {key: shape for key, shape in shapes.items() if key != name+'_nylon_adjuster'},
                    'Rigid mechanism intersects provisional switch')
            head_z = hh[name+'_nylon_adjuster'].bounding_box().max.Z
            service = {key: value for key, value in shapes.items() if key not in ('lid', 'desk_bracket')}
            service['measured_plug_box'] = usb['nominal']
            c.clear(c.cyl(1.5, 15, sx, sy, head_z+.05), service,
                    'Contact screwdriver path obstructed with USB installed')
            rear = bp['mounting_face_x']-14.2
            for dy in (-3, 3):
                driver = c.Pos(rear-33.05, bp['housing_y']+dy, bp['mount_hole_z'])*c.Rot(Y=90)*c.cyl(2, 30)
                c.clear(driver, shapes | {'measured_plug_box': usb['nominal']},
                        'Cartridge mounting screwdriver path obstructed with USB installed')
            driver_records.append({'button': name, 'contact_driver_diameter_mm': 3, 'cartridge_driver_diameter_mm': 4})
        nominal_records.append({'travel_mm': travels, 'measured_and_expanded_outboard_plug': 'clear',
                                'provisional_centered_cable': 'clear', 'driver_paths': driver_records})
        for dx, dy, dz in product(*axes):
            moved = c.Pos(dx, dy, dz)
            board = c.box(p['pcb_width'], p['pcb_length'], p['pcb_thickness'], dx, dy, board_bottom+dz)
            c.clear(board, shapes, 'Actual PCB thickness envelope intersects retained geometry at a placement limit')
            plug_hits = hits(c, moved*usb['nominal'], shapes)
            cable_hits = hits(c, moved*usb['cable'], shapes)
            entry = {'travel_mm': travels, 'board_and_plug_translation_local_mm': [dx, dy, dz],
                     'actual_pcb_slab': 'clear', 'conservative_plug_intersections': plug_hits,
                     'provisional_straight_cable_intersections': cable_hits,
                     'status': 'unresolved_envelope_contacts' if plug_hits or cable_hits else 'sampled_clear'}
            play_records.append(entry)
            for kind, values in (('plug', plug_hits), ('provisional_cable', cable_hits)):
                for name, data in values.items():
                    key = kind+'/'+name
                    if key not in worst or data['volume_mm3'] > worst[key]['volume_mm3']:
                        worst[key] = data | {'board_and_plug_translation_local_mm': [dx, dy, dz],
                                             'travel_mm': travels}
    return {'nominal_independent_states': nominal_records,
            'board_play': {'translations_x_mm': list(axes[0]), 'translations_y_mm': list(axes[1]),
                           'translations_z_mm': list(axes[2]), 'sample_count': len(play_records),
                           'worst_intersections_by_part': worst, 'samples': play_records,
                           'status': 'unresolved_envelope_contacts' if worst else 'sampled_clear',
                           'interpretation': 'PCB and plug move together; contact mechanisms stay fixed. Conservative box contacts at placement limits are not a passing physical fit or proof the real tapered plug fails.'},
            'cable_probe': {'diameter_mm_measured': p['usb_cable_diameter'],
                            'axis_height_above_perfboard_provisional_mm': usb['provisional_cable_axis_z']-(board_bottom+p['pcb_thickness']),
                            'axis_height_method': 'Assumed midpoint of plug thickness, not a user-measured cable axis',
                            'straight_length_outward_from_flexible_transition_mm': 30,
                            'interpretation': 'One provisional straight segment; cable bending and complete routing are not verified.'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--nominal-only', action='store_true', help='Diagnostic run without the clearance variant')
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    helper = Path(__file__).with_name('check-cable-retention.py')
    previous_checker = Path(__file__).with_name('check-measured-button-alignment.py')
    c = load(helper, 'measured_usb_geometry_helpers')
    mechanisms = load(previous_checker, 'measured_usb_existing_mechanism_helpers')
    before, old_hashes = c.hashes(source), c.hashes(baseline)
    p = json.loads((source/'parameters.json').read_text())
    measured = {'usb_plug_width': 10, 'usb_plug_thickness': 6, 'usb_plug_projection': 20,
                'usb_plug_underside_above_pcb': 9, 'usb_center_from_bottom': 23, 'usb_cable_diameter': 3.5}
    c.require(all(p[key] == value for key, value in measured.items()), 'Confirmed USB measurement mapping changed')
    c.require(p['usb_fit_clearance'] == .2, 'Nominal design clearance changed')
    old = load(baseline/'model.py', 'preserved013_before_usb_relief').build(
        json.loads((baseline/'parameters.json').read_text()))
    scenarios = [('nominal_clearance0_2', p)]
    if not args.nominal_only:
        scenarios.append(('variant_clearance0_25', p | {'usb_fit_clearance': .25}))
    reports = []
    for label, params in scenarios:
        new, report = mechanisms.check_model(source, c, params, label)
        usb = independent_usb(c, params)
        print(label+': material identity, insert wall and unmodified guide bearings', flush=True)
        report['preservation_and_material'] = preservation_and_material(c, new, old, params, usb)
        print(label+': cartridge loading, hard stops and magnet retention', flush=True)
        report['cartridges_without_usb'] = check_cartridges_without_usb(c, new, params)
        report['loading_with_usb'] = with_plug_assembly_paths(c, new, usb)
        print(label+': measured USB states and coupled PCB placement limits', flush=True)
        report['usb_and_board_poses'] = usb_motion_and_board_poses(c, new, params, usb)
        report['parameter_overrides'] = {key: value for key, value in params.items() if p[key] != value}
        report['usb_nominal_bounds_local_mm'] = usb['bounds']
        reports.append(report)
    c.require(c.hashes(source) == before and c.hashes(baseline) == old_hashes, 'Source changed during validation')
    result = {'status': 'passed', 'scope': 'Nominal geometry and bounded mechanism checks passed; physical fit and reported placement-limit envelope contacts remain unresolved.',
              'source_hashes': before, 'baseline_hashes': old_hashes,
              'checker_sha256': c.sha(Path(__file__)), 'geometry_helper_sha256': c.sha(helper),
              'reused_mechanism_checker_sha256': c.sha(previous_checker),
              'confirmed_user_measurements_mm': measured, 'parameter_variant_validated': not args.nominal_only,
              'scenarios': reports, 'physical_fit_tested': False,
              'limitations': ['Uniform maximum-width box includes strain relief and may overestimate actual molded plug shape.',
                              'The plug/jack portion inboard of the perfboard left edge is unmeasured and excluded.',
                              'Cable diameter is measured; its axis height, bend radius and complete route are not.',
                              'Switch height/travel, print tolerances, magnetic return, guide friction and material strength require physical tests.',
                              'Insertion and motion are finite samples, not a continuous swept-volume proof.',
                              'Board-play intersections are reported explicitly and do not establish a physical fit at every board position.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': 'passed', 'scenarios': len(reports), 'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
