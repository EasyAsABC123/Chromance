"""Exact revision012 lower retention frame, with a coupon-only floor window."""
from pathlib import Path
from fdm_cad.build import load_model
from build123d import Align, Box, Pos


def build(params):
    full = load_model(Path(__file__).with_name('enclosure_model.py'), params)
    p = params
    body = full['case_local_assembly']['body']
    info = full['measurements']['pcb_fasteners']
    h = info['clamp_top_local_z_mm']
    bounds = body.bounding_box()
    lower = [bounds.min.X-1, bounds.min.Y-1, 0]
    upper = [bounds.max.X+1, bounds.max.Y+1, h]
    crop = Pos(*lower)*Box(*(b-a for a,b in zip(lower,upper)),align=(Align.MIN,Align.MIN,Align.MIN))
    # Keep the 44 x 66 mm nominal window, at least 1 mm inboard of the deeper
    # shelf faces across the supported parameter range. Interfaces stay intact.
    win_w,win_l = p['pcb_width']-5, p['pcb_length']-4
    assert p['pcb_width']/2-p['board_edge_overlap']-win_w/2 >= 1-1e-8
    window = Pos(0,0,-1)*Box(win_w,win_l,h+2,align=(Align.CENTER,Align.CENTER,Align.MIN))
    frame = (body & crop)-window
    clamps = {n:s for n,s in full['case_local_assembly'].items() if n.startswith('pcb_clamp_')}
    parts = {'board_fit_frame':frame} | {n:full['parts'][n] for n in clamps}
    for name,shape in parts.items():
        assert shape.is_valid and len(shape.solids())==1 and abs(shape.bounding_box().min.Z)<.001, name
    x_play = .4+p['board_fit_width_extra']/2
    pcb = Pos(0,0,info['board_bottom_local_z_mm'])*Box(p['pcb_width'],p['pcb_length'],p['pcb_thickness'],align=(Align.CENTER,Align.CENTER,Align.MIN))
    return {
        'title':'Easier PCB fit and deeper shelves / test 007',
        'parts':parts, 'assembly':{'board_fit_frame':frame}|clamps,
        'reference_pcb':pcb, 'full_model':full,
        'measurements':{
            'source_revision':'012-easier-board-fit',
            'pcb_xyz_mm':[p['pcb_width'],p['pcb_length'],p['pcb_thickness']],
            'crop_bounds_local_mm':[lower,upper],
            'coupon_floor_window_xy_mm':[win_w,win_l],
            'frame_height_mm':h,
            'board_bottom_z_mm':info['board_bottom_local_z_mm'],
            'board_top_z_mm':info['board_top_local_z_mm'],
            'locating_gap_width_mm':p['pcb_width']+2*x_play,
            'fit_width_extra_total_mm':p['board_fit_width_extra'],
            'ledge_inner_gap_width_mm':p['pcb_width']-2*p['board_edge_overlap'],
            'board_slot_height_mm':p['pcb_thickness']+p['board_vertical_play'],
            'vertical_play_mm':p['board_vertical_play'],
            'x_play_each_direction_mm':x_play,
            'y_play_each_direction_mm':.4,
            'nominal_edge_overlap_mm':p['board_edge_overlap'],
            'minimum_edge_overlap_mm':p['board_edge_overlap']-x_play,
            'pcb_fasteners':info,
            'physical_fit_tested':False,
            'scope':'Exact full-width lower frame and four clamps. Central floor removed only for coupon; upper shell, buttons, lid, cable seat, desk mounting and full-height tool access are omitted.',
        },
        'notes':[
            'Print one frame and four clamps at 100% scale. Interfaces are exact revision012 body/clamp geometry, cropped at clamp-top height, with a central floor window to reduce material.',
            'Body frame floor-down and clamps flat match the final orientation. Use the intended final material/nozzle/layer height/compensation; these geometry 3MF files contain no verified slicer profile.',
            'Use four M3x5 heat-set inserts and four M3x6 socket screws. OD4.6/pilot4.0 mm are provisional. Install flush before placing the board; do not substitute M3x8 screws, which bottom in the blind pilots.',
            'Place the unpowered 49x70x1 mm PCB on all four shelves. Check that shelves and clamps touch bare board only, with no solder/component contact. Tighten clamps onto their printed shoulders without bending the board.',
            f"Measure the {p['pcb_width']+2*x_play:g} mm locating gap and {p['pcb_width']-2*p['board_edge_overlap']:g} mm gap between inner shelf faces at both front/rear pairs. Capture slot is {p['pcb_thickness']+p['board_vertical_play']:g} mm high, leaving {p['board_vertical_play']:g} mm vertical play.",
            f"Shelves and matching upper clamps overlap the centered PCB by {p['board_edge_overlap']:g} mm. Minimum overlap after full lateral movement is {p['board_edge_overlap']-x_play:g} mm. Verify this wider contact strip is bare board on both faces.",
            'Support the board while turning the assembled frame over; it must stay captured without rocking or slipping off the ledges. Verify the actual 52 mm populated span clears the clamps.',
            'Start with supports off and inspect short horizontal pilot roofs in the slicer. The center window omits underside collision checking there; check protrusions against the 6.6 mm allowance separately.',
            'This short open frame cannot establish full shell stiffness/warping, long heat-set tool reach, button alignment, lid or mount fit, or load capacity. Physical results remain pending.',
        ],
    }
