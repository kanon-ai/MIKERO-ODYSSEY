"""Hand-drawn indexed SCREEN 5 artwork. No external artwork or BIOS included."""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import base_assets as base

# Ink, jade masonry, warm ivory and amber; all values are native 3-bit RGB.
PAL=[(0,0,0),(4,5,4),(1,1,2),(2,2,4),(3,4,5),(2,4,4),(5,6,7),(2,6,6),(3,2,2),(7,3,2),(7,5,2),(6,4,3),(4,3,5),(6,4,6),(5,6,6),(7,7,6)]
def tile(t,frame=0):
 im=Image.new('P',(16,16),1);d=ImageDraw.Draw(im)
 def rect(box,c):d.rectangle(box,fill=c)
 def ell(box,c):d.ellipse(box,fill=c)
 if t==1:
  d.rounded_rectangle((0,0,15,15),radius=3,fill=2)
  d.rounded_rectangle((1,1,14,13),radius=3,fill=4)
  d.line((4,1,11,1),fill=6);d.line((2,3,2,7),fill=6)
  d.line((4,13,12,13),fill=3);d.point((13,11),fill=3)
  d.line((6,6,9,6),fill=5)
 elif t==17:
  rect((0,0,15,15),0)
  d.rounded_rectangle((0,0,15,15),radius=3,fill=2)
  d.line((3,15,12,15),fill=0)
 elif t==0:pass
 elif t in (16,18):rect((0,0,15,15),0)
 elif t==10 or t==27:
  # Six opaque sprite planes, with rounded ivory face and an orange patch.
  pts=[(2,1),(6,4),(9,4),(13,1),(14,9),(12,11),(12,14),(9,15),(6,14),(3,15),(3,11),(1,9)]
  d.polygon(pts,fill=2);d.polygon([(3,3),(6,5),(11,5),(12,3),(13,8),(11,11),(4,11),(2,8)],fill=15)
  d.polygon([(3,3),(6,5),(6,8),(2,7)],fill=9);d.polygon([(10,5),(12,3),(13,7),(10,7)],fill=9)
  rect((4,7,4,8),2);rect((10,7,10,8),2);rect((7,9,8,9),9)
  d.line((6,10,9,10),fill=2);rect((4,11,11,12),7);rect((5,13,10,14),5)
  rect((4 if frame%2 else 3,14,5,14),15);rect((10,14,12 if frame%2 else 11,14),15);rect((7,12,8,12),10)
  if t==27:im=im.rotate(90)
 elif t==7:
  ell((3,0,6,7),15);ell((9,0,12,7),15);rect((4,1,4,4),13);rect((10,1,10,4),13)
  ell((2,5,13,12),15);rect((5,8,5,9),2);rect((10,8,10,9),2);rect((7,10,8,10),13)
  rect((4,12,11,14),7);rect((6,12,9,13),15);rect((3,15,6,15),15);rect((10,15,12,15),15)
 elif t in (11,15):
  ell((1,5,14,14),2);ell((2,5,13,13),5 if t==11 else 12);ell((3,5,12,10),7 if t==11 else 13)
  d.line((4,7,6,6),fill=15);rect((5,9,5,10),2);rect((10,9,10,10),2);rect((7,12,9,12),2)
  if t==15:d.polygon([(4,6),(3,1),(6,3),(8,0),(10,3),(13,1),(12,6)],fill=10);rect((5,5,11,5),15)
 elif t==12:
  ell((0,7,5,10),10);ell((10,7,15,10),10);ell((4,3,12,13),11);ell((4,3,11,11),10)
  rect((6,6,6,7),2);rect((10,6,10,7),2);rect((7,9,9,9),9);rect((7,1,8,3),15)
 elif t==13:
  ell((4,6,11,14),11);ell((5,6,10,13),15);ell((0,1,15,9),8);ell((1,1,14,7),9)
  ell((3,3,5,5),15);ell((9,2,11,4),15);rect((6,10,6,11),2);rect((9,10,9,11),2)
 elif t==14:
  for box in [(0,7,15,13),(1,4,9,12),(6,2,14,12)]:ell(box,14)
  for box in [(1,6,14,11),(2,3,8,10),(7,2,13,9)]:ell(box,15)
  rect((5,8,5,9),2);rect((10,8,10,9),2);rect((7,11,9,11),7)
 elif t in (2,9):
  rect((2,1,13,15),2);d.arc((2,0,13,12),180,360,fill=10,width=2);rect((2,6,3,14),5);rect((12,6,13,14),5)
  if t==9:ell((5,4,10,13),12);ell((6,5,9,12),7)
  else:
   for y in (8,11,14):rect((4,y,11,y),14);rect((4,y+1,11,y+1),4)
 elif t==3:
  rect((6,1,9,3),10);rect((6,4,9,5),14);ell((3,5,12,14),14);ell((4,7,11,13),7);rect((5,7,5,10),15);rect((7,10,9,11),5)
 elif t in (4,20):
  for x,y in [(2,8),(7,9),(5,3)]:ell((x,y,x+4,y+5),11);ell((x,y,x+3,y+3),10);d.point((x+1,y+1),fill=15)
 elif t==5:
  rect((1,5,14,13),8);ell((1,2,14,10),11);rect((2,5,13,13),11);rect((3,8,12,12),8);rect((2,5,13,6),10);rect((2,12,13,13),10);rect((7,7,8,10),15)
 elif t==6:
  d.polygon([(2,8),(6,4),(11,5),(13,3),(13,12),(10,10),(6,11)],fill=5);d.polygon([(2,7),(6,4),(10,5),(12,4),(12,10),(9,9),(6,10)],fill=7);rect((5,6,5,7),15);d.point((6,6),fill=2)
 elif t==8:
  ell((2,7,13,14),3);d.polygon([(3,12),(5,7),(7,12),(9,7),(11,12)],fill=14)
 elif t==19:
  ell((4,7,11,13),13)
  for box in [(1,3,4,7),(5,1,8,5),(10,2,13,6)]:ell(box,15)
 elif t==28:rect((0,3,15,4),11);rect((0,0,15,2),15)
 elif t in (29,30):
  rect((1,5,14,14),11);rect((3,7,12,12),2)
  for x in range(1,15,3):rect((x,2,x+2,5),9 if x%2 else 15)
  rect((1,13,14,14),10)
  if t==29:d.polygon([(4,9),(7,7),(10,9),(12,7),(12,11),(10,10),(7,11)],fill=7)
 elif t==31:
  ell((2,2,9,9),10);ell((4,4,7,7),1);d.line((8,8,13,13),fill=10,width=2);rect((11,10,13,11),15)
 elif 21<=t<=26:
  ch='MIKERO'[t-21];rows=base.FONT[ch]
  for y,row in enumerate(rows):
   for x,c in enumerate(row):
    if c=='1':rect((x*2+3,y*2+1,x*2+4,y*2+2),15 if y<3 else 7 if y<5 else 10)
 if t in (3,4,5,6,7,11,12,13,14,15,19,20,29,30,31):
  original=im.copy();mask=Image.new('L',(16,16));mask.putdata([255 if v!=1 else 0 for v in im.getdata()]);edge=mask.filter(ImageFilter.MaxFilter(3))
  im.paste(2,mask=edge);im.paste(original,mask=mask)
 return im

def generate_bitmap(build):
 atlas=Image.new('P',(256,128),0)
 for t in range(32):atlas.paste(tile(t),((t%16)*16,(t//16)*16))
 for c in range(128):
  x=(c%32)*8;y=32+(c//32)*8;d=ImageDraw.Draw(atlas)
  if c in range(94,98):d.line((x,y+3,x+7,y+3),fill=5);continue
  rows=base.FONT.get(chr(c),[])
  for yy,row in enumerate(rows):
   for xx,b in enumerate(row):
    if b=='1':d.point((x+xx+1,y+yy),fill=15 if yy<3 else 14 if yy<5 else 7)
 # HUD-only 8x8 symbols and restrained frame pieces (unused lowercase slots).
 icons={112:['.##.##..','.##.##..','........','..####..','.######.','.######.','..####..','........'],113:['...##...','..####..','...##...','..####..','.######.','.######.','..####..','........'],114:['........','...###.#','..######','.#######','..######','...###.#','........','........'],115:['..####..','.######.','.##..##.','.##..##.','.######.','..####..','........','........']}
 for c,rows in icons.items():
  x=(c%32)*8;y=32+(c//32)*8;d=ImageDraw.Draw(atlas)
  for yy,row in enumerate(rows):
   for xx,v in enumerate(row):
    if v=='#':d.point((x+xx,y+yy),fill=([13,7,7,10][c-112] if yy>1 else 15))
 for c in range(116,122):
  x=(c%32)*8;y=32+(c//32)*8;d=ImageDraw.Draw(atlas)
  if c==116:d.line((x,y+4,x+7,y+4),fill=5)
  if c==117:d.line((x+1,y+7,x+1,y+4,x+7,y+4),fill=5)
  if c==118:d.line((x,y+4,x+7,y+4,x+7,y+7),fill=5)
  if c==119:d.line((x+3,y+1,x+3,y+6),fill=2)
  if c==120:d.line((x+1,y,x+1,y+7),fill=3)
  if c==121:d.line((x+7,y,x+7,y+7),fill=3)
 # Direction arrows occupy the original 0..31 character slots.
 import math
 for direction in range(8):
  im=Image.new('P',(16,16),0);d=ImageDraw.Draw(im);a=direction*math.pi/4-math.pi/2
  pts=[(8+math.cos(a)*6,8+math.sin(a)*6),(8+math.cos(a+2.5)*5,8+math.sin(a+2.5)*5),(8+math.cos(a-2.5)*5,8+math.sin(a-2.5)*5)]
  d.polygon(pts,fill=10)
  for q in range(4):c=direction*4+q;atlas.paste(im.crop(((q%2)*8,(q//2)*8,(q%2)*8+8,(q//2)*8+8)),((c%32)*8,32+(c//32)*8))
 for j,t in enumerate((11,12,13,14,15,7,3,6)):
  for f in range(4):
   im=tile(t,f)
   if f==1 and t in (11,12,14):
    shifted=Image.new('P',(16,16),1);shifted.paste(im,(0,-1));im=shifted
   if f==3 and t in (11,15):
    d=ImageDraw.Draw(im);d.line((5,10,6,10),fill=2);d.line((10,10,11,10),fill=2)
   atlas.paste(im,(((j*4+f)%16)*16,64+((j*4+f)//16)*16))
 pixels=list(atlas.getdata());packed=bytes((pixels[i]<<4)|pixels[i+1] for i in range(0,len(pixels),2))
 # Six sprite planes, four poses. Dedicated effects use plane 6/7.
 patterns=bytearray();colors=[2,5,7,9,10,15]
 for f in range(4):
  im=tile(10,f)
  for color in colors:
   patterns+=bytes(sum((im.getpixel((x+i,y))==color)<<(7-i) for i in range(8)) for x in (0,8) for y in range(16))
 patterns+=bytes(sum((tile(19).getpixel((x+i,y))!=1)<<(7-i) for i in range(8)) for x in (0,8) for y in range(16))
 patterns+=bytes(sum((2<((x+i-8)**2+(y-8)**2)<45)<<(7-i) for i in range(8)) for x in (0,8) for y in range(16))
 palette=bytearray()
 for mid,hi,shade in [((3,4,5),(5,6,7),(2,2,4)),((5,3,5),(7,5,6),(3,2,4)),((2,4,6),(4,7,7),(1,2,4)),((4,5,6),(6,7,7),(2,3,5)),((6,3,3),(7,6,4),(3,2,3)),((5,4,2),(7,6,4),(3,2,2)),((3,4,5),(6,6,7),(2,2,4)),((3,3,5),(6,5,7),(2,1,3))]:
  pal=list(PAL);pal[4]=mid;pal[6]=hi;pal[3]=shade
  palette.extend(v for r,g,b in pal for v in ((r<<4)|b,g))
 bank=packed[:12288]+patterns+palette
 assert len(bank)<=16384
 (build/'bitmap.bin').write_bytes(bank.ljust(16384,b'\xff'))
 rgb=[v*255//7 for c in PAL for v in c];atlas.putpalette(rgb+[0]*(768-len(rgb)));atlas.resize((768,384),Image.Resampling.NEAREST).save(build/'atlas-preview.png')
