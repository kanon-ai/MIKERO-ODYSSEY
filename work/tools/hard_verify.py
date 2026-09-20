from pathlib import Path
import json,hashlib
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text());checks=[]
def check(n,b):
 print(n,bool(b),flush=True);checks.append(dict(name=n,passed=bool(b)));assert b,n
for std in ('ntsc','pal'):
 with OpenMSX(std,capture=std=='ntsc',work=R/'work') as e:
  e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(4)
  def get(n,z=1):return e.read_symbol(S,n,z)
  def put(n,v,z=1):e.write_block('memory',S[n],int(v).to_bytes(z,'little'))
  def tile(x,y,t):e.write_block('memory',S['map']+64*y+x,bytes([t]))
  def tap(k,row=8,wait=.5):
   e.command(f'keymatrixdown {row} {k};after time 0.035 {{keymatrixup {row} {k}}}');e.run_for(wait)
  for key,expected in ((16,2),(128,0),(128,1),(128,2),(128,0),(16,2)):
   tap(key);check(std+f'-menu-{key}-{expected}',get('difficulty')==expected)
  if std=='ntsc':e.screenshot(O/'title-hard.png',640)
  tap(1,wait=2)
  check(std+'-hard-normal-start',get('depth_max')==30 and get('potions')==2 and get('potion_limit')==5 and get('food',2)==300 and get('hp')==24)
  check(std+'-one-key',e.read_block('memory',S['map'],4096).count(31)==1 and get('has_key')==0)
  def room():
   m=bytearray([1]*4096)
   for y in range(1,20):
    for x in range(1,20):m[y*64+x]=0
   e.write_block('memory',S['map'],m)
   e.write_block('memory',S['walked'],bytes(512))
   for n,v in dict(difficulty=2,depth=1,depth_max=30,mode=1,px=10,py=10,hp=24,maxhp=24,has_key=0,enemy_count=0,dirty=1,prev_input=0,repeat=0,foodclock=0,rescue_pending=0,ending_pending=0).items():put(n,v)
   for n,v in dict(score=0,explored=0,food=400,turn_count=0).items():put(n,v,2)
   e.run_for(.5)
  room();tile(11,10,2);tap(128)
  check(std+'-locked-stairs-cost-normal-turn',get('depth')==1 and get('px')==11 and get('food',2)==399 and get('score',2)==1)
  tile(12,10,31);tap(128)
  check(std+'-automatic-key-pickup',get('has_key')==1 and get('food',2)==398 and e.read_block('memory',S['map']+652,1)==b'\0')
  scr=e.read_block('memory',S['screen'],768)
  check(std+'-key-hud',scr[6:9]==b'KEY')
  if std=='ntsc':e.screenshot(O/'hard-key-found.png',640)
  tap(16,wait=2)
  check(std+'-key-used-new-floor',get('depth')==2 and get('has_key')==0 and get('score',2)==202 and e.read_block('memory',S['map'],4096).count(31)==1)
  room();put('depth',30);tile(11,10,9);tap(128)
  check(std+'-final-gate-locked',get('mode')==1 and get('ending_pending')==0)
  put('has_key',1);put('enemy_count',1);put('ex',18);put('ey',18);put('eh',96);put('et',15);tap(16);tap(128)
  check(std+'-key-does-not-bypass-king',get('mode')==1)
  put('eh',0);tap(16);tap(128,wait=5)
  check(std+'-key-and-king-allow-ending',get('mode')==3 and get('ending_pending')==0)
  # Real defeat updates exactly one difficulty's record and retry restores it.
  for d in (0,1,2):
   room();put('difficulty',d);put('hp',1);put('food',0,2);put('score',111*(d+1),2);put('high_score',0,2);tap(1,wait=2.5)
   check(std+f'-record-{d}',int.from_bytes(e.read_block('memory',S['best_score']+2*d,2),'little')==111*(d+1))
   tap(1,wait=2);check(std+f'-record-retry-{d}',get('high_score',2)==111*(d+1) and get('has_key')==0)
  check(std+'-separate-records',e.read_block('memory',S['best_score'],6)==b'o\0\xde\0M\1')
  check(std+'-vram',e.timing_violations()==0)
(O/'hard-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),checks=checks,method='NTSC/PAL native execution, controlled fixtures and real input; no physical hardware claim.'),indent=2))
