"""SCREEN 5 title only: existing character faces, new illustrated composition."""
from PIL import Image,ImageDraw,ImageFilter
from bitmap_assets import PAL,tile
from base_assets import FONT

def make_title(build):
 im=Image.new('P',(256,192),2);d=ImageDraw.Draw(im)
 # Quiet framed cover, without flicker or a patterned floor.
 d.rounded_rectangle((8,7,247,134),radius=10,fill=3)
 d.rounded_rectangle((10,9,245,132),radius=9,fill=2)
 def lettering(text,y,scale,color):
  width=(len(text)*6-1)*scale;x=(256-width)//2
  for i,c in enumerate(text):
   for yy,row in enumerate(FONT[c]):
    for xx,v in enumerate(row):
     if v=='1':
      box=(x+(i*6+xx)*scale,y+yy*scale,x+(i*6+xx+1)*scale-1,y+(yy+1)*scale-1)
      d.rectangle((box[0]+1,box[1]+2,box[2]+1,box[3]+2),fill=3)
      d.rectangle(box,fill=color if yy<4 else 14)
 lettering('MIKERO',16,3,15)
 lettering('ODYSSEY',42,2,10)
 # A welcoming gate, a low garden terrace, and familiar companions.
 d.rounded_rectangle((35,64,84,124),radius=23,fill=4)
 d.rounded_rectangle((40,69,79,130),radius=19,fill=6)
 d.rounded_rectangle((44,74,75,128),radius=15,fill=12)
 d.rounded_rectangle((48,78,71,128),radius=11,fill=13)
 d.rectangle((34,119,222,132),fill=5)
 d.line((35,119,220,119),fill=6)
 d.rectangle((0,138,255,191),fill=0)
 def actor(t,x,y,scale):
  a=tile(t).resize((16*scale,16*scale),Image.Resampling.NEAREST)
  mask=Image.new('L',a.size);mask.putdata([255 if p!=1 else 0 for p in a.getdata()]);im.paste(a,(x,y),mask)
 actor(10,100,74,3)
 actor(7,173,92,2)
 actor(11,58,102,1)
 # Two quiet leaves echo the cape, without a field of sparkling dots.
 d.ellipse((25,110,38,120),fill=5);d.ellipse((215,108,230,120),fill=5)
 pixels=list(im.getdata());raw=bytes((pixels[i]<<4)|pixels[i+1] for i in range(0,len(pixels),2))
 # PackBits: 0..127 literals (n+1), 128..255 repeats (n-125).
 packed=bytearray();previous=None
 for y in range(192):
  row=raw[y*128:(y+1)*128]
  if row==previous:packed.append(0);continue
  prev=previous;previous=row;packed.append(1);i=0
  while i<128:
   same=0
   while prev is not None and i+same<128 and row[i+same]==prev[i+same]:same+=1
   if same>=3:packed.extend((254,same));i+=same;continue
   run=1
   while i+run<128 and row[i+run]==row[i] and run<128:run+=1
   if run>=3:packed.extend((run+125,row[i]));i+=run;continue
   start=i;i+=run
   while i<128 and i-start<128:
    if i+2<128 and row[i]==row[i+1]==row[i+2]:break
    if prev is not None and i+2<128 and row[i:i+3]==prev[i:i+3]:break
    i+=1
   packed.append(i-start-1);packed.extend(row[start:i])
 assert len(packed)<=0x4000-0x3440, f'Title exceeds reserved graphics-bank space: {len(packed)}'
 bank=bytearray((build/'bitmap.bin').read_bytes());bank[0x3440:0x3440+len(packed)]=packed;(build/'bitmap.bin').write_bytes(bank)
 rgb=[v*255//7 for c in PAL for v in c];im.putpalette(rgb+[0]*(768-len(rgb)));im.resize((768,576),Image.Resampling.NEAREST).save(build/'title-art.png')
 print('Title packed bytes:',len(packed))
