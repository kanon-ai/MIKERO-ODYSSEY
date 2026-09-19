from pathlib import Path
import json, hashlib
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2]
S=json.loads((R/'work/build/symbols.json').read_text())
rows=[]
for std in ('ntsc','pal'):
 with OpenMSX(std,work=R/'work') as e:
  e.load_rom(R/'outputs/MIKERO-ODYSSEY.rom','ASCII16')
  bp=e.command(f'debug set_bp {S["hardware"]} {{}} {{debug write memory 0xf3db 1; incr ::startup_hits}}')
  e.command('set ::startup_hits 0')
  e.run_for(5)
  assert int(e.command('set ::startup_hits'))==1
  assert e.read_block('memory',0xf3db,1)==b'\0'
  e.command(f'debug remove_bp {bp}')
  def tap(mask):
   e.key(8,mask);e.run_for(.09);e.key(8,mask,False);e.run_for(.6)
   assert e.read_block('memory',0xf3db,1)==b'\0'
  tap(128);tap(16);tap(1)
  e.run_for(2)
  assert e.read_symbol(S,'mode')==1
  e.command('set ::psg_writes 0')
  wp=e.command('debug set_watchpoint write_io 0xa1 {} {incr ::psg_writes}')
  before=e.read_symbol(S,'music_pos')
  tap(1)
  after=e.read_symbol(S,'music_pos')
  count=int(e.command('set ::psg_writes'))
  print(std,before,after,count,flush=True)
  assert after==(before+1)%64 and count>0
  e.command(f'debug remove_watchpoint {wp}')
  assert e.timing_violations()==0
  rows.append(dict(standard=std,forced_click_on_before_init=True,click_off_after_init_and_keys=True,music_advanced=True,psg_writes=count,vram_violations=0))
new=(R/'outputs/MIKERO-ODYSSEY.rom').read_bytes()
assert hashlib.sha256(new[16384:32768]).hexdigest()=='b8ab37cd650406d593934ede6237f8a24c7e4406945e53e9e2a6bedde7ec68f5'
assert hashlib.sha256(new[32768:]).hexdigest()=='378738b2c0612c947c6edd65e18ba7f5511f1d5c19e36479a2b8b63e17e6dec7'
report=dict(rom_sha256=hashlib.sha256(new).hexdigest(),checks=rows,graphics_and_maps_unchanged=True,blueMSX_and_physical_audio_tested=False)
(R/'outputs/keyclick-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
