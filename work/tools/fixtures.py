"""Focused emulator scenarios using explicitly injected RAM fixtures.
These tests do not stand in for the separate input-only campaign.
"""
from pathlib import Path
import json,hashlib
from emulator_support import OpenMSX
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs'
S=json.loads((ROOT/'work/build/symbols.json').read_text());ROM=OUT/'MIKERO-ODYSSEY.rom'
checks=[]
def check(n,b,**d):
 print(n,bool(b),d,flush=True);checks.append(dict(name=n,passed=bool(b),**d));assert b,n
with OpenMSX('ntsc',work=ROOT/'work') as e:
 e.load_rom(ROM,'ASCII16');e.run_for(5)
 def get(n,size=1):return e.read_symbol(S,n,size)
 def setv(n,v,size=1):e.write_block('memory',S[n],v.to_bytes(size,'little'))
 def tap(row,mask):
  e.command(f'keymatrixdown {row} {mask};after time 0.05 {{keymatrixup {row} {mask}}}');e.run_for(.7)
 tap(8,1);e.run_for(1)
 def setup():
  m=bytearray([1]*4096)
  for y in range(6,15):
   for x in range(6,15):m[y*64+x]=0
  e.write_block('memory',S['map'],m);e.write_block('memory',S['seen'],bytes(512))
  for n,v in {'mode':1,'px':10,'py':10,'hp':20,'maxhp':24,'level':1,'xp':0,'attack':3,'potions':3,'gold':10,'enemy_count':0,'foodclock':0,'turns':0,'prev_input':0,'repeat':0,'dirty':1}.items():setv(n,v)
  setv('food',200,2);setv('turn_count',0,2);e.run_for(.7)
 def tile(x,y,t):e.write_block('memory',S['map']+y*64+x,bytes([t]))
 setup();tile(11,10,5);tap(8,128)
 check('chest-gold-potion-consumed',get('gold')==20 and get('potions')==4 and e.read_block('memory',S['map']+10*64+11,1)==b'\0')
 setup();tile(11,10,6);tap(8,128);check('ration-restores-food',get('food',2)==299)
 setup();tile(11,10,7);setv('hp',5);tap(8,128);check('keeper-heals-for-five-gold',get('hp')==24 and get('gold')==5 and get('px')==10)
 setup();tile(11,10,7);setv('gold',4);setv('hp',5);tap(8,128);check('keeper-insufficient-gold',get('hp')==5 and get('gold')==4)
 setup();tile(11,10,8);tap(8,128);check('spikes-damage-and-remove',get('hp')==17 and e.read_block('memory',S['map']+10*64+11,1)==b'\0')
 setup();setv('hp',5);tap(5,128);check('Z-potion-heals-and-costs-turn',get('hp')==21 and get('potions')==2 and get('turn_count',2)==1)
 setup();setv('hp',5);setv('potions',0);tap(5,128);check('no-potion-no-turn',get('hp')==5 and get('turn_count',2)==0)
 setup();tile(11,10,1);tile(12,10,3);e.write_block('memory',S['seen'],bytes(512));setv('dirty',1);e.run_for(.7)
 sc=e.read_block('memory',S['screen'],768)
 check('wall-occludes-items',sc[11*32+17]==132 and sc[11*32+19]==192)
 setup();setv('depth',30);tile(11,10,9);setv('enemy_count',1);setv('ex',12);setv('ey',10);setv('eh',24);setv('et',15)
 tap(8,128);check('crown-locked-by-warden',get('mode')==1)
 setv('attack',30);tap(8,128);check('warden-defeated',get('eh')==0)
 tap(8,16);tap(8,128);check('crown-victory-after-warden',get('mode')==3)
 setup();setv('hp',1);setv('food',0,2);tap(8,1);e.run_for(1.2);check('starvation-game-over',get('mode')==2 and get('hp')==0)
 tap(8,1);e.run_for(1);check('space-restart-after-death',get('mode')==1 and get('depth')==1 and get('hp')==24)
 check('strict-VRAM-timing-fixtures',e.timing_violations()==0,violations=e.timing_violations())
(OUT/'verification-fixtures.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'method':'Injected RAM fixtures; actual Z80/VDP execution and keyboard actions','checks':checks},indent=2)+'\n')
