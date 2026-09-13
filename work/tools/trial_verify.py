from pathlib import Path
import json,hashlib,wave
from emulator_support import OpenMSX,tcl_word
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs';ROM=OUT/'MIKERO-ODYSSEY.rom';S=json.loads((ROOT/'work/build/symbols.json').read_text())
r={'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'checks':[],'method':'Controlled RAM fixtures, real keyboard actions and PSG register reads; not an input-only campaign.'}
def check(n,b,**kw):
 print(n,bool(b),kw,flush=True);r['checks'].append(dict(name=n,passed=bool(b),**kw));assert b,n
for std in ('ntsc','pal'):
 with OpenMSX(std,capture=True,work=ROOT/'work') as e:
  e.load_rom(ROM,'ASCII16');e.run_for(5)
  get=lambda n,z=1:e.read_symbol(S,n,z)
  def put(n,v,z=1):e.write_block('memory',S[n],int(v).to_bytes(z,'little'))
  def key(mask):e.key(8,mask);e.run_for(.09);e.key(8,mask,False);e.run_for(.04)
  key(1);e.run_for(1.5)
  def setup():
   m=bytearray([1]*4096)
   for y in range(5,16):
    for x in range(5,16):m[y*64+x]=0
   e.write_block('memory',S['map'],m);e.write_block('memory',S['seen'],bytes(512))
   for n,v in dict(mode=1,px=10,py=10,enemy_count=0,hp=20,maxhp=24,prev_input=0,repeat=0,dirty=1,music_pos=0,music_age=0,music_volume=0).items():put(n,v)
   put('food',400,2);e.run_for(.8)
  def tile(x,y,t):e.write_block('memory',S['map']+y*64+x,bytes([t]))
  setup();check(std+'-idle-silent',get('music_pos')==0 and e.read_block('PSG regs',9,1)==b'\0')
  key(128);check(std+'-one-step-one-note',get('px')==11 and get('music_pos')==1,x=get('px'),pos=get('music_pos'),mode=get('mode'))
  regs=e.read_block('PSG regs',0,16);check(std+'-D5-tone-and-low-volume',(regs[2]|regs[3]<<8)==191 and 0<regs[9]<=6 and regs[7]&2==0)
  e.run_for(.4);check(std+'-stop-decays-to-silence',get('music_age')==0 and e.read_block('PSG regs',9,1)==b'\0')
  tile(12,10,1);key(128);check(std+'-wall-no-music-step',get('music_pos')==1)
  key(1);check(std+'-wait-no-music-step',get('music_pos')==1)
  tile(12,10,0)
  for n,v in dict(enemy_count=1,ex=12,ey=10,eh=80,et=11).items():put(n,v)
  key(128);check(std+'-attack-no-music-step',get('music_pos')==1)
  setup();tile(11,10,4);key(128);check(std+'-pickup-effect-coexists',get('music_pos')==1 and get('effect_age')>0 and get('music_volume')<=6,pos=get('music_pos'),age=get('effect_age'),x=get('px'))
  setup();put('music_pos',18);key(128);check(std+'-melody-loops',get('music_pos')==0)
  setup();put('score',1000,2);put('high_score',500,2);put('depth',12);put('hp',1);put('food',0,2);key(1);e.run_for(.3)
  check(std+'-loss-records-score-floor',get('mode')==2 and get('high_score',2)==1000 and get('record_floor')==12)
  e.screenshot(OUT/f'trial-result-{std}.png',640)
  key(1);e.run_for(1.4);check(std+'-restart-keeps-record',get('mode')==1 and get('score',2)==0 and get('high_score',2)==1000 and get('record_floor')==12 and get('music_pos')==0)
  setup();put('score',999,2);put('depth',20);put('hp',1);put('food',0,2);key(1);e.run_for(.2);check(std+'-lower-score-keeps-best',get('high_score',2)==1000 and get('record_floor')==12)
  setup();put('score',1000,2);put('depth',20);put('hp',1);put('food',0,2);key(1);e.run_for(.2);check(std+'-tie-prefers-deeper',get('record_floor')==20)
  setup();put('score',65520,2);tile(11,10,4);key(128);check(std+'-score-saturates',get('score',2)==65535)
  setup();put('depth',30);put('score',1234,2);tile(11,10,9);key(128);e.run_for(.3);check(std+'-30-floor-finish-bonus',get('mode')==3 and get('score',2)==4234)
  e.screenshot(OUT/f'trial-clear-{std}.png',640)
  check(std+'-strict-VRAM',e.timing_violations()==0)
(OUT/'trial-verification.json').write_text(json.dumps(r,indent=2))
