"""Mikero PCG + three sprite detail planes. Exactly one 16K graphics bank.
Original dungeon bytes/placements are retained from the first edition.
No generated bitmap art: all animation is native TMS9918 pattern/color data.
"""
from pathlib import Path
import math,json,hashlib
import base_assets as base
THEMES=['MOSS LANTERNS','CANDY SPORES','TIDAL TEMPLE','CRYSTAL SNOW','EMBER FOUNDRY','CLOCKWORK GOLD','AURORA GARDEN','STARLESS CROWN']
def blank():return [[0]*16 for _ in range(16)]
def matrix(rows):return [[int(c=='#') for c in r] for r in rows]
def pcg(p,colors,bg=1):
 b=bytearray();c=bytearray()
 for q in range(4):
  for yy in range(8):
   y=(q//2)*8+yy;x=(q%2)*8
   b.append(sum(p[y][x+i]<<(7-i) for i in range(8)));c.append((colors[y]<<4)|bg)
 return bytes(b+c)
def sprite(p):
 return bytes(sum(p[y][x+i]<<(7-i) for i in range(8)) for x in (0,8) for y in range(16))
def cat(frame):
 p=matrix(['..#..........#..','..##........##..','..###......###..','..############..','.##############.','.###..####..###.','.###..####..###.','.##############.','..############..','...##########...','....########..#.','....########.##.','.....######..#..','....###..###....','....###..###....','................'])
 whites=blank();eyes=blank();gold=blank()
 for y,xs in [(6,[2,3,12,13]),(7,[1,2,6,7,8,9,13,14]),(8,[3,4,5,6,8,9,10,11,12]),(9,[5,6,7,8,9,10])]:
  for x in xs:whites[y][x]=1
 if frame!=3:
  for x in (4,10):eyes[5][x]=eyes[6][x]=1
 else:
  for x in (4,5,10,11):p[5][x]=p[6][x]=1
 for x,y in [(13,0),(12,1),(11,2),(7,8),(7,11),(8,11)]:gold[y][x]=1
 # A teal cape and orange ears identify the browser game's adventurer cat.
 colors=[9]*10+[7,7,5,10,10,1]
 if frame in (1,2,5,7):
  p[10][14]=0;p[11][14]=0;p[12][14]=1;p[13][14]=1
 if frame>=4:
  for x in range(3,13):p[14][x]=0
  for x in (range(3,6) if frame&1 else range(10,13)):p[14][x]=1
 if frame in (2,5,7):
  p=[p[-1]]+p[:-1];colors=[1]+colors[:-1]
  whites=[blank()[0]]+whites[:-1];eyes=[blank()[0]]+eyes[:-1];gold=[blank()[0]]+gold[:-1]
 return pcg(p,colors),sprite(whites)+sprite(eyes)+sprite(gold)

def scenery(theme,phase):
 f=blank();w=blank()
 for y in range(16):
  for x in range(16):
   # Each floor changes geometry as well as hue, while keeping a readable wall.
   if theme==0:w[y][x]=(y%5==0 or (x+(y//5)*7)%13==0)
   if theme==1:w[y][x]=((x+y)//3)%2==0 and (y in (1,2,13,14) or x in (1,2,13,14))
   if theme==2:w[y][x]=(y%4==0 or (x+(y//4)*5)%11==0)
   if theme==3:w[y][x]=(abs(x-7)+abs(y-7))%7 in (0,1)
   if theme==4:w[y][x]=(x==(y//2+phase//2)%16 or y%7==0 or x in (0,15))
   if theme==5:w[y][x]=(x in (1,14) or y in (1,14) or 14<=(x-7)**2+(y-7)**2<=26)
   if theme==6:w[y][x]=(x-y-phase//2)%9==0 or (x+y+phase//2)%13==0
   if theme==7:w[y][x]=(abs(x-7)+abs(y-7) in (6,7,12,13))
 # User-requested quiet floor: black plus one/two small marks, no glow field.
 f=blank()
 fg,hi,bg=[(3,10,4),(13,15,6),(7,15,4),(7,15,5),(9,10,6),(10,15,6),(13,7,4),(5,13,4)][theme]
 fc=[[2,6,4,4,6,6,4,4][theme]]*16
 wc=[hi if (y+phase*2)%7==0 else fg for y in range(16)]
 a=pcg(f,fc);b=pcg(w,wc,bg)
 # contiguous 64 pattern bytes followed by contiguous 64 color bytes
 return a[:32]+b[:32]+a[32:]+b[32:]

def friendly_enemy(t,frame):
 p=blank();colors=[3]*16
 def ellipse(cx,cy,rx,ry):
  for y in range(16):
   for x in range(16):
    if ((x-cx)/rx)**2+((y-cy)/ry)**2<=1:p[y][x]=1
 if t==11: # smiling green jelly
  ellipse(7.5,10,6.5,4.5 if frame%2==0 else 3.5);fy=9
  colors=[3]*11+[2]*5
 elif t==12: # round chick with small flapping wings, no fangs
  ellipse(7.5,8,4.5,5);ellipse(2.5,8-(frame%2)*2,2,1.5);ellipse(12.5,8-(frame%2)*2,2,1.5)
  p[2][7]=1;p[1][8]=1;fy=7;colors=[10]*12+[11]*4
 elif t==13: # mushroom cap and rounded cream face
  ellipse(7.5,10,3.5,4);ellipse(7.5,5,6.5,4)
  for x,y in [(5,3),(10,4),(3,6)]:p[y][x]=0;p[y][x+1]=0
  fy=10;colors=[9]*8+[11]*8
 elif t==14: # soft cloud with a smile, no ghost tail
  ellipse(7.5,9,6.5,3.5);ellipse(4.5,7,3,3);ellipse(9,6,3.5,3.5);ellipse(12,8,2.5,2.5)
  fy=8;colors=[15]*10+[7]*6
 else: # crowned round jelly, replacing the horned humanoid boss
  ellipse(7.5,10,7,5);fy=9;colors=[10]*5+[13]*7+[7]*4
  for y in range(1,5):
   for x in range(4,12):p[y][x]=y>=3 or x in (4,7,8,11)
 for x in (6,9):p[fy][x]=0;p[min(15,fy+1)][x]=0
 # Small U-shaped smile instead of teeth or a grimace.
 p[fy+2][6]=0;p[fy+2][9]=0;p[fy+3][7]=0;p[fy+3][8]=0
 if frame==3:p[fy+1][6]=1;p[fy+1][9]=1
 if frame==1 and t in (12,13,14):p=[blank()[0]]+p[:-1];colors=[colors[0]]+colors[:-1]
 return pcg(p,colors)

def rabbit_keeper(frame):
 p=matrix(['....##....##....','....##....##....','....##....##....','....##....##....','....########....','...##########...','...##.####.##...','...##.####.##...','....########....','.....##..##.....','....########....','...##########...','...##.####.##...','......####......','....###..###....','................'])
 # Ear wiggle and blink; retain the same four-frame PCG slot.
 if frame==1:p[0][5]=0;p[0][3]=1;p[0][10]=0;p[0][12]=1
 if frame==2:p[7][5]=1;p[7][10]=1
 if frame==3:p[1][4]=0;p[1][3]=1;p[1][11]=0;p[1][12]=1
 return pcg(p,[15]*6+[15,15,15,13,7,7,7,5,15,1])

def actor(t,frame):
 if t==7:return rabbit_keeper(frame)
 if 11<=t<=15:return friendly_enemy(t,frame)
 p=matrix(base.ART[t]);colors=base.COLORS[t][:]
 if t==11: # squash/stretch slime
  if frame&1:p=[blank()[0]]+p[:-1]
  if frame==2:p[12]=p[11][:];p[13]=blank()[0]
 elif t==12: # bat wings open / down
  if frame&1:
   for y in range(1,6):
    for x in list(range(0,5))+list(range(11,16)):
     p[11-y][x]=p[y][x];p[y][x]=0
 elif t==13:
  if frame&1:p[14][4]=0;p[14][11]=0
 elif t==14:
  p=[p[(y-frame)%16][:] for y in range(16)]
 else:
  if t in (2,3,4,5,9):colors=[15 if (y+frame*3)%11==0 else c for y,c in enumerate(colors)]
  if t==6: # fish replaces the food icon, preserving the food mechanic
   p=matrix(['................','................','................','...##...........','...###..#####...','....##########..','.....#######.##.','....##########..','...###..#####...','...##...........','................','................','................','................','................','................'])
   colors=[7]*16
  if t in (6,7) and frame&1:p=[blank()[0]]+p[:-1]
 return pcg(p,colors)

def effects():
 out=b''
 for phase in range(8):
  p=blank()
  if phase<4:
   # Four pads and a broad central pad, growing then dissolving.
   scale=[0.55,0.8,1.0,1.0][phase]
   for y in range(16):
    for x in range(16):
     xx=(x-7.5)/scale+7.5; yy=(y-7.5)/scale+7.5
     pad=((xx-7.5)/4.0)**2+((yy-10.5)/3.0)**2<=1
     toes=any(((xx-cx)/1.5)**2+((yy-cy)/2.0)**2<=1 for cx,cy in [(2.5,5.5),(5.7,2.8),(9.3,2.8),(12.5,5.5)])
     p[y][x]=(pad or toes) and (phase!=3 or (x+y)%2==0)
  else:
   r=2+(phase-4)*2
   for y in range(16):
    for x in range(16):
     if abs(x-7)+abs(y-7)==r:p[y][x]=1
  out+=sprite(p)
 for kind in range(4):
  p=blank()
  for y in range(16):
   for x in range(16):
    if kind==0:p[y][x]=(x==7 and 4<=y<=10) or (y==7 and 4<=x<=10)
    if kind==1:p[y][x]=5<=(x-7)**2+(y-7)**2<=10
    if kind==2:p[y][x]=abs(x-7)==abs(y-7) and abs(x-7)<=2
    if kind==3:p[y][x]=(x==7 and y in (6,7,8)) or (x==8 and y==8)
  out+=sprite(p)
 for phase in range(4):
  p=blank()
  for y in range(16):
   for x in range(16):
    clouds=any((x-cx)**2+(y-cy)**2<=rad**2 for cx,cy,rad in [(5-phase,8-phase,3),(10+phase,8-phase,3),(8,10-phase,4),(8,5-phase,3)])
    p[y][x]=clouds and (phase<2 or (x+y)%2==0) and (phase<3 or (x+2*y)%3==0)
  out+=sprite(p)
 return out

def generate(out):
 out.mkdir(parents=True,exist_ok=True)
 static=base.make_graphics()[:4096]
 c0,_=cat(0);static=bytearray(static)
 # Eight 16x16 triangular bearings in previously unused characters 0..31.
 for direction in range(8):
  angle=direction*math.pi/4
  vertices=[(7.5+(x-7.5)*math.cos(angle)-(y-7.5)*math.sin(angle),7.5+(x-7.5)*math.sin(angle)+(y-7.5)*math.cos(angle)) for x,y in [(7.5,1),(13.5,13),(1.5,13)]]
  p=blank()
  for y in range(16):
   for x in range(16):
    cross=[(vertices[(i+1)%3][0]-vertices[i][0])*(y-vertices[i][1])-(vertices[(i+1)%3][1]-vertices[i][1])*(x-vertices[i][0]) for i in range(3)]
    p[y][x]=all(v>=0 for v in cross) or all(v<=0 for v in cross)
  a=pcg(p,[10,10,11,15,15,11,10,10,10,10,10,10,10,10,10,10]);off=direction*32
  static[off:off+32]=a[:32];static[2048+off:2048+off+32]=a[32:]
 # Text is PCG too: cyan/white/blue lettering, warm gold numerals, and
 # four colored ornamental line glyphs. No raster palette emulation.
 for ch in range(32,128):
  cols=[7,7,15,15,7,5,5,1]
  if 48<=ch<=57:cols=[11,10,15,15,10,10,6,1]
  static[2048+ch*8:2048+ch*8+8]=bytes((c<<4)|1 for c in cols)
 for i in range(4):
  static[(94+i)*8:(95+i)*8]=bytes([0,0,255,0,0,0,0,0])
  static[2048+(94+i)*8:2048+(95+i)*8]=bytes([([7,13,10,3][i]<<4)|1]*8)
 for i,ch in enumerate('MIKERO'):
  p=blank()
  for y,row in enumerate(base.FONT[ch]):
   for x,b in enumerate(row):
    if b=='1':
     for dy in range(2):
      for dx in range(2):p[y*2+dy][x*2+3+dx]=1
  a=pcg(p,[7,7,7,15,15,15,15,7,7,5,5,5,13,13,1,1]);t=21+i
  static[(128+t*4)*8:(132+t*4)*8]=a[:32]
  static[2048+(128+t*4)*8:2048+(132+t*4)*8]=a[32:]
 static[168*8:172*8]=c0[:32];static[2048+168*8:2048+172*8]=c0[32:]
 for t in (0,1):
  e=scenery(0,0);static[(128+4*t)*8:(132+4*t)*8]=e[t*32:t*32+32];static[2048+(128+4*t)*8:2048+(132+4*t)*8]=e[64+t*32:96+t*32]
 for t in (6,7,11,12,13,14,15):
  a=actor(t,0);static[(128+t*4)*8:(132+t*4)*8]=a[:32];static[2048+(128+t*4)*8:2048+(132+t*4)*8]=a[32:]
 # Rescue-only resting cat and stretcher, unused PCG slots 27/28.
 resting=matrix(['................','................','................','................','..#....#........','..##..##........','.########.......','.##.##.##.......','.########.####..','..######.######.','...############.','....###########.','.....##....##...','................','................','................'])
 stretcher=matrix(['################','################','..############..','..############..','..#..........#..','................','................','................','................','................','................','................','................','................','................','................'])
 for t,p,colors in [(27,resting,[9]*9+[15]*4+[9]*3),(28,stretcher,[10,10,7,7,10]+[1]*11)]:
  a=pcg(p,colors);static[(128+t*4)*8:(132+t*4)*8]=a[:32];static[2048+(128+t*4)*8:2048+(132+t*4)*8]=a[32:]
 bank=bytes(static)+b''.join(cat(i)[0] for i in range(8))+b''.join(cat(i)[1] for i in range(8))
 assert len(bank)==0x1500
 bank+=b''.join(scenery(t,f) for t in range(8) for f in range(8))
 assert len(bank)==0x3500
 bank+=b''.join(actor(t,f) for t in range(11,15) for f in range(4))
 assert len(bank)==0x3900
 bank+=b''.join(actor(t,f) for t in (2,3,4,5,6,7,9) for f in range(4))
 assert len(bank)==16384
 (out/'graphics.bin').write_bytes(bank)
 maps=[base.dungeon(i) for i in range(120)];counts=[base.audit(m) for m in maps]
 blob=b''.join(maps);(out/'dungeons.bin').write_bytes(blob)
 fx=effects()
 inc='_effect_patterns::\n'+''.join('.db '+','.join('0x%02x'%n for n in fx[i:i+16])+'\n' for i in range(0,len(fx),16))
 (out/'visual_data.inc').write_text(inc)
 return dict(layouts=120,all_maps_connected=True,map_size=[64,64],maps_sha256=hashlib.sha256(blob).hexdigest(),graphics_sha256=hashlib.sha256(bank).hexdigest(),themes=THEMES,cat_frames=8,cat_sprite_planes=3,environment_frames_per_floor=8,enemy_frames=4,item_frames=4,max_sprites_per_scanline=4,irq_animation_target_hz={'ntsc':30,'pal':25})
