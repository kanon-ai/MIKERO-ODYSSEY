"""Keyboard-only campaign. Full-map read-only planner, not a human difficulty rating."""
from pathlib import Path
import hashlib,heapq,json,sys,time
from emulator_support import OpenMSX
R=Path(__file__).resolve().parents[2];O=R/'outputs';S=json.loads((R/'work/build/symbols.json').read_text())
difficulty=int(sys.argv[1]) if len(sys.argv)>1 else 0
seed=int(sys.argv[2]) if len(sys.argv)>2 else 0
policy=sys.argv[3] if len(sys.argv)>3 else 'balanced'
label=f'{"normal" if difficulty else "easy"}-{seed}-{policy}'
ROM=O/'MIKERO-ODYSSEY.rom';history=[];began=time.monotonic();actions=0
def path(s,target):
 start=s['py']*64+s['px'];heap=[(0,start)];cost={start:0};prev={};occupied={p['y']*64+p['x'] for p in s['enemies']}
 while heap:
  c,p=heapq.heappop(heap)
  if c!=cost[p]:continue
  if p==target:
   route=[]
   while p!=start:route.append(p);p=prev[p]
   return route[::-1],c
  for n in (p-64,p+64,p-1,p+1):
   if not 0<=n<4096 or s['map'][n] in (1,7):continue
   nc=c+1+(8 if s['map'][n]==8 else 0)+(5 if n in occupied and policy!='rush' else 0)
   if nc<cost.get(n,99999):cost[n]=nc;prev[n]=p;heapq.heappush(heap,(nc,n))
 return [],99999
with OpenMSX('ntsc',work=R/'work') as e:
 e.load_rom(ROM,'ASCII16');e.run_for(4+seed*.137)
 def snap():
  raw=e.read_block('memory',0xc000,0x1a00)
  def get(n,z=1):return int.from_bytes(raw[S[n]-0xc000:S[n]-0xc000+z],'little')
  s={n:get(n) for n in ('mode','depth','px','py','hp','maxhp','level','xp','attack','potions','gold','enemy_count','keeper_used','boss_charge','dirty','ending_pending')}
  s.update({n:get(n,2) for n in ('food','score','turn_count','screen_count')})
  s['map']=raw[:4096];s['enemies']=[dict(x=get('ex') if False else raw[S['ex']-0xc000+i],y=raw[S['ey']-0xc000+i],hp=raw[S['eh']-0xc000+i],type=raw[S['et']-0xc000+i]) for i in range(s['enemy_count']) if raw[S['eh']-0xc000+i]]
  return s
 def tap(mask,row=8):
  before=snap();e.command(f'keymatrixdown {row} {mask};after time 0.03 {{keymatrixup {row} {mask}}}');e.run_for(.22)
  after=snap()
  if after['depth']!=before['depth']:e.run_for(1.3)
  else:
   for _ in range(6):
    if not snap()['dirty']:break
    e.run_for(.05)
 def move(s,n):tap({-64:32,64:64,-1:16,1:128}[n-s['py']*64-s['px']])
 if difficulty:tap(128)
 tap(1);e.run_for(1.5);last_floor=0;heals=0;retreats=0;wait_spot=None;approach_waits=0;initiative_waits=0
 for actions in range(12000):
  s=snap();here=s['py']*64+s['px'];m=s['map']
  if here!=wait_spot:wait_spot=here;approach_waits=0
  if s['depth']!=last_floor:
   last_floor=s['depth'];entry={k:s[k] for k in ('depth','hp','maxhp','potions','level','food','score')};entry['action']=actions;history.append(entry);print(label,'FLOOR',entry,flush=True)
  if s['mode']!=1:break
  adjacent=[a for a in s['enemies'] if abs(a['x']-s['px'])+abs(a['y']-s['py'])==1]
  boss=next((a for a in s['enemies'] if a['type']==15),None)
  occupied={a['y']*64+a['x'] for a in s['enemies']}
  if difficulty and policy!='rush' and boss and s['boss_charge'] and boss in adjacent:
   options=[n for n in (here-64,here+64,here-1,here+1) if m[n] not in (1,7,8,9) and n not in occupied]
   if options:move(s,min(options,key=lambda n:sum(abs(n%64-a['x'])+abs(n//64-a['y'])==1 for a in s['enemies'])));retreats+=1;continue
  amount=12 if difficulty else 16
  danger=sum(10 if a['type']==15 and difficulty else (1+(a['type']-11)//2+s['depth']//6 if difficulty else 4 if a['type']==15 else 1+(a['type']-11)//2+s['depth']//4) for a in adjacent)
  if s['potions'] and (s['hp']<=s['maxhp']-amount or s['hp']<=danger+2):tap(128,5);heals+=1;continue
  # At low health, collect the nearby entrance medicine before engaging.
  # This is a route choice made through normal keys, not a health injection.
  if policy=='safe_route' and not s['potions'] and s['hp']<=12 and s['px']<12 and s['py']<12 and m[259]==3:
   emergency,cost=path(s,259)
   if emergency and cost<=12 and emergency[0] not in occupied:move(s,emergency[0]);continue
  # Do not endlessly walk around a pursuer while it attacks every turn.
  if adjacent:
   approach_waits=0;opponent=min(adjacent,key=lambda a:a['hp']);move(s,opponent['y']*64+opponent['x']);continue
  target=55*64+55
  if policy!='rush':
   # The one Keeper treatment is useful before leaving the entrance.
   if s['hp']<=s['maxhp']-12 and s['gold']>=(15 if difficulty else 5) and not s['keeper_used'] and s['px']<12 and s['py']<12:
    keeper=7*64+8
    if abs(s['px']-8)+abs(s['py']-7)==1:move(s,keeper);continue
    neighbors=[keeper-64,keeper+64,keeper-1,keeper+1];target=min(neighbors,key=lambda p:path(s,p)[1])
   elif m[199]==5:target=199
   elif policy=='prepared' and s['food']<500 and s['px']<12 and s['py']<12 and m[451]==6:target=451
   else:
    wanted=6 if s['food']<90 else 3 if s['potions']<=(1 if difficulty else 2) else None
    if wanted:
     choices=[i for i,t in enumerate(m) if t==wanted]
     if choices:
      candidate=min(choices,key=lambda p:path(s,p)[1])
      if policy not in ('route','safe_route','tactical','prepared') or path(s,candidate)[1]<=(80 if wanted==6 else 40):target=candidate
  if boss and abs(s['px']-boss['x'])+abs(s['py']-boss['y'])<=7:
   if difficulty and policy!='rush' and abs(s['px']-boss['x'])+abs(s['py']-boss['y'])==2:tap(1);continue
   target=boss['y']*64+boss['x']
  route,_=path(s,target)
  if route:
   # Let a creature two squares away approach before using the paw.
   # Moving into adjacency otherwise grants it a free bump first.
   n=route[0]
   threats=[a for a in s['enemies'] if abs(a['x']-s['px'])+abs(a['y']-s['py'])==2 and abs(a['x']-n%64)+abs(a['y']-n//64)==1]
   if policy in ('tactical','prepared') and threats and n not in occupied and approach_waits<2:
    approach_waits+=1;initiative_waits+=1;tap(1);continue
   move(s,n)
  else:
   options=[n for n in (here-64,here+64,here-1,here+1) if m[n] not in (1,7)]
   if not options:raise AssertionError('No legal route')
   move(s,options[0])
  if actions%300==0:print(label,'action',actions,'HP',s['hp'],'POT',s['potions'],flush=True)
 e.run_for(3);s=snap()
 report=dict(rom_sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),difficulty='NORMAL' if difficulty else 'EASY',seed_wait=seed,policy=policy,input_only=True,gameplay_ram_writes=0,planner_observes_full_map=True,actions=actions+1,heals=heals,boss_retreats=retreats,initiative_waits=initiative_waits,history=history,final={k:v for k,v in s.items() if k not in ('map','enemies')},cleared=s['mode']==3 and s['depth']==(30 if difficulty else 15) and not s['ending_pending'],strict_VRAM_violations=e.timing_violations(),wall_seconds=time.monotonic()-began)
 (O/f'campaign-{label}.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!='history'},indent=2),flush=True)
 assert e.timing_violations()==0
