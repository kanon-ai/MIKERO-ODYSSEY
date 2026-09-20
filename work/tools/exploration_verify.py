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
  def at(x,y):return e.read_block('memory',S['map']+64*y+x,1)[0]
  def tap(k,row=8,wait=.5):
   e.command(f'keymatrixdown {row} {k};after time 0.035 {{keymatrixup {row} {k}}}');e.run_for(wait)
  tap(128);tap(1,wait=2)
  if std=='ntsc':e.screenshot(O/'shop-entrance.png',640)
  check(std+'-entrance-shop',at(8,3)==29 and get('explored',2)==0)
  # Test both modes with identical controlled room fixtures and actual key input.
  for mode in (0,1,2):
   def room():
    m=bytearray([1]*4096)
    for y in range(1,20):
     for x in range(1,20):m[y*64+x]=0
    e.write_block('memory',S['map'],m)
    e.write_block('memory',S['walked'],bytes(512))
    for n,v in dict(difficulty=mode,px=10,py=10,mode=1,hp=20,maxhp=24,enemy_count=0,dirty=1,prev_input=0,repeat=0,foodclock=0,rescue_pending=0,ending_pending=0).items():put(n,v)
    for n,v in dict(score=0,explored=0,food=400,turn_count=0).items():put(n,v,2)
    e.write_block('memory',S['walked']+(650>>3),bytes([1<<(650&7)]));e.run_for(.5)
   tag=f'{std}-mode{mode}'
   room();tap(128)
   check(tag+'-new-step-score-and-food',get('score',2)==1 and get('explored',2)==1 and get('food',2)==399)
   tap(16);tap(128)
   check(tag+'-no-revisit-farming',get('score',2)==1 and get('explored',2)==1 and get('food',2)==397)
   tap(1);tile(12,10,1);tap(128)
   check(tag+'-wait-wall-no-exploration',get('score',2)==1 and get('turn_count',2)==4)
   room();tile(11,10,4);tap(128)
   check(tag+'-gold-plus-exploration',get('score',2)==26 and get('explored',2)==1)
   room();tile(11,10,29);put('gold',24);tap(128)
   check(tag+'-cannot-buy-with-24',get('gold')==24 and get('food',2)==400 and at(11,10)==29 and get('turn_count',2)==0)
   put('gold',25);put('food',900,2);tap(128)
   check(tag+'-no-wasted-purchase-near-cap',get('gold')==25 and at(11,10)==29 and get('food',2)==900)
   put('food',899,2);tap(128)
   check(tag+'-buy-once-at-price',get('gold')==0 and get('food',2)==999 and at(11,10)==30 and get('px')==10 and get('score',2)==0 and get('hp')==20)
   put('gold',250);put('food',400,2);e.key(8,128);e.run_for(2);e.key(8,128,False);e.run_for(.5)
   check(tag+'-held-input-cannot-restock',get('gold')==250 and get('food',2)==400 and at(11,10)==30 and get('turn_count',2)==0)
   tap(16);tap(128);tap(128)
   check(tag+'-return-cannot-restock',at(11,10)==30 and get('gold')==250 and get('food',2)==398)
   # Enemy cannot enter or consume the shop, in either state.
   for t in (29,30):
    room();tile(9,10,t);put('enemy_count',1);put('ex',8);put('ey',10);put('eh',10);put('et',12);tap(1)
    check(tag+f'-shop{t}-blocks-enemy',get('ex')==8 and get('ey')==10 and at(9,10)==t)
   room();tile(11,10,2);put('has_key',1);put('depth',1);put('depth_max',30 if mode else 15);tap(128,wait=2)
   w=e.read_block('memory',S['walked'],512)
   check(tag+'-next-floor-reset',get('depth')==2 and at(8,3)==29 and sum(b.bit_count() for b in w)==1 and get('explored',2)==1 and get('score',2)==201)
   # Entry point is pre-marked; exploring two new cells gives two points.
   put('enemy_count',0);tap(16);tap(128)
   check(tag+'-entry-not-farmable',get('explored',2)==2 and get('score',2)==202)
   put('hp',1);put('food',0,2);put('explored',1234,2);tap(1,wait=2.5)
   scr=e.read_block('memory',S['screen'],768)
   check(tag+'-results-exploration-count',scr[16*32+5:16*32+13]==b'EXPLORED' and scr[16*32+17:16*32+22]==b'01234')
   tap(1,wait=2)
   check(tag+'-retry-clears-exploration',get('mode')==1 and get('score',2)==0 and get('explored',2)==0 and at(8,3)==29)
  check(std+'-keyclick-off',e.read_block('memory',0xf3db,1)==b'\0')
  check(std+'-strict-vram',e.timing_violations()==0)
 # Audio and scroll code is exactly the known-good implementation.
assert hashlib.sha256((R/'work/source/animation.s').read_text().encode()).hexdigest()=='7aee6d3648da1562638ea67f4282c3e718c62431e9fd36264ff2a6af441c9ad0'
(O/'exploration-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),checks=checks,audio_and_scroll_assembly_unchanged=True,method='NTSC/PAL actual Z80 execution with controlled RAM fixtures and real keys; physical hardware untested.'),indent=2))
