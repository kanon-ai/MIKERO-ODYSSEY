"""Verify existing openMSX save/resume, without adding cartridge save hardware."""
from pathlib import Path
import json,hashlib
from emulator_support import OpenMSX,tcl_word
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text())
names=('mode','difficulty','depth','px','py','hp','potions','gold','level')
def state(e):return {n:e.read_symbol(S,n) for n in names}
with OpenMSX('ntsc',work=R/'work') as e:
 e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(4)
 e.command('keymatrixdown 8 1;after time 0.04 {keymatrixup 8 1}');e.run_for(1.5)
 bindings=e.command('bind');assert 'F8+ALT:  savestate' in bindings and 'F7+ALT:  loadstate' in bindings
 before=state(e);saved=Path(e.command('savestate mikero-v1.6-verification'))
 assert saved.is_file()
 e.command('keymatrixdown 8 128;after time 0.5 {keymatrixup 8 128}');e.run_for(.9)
 assert state(e)['px']!=before['px']
 e.command('loadstate mikero-v1.6-verification');assert state(e)==before
with OpenMSX('ntsc',work=R/'work') as e:
 e.command('set restored [restore_machine '+tcl_word(saved.as_posix())+'];activate_machine $restored')
 assert state(e)==before
report=dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),save_binding='ALT+F8',load_binding='ALT+F7',same_process_restore=True,new_process_restore=True,rom_native_save=False,save_files_distributed=False)
(O/'save-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
