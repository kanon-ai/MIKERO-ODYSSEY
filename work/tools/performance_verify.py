from pathlib import Path
import hashlib,json,statistics,os
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];results={}
for label,root in [('baseline',Path(os.environ.get('MIKERO_BASELINE_ROOT',R.parent/'neko-worldview'))),('candidate',R)]:
 S=json.loads((root/'work/build/symbols.json').read_text());rows=[]
 for std in ('ntsc','pal'):
  with OpenMSX(std,work=R/'work') as e:
   e.load_rom(root/'outputs/MIKERO-ODYSSEY.rom','ASCII16');e.run_for(4)
   e.command('keymatrixdown 8 1;after time 0.035 {keymatrixup 8 1}');e.run_for(1.8)
   m=bytearray(4096)
   for i in range(64):m[i]=m[4032+i]=m[i*64]=m[i*64+63]=1
   e.write_block('memory',S['map'],m)
   for name,value in dict(px=5,py=30,enemy_count=0,hp=24,maxhp=24,dirty=1,prev_input=0,repeat=0).items():e.write_block('memory',S[name],bytes([value]))
   e.run_for(.6);e.command('set ::moves {};set ::irq_begin 0;set ::irq_peak 0')
   a=e.command(f'debug set_bp {S["move_player"]} {{}} {{lappend ::moves [machine_info time]}}')
   b=e.command(f'debug set_bp {S["anim_isr"]} {{}} {{set ::irq_begin [machine_info time]}}')
   c=e.command(f'debug set_bp {S["anim_done"]} {{}} {{set dt [expr {{[machine_info time]-$::irq_begin}}];if {{$dt>$::irq_peak}} {{set ::irq_peak $dt}}}}')
   e.key(8,128);e.run_for(2.4);e.key(8,128,False);e.run_for(.5)
   times=[float(t) for t in e.command('set ::moves').split()];intervals=[1000*(b-a) for a,b in zip(times,times[1:])]
   peak=float(e.command('set ::irq_peak'))*1000
   assert intervals and e.timing_violations()==0 and peak<16.68
   rows.append(dict(standard=std,moves_in_2_4_seconds=len(times),median_move_interval_ms=statistics.median(intervals),max_irq_ms=peak,strict_VRAM_violations=0))
 results[label]=dict(rom_sha256=hashlib.sha256((root/'outputs/MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),measurements=rows)
for old,new in zip(results['baseline']['measurements'],results['candidate']['measurements']):
 new['speedup']=old['median_move_interval_ms']/new['median_move_interval_ms'];assert new['speedup']>1.5
results['method']='Actual held-key movement in identical empty room; emulated elapsed time, NTSC/PAL, not host wall-clock or real hardware.'
(R/'outputs/performance-verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
