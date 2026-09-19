"""Native per-frame, keyboard-only footage at the ROM's actual NTSC speed."""
from pathlib import Path
import hashlib,json
from PIL import Image
from emulator_support import OpenMSX,tcl_word
R=Path(__file__).resolve().parents[2];O=R/'outputs';F=R/'work/media-frames';F.mkdir(exist_ok=True)
S=json.loads((R/'work/build/symbols.json').read_text());ROM=O/'MIKERO-ODYSSEY.rom'
with OpenMSX('ntsc',capture=True,work=R/'work') as e:
 e.load_rom(ROM,'ASCII16');e.run_for(5);e.screenshot(O/'title.png',640)
 e.command('keymatrixdown 8 1;after time 0.04 {keymatrixup 8 1}');e.run_for(1.5)
 e.command('set ::capture_i 0;set ::capture_on 1;set ::capture_times {};set ::capture_dir '+tcl_word(F.as_posix())+''';proc capture_gameplay {} {
  if {!$::capture_on} {return}
  openmsx::internal_screenshot -raw -size 320 [format {%s/%04d.png} $::capture_dir $::capture_i]
  lappend ::capture_times [machine_info time]
  incr ::capture_i
  after frame capture_gameplay
 };after frame capture_gameplay''')
 states=[];e.run_for(.5)
 for row,key,seconds in [(8,128,1.2),(8,32,.8),(8,16,1.2),(8,64,1.0),(8,128,1.5),(5,128,.06),(8,32,1.2),(8,16,1.5),(8,64,1.5),(8,128,1.5)]:
  e.key(row,key);e.run_for(seconds);e.key(row,key,False);e.run_for(.2)
  state={n:e.read_symbol(S,n,2 if n in ('turn_count','score') else 1) for n in ('px','py','hp','depth','mode','turn_count','score')}
  assert state['mode']==1,state
  states.append(dict(row=row,key=key,held_seconds=seconds,**state))
 e.run_for(.5);e.command('set ::capture_on 0')
 times=[float(t) for t in e.command('set ::capture_times').split()]
 assert e.timing_violations()==0
images=[Image.open(F/f'{i:04d}.png').convert('RGB') for i in range(len(times))]
colors=set()
for im in images:colors.update(im.getdata())
assert len(colors)<=256
pal=Image.new('P',(1,1));entries=[v for c in sorted(colors) for v in c];pal.putpalette(entries+[0]*(768-len(entries)))
frames=[im.quantize(palette=pal,dither=Image.Dither.NONE).resize((640,480),Image.Resampling.NEAREST) for im in images]
step=(times[-1]-times[0])/(len(times)-1)
edges=[round((t-times[0])*100)*10 for t in times]+[round((times[-1]+step-times[0])*100)*10]
durations=[b-a for a,b in zip(edges,edges[1:])]
assert min(durations)>=10
frames[0].save(O/'gameplay.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=1)
with Image.open(O/'gameplay.gif') as gif:
 total=0
 for i in range(gif.n_frames):gif.seek(i);gif.load();total+=gif.info['duration']
 assert total==sum(durations)
 report=dict(rom_sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),source_frames=len(times),gif_frames=gif.n_frames,duration_ms=total,emulated_duration_ms=(times[-1]+step-times[0])*1000,speed_multiplier=1,gameplay_ram_writes=0,strict_VRAM_violations=0,method='Native NTSC frame capture, real keyboard holds, actual emulated timestamps rounded to GIF 10ms units, exact palette and nearest-neighbor 2x.',actions=states)
(O/'media-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
