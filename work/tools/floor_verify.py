from pathlib import Path
import json,hashlib
from emulator_support import OpenMSX
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs';ROM=OUT/'MIKERO-ODYSSEY.rom';S=json.loads((ROOT/'work/build/symbols.json').read_text());checks=[]
with OpenMSX('ntsc',capture=True,work=ROOT/'work') as e:
 e.load_rom(ROM,'ASCII16');e.run_for(5)
 def put(n,v):e.write_block('memory',S[n],bytes([v]))
 def get(n,z=1):return e.read_symbol(S,n,z)
 def tap(mask):e.key(8,mask);e.run_for(.09);e.key(8,mask,False);e.run_for(1.2)
 tap(1)
 for floor in range(1,31):
  assert get('depth')==floor and get('anim_theme')==(floor-1)%8
  assert e.read_block('physical VRAM',0x400,32)==bytes(32)
  assert e.read_block('memory',S['map']+55*64+55,1)==bytes([9 if floor==30 else 2])
  types=e.read_block('memory',S['et'],get('enemy_count'))
  assert (15 in types)==(floor==30)
  checks.append({'floor':floor,'theme':get('anim_theme'),'passed':True})
  if floor in (9,16,24,30):e.screenshot(OUT/f'trial-floor-{floor}.png',640)
  if floor<30:
   x=get('px');y=get('py');put('enemy_count',0);e.write_block('memory',S['map']+y*64+x+1,b'\x02');tap(128)
 assert get('score',2)==5800
 assert e.timing_violations()==0
(OUT/'floor-transition-verification.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'method':'Injected adjacent stairs; tests every real load_floor transition 1 through 30, separate from input-only campaign.','checks':checks,'arrival_score':5800,'strict_vram_violations':0},indent=2));print('All 30 floor transitions, theme bounds, final crown, boss placement, arrival score passed')
