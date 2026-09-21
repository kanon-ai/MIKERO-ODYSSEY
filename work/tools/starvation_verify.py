from pathlib import Path
import hashlib,json
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text());checks=[]
def check(n,b):
 print(n,bool(b),flush=True);checks.append(dict(name=n,passed=bool(b)));assert b,n
for std in ('ntsc','pal'):
 with OpenMSX(std,work=R/'work') as e:
  e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(4)
  def get(n,z=1):return e.read_symbol(S,n,z)
  def put(n,v,z=1):e.write_block('memory',S[n],int(v).to_bytes(z,'little'))
  def tile(x,y,t):e.write_block('memory',S['map']+64*y+x,bytes([t]))
  def tap(k,row=8,wait=.35):
   e.command(f'keymatrixdown {row} {k};after time 0.035 {{keymatrixup {row} {k}}}');e.run_for(wait)
  tap(1,wait=2)
  for d in (0,1,2):
   tag=f'{std}-mode{d}'
   def room():
    m=bytearray([1]*4096)
    for y in range(3,20):
     for x in range(3,20):m[y*64+x]=0
    e.write_block('memory',S['map'],m)
    for n,v in dict(difficulty=d,depth=1,depth_max=30 if d else 15,mode=1,px=10,py=10,hp=20,maxhp=24,enemy_count=0,dirty=1,prev_input=0,repeat=0,foodclock=0,hungerclock=0,rescue_pending=0,ending_pending=0,has_key=0).items():put(n,v)
    for n,v in dict(food=0,turn_count=0).items():put(n,v,2)
    e.run_for(.4)
   room()
   for i in range(19):tap(128 if i%2==0 else 16)
   check(tag+'-nineteen-steps-no-damage',get('hp')==20 and get('hungerclock')==19 and get('turn_count',2)==19)
   tap(16);check(tag+'-twentieth-step-one-damage',get('hp')==19 and get('hungerclock')==0)
   for i in range(20):tap(1)
   check(tag+'-twenty-waits-one-damage',get('hp')==18 and get('turn_count',2)==40)
   room();put('food',1,2);tap(1)
   check(tag+'-last-food-no-hunger-charge',get('food',2)==0 and get('hp')==20 and get('hungerclock')==0)
   put('hungerclock',19);tile(11,10,1);tap(128)
   check(tag+'-wall-no-hunger-tick',get('hungerclock')==19 and get('hp')==20)
   room();put('hungerclock',19);tile(11,10,6);tap(128)
   check(tag+'-fish-resets-before-damage',get('hp')==20 and get('food',2)==99 and get('hungerclock')==0)
   room();put('hungerclock',19);tile(11,10,29);put('gold',25);tap(128)
   check(tag+'-shop-resets-immediately',get('food',2)==100 and get('hungerclock')==0 and get('hp')==20 and get('gold')==0)
   room();put('hungerclock',19);put('hp',5);put('potions',1);tap(128,row=5)
   check(tag+'-healing-action-counted',get('hp')==(16 if d else 20) and get('potions')==0 and get('hungerclock')==0)
   room();put('hungerclock',19);put('enemy_count',1);put('ex',11);put('ey',10);put('eh',1);put('et',11);put('xp',0);put('attack',3);tap(128)
   check(tag+'-paw-action-counted',get('eh')==0 and get('hp')==19 and get('hungerclock')==0)
   room();put('food',100,2)
   for i in range(28 if d else 14):tap(1)
   check(tag+'-fed-regeneration-unchanged',get('hp')==21 and get('food',2)==100-(28 if d else 14) and get('hungerclock')==0)
   room();put('hp',1);put('hungerclock',18);tile(11,10,31);tap(128)
   check(tag+'-last-chance-key',get('has_key')==1 and get('hp')==1 and get('mode')==1)
   tile(12,10,2);tap(128,wait=2)
   check(tag+'-key-allows-escape-and-reset',get('depth')==2 and get('hungerclock')==0 and get('food',2)>0 and get('mode')==1)
   room();put('hp',1);put('hungerclock',19);tap(1,wait=2)
   check(tag+'-twentieth-action-still-rescues',get('hp')==0 and get('mode')==2 and get('rescue_pending')==0)
   tap(1,wait=2);check(tag+'-retry-clears-counter',get('mode')==1 and get('hungerclock')==0)
  check(std+'-vram',e.timing_violations()==0)
  check(std+'-keyboard-click-disabled',e.read_block('memory',0xf3db,1)==b'\0')
rom=(O/'MIKERO-ODYSSEY.rom').read_bytes()
assert hashlib.sha256(rom[16384:]).hexdigest()=='0b223412509f08db1eea295a50a6cbe1e890a12a9f9727ad33bc36aa741603f4'
(O/'starvation-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256(rom).hexdigest(),checks=checks,graphics_and_maps_unchanged=True,physical_hardware_tested=False),indent=2))
