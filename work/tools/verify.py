"""Native ROM validation. Campaign uses keyboard input and read-only observation.
Focused edge-case tests are separately identified as injected fixtures.
"""
from pathlib import Path
import json,hashlib,heapq,sys,time
from emulator_support import OpenMSX
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs'
S=json.loads((ROOT/'work/build/symbols.json').read_text())
ROM=OUT/'MIKERO-ODYSSEY.rom'
report={'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'checks':[],'physical_hardware_tested':False}
def check(name,ok,**extra):
 report['checks'].append(dict(name=name,passed=bool(ok),**extra));print(name,bool(ok),extra,flush=True)
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 assert ok,name
def snap(e):
 raw=e.read_block('memory',0xc000,0x1700)
 get=lambda n:raw[S[n]-0xc000]
 s={n:get(n) for n in ('mode','depth','px','py','hp','maxhp','level','xp','attack','potions','gold','enemy_count','kill_count','heal_count','damage_count','page')}
 for n in ('food','turn_count','screen_count','score','high_score'):s[n]=int.from_bytes(raw[S[n]-0xc000:S[n]-0xc000+2],'little')
 s['map']=raw[:4096];s['screen']=raw[0x1200:0x1500]
 s['enemies']=[dict(x=raw[S['ex']-0xc000+i],y=raw[S['ey']-0xc000+i],hp=raw[S['eh']-0xc000+i],type=raw[S['et']-0xc000+i]) for i in range(s['enemy_count']) if raw[S['eh']-0xc000+i]]
 return s
KEYS={'up':(8,32),'down':(8,64),'left':(8,16),'right':(8,128),'wait':(8,1),'heal':(5,128)}
def tap(e,key):
 row,mask=KEYS[key]
 e.command(f'keymatrixdown {row} {mask};after time 0.045 {{keymatrixup {row} {mask}}}')
 e.run_for(.55)
 for _ in range(40):
  if not e.read_symbol(S,'dirty'):break
  e.run_for(.05)
 else:raise AssertionError('Frame did not finish')
 e.run_for(.04)
def path(s,target):
 start=s['py']*64+s['px'];front=[(0,start)];cost={start:0};prev={};m=s['map'];occupied={e['y']*64+e['x'] for e in s['enemies']}
 while front:
  c,p=heapq.heappop(front)
  if c!=cost[p]:continue
  if p==target:
   q=[]
   while p!=start:q.append(p);p=prev[p]
   return q[::-1]
  for n in (p-64,p+64,p-1,p+1):
   if not 0<=n<4096 or m[n] in (1,7):continue
   nc=c+1+(5 if m[n]==8 else 0)+(2 if n in occupied else 0)
   if nc<cost.get(n,99999):cost[n]=nc;prev[n]=p;heapq.heappush(front,(nc,n))
 return []
def direction(s,n):
 d=n-(s['py']*64+s['px']);return {-64:'up',64:'down',-1:'left',1:'right'}[d]
standard=sys.argv[1] if len(sys.argv)>1 else 'ntsc'
with OpenMSX(standard,capture=True,work=ROOT/'work') as e:
 e.load_rom(ROM,'ASCII16');e.run_for(5)
 report['machine']=e.machine_info();check('32KiB-main-RAM',report['machine']['ram_bytes']==32768);check('16KiB-VRAM',report['machine']['vram_bytes']==16384)
 check('title-on-boot',snap(e)['mode']==0)
 e.screenshot(OUT/f'title-{standard}.png',640)
 e.command('set throttle false')
 tap(e,'wait');e.run_for(1);s=snap(e);check('space-start',s['mode']==1 and s['depth']==1 and s['hp']==24)
 check('19-PCG-enemies-loaded',s['enemy_count']==19)
 check('player-at-fixed-center',s['screen'][11*32+15:11*32+17]==bytes((168,169)) and s['screen'][12*32+15:12*32+17]==bytes((170,171)))
 t=s['turn_count'];e.run_for(2);check('turn-based-idle',snap(e)['turn_count']==t)
 tap(e,'left');s2=snap(e);check('left-arrow-scroll',s2['px']==s['px']-1 and s2['py']==s['py'] and s2['screen']!=s['screen'])
 check('center-stays-fixed-after-scroll',s2['screen'][11*32+15:11*32+17]==bytes((168,169)))
 for _ in range(4):tap(e,'left')
 s=snap(e);t=s['turn_count'];tap(e,'left');check('solid-wall-no-turn',snap(e)['px']==1 and snap(e)['turn_count']==t,x=snap(e)['px'],turns=snap(e)['turn_count'],before=t)
 tap(e,'right');tap(e,'right');tap(e,'up');s=snap(e)
 check('potion-pickup',s['potions']==4 and s['map'][4*64+3]==0)
 pots=s['potions'];tap(e,'heal');check('full-health-does-not-waste-potion',snap(e)['potions']==pots)
 e.command('set throttle true');e.run_for(.3);e.screenshot(OUT/f'exploration-{standard}.png',640);e.command('set throttle false')
 if standard=='ntsc':
  e.command('set renderer none')
  captures=[];floor_actions={};last_floor=0;start_time=time.monotonic()
  for action in range(7500):
   s=snap(e)
   if s['depth']!=last_floor:
    e.run_for(1);s=snap(e);last_floor=s['depth'];floor_actions[last_floor]=action
    print('CAMPAIGN floor',last_floor,'action',action,'HP',s['hp'],'potions',s['potions'],flush=True)
   if s['mode']!=1:break
   if action%100==0:print('campaign',action,'xy',s['px'],s['py'],'hp',s['hp'],'level',s['level'],flush=True)
   if s['hp']<=s['maxhp']-14 and s['potions']:
    tap(e,'heal');continue
   target=55*64+55
   # Claim starting chest every floor; it supplies a potion and keeper money.
   if s['map'][3*64+7]==5:target=3*64+7
   if s['food']<90 or s['potions']==0:
    wanted=6 if s['food']<90 else 3
    choices=sorted((abs(i%64-s['px'])+abs(i//64-s['py']),i) for i,t in enumerate(s['map']) if t==wanted)
    if choices:target=choices[0][1]
   # Final warden must be defeated, not bypassed by the path planner.
   if s['depth']==30:
    boss=next((en for en in s['enemies'] if en['type']==15),None)
    if boss and abs(s['px']-55)+abs(s['py']-55)<10:target=boss['y']*64+boss['x']
   route=path(s,target)
   if not route:
    if target==s['py']*64+s['px']:tap(e,'left')
    else:raise AssertionError(('No route',s['depth'],target))
   else:tap(e,direction(s,route[0]))
  s=snap(e)
  report['campaign']={'input_only':True,'gameplay_ram_writes':0,'actions':action,'floors':floor_actions,'final':{k:v for k,v in s.items() if k not in ('map','screen','enemies')},'wall_seconds':time.monotonic()-start_time}
  report['full_thirty_floor_clear_observed']=s['mode']==3 and s['depth']==30
  check('keyboard-only-trial-result',s['mode'] in (2,3) and s['high_score']>=s['score'] and (s['depth']==30 if s['mode']==3 else s['hp']==0),actions=action,floor=s['depth'],score=s['score'])
  check('combat-and-level-up',s['kill_count']>0 and s['level']>1,kills=s['kill_count'],level=s['level'])
  check('damage-and-Z-healing',s['damage_count']>0 and s['heal_count']>0,damage_events=s['damage_count'],heals=s['heal_count'])
  e.command('set renderer SDLGL-PP;set throttle true');e.run_for(.8);e.screenshot(OUT/'campaign-result.png',640)
  tap(e,'wait');e.run_for(1);check('restart-after-result',snap(e)['mode']==1 and snap(e)['depth']==1)
 check('strict-VRAM-timing',e.timing_violations()==0,violations=e.timing_violations())
report['standard']=standard
(OUT/f'verification-{standard}.json').write_text(json.dumps(report,indent=2)+'\n')
