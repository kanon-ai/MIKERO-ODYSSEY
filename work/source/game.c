/* MIKERO-ODYSSEY: original MSX1 / ASCII16 / 32 KiB main RAM.
   SDCC default calling convention. All mutable game data is in C000-EFFF.
   Actors remain PCG. Mikero's detail colors and effects use sprite planes. */
typedef unsigned char u8;
typedef signed char i8;
typedef unsigned int u16;
typedef signed int i16;
#define MEM(a) (*(volatile u8 *)(a))
#define FLOOR 0
#define WALL 1
#define STAIRS 2
#define POTION 3
#define GOLD 4
#define CHEST 5
#define FOOD 6
#define SHRINE 7
#define TRAP 8
#define CROWN 9
#define HERO 10
#define SLIME 11
#define BAT 12
#define KNIGHT 13
#define GHOST 14
#define BOSS 15
#define DARK 16
#define OLDWALL 17
#define OLDFLOOR 18
#define SPARK 19
#define GEM 20
#define SHOP 29
#define SOLDOUT 30
#define KEY 31
#define MAXEN 20
u8 map[4096],seen[512],screen[768],sight[135];
u8 scroll_screen[768],scroll_under[4];
const u8 *view_origin;
u8 view_visible(u8 cell);
u8 render_x,render_y,render_cell,render_cols,render_rows;
const u8 *render_map;
void render_view(void);
i8 scroll_dx,scroll_dy;
u8 *copy_dst;const u8 *copy_src;u16 copy_len;
void copy_bytes(void) __naked {
 __asm
 ld hl,(_copy_src)
 ld de,(_copy_dst)
 ld bc,(_copy_len)
 ldir
 ret
 __endasm;
}
u8 ex[MAXEN],ey[MAXEN],eh[MAXEN],et[MAXEN];
u8 mode,depth,px,py,hp,maxhp,level,xp,potions,gold,attack,seed,variant;
u8 enemy_count,page,input,prev_input,repeat,dirty,paused,foodclock;
u8 hungerclock;
u8 turns,fx,fx_x,fx_y,sound_left,psg_mix,reg_num,reg_val;
u8 joy,trigger,keys,info_id,kill_count,heal_count,damage_count;
u16 food,rng,turn_count,screen_count;
u16 vaddr,vlen;
const u8 *vsrc;
const char *message;
/* Animation-only state, never used by dungeon/combat rules. */
u8 old_hook[5],anim_lock,anim_div,anim_clock,anim_pose,anim_oldpose,anim_oldphase,anim_theme;
u8 walk_timer,effect_kind,effect_age,anim_size,anim_banks,anim_item,anim_sat[41],hit_x,hit_y;
u16 anim_updates,anim_ptr,anim_target;
u8 anim_gap;
extern const u8 effect_patterns[];
void install_animation(void);
/* Run record survives SPACE restart, but not power-off. */
u16 score,high_score,music_period;
u8 record_floor,music_pos,music_age,music_volume;
u8 rescue_pending,rescue_phase;
u8 difficulty,depth_max,potion_limit,keeper_used,boss_charge,ending_pending,ending_phase,menu_key;
u16 best_score[3];u8 best_floor[3];
u8 has_key;
volatile u8 frame_tick;
u8 walked[512];
u16 explored;
extern const u8 gate_patterns[],gate_colors[];
u8 goal_x,goal_y,goal_known;
/* Action-driven fragments of the Nutcracker March, not one note per step.
   Sequencing and decay run in the VBlank hook; no queued or idle phrases. */
u8 music_frag;
void music_reset(void);
void music_step(void);
void add_score(u16 n){if(score>65535-n)score=65535;else score+=n;}
void finish_run(u8 result){
 mode=result;rescue_pending=result==2;ending_pending=result==3;repeat=1;
 if(score>high_score || (score==high_score && depth>record_floor)){high_score=score;record_floor=depth;}
 best_score[difficulty]=high_score;best_floor[difficulty]=record_floor;
}
void regwrite(void) __naked {
 __asm
 di
 ld a,(_reg_val)
 out (0x99),a
 ld a,(_reg_num)
 or #0x80
 out (0x99),a
 ei
 ret
 __endasm;
}
void upload(void) __naked {
 __asm
 di
 ld hl,(_vaddr)
 ld a,l
 out (0x99),a
 ld a,h
 or #0x40
 out (0x99),a
 ld hl,(_vsrc)
 ld bc,(_vlen)
001$:
 ld a,(hl)
 out (0x98),a
 inc hl
 dec bc
 ld a,b
 or c
 jr nz,001$
 ei
 ret
 __endasm;
}
void frame(void) __naked {
 __asm
 ei
 halt
 ret
 __endasm;
}
void input_read(void) __naked {
 __asm
 xor a
 call 0x00d5
 ld (_joy),a
 ld a,#1
 call 0x00d5
 ld b,a
 ld a,(_joy)
 or b
 ld (_joy),a
 xor a
 call 0x00d8
 ld (_trigger),a
 ld a,#1
 call 0x00d8
 ld b,a
 ld a,(_trigger)
 or b
 ld (_trigger),a
 ld a,#5
 call 0x0141
 cpl
 ld b,a
 and #0x20
 ld (_menu_key),a
 ld a,b
 and #0x80
 ld (_keys),a
 ld a,#3
 call 0x00d8
 ld b,a
 ld a,(_keys)
 or b
 ld (_keys),a
 ret
 __endasm;
}
u8 sfx_kind,sfx_next;
void beep(void);
void sfx(u8 pitch) {
 sfx_next=pitch==80?0:(pitch==30 || pitch==32)?1:(pitch==20 || pitch==35 || pitch==48)?2:pitch==55?3:pitch>=190?4:pitch==24?5:pitch==40?6:7;
 beep();effect_kind=pitch==80?1:pitch>=190?3:2;effect_age=16;
}
u8 random8(void) {rng^=rng<<7;rng^=rng>>9;rng^=rng<<8;return (u8)rng;}
u16 index(u8 x,u8 y) {return ((u16)y<<6)+x;}
u8 tile(u8 x,u8 y) {if(x>63 || y>63)return WALL;return map[index(x,y)];}
void put(u8 x,u8 y,u8 t) {map[index(x,y)]=t;}
u8 dist(u8 a,u8 b) {return a>b?a-b:b-a;}
void say(const char *s) {message=s;dirty=1;}
void text(u8 x,u8 y,const char *s) {u16 p=(u16)y*32+x;while(*s && x++<32 && p<768)screen[p++]=*s++;}
const u16 decimal_places[]={10000,1000,100,10,1};
void number(u8 x,u8 y,u16 n,u8 digits) {
 u16 p=(u16)y*32+x,v;u8 c,i=5-digits;
 while(i<5){v=decimal_places[i++];c='0';while(n>=v){n-=v;c++;}screen[p++]=c;}
}
void clear_screen(void) __naked {
 __asm
 ld hl,#_screen
 ld de,#_screen+1
 ld bc,#767
 ld (hl),#32
 ldir
 ret
 __endasm;
}
void block(u8 x,u8 y,u8 t) {u16 p=(u16)y*32+x;u8 c=128+t*4;screen[p]=c;screen[p+1]=c+1;screen[p+32]=c+2;screen[p+33]=c+3;}
/* Fixed-size name transfer, paced for TMS9918A active display. */
void upload_names(void) __naked {
 __asm
 di
 ld hl,(_vaddr)
 ld a,l
 out (0x99),a
 ld a,h
 or #0x40
 out (0x99),a
 ld hl,(_vsrc)
 ld c,#0x98
 ld d,#3
010$:
 ld b,#0
011$:
 outi
 nop
 jp nz,011$
 dec d
 jr nz,010$
 ei
 ret
 __endasm;
}
void present(void) {
 page^=1;vaddr=page?0x1c00:0x1800;vsrc=screen;vlen=768;upload_names();
 frame();reg_num=2;reg_val=page?7:6;regwrite();screen_count++;dirty=0;
}
/* Build the half-step from the destination scene, retaining the entering
   edge from the old scene. Only names scroll; HUD and the cat stay fixed. */
void half_step(void) {
 u8 y;u16 p;
 screen[367]=scroll_under[0];screen[368]=scroll_under[1];
 screen[399]=scroll_under[2];screen[400]=scroll_under[3];
 if(scroll_dx) {
  for(y=3;y<21;y++) {
   p=(u16)y*32;
   if(scroll_dx>0){scroll_screen[p+1]=scroll_screen[p+2];copy_src=screen+p+1;copy_dst=scroll_screen+p+2;}
   else{scroll_screen[p+30]=scroll_screen[p+29];copy_src=screen+p+2;copy_dst=scroll_screen+p+1;}
   copy_len=29;copy_bytes();
  }
 } else {
  if(scroll_dy>0){copy_src=scroll_screen+129;copy_dst=scroll_screen+97;}
  else{copy_src=scroll_screen+609;copy_dst=scroll_screen+641;}
  copy_len=30;copy_bytes();
  if(scroll_dy>0){copy_src=screen+96;copy_dst=scroll_screen+128;}
  else{copy_src=screen+128;copy_dst=scroll_screen+96;}
  copy_len=544;copy_bytes();
 }
 block(15,11,HERO);
 scroll_screen[367]=168;scroll_screen[368]=169;
 scroll_screen[399]=170;scroll_screen[400]=171;
 copy_src=screen;copy_dst=scroll_screen;copy_len=96;copy_bytes();
 copy_src=screen+672;copy_dst=scroll_screen+672;copy_len=96;copy_bytes();
 page^=1;vaddr=page?0x1c00:0x1800;vsrc=scroll_screen;vlen=768;upload_names();
 frame();reg_num=2;reg_val=page?7:6;regwrite();screen_count++;
 scroll_dx=0;scroll_dy=0;
 frame();
}
/* Integer Bresenham rays. The target wall itself is visible; cells behind it are not. */
u8 visible(u8 tx,u8 ty) {
 i8 x=px,y=py,dx=dist(px,tx),dy=-(i8)dist(py,ty),sx=px<tx?1:-1,sy=py<ty?1:-1,err,e2;
 if(dx>7 || -dy>4 || dx-dy>9)return 0;
 err=dx+dy;
 while(x!=(i8)tx || y!=(i8)ty) {
  e2=err*2;if(e2>=dy){err+=dy;x+=sx;}if(e2<=dx){err+=dx;y+=sy;}
  if(x==(i8)tx && y==(i8)ty)return 1;
  if(tile(x,y)==WALL)return 0;
 }
 return 1;
}
u8 enemy_at(u8 x,u8 y) {u8 i;for(i=0;i<enemy_count;i++)if(eh[i] && ex[i]==x && ey[i]==y)return i;return 255;}
const char *theme(void) {
 switch((depth-1)%8+1){case 1:return "MOSS LANTERNS";case 2:return "CANDY SPORES";case 3:return "TIDAL TEMPLE";case 4:return "CRYSTAL SNOW";case 5:return "EMBER FOUNDRY";case 6:return "CLOCKWORK GOLD";case 7:return "AURORA GARDEN";default:return "STARLESS CROWN";}
}
/* Eight coarse bearings; no path search, map reveal or game-state changes. */
void compass(void) {
 i8 dx=(i8)goal_x-(i8)px,dy=(i8)goal_y-(i8)py;
 u8 ax=dist(goal_x,px),ay=dist(goal_y,py),d,c;
 if(!goal_known || (!ax && !ay))return;
 if(ax>ay*2)d=dx>0?2:6;
 else if(ay>ax*2)d=dy>0?4:0;
 else if(dy<0)d=dx>0?1:7;
 else d=dx>0?3:5;
 c=d*4;screen[29]=c;screen[30]=c+1;screen[61]=c+2;screen[62]=c+3;
}
void draw(void) {
 u8 x,y,i;
 if((scroll_dx || scroll_dy) && mode==1){copy_src=screen;copy_dst=scroll_screen;copy_len=768;copy_bytes();}
 clear_screen();
 view_origin=map+index(px,py);
 text(1,0,difficulty==2?"HARD":difficulty?"NORMAL":"EASY");if(difficulty==2)text(6,0,has_key?"KEY":"---");text(10,0,"F");number(11,0,depth,2);text(14,0,"LV");number(16,0,level,2);text(21,0,"G");number(22,0,gold,3);
 text(1,1,"HP");number(4,1,hp,2);text(6,1,"/");number(7,1,maxhp,2);text(11,1,"POT");number(15,1,potions,2);text(20,1,"FOOD");number(25,1,food,3);
 if(mode==1)compass();
 for(x=0;x<32;x++){screen[64+x]=94+(x&3);screen[672+x]=94+(x&3);}
 render_view();
 /* Overlay each visible actor once instead of searching 19 actors per cell. */
 for(i=0;i<enemy_count;i++)if(eh[i]) {
  x=ex[i]-px+7;y=ey[i]-py+4;
  if(x<15 && y<9 && sight[y*15+x])block(x*2+1,y*2+3,et[i]);
 }
 scroll_under[0]=screen[367];scroll_under[1]=screen[368];scroll_under[2]=screen[399];scroll_under[3]=screen[400];
 block(15,11,HERO);
 if(fx){block(fx_x,fx_y,SPARK);fx=0;}
 text(1,22,message);
 text(1,23,mode>=2?"SPACE:NEW GAME   X:TITLE":"ARROWS:MOVE SPACE:WAIT Z:HEAL");
 if(mode>=2){
  for(y=7;y<19;y++)text(2,y,"                            ");
  if(mode==3)text(9,8,"GATE CLOSED!");
  text(5,10,"FLOOR");number(12,10,depth,2);text(16,10,"/");number(18,10,depth_max,2);
  text(5,12,"SCORE");number(14,12,score,5);
  text(5,14,difficulty==2?"BEST HARD":difficulty?"BEST NORMAL":"BEST EASY");number(17,14,high_score,5);
  text(5,15,"BEST RUN FLOOR");number(21,15,record_floor,2);
  text(5,16,"EXPLORED");number(17,16,explored,5);
  text(5,17,"SPACE: NEW GAME ");
 }
 if((scroll_dx || scroll_dy) && mode==1)half_step();
 scroll_dx=0;scroll_dy=0;
 present();
}
/* A separate, input-free rescue scene before the score screen. */
void rescue_tile(i8 x,u8 y,u8 t) {
 u8 q; i8 xx;u8 yy;
 for(q=0;q<4;q++) {
  xx=x+(q&1);yy=y+(q>>1);
  if(xx>=0 && xx<32)screen[(u16)yy*32+(u8)xx]=128+t*4+q;
 }
}
void rescue_scene(void) {
 u8 n,i,pose; i8 x;
 scroll_dx=0;scroll_dy=0;effect_age=0;walk_timer=0;
 rescue_phase=1;
 for(n=0;n<7;n++) {
  clear_screen();
  text(5,7,"KEEPERS: LET US HELP!");
  x=n<3?11:11+(n-3);
  rescue_tile(x,11,SHRINE);rescue_tile(x+8,11,SHRINE);
  rescue_tile(x+4,11,27);
  rescue_tile(x+2,13,28);rescue_tile(x+4,13,28);rescue_tile(x+6,13,28);
  /* Existing rabbit ear/blink frames, only during this scene. */
  MEM(0x7000)=1;pose=n&3;
  for(i=0;i<3;i++) {
   vaddr=156*8+(u16)i*2048;vsrc=(const u8*)(0xbe00+(u16)pose*64);vlen=32;upload();
   vaddr+=0x2000;vsrc+=32;upload();
  }
  present();
  for(i=0;i<5;i++)frame();
  rescue_phase=2;
 }
 rescue_pending=0;rescue_phase=3;dirty=1;
}
void graphics(void) {
 u8 i;anim_lock=1;anim_theme=depth?(depth-1)%8:0;MEM(0x7000)=1;
 for(i=0;i<3;i++){
  vaddr=(u16)i*0x800;vsrc=(const u8*)0x8000;vlen=2048;upload();
  vaddr=0x2000+(u16)i*0x800;vsrc=(const u8*)0x8800;upload();
  vsrc=(const u8*)(0x9500+(u16)anim_theme*1024);vaddr=0x400+(u16)i*0x800;vlen=64;upload();
  vsrc+=64;vaddr+=0x2000;upload();
 }
 vsrc=effect_patterns;vaddr=0x3860;vlen=512;upload();
 reg_num=1;reg_val=0xe2;regwrite();reg_num=5;reg_val=0x36;regwrite();reg_num=6;reg_val=7;regwrite();
 anim_oldphase=255;anim_oldpose=255;anim_lock=0;
}
/* The portal uses 48 temporary PCG characters. Restore normal art afterwards. */
void closing_scene(void) {
 u8 f,x,y,b,i;
 scroll_dx=0;scroll_dy=0;effect_age=0;walk_timer=0;anim_lock=1;
 anim_sat[0]=208;vaddr=0x1b00;vsrc=anim_sat;vlen=1;upload();
 reg_num=5;reg_val=0x36;regwrite();
 for(f=0;f<4;f++) {
  ending_phase=f+1;clear_screen();
  text(f==3?8:5,3,f==3?"THE GATE CLOSES.":"ONE LAST LITTLE PAW...");
  for(y=0;y<8;y++)for(x=0;x<6;x++)screen[(u16)(y+7)*32+x+13]=176+y*6+x;
  block(15,16,HERO);block(9,16,SHRINE);block(21,16,SHRINE);
  for(b=0;b<3;b++) {
   vaddr=176*8+(u16)b*2048;vsrc=gate_patterns+(u16)f*384;vlen=384;upload();
   vaddr+=0x2000;vsrc=gate_colors;upload();
  }
  present();
  if(!f){
   /* The same three face/detail planes as the title's idle cat, at (120,128). */
   MEM(0x7000)=1;vaddr=0x3800;vsrc=(const u8*)0x9200;vlen=96;upload();
   for(b=0;b<3;b++){anim_sat[b*4]=127;anim_sat[b*4+1]=120;anim_sat[b*4+2]=b*4;anim_sat[b*4+3]=b==0?15:b==1?3:10;}
   anim_sat[12]=208;vaddr=0x1b00;vsrc=anim_sat;vlen=13;upload();
  }
  for(i=0;i<(f==3?24:12);i++)frame();
 }
 ending_pending=0;graphics();dirty=1;
}
void load_floor(void) {
 u16 n;u8 t,i,pc=0,cc=0,fc=0;
 scroll_dx=0;scroll_dy=0;
 anim_lock=1;
 variant=(seed+depth*13)%120;
 MEM(0x7000)=2+variant/4;
 vsrc=(const u8*)(0x8000+(u16)(variant&3)*4096);
 for(n=0;n<4096;n++)map[n]=vsrc[n];
 for(n=0;n<512;n++){seen[n]=0;walked[n]=0;}
 walked[325>>3]=1<<(325&7);
 enemy_count=0;goal_known=0;keeper_used=0;boss_charge=0;
 for(n=0;n<4096;n++) {
  t=map[n];
  /* Keep the opening supplies, spread the rest across each original layout. */
  if(t==POTION && n!=259){if((pc*5+variant)%12>=(difficulty?3:5))map[n]=FLOOR;pc++;}
  if(t==CHEST && n!=199){if(difficulty || (cc*3+variant)%7>=2)map[n]=FLOOR;cc++;}
  if(difficulty && t==FOOD && n!=451){if((fc*5+variant)%14>=3)map[n]=FLOOR;fc++;}
  if(t==STAIRS || t==CROWN){goal_x=n&63;goal_y=n>>6;goal_known=1;}
  if(t>=32 && t<=36){
   i=enemy_count++;
   ex[i]=n&63;ey[i]=n>>6;et[i]=t-32+SLIME;eh[i]=2+(t-32)*2+depth/2;
   if(difficulty)eh[i]=5+(t-32)*2+depth/3+depth/8;
   if(t==36){if(depth==depth_max){et[i]=BOSS;eh[i]=difficulty?96:24;}else{et[i]=KNIGHT;eh[i]=difficulty?9+depth/2+depth/8:5+depth;}}
   map[n]=FLOOR;
  }
  if(t==CROWN && depth<depth_max)map[n]=STAIRS;
 }
 px=5;py=5;foodclock=0;hungerclock=0;
 map[200]=SHOP;
 has_key=0;
 if(difficulty==2){
  n=(u16)variant*31;
  while(map[n]!=FLOOR || (n&63)<12 || (n>>6)<12 || dist(n&63,goal_x)+dist(n>>6,goal_y)<8)n=(n+1)&4095;
  map[n]=KEY;
 }
 if(food<(difficulty?150:250))food=difficulty?150:250;
 graphics();say(theme());sfx(40);
}
void new_game(void) {
 seed=(u8)rng;depth=1;hp=24;maxhp=24;level=1;xp=0;attack=3;potions=difficulty?2:3;gold=0;
 depth_max=difficulty?30:15;potion_limit=difficulty?5:9;
 high_score=best_score[difficulty];record_floor=best_floor[difficulty];
 rescue_pending=0;ending_pending=0;ending_phase=0;repeat=0;
 score=0;explored=0;music_reset();
 food=difficulty?300:400;mode=1;turns=0;turn_count=0;kill_count=0;heal_count=0;damage_count=0;
 load_floor();
}
void hurt(u8 n) {
 damage_count++;
 if(hp<=n){hp=0;finish_run(2);say("A GOOD TRY! LET US REST.");sfx(240);}
 else{hp-=n;sfx(190);}
}
void enemy_turn(void) {
 u8 i,dx,dy,nx,ny,n,j;
 for(i=0;i<enemy_count && mode==1;i++)if(eh[i]) {
  dx=dist(ex[i],px);dy=dist(ey[i],py);
  if(dx+dy>10)continue;
  if(dx+dy==1){
   n=et[i]==BOSS?4:1+(et[i]-SLIME)/2+depth/4;
   if(difficulty){
    n=1+(et[i]-SLIME)/2+depth/6;
    if(et[i]==BOSS){if(!boss_charge){boss_charge=1;say("THE KING TAKES A DEEP BREATH!");continue;}boss_charge=0;n=10;}
   }
   say(et[i]==BOSS?"THE KING BUMPS INTO YOU!":"A CREATURE BUMPS INTO YOU!");hurt(n);continue;
  }
  if(difficulty && et[i]==BOSS && boss_charge){boss_charge=0;say("POOF! THE KING MISSES!");continue;}
  if(!visible(ex[i],ey[i]))continue;
  if(et[i]==SLIME && (turns&1))continue;
  if(et[i]==KNIGHT && (turns%3)==0)continue;
  nx=ex[i];ny=ey[i];
  if(dx && (!dy || (random8()&1)))nx+=ex[i]<px?1:-1;
  else if(dy)ny+=ey[i]<py?1:-1;
  n=tile(nx,ny);j=enemy_at(nx,ny);
  if(n!=WALL && n!=SHRINE && n!=SHOP && n!=SOLDOUT && j==255 && (nx!=px || ny!=py)){ex[i]=nx;ey[i]=ny;}
 }
}
void tick_turn(void) {
 music_step();turns++;turn_count++;enemy_turn();
 if(mode!=1)return;
 if(food) {hungerclock=0;food--;if(++foodclock==(difficulty?28:14)){foodclock=0;if(hp<maxhp)hp++;}}
 else {say("STARVING! FIND SOME FOOD.");if(++hungerclock==20){hungerclock=0;hurt(1);}}
 dirty=1;
}
void fight(u8 i) {
 u8 dmg=attack+(random8()&1);
 hit_x=120+(ex[i]-px)*16;hit_y=87+(ey[i]-py)*16;
 sfx(80);say("PAW TAP! PON!");
 if(eh[i]<=dmg) {
  eh[i]=0;kill_count++;add_score(et[i]==BOSS?200:20+(et[i]-SLIME)*10);xp+=et[i]==BOSS?12:2;gold+=gold<250?1:0;
  say("POOF! +XP +GOLD");
  if(et[i]==BOSS)say("POOF! THE GATE IS AHEAD!");
  if(xp>=5+level*3){xp=0;if(level<15){level++;maxhp+=2;attack++;}if(difficulty){hp+=6;if(hp>maxhp)hp=maxhp;}else hp=maxhp;say(difficulty?"LEVEL UP! +6 HEALTH.":"LEVEL UP! HEALTH RESTORED.");sfx(24);}
 }else eh[i]-=dmg;
 tick_turn();
 if(!eh[i] && mode==1){effect_kind=4;effect_age=32;}
}
void move_player(i8 dx,i8 dy) {
 u8 nx=px+dx,ny=py+dy,t=tile(nx,ny),i=enemy_at(nx,ny);
 u16 step;
 if(t==WALL){say("A WALL BLOCKS THE WAY.");return;}
 if(i!=255){fight(i);return;}
 if(t==SHOP || t==SOLDOUT){
  if(t==SOLDOUT)say("SHOP: SOLD OUT. THANK YOU!");
  else if(gold<25)say("SHOP: FISH 25G / +100 FOOD.");
  else if(food>899)say("SHOP: YOU HAVE ENOUGH FOOD.");
  else {gold-=25;food+=100;hungerclock=0;put(nx,ny,SOLDOUT);say("SHOP: +100 FOOD. THANK YOU!");sfx(55);}
  return;
 }
 if(t==SHRINE){
  if(difficulty){
   if(keeper_used)say("KEEPER: NO BANDAGES LEFT.");
   else if(gold>=15 && hp<maxhp){gold-=15;hp+=24;if(hp>maxhp)hp=maxhp;keeper_used=1;say("KEEPER: ALL PATCHED UP!");sfx(30);}
   else say("KEEPER: +24 HP FOR 15 GOLD.");
   return;
  }
  if(gold>=5 && hp<maxhp){gold-=5;hp=maxhp;say("KEEPER: ALL PATCHED UP!");sfx(30);}
  else say("KEEPER: FULL HEAL FOR 5 GOLD.");return;
 }
 px=nx;py=ny;scroll_dx=dx;scroll_dy=dy;walk_timer=16;say(theme());
 step=index(px,py);
 if(!(walked[step>>3]&(1<<(step&7)))){walked[step>>3]|=1<<(step&7);add_score(1);if(explored<65535)explored++;}
 if(dist(px,8)+dist(py,3)==1)say(map[200]==SHOP?"SHOP: FISH 25G / +100 FOOD.":"SHOP: SOLD OUT. THANK YOU!");
 if(t==POTION){if(potions<potion_limit){potions++;put(px,py,FLOOR);say("POTION FOUND. Z TO DRINK.");sfx(35);}else say("POT PACK FULL. LEFT HERE.");}
 if(t==GOLD){add_score(25);gold=gold<246?gold+5:250;put(px,py,FLOOR);say("FIVE GOLD PIECES FOUND.");sfx(48);}
 if(t==CHEST){add_score(100);gold=gold<241?gold+10:250;put(px,py,FLOOR);if(potions<potion_limit){potions++;say("CHEST: 10 GOLD AND A POTION!");}else{put(px,py,POTION);say("CHEST: GOLD. POTION LEFT HERE.");}sfx(20);}
 if(t==FOOD){food+=100;if(food>999)food=999;put(px,py,FLOOR);say("FRESH RATIONS. +100 FOOD");sfx(55);}
 if(t==KEY){has_key=1;put(px,py,FLOOR);say("KEY FOUND! THE WAY IS OPEN.");sfx(48);}
 if(t==TRAP){put(px,py,FLOOR);say("SPIKES! YOU LOSE 3 HEALTH.");hurt(3);}
 if(difficulty==2 && !has_key && (t==STAIRS || t==CROWN)){say("LOCKED! FIND THE FLOOR KEY.");tick_turn();return;}
 if(t==STAIRS){add_score(200);depth++;load_floor();music_step();return;}
 if(t==CROWN){
  for(i=0;i<enemy_count;i++)if(et[i]==BOSS && eh[i]){say("MEET THE SLIME KING FIRST!");tick_turn();return;}
  add_score(difficulty?3000:1500);finish_run(3);say("THE GATE IS CLOSED. WELL DONE!");sfx(16);return;
 }
 if(mode==1)tick_turn();
}
void heal(void) {
 if(!potions){say("NO POTIONS LEFT.");return;}
 if(hp==maxhp){say("YOUR HEALTH IS ALREADY FULL.");return;}
 potions--;heal_count++;hp+=difficulty?12:16;if(hp>maxhp)hp=maxhp;say(difficulty?"POTION: 12 HEALTH RESTORED.":"POTION: 16 HEALTH RESTORED.");sfx(32);tick_turn();
}
void title(void) {
 u8 x,y;
 clear_screen();
 for(x=1;x<31;x++){screen[32+x]=94+(x&3);screen[704+x]=94+(x&3);}
 for(x=0;x<6;x++)block(5+x*4,3,21+x);
 text(9,6,"MIKERO-ODYSSEY");
 for(y=8;y<14;y+=2)for(x=3;x<29;x+=2)block(x,y,FLOOR);
 for(x=3;x<29;x+=2){block(x,8,WALL);block(x,14,WALL);}
 block(5,10,SLIME);block(9,12,POTION);block(13,10,HERO);block(17,12,CHEST);block(21,10,KNIGHT);block(25,12,CROWN);
 text(6,17,"SPACE / FIRE TO BEGIN");text(6,19,difficulty==2?"HARD   - 30 FLOORS":difficulty?"NORMAL - 30 FLOORS":"EASY   - 15 FLOORS");text(4,20,"LEFT/RIGHT: SELECT MODE");if(difficulty==2)text(5,21,"FIND A KEY EACH FLOOR");text(4,23,"WALK A LITTLE. FIND A LOT.");present();
}
void hardware(void) __naked {
 __asm
 ld a,#15
 ld (0xf3e9),a
 ld a,#1
 ld (0xf3ea),a
 ld (0xf3eb),a
 ld a,#2
 call 0x005f
 xor a
 ld (0xf3db),a ; BIOS CLIKSW: disable keyboard click, keep PSG music and effects.
 ld a,#7
 out (0xa0),a
 in a,(0xa2)
 and #0xc0
 or #0x38
 ld (_psg_mix),a
 ei
 ret
 __endasm;
}
void main(void) {
 hardware();music_reset();rng=0xace1;depth=0;graphics();
 title();
 install_animation();
 for(;;) {
  frame();input_read();
  input=keys?10:trigger?9:joy;
  if(mode==0){random8();if((input==3 || input==7) && input!=prev_input){if(input==3){if(++difficulty==3)difficulty=0;}else{if(difficulty) difficulty--;else difficulty=2;}title();}if(input==9 && prev_input!=9){new_game();draw();}}
  else if(mode>=2){if(!input)repeat=0;if(menu_key){mode=0;depth=0;graphics();title();}else if(input==9 && prev_input!=9 && !repeat){new_game();draw();}}
  else {
   if(!input)repeat=0;
   if(input && (input!=prev_input || !repeat || (i8)(frame_tick-repeat)>=0)) {
    repeat=frame_tick+6;if(!repeat)repeat=1;
    if(input==1)move_player(0,-1);if(input==3)move_player(1,0);if(input==5)move_player(0,1);if(input==7)move_player(-1,0);
    if(input==9){say("YOU WAIT AND LISTEN.");tick_turn();}
    if(input==10)heal();
   }
   if(rescue_pending)rescue_scene();
   if(ending_pending)closing_scene();
   if(dirty)draw();
  }
  prev_input=input;
 }
}
