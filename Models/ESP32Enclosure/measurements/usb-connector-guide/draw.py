"""Draw a new, deterministic measurement schematic; no photographs are edited.

Illustrated connector proportions are arbitrary. Only the named datums and
dimension endpoints are instructions; this does not measure or validate a plug.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

OUT = Path(__file__).resolve().parent
INK='#243344'; GREEN='#b5d6b1'; GREEN_EDGE='#397a42'; BLUE='#83acc9'
ORANGE='#f4b36b'; ORANGE_EDGE='#9d5c1b'; GRAY='#acb4bd'
COL={'A':'#216ab5','B':'#bc5b0e','C':'#216ab5','D':'#008277','E':'#8046a0','F':'#526173'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'svg.fonttype':'none'})
fig=plt.figure(figsize=(16,11), facecolor='white')
fig.text(.045,.965,'USB connector measurement guide',fontsize=26,weight='bold',color=INK)
fig.text(.045,.93,'Plug fully seated  •  All answers in mm  •  Schematic — connector size is not to scale',fontsize=14,color=INK)
plan=fig.add_axes([.04,.34,.46,.54]); side=fig.add_axes([.53,.34,.43,.54])
for ax in (plan,side):
    ax.set_axis_off(); ax.set_aspect('equal')

def rect(ax,x,y,w,h,color,edge=INK,z=2,lw=1.5):
    p=Rectangle((x,y),w,h,facecolor=color,edgecolor=edge,linewidth=lw,zorder=z)
    ax.add_patch(p);return p

def line(ax,xs,ys,color=INK,dashed=False,z=4,lw=1):
    ax.plot(xs,ys,color=color,linestyle=(0,(4,3)) if dashed else '-',linewidth=lw,zorder=z)

def dim(ax,start,end,letter,label_position):
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle='<->',mutation_scale=15,
                 shrinkA=0,shrinkB=0,color=COL[letter],linewidth=2,zorder=8))
    ax.text(*label_position,letter,color=COL[letter],fontsize=21,weight='bold',
            ha='center',va='center',zorder=9,
            bbox=dict(facecolor='white',edgecolor='none',pad=1.5))

def note(ax,text,xy,xytext,size=10,ha='left'):
    ax.annotate(text,xy=xy,xytext=xytext,ha=ha,va='center',fontsize=size,color=INK,
                arrowprops=dict(arrowstyle='-',color=INK,lw=1.2),zorder=10)

# TOP VIEW: green perfboard is [0,49] x [0,70]. USB centerline y=23 in
# this illustration only; E intentionally requests the real centerline.
plan.set_xlim(-58,81);plan.set_ylim(-8,82)
plan.text(-55,79,'TOP VIEW',color=INK,fontsize=18,weight='bold')
rect(plan,0,0,49,70,GREEN,GREEN_EDGE)
for x in (8,21,34):rect(plan,x,59,10,7,BLUE)
plan.text(24.5,74,'Terminals at top',ha='center',fontsize=11,color=INK)
rect(plan,-.5,9,51,26,BLUE)
rect(plan,25,13,17,17,'#d9dfe4')
plan.text(33.5,21.5,'ESP32',ha='center',va='center',fontsize=11,color=INK)
for y,name in ((31,'EN'),(15,'BOOT')):
    rect(plan,1,y-1.5,3,3,'white')
    plan.text(6,y,name,fontsize=8,va='center',color=INK)
rect(plan,-2,19,7,8,'#d9dfe4')
rect(plan,-23,16,21,14,ORANGE,ORANGE_EDGE)
plan.add_patch(Polygon([(-35,20),(-23,18),(-23,28),(-35,26)],
    closed=True,facecolor=ORANGE,edgecolor=ORANGE_EDGE,linewidth=1.5,zorder=2))
rect(plan,-49,21,-35-(-49),4,GRAY)
for x in (-33,-30,-27):line(plan,[x,x],[19.7,26.3],ORANGE_EDGE,z=3)
note(plan,'Plug + molded\nstrain relief',(-15,30),(-42,44),size=11)
line(plan,[-51,70],[23,23],INK,True)
# A extension lines terminate at the actual top/bottom orange body edges.
line(plan,[-53,-14],[30,30],COL['A'])
line(plan,[-53,-14],[16,16],COL['A'])
dim(plan,(-52,16),(-52,30),'A',(-57,23))
# E starts at the green substrate BOTTOM edge, not the blue daughterboard.
line(plan,[49,70],[0,0],COL['E'])
line(plan,[49,70],[23,23],COL['E'])
dim(plan,(67,0),(67,23),'E',(73,11.5))
plan.text(24.5,-4,'PERFBOARD BOTTOM EDGE',ha='center',va='center',fontsize=10,weight='bold',color=GREEN_EDGE)
note(plan,'USB centerline',(49,23),(50,42),size=10)

# SIDE VIEW: both height arrows share z=0, the TOP of green substrate.
# Connector drawing lies above it, with maximum z=15, minimum z=5.
side.set_xlim(-57,56);side.set_ylim(-24,47)
side.text(-55,44,'SIDE VIEW',color=INK,fontsize=18,weight='bold')
side.text(-55,38,'Look along the board’s long edge',fontsize=10,color=INK)
rect(side,0,-1.6,49,1.6,GREEN,GREEN_EDGE)
for x in (9,39):rect(side,x,0,2,5.2,'#7c8996')
rect(side,0,5.2,47,1,BLUE)
rect(side,21,6.2,18,5,'#d9dfe4')
rect(side,-2,6,7,8,'#d9dfe4')
rect(side,-23,5,21,10,ORANGE,ORANGE_EDGE)
side.add_patch(Polygon([(-35,8),(-23,6.5),(-23,13.5),(-35,12)],
    closed=True,facecolor=ORANGE,edgecolor=ORANGE_EDGE,linewidth=1.5,zorder=2))
rect(side,-46,8,-35-(-46),4,GRAY)
for x in (-33,-30,-27):line(side,[x,x],[7.8,12.2],ORANGE_EDGE,z=3)
# Green top is z=0. Dashed reference is drawn only outside the green board.
line(side,[-54,0],[0,0],GREEN_EDGE,True,lw=1.5)
line(side,[49,54],[0,0],GREEN_EDGE,True,lw=1.5)
note(side,'PERFBOARD TOP SURFACE\nB and D both start here',(23,0),(13,-9),size=10)
note(side,'ESP32 board',(40,6.2),(28,25),size=10)
note(side,'Flexible cable\nbegins here',(-35,12),(-43,27),size=10)
line(side,[-35,-35],[8,-18],INK,True)
line(side,[0,0],[-1.6,-18],GREEN_EDGE,True)
# B: arrow head at exact body top z=15; other head exactly datum z=0.
line(side,[-53,-15],[15,15],COL['B'])
dim(side,(-51,0),(-51,15),'B',(-55,7.5))
# D: no thickness measurement: plug lowest underside z=5 to datum z=0.
dim(side,(-13,0),(-13,5),'D',(-7,2.5))
# C: actual left-edge datum x=0 to rigid/strain-relief end x=-35.
dim(side,(-35,-14),(0,-14),'C',(-17.5,-20))
side.text(3,-20,'PERFBOARD\nLEFT EDGE',fontsize=9,color=GREEN_EDGE,ha='left',va='center')

# Large legend and answer template, with optional independent cable section.
fig.add_artist(plt.Line2D([.045,.955],[.325,.325],color='#d5dde5',lw=1))
left=[('A','Widest plug / molded strain-relief width'),
      ('B','Highest point above the perfboard top'),
      ('C','Projection past the left edge to flexible cable')]
right=[('D','Lowest underside above the perfboard top'),
       ('E','USB centerline from the perfboard bottom'),
       ('F','Optional: flexible cable diameter')]
for x,items in ((.05,left),(.53,right)):
    for y,(letter,definition) in zip((.275,.225,.175),items):
        fig.text(x,y,letter,color=COL[letter],weight='bold',fontsize=20,va='center')
        fig.text(x+.03,y,definition,fontsize=12,va='center',color=INK)
inset=fig.add_axes([.88,.13,.07,.07]);inset.set_aspect('equal');inset.set_axis_off()
inset.set_xlim(-1.3,1.3);inset.set_ylim(-1.3,1.3)
inset.add_patch(Circle((0,0),1,facecolor=GRAY,edgecolor=INK))
inset.add_patch(FancyArrowPatch((-1,0),(1,0),arrowstyle='<->',mutation_scale=12,
                              color=INK,shrinkA=0,shrinkB=0,linewidth=1.5))
inset.text(0,.48,'F',ha='center',va='center',weight='bold',color=INK,fontsize=12)
fig.text(.05,.095,'Reply:  A=__   B=__   C=__   D=__   E=__ mm     (F optional)',
         fontsize=20,weight='bold',color=INK)
fig.text(.05,.055,'Measure the connected plug. Use the green perfboard edges and top surface as the references.',
         fontsize=12,color=INK)
fig.savefig(OUT/'usb-measurements.png',dpi=160,facecolor='white')
fig.savefig(OUT/'usb-measurements.svg',facecolor='white')
svg_path = OUT/'usb-measurements.svg'
svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines())+'\n')
print(OUT/'usb-measurements.png')
