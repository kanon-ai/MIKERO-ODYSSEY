from pathlib import Path
import subprocess,os,json,hashlib,re,sys,shutil
from assets import generate
ROOT=Path(__file__).resolve().parent
BUILD=ROOT.parent/'build';BUILD.mkdir(parents=True,exist_ok=True)
OUT=ROOT.parent.parent/'outputs';OUT.mkdir(exist_ok=True)
if os.environ.get('SDCC_BIN'):
 binpath=Path(os.environ['SDCC_BIN'])
 os.environ['PATH']=str(binpath)+os.pathsep+os.environ['PATH']
 sdcc=binpath/('sdcc.exe' if os.name=='nt' else 'sdcc')
 asm=binpath/('sdasz80.exe' if os.name=='nt' else 'sdasz80')
else:
 sdcc=shutil.which('sdcc');asm=shutil.which('sdasz80')
 if not sdcc or not asm:raise SystemExit('Install SDCC on PATH, or set SDCC_BIN to its bin directory.')

def run(args):subprocess.run([str(a) for a in args],cwd=BUILD,check=True)
report=generate(BUILD)
run([asm,'-plosgff','crt0.rel',ROOT/'crt0.s'])
run([asm,'-plosgff','animation.rel',ROOT/'animation.s'])
run([sdcc,'-mz80','--opt-code-speed','--no-std-crt0','--code-loc','0x4100','--data-loc','0xc000','--out-fmt-ihx','-o','game.ihx','crt0.rel','animation.rel',ROOT/'game.c'])
rom=bytearray([255]*16384);high=0
for line in (BUILD/'game.ihx').read_text().splitlines():
 b=bytes.fromhex(line[1:]);count=b[0];addr=int.from_bytes(b[1:3],'big');typ=b[3]
 assert sum(b)%256==0
 if typ==0:
  assert 0x4000<=addr and addr+count<=0x8000,f'Code exceeds fixed 16K bank: {addr:04x}'
  rom[addr-0x4000:addr-0x4000+count]=b[4:4+count];high=max(high,addr+count)
symbols={name.lstrip('_'):int(addr,16) for addr,name in re.findall(r'^\s*([0-9A-Fa-f]{8})\s+(_\w+)\s',(BUILD/'game.map').read_text(),re.M)}
ram_bytes=int(re.search(r'([0-9A-Fa-f]{8})\s+l__DATA\b',(BUILD/'game.map').read_text())[1],16)
assert 0xc000+ram_bytes<=0xf000,'Game data overlaps reserved stack area'
(BUILD/'symbols.json').write_text(json.dumps(symbols,indent=2))
rom+=(BUILD/'graphics.bin').read_bytes()+(BUILD/'dungeons.bin').read_bytes()
assert len(rom)==524288
out=OUT/'MIKERO-ODYSSEY.rom'
if not out.exists() or out.read_bytes()!=rom:out.write_bytes(rom)
report.update(rom_bytes=len(rom),mapper='ASCII16',code_end=hex(high),code_used=high-0x4000,ram_start='0xc000',static_ram_bytes=ram_bytes,ram_end=hex(0xc000+ram_bytes),required_main_ram_bytes=32768,required_vram_bytes=16384,viewport_blocks=[15,9],scroll_step_pixels=16,sha256=hashlib.sha256(rom).hexdigest(),physical_hardware_tested=False)
(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
