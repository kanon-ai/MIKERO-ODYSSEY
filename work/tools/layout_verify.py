"""Run the cartridge's floor loader for all 120 variants in both modes."""
from pathlib import Path
import hashlib,json,os
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text());maps=(R/'work/build/dungeons.bin').read_bytes();checks=[]
with OpenMSX('ntsc',work=R/'work') as e:
 e.load_rom(O/'MIKERO-ODYSSEY.rom','ASCII16');e.run_for(4)
 e.command('keymatrixdown 8 1;after time 0.04 {keymatrixup 8 1}');e.run_for(1.5)
 def put(n,v):e.write_block('memory',S[n],bytes([v]))
 normal_maps={}
 for difficulty in (0,1,2):
  for variant in range(120):
   for n,v in dict(mode=1,difficulty=difficulty,has_key=1,depth_max=30 if difficulty else 15,depth=0,seed=(variant-13)%120,px=10,py=10,enemy_count=0,hp=24,maxhp=24,repeat=0,prev_input=0).items():put(n,v)
   e.write_block('memory',S['map']+10*64+11,b'\x02')
   e.run_for(.25)
   e.command('keymatrixdown 8 128;after time 0.04 {keymatrixup 8 128}');e.run_for(1.5)
   actual=e.read_block('memory',S['map'],4096);original=maps[variant*4096:(variant+1)*4096]
   assert e.read_symbol(S,'variant')==variant,(difficulty,variant,{n:e.read_symbol(S,n) for n in ('variant','depth','mode','px','py','seed')})
   counts={t:actual.count(t) for t in (3,4,5,6,7,29)}
   assert counts==({3:4,4:19,5:1,6:4,7:1,29:1} if difficulty else {3:6,4:19,5:3,6:15,7:1,29:1}),counts
   assert actual[200]==29 and original[200]==0
   if difficulty<2:
    assert all(a==b or (n==200 and a==0 and b==29) or (a in (3,5,6) and b==0) or (32<=a<=36 and b==0) or (a==9 and b==2) for n,(a,b) in enumerate(zip(original,actual)))
   if difficulty==1:normal_maps[variant]=(actual,e.read_block('memory',S['eh'],20))
   if difficulty==2:
    normal,health=normal_maps[variant]
    assert sum(a!=b for a,b in zip(normal,actual))==1
    assert all(a==b or (a==0 and b==31) for a,b in zip(normal,actual))
    assert health==e.read_block('memory',S['eh'],20)
    assert actual.count(31)==1 and e.read_symbol(S,'has_key')==0
   visited={325};queue=[325]
   for p in queue:
    for n in (p-64,p+64,p-1,p+1):
     if 0<=n<4096 and actual[n] not in (1,7,29) and n not in visited:visited.add(n);queue.append(n)
   assert 55*64+55 in visited and 199 in visited and 451 in visited
   if difficulty==2:assert actual.index(31) in visited
   assert actual[259]==3 and actual[199]==5 and actual[451]==6
   checks.append(dict(name=f'mode{difficulty}-variant{variant}-supplies-and-terrain',passed=True))
  print('mode',difficulty,'all 120 layouts passed',flush=True)
 assert e.timing_violations()==0
assert hashlib.sha256((R/'work/source/animation.s').read_text().encode()).hexdigest()=='7aee6d3648da1562638ea67f4282c3e718c62431e9fd36264ff2a6af441c9ad0'
(O/'layout-verification.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((O/'MIKERO-ODYSSEY.rom').read_bytes()).hexdigest(),checks=checks,music_code_and_tables_unchanged=True,strict_VRAM_violations=0),indent=2))
