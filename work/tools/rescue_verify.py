from pathlib import Path
import json,hashlib
from emulator_support import OpenMSX,tcl_word
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text());checks=[]
def check(n,b,**v):
 print(n,bool(b),v,flush=True);checks.append(dict(name=n,passed=bool(b),**v));assert b,n
for std in ('ntsc','pal'):
 with OpenMSX(std,capture=std=='ntsc',work=R/'work') as e:
  e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(5)
  def get(n,z=1):return e.read_symbol(S,n,z)
  def put(n,v,z=1):e.write_block('memory',S[n],int(v).to_bytes(z,'little'))
  def tap(key):e.command(f'keymatrixdown 8 {key};after time 0.06 {{keymatrixup 8 {key}}}');e.run_for(1.5)
  tap(1)
  for cause in ('starvation','trap','enemy'):
   m=bytearray([1]*4096)
   for y in range(5,16):
    for x in range(5,16):m[y*64+x]=0
   e.write_block('memory',S['map'],m)
   for n,v in dict(mode=1,px=10,py=10,hp=1,maxhp=24,enemy_count=0,dirty=1,prev_input=0,repeat=0,rescue_phase=0).items():put(n,v)
   put('food',0 if cause=='starvation' else 400,2);put('score',1234,2);put('high_score',0,2);e.run_for(.8)
   if cause=='trap':e.write_block('memory',S['map']+651,b'\10')
   if cause=='enemy':
    for n,v in dict(enemy_count=1,ex=11,ey=10,eh=80,et=12).items():put(n,v)
   e.command('set ::rescue_flips {}')
   bp=e.command(f'debug set_bp {S["regwrite"]} {{[debug read memory {S["reg_num"]}]==2}} {{lappend ::rescue_flips [list [machine_info time] [debug read memory {S["rescue_phase"]}] [binary encode hex [debug read_block VRAM [expr {{[debug read memory {S["reg_val"]}]*1024}}] 768]]]}}')
   key=128 if cause=='trap' else 1
   e.key(8,key);e.run_for(.25)
   if std=='ntsc' and cause=='starvation':e.screenshot(O/'rescue.png',640)
   e.run_for(1.4)
   check(std+'-'+cause+'-held-key-no-restart',get('mode')==2 and get('rescue_pending')==0 and get('rescue_phase')==3)
   e.key(8,key,False);e.run_for(.1);e.command(f'debug remove_bp {bp}')
   trace=[]
   for row in e.command('join $::rescue_flips ";"').split(';'):
    t,phase,data=row.split();trace.append((float(t),int(phase),bytes.fromhex(data)))
   rescue=[r for r in trace if r[1] in (1,2)];result=[r for r in trace if r[1]==3]
   check(std+'-'+cause+'-rescue-before-results',len(rescue)==7 and len(result)==1 and trace[0][1] in (1,2),phases=[r[1] for r in trace])
   check(std+'-'+cause+'-two-keepers-and-stretcher',all(all(r[2].count(c)==2 for c in range(156,160)) and all(r[2].count(c)==1 for c in range(236,240)) and all(r[2].count(c)==3 for c in range(240,244)) for r in rescue))
   check(std+'-'+cause+'-carrying-starts',rescue[-1][2].index(236)>rescue[0][2].index(236))
   check(std+'-'+cause+'-quiet-rescue-text',all(r[2][18*32:19*32]==b' '*32 for r in rescue))
   duration=result[0][0]-rescue[0][0]
   check(std+'-'+cause+'-brief-scene',.5<duration<1.6,seconds=duration)
   check(std+'-'+cause+'-removed-message-and-record',all(b'MIKERO IS SAFE!' not in row[2] for row in trace) and get('score',2)==1234 and get('high_score',2)==1234 and get('hp')==0)
   tap(1);check(std+'-'+cause+'-restart',get('mode')==1 and get('hp')==24 and get('high_score',2)==1234)
  check(std+'-strict-VRAM',e.timing_violations()==0)
(O/'rescue-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),checks=checks,method='Three controlled exhaustion causes, actual emulated key input, VRAM flips and native screenshot; not physical hardware.'),indent=2))
