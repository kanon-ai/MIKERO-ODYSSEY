from pathlib import Path
import json
from emulator_support import OpenMSX,tcl_word
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text())
with OpenMSX('ntsc',capture=True,work=R/'work') as e:
 e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(5);e.key(8,1);e.run_for(.09);e.key(8,1,False);e.run_for(2)
 m=bytearray([1]*4096)
 for y in range(5,16):
  for x in range(5,16):m[y*64+x]=0
 e.write_block('memory',S['map'],m)
 for n,v in dict(px=10,py=10,enemy_count=0,music_pos=0,dirty=1).items():e.write_block('memory',S[n],bytes([v]))
 e.run_for(1);assert e.read_block('PSG regs',8,2)==bytes(2)
 e.command('record start -audioonly '+tcl_word((O/'walking-march.wav').as_posix()))
 for i in range(19):
  k=128 if i%2==0 else 16;e.key(8,k);e.run_for(.09);e.key(8,k,False);e.run_for(.55)
  assert e.read_symbol(S,'music_pos')==(i+1)%19,(i,e.read_symbol(S,'music_pos'))
 e.run_for(.5);e.command('record stop')
 print('19 footsteps and quiet tail recorded')
