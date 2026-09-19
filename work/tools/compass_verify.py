from pathlib import Path
import json,hashlib
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text());checks=[]
def check(n,b):
 print(n,bool(b),flush=True);checks.append(dict(name=n,passed=bool(b)));assert b,n
for std in ('ntsc','pal'):
 with OpenMSX(std,capture=std=='ntsc',work=R/'work') as e:
  e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(5)
  def put(n,v,z=1):e.write_block('memory',S[n],v.to_bytes(z,'little'))
  def get(n,z=1):return e.read_symbol(S,n,z)
  def tap(key,t=1.5):e.command(f'keymatrixdown 8 {key};after time 0.06 {{keymatrixup 8 {key}}}');e.run_for(t)
  tap(1)
  check(std+'-goal-loaded-before-discovery',get('goal_known')==1 and get('goal_x')==55 and get('goal_y')==55)
  if std=='ntsc':e.screenshot(O/'compass.png',640)
  put('enemy_count',0)
  for d,(x,y) in enumerate([(55,60),(50,60),(50,55),(50,50),(55,50),(60,50),(60,55),(60,60)]):
   put('px',x);put('py',y);put('dirty',1);t=get('turn_count',2);e.run_for(.6)
   screen=e.read_block('memory',S['screen'],768)
   check(std+'-bearing-'+str(d),[screen[i] for i in [29,30,61,62]]==list(range(d*4,d*4+4)) and get('turn_count',2)==t)
   check(std+'-keyhelp-'+str(d),b'Z:HEAL' in screen[736:])
  put('px',55);put('py',55);put('dirty',1);e.run_for(.6)
  check(std+'-at-goal-no-false-direction',e.read_block('memory',S['screen']+29,2)==b'  ')
  for floor in [2,15,30]:
   put('difficulty',int(floor==30));put('depth_max',30 if floor==30 else 15)
   put('depth',floor-1);put('px',54);put('py',55);put('enemy_count',0);e.write_block('memory',S['map']+55*64+55,bytes([2]));tap(128)
   m=e.read_block('memory',S['map'],4096)
   check(std+'-floor-'+str(floor)+'-target',get('depth')==floor and m[get('goal_y')*64+get('goal_x')]==(9 if floor in (15,30) else 2))
  check(std+'-strict-VRAM',e.timing_violations()==0)
(O/'compass-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),checks=checks),indent=2))
