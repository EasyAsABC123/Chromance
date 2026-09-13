"""Render actual button assembly geometry from an explicit revision snapshot.

Run from the packaged workbench: python assembly-guides/014-buttons/render-guide.py
Optional --source and --output select another complete model snapshot/directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from fdm_cad.build import load_model
from fdm_cad.preview import _rasterize
from build123d import Align, Box, Pos
import matplotlib.pyplot as plt
import numpy as np
import trimesh

BG = '#f4f5f6'
INK = '#253343'
COLORS = {'frame':'#788796','slider':'#55b6d0','rear_keeper':'#a794c2',
          'moving_magnet_keeper':'#e8ac56','fixed_magnet':'#d06c70',
          'moving_magnet':'#d06c70','contact_heatset_insert':'#c69d45',
          'nylon_adjuster':'#d0d7dd','nylon_jam_nut':'#e7dcc8',
          'mount_screw_1':'#85929d','mount_screw_2':'#85929d','body_section':'#b1b9c2',
          'board_reference':'#b8cdb8','plug_nominal':'#e3b367'}


def box_bounds(lo, hi):
    return Pos(*lo)*Box(*(b-a for a,b in zip(lo,hi)), align=(Align.MIN,)*3)


def mesh(shape):
    vertices, faces = shape.tessellate(0.02, 0.08)
    result = trimesh.Trimesh(vertices=[list(v) for v in vertices], faces=faces, process=True)
    result.fix_normals(multibody=True)
    return result


def draw_scene(fig, rect, shapes, elevation=22, azimuth=-65, width=1500, height=1150):
    entries = [(COLORS.get(name,'#788796'),mesh(shape)) for name,shape in shapes.items()]
    image = _rasterize(entries, elevation, azimuth, width=width, height=height)
    ax = fig.add_axes(rect); ax.imshow(image); ax.axis('off')
    az, el = np.radians([azimuth,elevation])
    camera = np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right = np.array([-np.sin(az),np.cos(az),0.0]); up = np.cross(camera,right)
    basis = np.stack([right,up,camera],axis=1)
    projected = np.concatenate([m.vertices for _,m in entries]) @ basis
    lower,upper = projected[:,:2].min(axis=0),projected[:,:2].max(axis=0)
    scale = min((width-120)/max(upper[0]-lower[0],1),(height-90)/max(upper[1]-lower[1],1))
    center=(upper+lower)/2
    def project(point):
        xy=(np.asarray(point) @ basis)[:2]
        xy=(xy-center)*scale
        return np.array([width/2+xy[0],height/2-xy[1]])
    return ax,project


def tag(ax, project, point, label, offset=(0,0), color=INK):
    ax.annotate(label,xy=project(point),xytext=offset,textcoords='offset points',
                ha='center',va='center',fontsize=12,weight='bold',color=color,
                bbox={'boxstyle':'circle,pad=.25','fc':'white','ec':color,'lw':1.3},
                arrowprops={'arrowstyle':'-','color':color,'lw':1.1} if offset!=(0,0) else None)


def note(ax, project, point, text, offset, color=INK, align='left'):
    ax.annotate(text,xy=project(point),xytext=offset,textcoords='offset points',
                ha=align,va='center',fontsize=12,color=color,
                bbox={'boxstyle':'round,pad=.35','fc':BG,'ec':'none','alpha':.96},
                arrowprops={'arrowstyle':'-','color':color,'lw':1.2})


def arrow(ax, project, start, end, color=INK, width=2):
    ax.annotate('',xy=project(end),xytext=project(start),
                arrowprops={'arrowstyle':'-|>','color':color,'lw':width,'mutation_scale':18})


def page(title, subtitle, revision):
    fig=plt.figure(figsize=(14.4,10.8),dpi=150,facecolor=BG)
    fig.text(.035,.952,title,size=23,weight='bold',color=INK)
    fig.text(.035,.916,subtitle,size=12,color='#536171')
    fig.text(.035,.022,f'Actual revision {revision} CAD • hardware proxies have no threads • assembly illustration, not a fit guarantee',size=10,color='#6c7986')
    return fig


def render_usb_clearance(full, params, output, revision):
    """Show actual local CAD crops and the measured rectangular USB envelope."""
    info=full['measurements']['usb_clearance']
    case=full['case_local_assembly']
    bp=full['buttons']['boot']['params']
    lo,hi=info['nominal_plug_bounds_local_mm']
    board_top=info['board_top_z_mm']
    # Clip display copies only. These bounds expose the forward BOOT rail and
    # both inboard arms while hiding tall finger pads and unrelated shell parts.
    crop_bounds=[[lo[0]-.6,bp['housing_y']-7.1,board_top-1.1],
                 [full['buttons']['reset']['params']['tip_x']+4.8,
                  full['buttons']['reset']['params']['housing_y']+6.1,hi[2]+.9]]
    crop=box_bounds(*crop_bounds)
    shapes={'frame':case['boot_frame']&crop,
            'slider':case['reset_slider']&crop,
            'rear_keeper':case['boot_slider']&crop}
    board_bounds=[[-params['pcb_width']/2,crop_bounds[0][1],board_top-params['pcb_thickness']],
                  [crop_bounds[1][0],crop_bounds[1][1],board_top]]
    shapes['board_reference']=box_bounds(*board_bounds)
    fig=page('USB relief / actual arms and measured plug envelope',
             'Case-local bench view. Display crops expose the notches; the USB box is a reference, not a printed part.',revision)
    fig.text(.055,.856,'RELIEFS EXPOSED',size=13,weight='bold',color=INK)
    fig.text(.55,.856,'PLUG AT NOMINAL CENTERED PCB POSITION',size=13,weight='bold',color=INK)
    ax,project=draw_scene(fig,(.015,.265,.515,.555),shapes,
                          elevation=32,azimuth=45,width=1150,height=1000)
    note(ax,project,[lo[0]+3.5,bp['housing_y']+6.3,lo[2]-params['usb_fit_clearance']],
         'BOOT forward rail\nopens upward',(10,115))
    note(ax,project,[-33,lo[1]-.2,21.5],
         'BOOT arm loading relief',(-175,105))
    reset_boss_top=full['buttons']['reset']['measurements']['contact_boss_top_z_at_rest_mm']
    note(ax,project,[hi[0]+params['usb_fit_clearance'],hi[1]+params['usb_fit_clearance'],reset_boss_top],
         'RESET corner relief',(60,-95))
    seated=shapes|{'plug_nominal':full['usb_relief_references_local']['plug_nominal']}
    ax,project=draw_scene(fig,(.52,.265,.46,.555),seated,
                          elevation=0,azimuth=180,width=1000,height=1000)
    ax.set_xlim(-140,1230);ax.set_ylim(1170,-100)
    dim='#28617d'
    def dimension(start,end,label,offset=(8,0)):
        a,b=project(start),project(end)
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'<->','color':dim,'lw':1.3})
        ax.annotate(label,xy=(a+b)/2,xytext=offset,textcoords='offset points',
                    ha='center' if offset[0]==0 else 'left',va='center',fontsize=11,
                    weight='bold',color=dim,bbox={'fc':BG,'ec':'none','pad':2})
    x=lo[0]
    dimension([x,lo[1],hi[2]+1.4],[x,hi[1],hi[2]+1.4],
              f'{params["usb_plug_width"]:g} mm wide',(0,13))
    dimension([x,lo[1]-1.8,lo[2]],[x,lo[1]-1.8,hi[2]],
              f'{params["usb_plug_thickness"]:g} mm',(8,0))
    note(ax,project,[x,(lo[1]+hi[1])/2,hi[2]],
         f'Top: local Z{hi[2]:g}\nDiagram B = {info["plug_top_above_pcb_derived_mm"]:g} above PCB',(-205,60))
    note(ax,project,[x,(lo[1]+hi[1])/2,lo[2]],
         f'Underside: local Z{lo[2]:g}\nD = {params["usb_plug_underside_above_pcb"]:g} above PCB',(-190,-30))
    note(ax,project,[info['board_left_x_mm'],-11,board_top],
         f'PCB top: local Z{board_top:g}',(-50,-35))
    fig.text(.05,.207,
             f'Measured plug: {params["usb_plug_width"]:g} mm wide × {params["usb_plug_thickness"]:g} mm thick × {params["usb_plug_projection"]:g} mm outboard projection.',
             size=13,weight='bold',color=INK)
    fig.text(.05,.167,
             'The maximum-width box covers the full projection. The actual taper and strain-relief profile remain unmeasured.',
             size=11.5,color='#536171')
    fig.text(.05,.125,
             f'The user clarified raw B = 6 as thickness. Original diagram B is top height: 9 + 6 = 15 mm above the PCB.',
             size=11.5,color='#536171')
    fig.text(.05,.084,
             f'Provisional clearance {params["usb_fit_clearance"]:g} mm; full {params["button_stroke"]:g} mm stroke. Board play, insertion and actual cable fit need test009.',
             size=11.5,color='#536171')
    fig.savefig(output/'05-usb-clearance.png',facecolor=BG);plt.close(fig)
    return {'printed_crop_bounds_local_mm':crop_bounds,
            'printed_sources':['boot_frame','reset_slider','boot_slider'],
            'board_reference_bounds_local_mm':board_bounds,
            'nominal_plug_bounds_local_mm':info['nominal_plug_bounds_local_mm'],
            'view':'Actual case-local printed shapes clipped for illustration; exact nominal plug reference is opaque in the second view.',
            'normalized_diagram_B_top_above_pcb_mm':info['plug_top_above_pcb_derived_mm'],
            'plug_thickness_mm':params['usb_plug_thickness']}


def main():
    here=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=here.parents[1]/'revisions/014-usb-clearance')
    parser.add_argument('--output',type=Path,default=here)
    args=parser.parse_args(); source=args.source.resolve(); output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    params=json.loads((source/'parameters.json').read_text()); full=load_model(source/'model.py',params)
    revision=source.name.split('-')[0]
    case=full['case_local_assembly']; original_hw=full['reference_hardware']; bp=full['buttons']['reset']['params']
    printed={name:case['reset_'+name] for name in ('frame','slider','rear_keeper','moving_magnet_keeper')}
    hardware={name:shape for key,shape in original_hw.items() if key.startswith('reset_') for name in [key[6:]]}
    face,y,tx,ty=bp['mounting_face_x'],bp['housing_y'],bp['tip_x'],bp['tip_y']
    mx=face-7.2
    body_crop=[[face-.3,y-8,0],[face+6.5,y+8,11]]
    body=case['body'] & box_bounds(*body_crop)
    offsets={'frame':[0,0,0],'slider':[0,0,22],'rear_keeper':[-18,0,0],
             'moving_magnet_keeper':[-20,0,22],'fixed_magnet':[-13,0,0],
             'moving_magnet':[-13,0,22],'contact_heatset_insert':[0,0,34],
             'nylon_jam_nut':[0,0,38],'nylon_adjuster':[0,0,51],
             'mount_screw_1':[-45,0,0],'mount_screw_2':[-45,0,0],'body_section':[16,0,0]}
    originals=printed | hardware | {'body_section':body}
    exploded={name:Pos(*offsets[name])*shape for name,shape in originals.items()}
    fig=page('RESET / EN cartridge — identify the parts','Bench orientation: lid opening up. Exploded offsets expose the parts; this is not a print layout.',revision)
    ax,project=draw_scene(fig,(.015,.08,.76,.81),exploded,elevation=20,azimuth=-115)
    labels={'frame':'A','slider':'B','rear_keeper':'C','moving_magnet_keeper':'D',
            'fixed_magnet':'1','moving_magnet':'2','contact_heatset_insert':'3',
            'nylon_adjuster':'4','nylon_jam_nut':'5','mount_screw_1':'6','body_section':'E'}
    tag_offsets={'frame':(12,-25),'slider':(-25,12),'rear_keeper':(-25,20),'moving_magnet_keeper':(-15,25),
                 'fixed_magnet':(-20,-15),'moving_magnet':(-20,12),'contact_heatset_insert':(30,0),
                 'nylon_adjuster':(30,0),'nylon_jam_nut':(30,0),'mount_screw_1':(-25,-12),'body_section':(25,-20)}
    for name,label in labels.items():
        bb=exploded[name].bounding_box(); point=(np.array(list(bb.min))+np.array(list(bb.max)))/2
        tag(ax,project,point,label,tag_offsets[name])
    legend=[('PRINTED PARTS',None),('A  Open-top frame','Holds the fixed magnet.'),
            ('B  Slider + long arm',f'Use the matching {revision} slider.'),('C  Large rear keeper','Closes and retains the cartridge.'),
            ('D  Tiny moving-magnet plug','Captured when C is installed.'),('E  Body mounting section','Two short M3×4 insert pilots.'),
            ('HARDWARE / ONE BUTTON',None),('1 + 2  Two Ø4×2 magnets','Axial magnetization; like poles face.'),
            ('3  M3×5 heat-set insert','Fits the slider contact boss.'),('4  Nylon M3×12 adjuster','Tip points down toward the switch.'),
            ('5  Nylon M3 jam nut','Locks the contact adjustment.'),('6  Two M3×18 bolts','Through keeper + frame into body.')]
    yy=.855
    for title,description in legend:
        fig.text(.775,yy,title,size=12 if description else 12.5,weight='bold',color=INK)
        if description:fig.text(.775,yy-.023,description,size=10.8,color='#536171');yy-=.067
        else:yy-=.035
    fig.savefig(output/'01-reset-exploded.png',facecolor=BG);plt.close(fig)

    # Offset sections follow this revision's guide and contact center axes.
    # Only display copies are cut; source assembly and printable files stay intact.
    divide_x=face+3
    cuts=[box_bounds([-120,-100,-10],[divide_x,y,100]),
          box_bounds([divide_x,-100,-10],[50,ty,100])]
    section_names=('frame','slider','rear_keeper','moving_magnet_keeper','fixed_magnet',
                   'moving_magnet','contact_heatset_insert','nylon_adjuster','nylon_jam_nut')
    sections={}
    for name in section_names:
        shape=originals[name]
        for cut in cuts:shape=shape-cut
        if len(shape.solids()):sections[name]=shape
    fig=page('How the magnetic return and contact fit together','Offset CAD section through the guide and contact axes. Bench press is downward; the installed desk orientation is flipped.',revision)
    ax,project=draw_scene(fig,(.025,.13,.95,.71),sections,elevation=0,azimuth=-90,width=1800,height=1150)
    # Like-pole labels denote the facing surfaces, not a measured polarity.
    fixed=hardware['fixed_magnet'].bounding_box(); moving=hardware['moving_magnet'].bounding_box()
    ftop=fixed.max.Z; mbottom=moving.min.Z
    note(ax,project,[mx,y,ftop],'Fixed Ø4×2 magnet',(-150,-40),color='#91474d')
    note(ax,project,[mx,y,mbottom],'Moving Ø4×2 magnet',(-150,38),color='#91474d')
    note(ax,project,[mx,y,(ftop+mbottom)/2],'Like poles face each other\nN↔N or S↔S',(-180,2),color='#91474d')
    # Short arrows point away from the gap to illustrate the repelling return.
    arrow(ax,project,[mx+2.7,y,ftop+.8],[mx+2.7,y,ftop-.4],color='#b95c62',width=1.6)
    arrow(ax,project,[mx+2.7,y,mbottom-.8],[mx+2.7,y,mbottom+.4],color='#b95c62',width=1.6)
    pad_top=printed['slider'].bounding_box().max.Z
    arrow(ax,project,[face-7.1,y,pad_top+1.7],[face-7.1,y,pad_top+.1],color='#247b99',width=2.5)
    note(ax,project,[face-7.1,y,pad_top],f'PRESS ↓\n{bp["stroke"]:g} mm modeled stroke',(-130,-10),color='#247b99')
    note(ax,project,[face-12.3,y,20.5],'Rear keeper captures\nthe stop lug + small plug',(-180,48))
    note(ax,project,[tx,ty,22.5],'M3×5 insert in the boss', (85,-5),color='#846526')
    note(ax,project,[tx,ty,26],'Nylon jam nut on top', (80,25))
    screw_top=hardware['nylon_adjuster'].bounding_box().max.Z
    arrow(ax,project,[tx,ty,screw_top+1.7],[tx,ty,screw_top+.1],color=INK)
    note(ax,project,[tx,ty,screw_top],'Adjuster enters from above', (70,45))
    tip_bottom=hardware['nylon_adjuster'].bounding_box().min.Z
    arrow(ax,project,[tx,ty,tip_bottom-.2],[tx,ty,tip_bottom-2.2],color='#247b99')
    note(ax,project,[tx,ty,tip_bottom],'Nylon tip pushes the switch\nCalibrate with lid accessible', (80,-42))
    fig.text(.04,.075,f'Magnet-face spacing: {mbottom-ftop:g} mm at rest → {mbottom-ftop-bp["stroke"]:g} mm at the modeled stop. This includes the intervening plastic.',size=12,color=INK)
    fig.text(.04,.048,'The keeper sets retention and travel. Verify free motion and return before placing the tip over the ESP32.',size=11,color='#536171')
    fig.savefig(output/'02-reset-cutaway.png',facecolor=BG);plt.close(fig)

    compare={'slider':case['reset_slider'],'rear_keeper':case['boot_slider']}
    fig=page('RESET and BOOT sliders — keep their long arms identified',f'Top view of the actual revision {revision} sliders, at their case positions. Keep the arms paired with their button.',revision)
    ax,project=draw_scene(fig,(.03,.20,.69,.67),compare,elevation=90,azimuth=-90,width=1300,height=900)
    for name,title,offset in [('reset','RESET / EN',(-150,20)),('boot','BOOT',(-150,-15))]:
        p=full['buttons'][name]['params'];note(ax,project,[p['tip_x'],p['tip_y'],24.8],title,offset)
    fig.text(.735,.79,'TINY MOVING-MAGNET PLUG',size=12,weight='bold',color=INK)
    draw_scene(fig,(.72,.43,.25,.31),{'moving_magnet_keeper':printed['moving_magnet_keeper']},elevation=28,azimuth=-55,width=650,height=550)
    plug_size=list(printed['moving_magnet_keeper'].bounding_box().size)
    fig.text(.735,.42,'Enlarged view — actual geometry',size=11,color='#536171')
    fig.text(.735,.385,' × '.join(f'{v:.2f}' for v in plug_size)+' mm',size=11,color=INK)
    fig.text(.735,.33,'Install into the slider pocket.\nThe large rear keeper must then\nclose the completed housing.',size=11,color='#536171',linespacing=1.5,va='top')
    spacing=abs(full['buttons']['reset']['params']['tip_y']-full['buttons']['boot']['params']['tip_y'])
    spacing_note=(f'Current modeled switch-tip spacing is {spacing:g} mm. '+
                  ('Measured XY applied; switch height, travel and physical fit remain pending.' if abs(spacing-14)<1e-8
                   else 'The reported 14 mm spacing still needs a separate actuator revision.'))
    fig.text(.04,.125,spacing_note,size=12,color=INK)
    fig.text(.04,.082,'These images explain assembly; they do not establish switch alignment, magnetic force or physical fit.',size=11,color='#536171')
    fig.savefig(output/'03-slider-comparison.png',facecolor=BG);plt.close(fig)

    # The substrate is a dimensioned reference envelope, not invented PCB detail.
    # Slider solids and contact axes come directly from this revision's assembly.
    align_info=full['measurements'].get('button_alignment')
    if align_info:
        bw,bl,thickness=params['pcb_width'],params['pcb_length'],params['pcb_thickness']
        board_top=full['measurements']['pcb_fasteners']['board_top_local_z_mm']
        board=box_bounds([-bw/2,-bl/2,board_top-thickness],[bw/2,bl/2,board_top])
        alignment_shapes={'board_reference':board,'slider':case['reset_slider'],
                          'rear_keeper':case['boot_slider']}
        fig=page('Button contact axes / measured board datums',
                 f'Actual revision {revision} sliders above a {bw:g} × {bl:g} mm substrate reference. PCB components are not modeled.',revision)
        ax,project=draw_scene(fig,(.04,.15,.93,.73),alignment_shapes,
                              elevation=90,azimuth=-90,width=1700,height=1200)
        ax.set_xlim(-30,1900);ax.set_ylim(1370,-90)
        dim_color='#28617d'
        def line(start,end,style='-'):
            a,b=project(start),project(end);ax.plot([a[0],b[0]],[a[1],b[1]],style,color=dim_color,lw=1.1)
        def dimension(start,end,label,text_offset=(8,0)):
            a,b=project(start),project(end)
            ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'<->','color':dim_color,'lw':1.4})
            ax.annotate(label,xy=(a+b)/2,xytext=text_offset,textcoords='offset points',
                        ha='left' if text_offset[0] else 'center',va='center',fontsize=12,weight='bold',
                        color=dim_color,bbox={'fc':BG,'ec':'none','pad':2})
        for name,label,dim_x in [('reset','RESET / EN',bw/2+7.5),('boot','BOOT',bw/2+15.5)]:
            px,py=align_info['tips_local_xy_mm'][name]
            center=project([px,py,board_top])
            ax.plot(center[0],center[1],marker='+',markersize=15,mew=1.8,color=dim_color)
            note(ax,project,[px,py,board_top],label,(50,18))
            line([px,py,board_top],[dim_x+1.5,py,board_top])
            line([bw/2,-bl/2,board_top],[dim_x+1.5,-bl/2,board_top])
            label_offset=(8,40) if name=='reset' else (8,0)
            dimension([dim_x,-bl/2,board_top],[dim_x,py,board_top],f'{py+bl/2:g} mm',label_offset)
        inset=align_info['left_edge_inset_mm'];inset_y=-bl/2-6
        line([-bw/2,-bl/2,board_top],[-bw/2,inset_y-1,board_top])
        line([-bw/2+inset,-bl/2,board_top],[-bw/2+inset,inset_y-1,board_top])
        dimension([-bw/2,inset_y,board_top],[-bw/2+inset,inset_y,board_top],f'{inset:g} mm',(0,-20))
        note(ax,project,[bw/2,bl/2,board_top],f'{bw:g} × {bl:g} mm board outline',(-25,25),align='right')
        fig.text(.045,.10,'Dimensions locate the contact axes from the left and bottom board edges. They do not set the vertical screw adjustment.',size=12,color=INK)
        fig.text(.045,.065,'Measured XY applied; switch height, travel, connector access and physical fit still require the small alignment test.',size=11,color='#536171')
        fig.savefig(output/'04-button-alignment.png',facecolor=BG);plt.close(fig)

    usb_illustration=render_usb_clearance(full,params,output,revision) if 'usb_clearance' in full['measurements'] else None
    names=['model.py','base_model.py','button_module.py','mounting.py','parameters.json']
    manifest={'source_revision':source.name,'source_path_from_guide':os.path.relpath(source,output),
        'source_sha256':{name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in names},
        'render_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'coordinate_frame':'Case-local bench orientation: +Z toward the open lid; press in -Z. The mounting wrapper flips the assembled enclosure for under-desk use.',
        'printed_source':'full.case_local_assembly: current extended pads and revision-specific slider arms, not standalone button-module defaults',
        'hardware_source':'full.reference_hardware: original case-local hardware proxies',
        'reset_exploded_translation_xyz_mm':offsets,'body_crop_bounds_local_mm':body_crop,
        'cutaway':'Display copies only: material in front of guide Y=housing_y is removed for X<mounting_face_x+3; material in front of contact Y=tip_y is removed farther inboard.',
        'magnet_polarity':'Labels illustrate like poles facing (N/N or S/S); actual polarity/return force is not inferred from CAD.',
        'magnified_keeper':'Same exact geometry, enlarged viewport; no new print geometry.',
        'printed_exports_created':False,'cad_geometry_modified':False,'physical_fit_tested':False,
        'images':['01-reset-exploded.png','02-reset-cutaway.png','03-slider-comparison.png']+(['04-button-alignment.png'] if align_info else [])+(['05-usb-clearance.png'] if usb_illustration else []),
        'board_alignment_reference':align_info,
        'usb_clearance_illustration':usb_illustration,
        'board_reference_geometry':'Measured rectangular substrate envelope only; no PCB components or switch bodies are inferred.'}
    (output/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':'rendered','output':str(output),'images':manifest['images']}))


if __name__=='__main__':main()
