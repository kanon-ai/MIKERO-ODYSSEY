from pathlib import Path
import json,hashlib
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text());checks=[]
def check(n,b,**v):
 print(n,bool(b),v,flush=True);checks.append(dict(name=n,passed=bool(b),**v));assert b,n
for std in ('ntsc','pal'):
 with OpenMSX(std,work=R/'work') as e:
  e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(5)
  def get(n,z=1):return e.read_symbol(S,n,z)
  def put(n,v,z=1):e.write_block('memory',S[n],int(v).to_bytes(z,'little'))
  def tap(mask):e.key(8,mask);e.run_for(.09);e.key(8,mask,False);e.run_for(.55)
  tap(1);e.run_for(1)
  def setup():
   m=bytearray([1]*4096)
   for y in range(3,19):
    for x in range(2,20):m[y*64+x]=0
   # Static landmarks in an open room, away from all four test destinations.
   for x,y,t in [(7,8,3),(13,8,5),(7,12,6),(13,12,4),(10,7,7)]:m[y*64+x]=t
   e.write_block('memory',S['map'],m);e.write_block('memory',S['seen'],bytes(512))
   for n,v in dict(px=10,py=10,enemy_count=0,hp=24,maxhp=24,dirty=1,mode=1,prev_input=0,repeat=0).items():put(n,v)
   put('food',400,2);e.run_for(.8)
  for dx,dy,key in [(1,0,128),(-1,0,16),(0,1,64),(0,-1,32)]:
   setup();old=e.read_block('memory',S['screen'],768);turn=get('turn_count',2);pos=get('music_pos')
   e.command('set ::flips {};set ::draw_start 0')
   a=e.command(f'debug set_bp {S["draw"]} {{}} {{set ::draw_start [machine_info time]}}')
   b=e.command(f'debug set_bp {S["regwrite"]} {{[debug read memory {S["reg_num"]}]==2}} {{lappend ::flips [list [expr {{[machine_info time]-$::draw_start}}] [binary encode hex [debug read_block VRAM [expr {{[debug read memory {S["reg_val"]}]*1024}}] 768]]]}}')
   tap(key);e.command(f'debug remove_bp {a};debug remove_bp {b}')
   rows=e.command('join $::flips ";"').split(';');frames=[];times=[]
   for row in rows:
    t,h=row.split();times.append(float(t));frames.append(bytes.fromhex(h))
   tag=f'{std}-{dx},{dy}'
   check(tag+'-two-flips-one-turn',len(frames)==2 and get('turn_count',2)==turn+1 and get('music_pos')==(pos+1)%64,times_ms=[round(t*1000,3) for t in times])
   half,final=frames
   check(tag+'-one-keeper-in-both-phases',all(all(f.count(c)==1 for c in (156,157,158,159)) for f in frames))
   check(tag+'-final-scene-upload',final==e.read_block('memory',S['screen'],768))
   check(tag+'-fixed-cat-HUD',all(half[i]==final[i] for i in list(range(96))+list(range(672,768))+[367,368,399,400]))
   errors=[]
   for y in range(3,21):
    for x in range(1,31):
     if x in (15,16) and y in (11,12):continue
     sx,sy=x-dx,y-dy
     if 1<=sx<=30 and 3<=sy<=20:
      # The destination cat replaces plain floor; its moving source must be floor.
      expected=128+((sx-1)&1)+2*((sy-3)&1) if sx in (15,16) and sy in (11,12) else final[sy*32+sx]
     else:expected=old[(y+dy)*32+x+dx]
     if half[y*32+x]!=expected:errors.append([x,y,half[y*32+x],expected])
   check(tag+'-exact-eight-pixel-phase',not errors,errors=errors[:4])
   check(tag+'-half-visible-at-least-one-frame',times[1]-times[0]>.015)
  setup();n=get('screen_count',2);t=get('turn_count',2);tap(1)
  check(std+'-wait-single-draw',get('screen_count',2)==n+1 and get('turn_count',2)==t+1)
  setup();e.write_block('memory',S['map']+10*64+11,b'\1');n=get('screen_count',2);t=get('turn_count',2);tap(128)
  check(std+'-wall-no-scroll-no-turn',get('screen_count',2)==n+1 and get('turn_count',2)==t)
  check(std+'-strict-VRAM',e.timing_violations()==0,violations=e.timing_violations())
(O/'scroll-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),checks=checks,method='Actual Z80 execution and VRAM page-flip snapshots, controlled room and real directional keys.'),indent=2))
