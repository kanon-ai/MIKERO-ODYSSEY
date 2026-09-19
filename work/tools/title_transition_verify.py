from pathlib import Path
import json
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];S=json.loads((R/'work/build/symbols.json').read_text());O=R/'outputs'
with OpenMSX('ntsc',capture=True,work=R/'work') as e:
 e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(4)
 def put(n,v):e.write_block('memory',S[n],bytes([v]))
 def tap(k,row=8):e.command(f'keymatrixdown {row} {k};after time 0.035 {{keymatrixup {row} {k}}}');e.run_for(.8)
 tap(1);e.run_for(1)
 put('enemy_count',0);put('px',54);put('py',55);put('depth',15);e.write_block('memory',S['map']+55*64+55,b'\x09');tap(128);e.run_for(3)
 tap(32,5);tap(128);e.run_for(1)
 screen=e.read_block('memory',S['screen'],768);reg=e.read_block('VDP regs',0,8)
 name=e.read_block('VRAM',reg[2]*1024,768)
 print('Names equal',screen==name,'regs',reg.hex(),flush=True)
 assert screen==name
 gfx=(R/'work/build/graphics.bin').read_bytes()
 for bank in range(3):
  data=e.read_block('VRAM',bank*2048,2048)
  bad=[ch for ch in range(32,128) if data[ch*8:ch*8+8]!=gfx[ch*8:ch*8+8]]
  print('font bank',bank,'bad',bad,flush=True);assert not bad
 e.screenshot(O/'title-normal-stable.png',640)
