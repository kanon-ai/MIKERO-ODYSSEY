"""Identical seeded RAM scenes in published and candidate ROMs, including map edges."""
from pathlib import Path
import hashlib,json,random,statistics,os
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];BASE=Path(os.environ.get('MIKERO_BASELINE_ROOT',R.parent/'neko-worldview'));results={};all_scenes={}
for label,root in [('baseline',BASE),('candidate',R)]:
 S=json.loads((root/'work/build/symbols.json').read_text());rom=root/'outputs/MIKERO-ODYSSEY.rom'
 times=[];scenes=[]
 for standard in ('ntsc','pal'):
  with OpenMSX(standard,work=R/'work') as e:
   e.load_rom(rom,'ASCII16');e.run_for(4)
   e.command('keymatrixdown 8 1;after time 0.04 {keymatrixup 8 1}');e.run_for(1.5)
   def put(n,v,z=1):e.write_block('memory',S[n],v.to_bytes(z,'little'))
   a=e.command(f'debug set_bp {S["draw"]} {{}} {{set ::draw_begin [machine_info time]}}')
   b=e.command(f'debug set_bp {S["regwrite"]} {{[debug read memory {S["reg_num"]}]==2}} {{lappend ::draw_times [expr {{[machine_info time]-$::draw_begin}}]}}')
   for case in range(24):
    rnd=random.Random(case+813);m=bytearray(rnd.choice([0,0,0,0,1,1,3,4,5,6,7,8,9]) for _ in range(4096))
    px,py=([(1,1),(62,1),(1,62),(62,62)][case] if case<4 else (rnd.randrange(4,60),rnd.randrange(4,60)))
    m[py*64+px]=0
    e.write_block('memory',S['map'],m);e.write_block('memory',S['seen'],bytes(rnd.randrange(256) for _ in range(512)))
    for n,v in dict(mode=1,px=px,py=py,hp=24,maxhp=24,enemy_count=0,depth=1,level=1,gold=0,potions=3,scroll_dx=0,scroll_dy=0,dirty=0).items():put(n,v)
    put('food',400,2);e.command('set ::draw_times {}');put('dirty',1);e.run_for(.7)
    times.append(float(e.command('lindex $::draw_times end'))*1000)
    # Viewport only: HUD can intentionally change in later difficulty builds.
    screen=e.read_block('memory',S['screen'],768)
    scenes.append(screen[96:672]+e.read_block('memory',S['seen'],512)+e.read_block('memory',S['sight'],135))
   e.command(f'debug remove_bp {a};debug remove_bp {b}')
   assert e.timing_violations()==0
 results[label]=dict(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),median_draw_ms=statistics.median(times),max_draw_ms=max(times))
 all_scenes[label]=scenes
assert all_scenes['baseline']==all_scenes['candidate'],'Renderer/visibility/exploration changed'
results.update(identical_scenes=48,viewport_seen_sight_identical=True,speedup=results['baseline']['median_draw_ms']/results['candidate']['median_draw_ms'])
(R/'outputs/render-comparison.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
