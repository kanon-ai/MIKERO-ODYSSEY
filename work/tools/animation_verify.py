from pathlib import Path
import json,hashlib,os
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text());gfx=(R/'work/build/graphics.bin').read_bytes();checks=[]
def check(name,ok):
 assert ok,name
 checks.append(dict(name=name,passed=True))
with OpenMSX('ntsc',work=R/'work') as e:
 e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(4)
 e.command('keymatrixdown 8 1;after time 0.04 {keymatrixup 8 1}');e.run_for(1.5)
 def put(n,v):e.write_block('memory',S[n],bytes([v]))
 for theme in range(8):
  if theme:
   for n,v in dict(px=54,py=55,enemy_count=0,depth=theme,dirty=1,repeat=0,prev_input=0).items():put(n,v)
   e.write_block('memory',S['map']+55*64+55,b'\x02');e.run_for(.3)
   e.command('keymatrixdown 8 128;after time 0.04 {keymatrixup 8 128}');e.run_for(1.5)
  found=set()
  for _ in range(32):
   e.run_for(.073)
   # An arbitrary emulator stop can be midway through the IRQ upload.
   # Finish any in-flight ISR, then inspect its complete three-bank result.
   put('anim_lock',1);e.run_for(.04)
   phase=e.read_symbol(S,'anim_oldphase');found.add(phase)
   src=gfx[0x1500+theme*1024+phase*128:0x1500+theme*1024+(phase+1)*128]
   for bank in range(3):
    actual=e.read_block('VRAM',0x400+bank*2048,64)+e.read_block('VRAM',0x2400+bank*2048,64)
    check(f'theme{theme}-phase{phase}-bank{bank}-floor-wall',actual==src)
   put('anim_lock',0)
  check(f'theme{theme}-all-eight-phases',found==set(range(8)))
 check('strict-VRAM',e.timing_violations()==0)
old=(Path(os.environ.get('MIKERO_BASELINE_ROOT',R.parent/'neko-worldview'))/'work/source/animation.s').read_text();new=(R/'work/source/animation.s').read_text()
check('music-implementation-unchanged',old[old.index('_music_reset::'):old.index('_beep::')]==new[new.index('_music_reset::'):new.index('_beep::')])
(O/'animation-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),checks=checks),indent=2));print(len(checks),'checks passed')
