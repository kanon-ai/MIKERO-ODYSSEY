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
#define MAXEN 20
u8 map[4096],seen[512],screen[768],sight[135];
u8 ex[MAXEN],ey[MAXEN],eh[MAXEN],et[MAXEN];
u8 mode,depth,px,py,hp,maxhp,level,xp,potions,gold,attack,seed,variant;
u8 enemy_count,page,input,prev_input,repeat,dirty,paused,foodclock;
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
extern const u8 effect_patterns[];
void install_animation(void);
/* Run record survives SPACE restart, but not power-off. */
u16 score,high_score,music_period;
u8 record_floor,music_pos,music_age,music_volume;
/* Nutcracker March, opening four bars, upper melody; one note per step.
   Composer's 1892 piano version, IMSLP57454 p.8. PSG clock 1789772.5 Hz. */
const u16 march_periods[]={191,191,191,191,170,170,152,191,170,191,191,191,191,170,170,152,191,170,170};
void add_score(u16 n){if(score>65535-n)score=65535;else score+=n;}
void finish_run(u8 result){
 mode=result;
 if(score>high_score || (score==high_score && depth>record_floor)){high_score=score;record_floor=depth;}
}
void music_write(void) __naked {
 __asm
 di
 ld a,#2
 out (0xa0),a
 ld a,(_music_period)
 out (0xa1),a
 ld a,#3
 out (0xa0),a
 ld a,(_music_period+1)
 out (0xa1),a
 ld a,#9
 out (0xa0),a
 ld a,(_music_volume)
 out (0xa1),a
 ei
 ret
 __endasm;
}
void music_tick(void){
 if(mode!=1){music_age=0;if(music_volume){music_volume=0;music_write();}return;}
 if(!music_age && !music_volume)return;
 music_volume=music_age?(music_age>4?6:music_age>2?4:2):0;
 if(sound_left && music_volume>2)music_volume=2;
 music_write();
}
void music_step(void){
 music_period=march_periods[music_pos];if(++music_pos==19)music_pos=0;
 music_age=6;music_volume=sound_left?2:6;music_write();
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
void beep(void) __naked {
 __asm
 ld a,#0
 out (0xa0),a
 ld a,(_reg_val)
 out (0xa1),a
 ld a,#1
 out (0xa0),a
 ld a,#1
 out (0xa1),a
 ld a,#7
 out (0xa0),a
 ld a,(_psg_mix)
 out (0xa1),a
 ld a,#8
 out (0xa0),a
 ld a,#10
 out (0xa1),a
 ret
 __endasm;
}
void silence(void) __naked {
 __asm
 ld a,#8
 out (0xa0),a
 xor a
 out (0xa1),a
 ret
 __endasm;
}
void sfx(u8 pitch) {reg_val=pitch;beep();sound_left=5;effect_kind=pitch==80?1:pitch>=190?3:2;effect_age=16;}
u8 random8(void) {rng^=rng<<7;rng^=rng>>9;rng^=rng<<8;return (u8)rng;}
u16 index(u8 x,u8 y) {return ((u16)y<<6)+x;}
u8 tile(u8 x,u8 y) {if(x>63 || y>63)return WALL;return map[index(x,y)];}
void put(u8 x,u8 y,u8 t) {map[index(x,y)]=t;}
u8 dist(u8 a,u8 b) {return a>b?a-b:b-a;}
void say(const char *s) {message=s;dirty=1;}
void text(u8 x,u8 y,const char *s) {u16 p=(u16)y*32+x;while(*s && x++<32 && p<768)screen[p++]=*s++;}
void number(u8 x,u8 y,u16 n,u8 digits) {u16 p=(u16)y*32+x+digits;while(digits--){screen[--p]='0'+n%10;n/=10;}}
void clear_screen(void) {u16 n;for(n=0;n<768;n++)screen[n]=32;}
void block(u8 x,u8 y,u8 t) {u16 p=(u16)y*32+x;u8 c=128+t*4;screen[p]=c;screen[p+1]=c+1;screen[p+32]=c+2;screen[p+33]=c+3;}
void present(void) {
 page^=1;vaddr=page?0x1c00:0x1800;vsrc=screen;vlen=768;upload();
 frame();reg_num=2;reg_val=page?7:6;regwrite();screen_count++;dirty=0;
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
void draw(void) {
 u8 x,y,wx,wy,t,i;u16 p;
 clear_screen();
 text(1,0,"MIKERO");text(10,0,"F");number(11,0,depth,2);text(14,0,"LV");number(16,0,level,2);text(21,0,"G");number(22,0,gold,3);
 text(1,1,"HP");number(4,1,hp,2);text(6,1,"/");number(7,1,maxhp,2);text(11,1,"POT");number(15,1,potions,2);text(20,1,"FOOD");number(25,1,food,3);
 for(x=0;x<32;x++){screen[64+x]=94+(x&3);screen[672+x]=94+(x&3);}
 for(y=0;y<9;y++)for(x=0;x<15;x++) {
  wx=px+x-7;wy=py+y-4;t=DARK;
  if(wx<64 && wy<64) {
   p=index(wx,wy);
   if(visible(wx,wy)) {
    seen[p>>3]|=1<<(p&7);t=map[p];
   } else if(seen[p>>3]&(1<<(p&7)))t=map[p]==WALL?OLDWALL:OLDFLOOR;
  }
  sight[y*15+x]=t!=DARK && t!=OLDWALL && t!=OLDFLOOR;
  block(x*2+1,y*2+3,t);
 }
 /* Overlay each visible actor once instead of searching 19 actors per cell. */
 for(i=0;i<enemy_count;i++)if(eh[i]) {
  x=ex[i]-px+7;y=ey[i]-py+4;
  if(x<15 && y<9 && sight[y*15+x])block(x*2+1,y*2+3,et[i]);
 }
 block(15,11,HERO);
 if(fx){block(fx_x,fx_y,SPARK);fx=0;}
 text(1,22,message);
 text(1,23,"SCORE");number(7,23,score,5);text(16,23,"BEST");number(22,23,high_score,5);
 if(mode>=2){
  for(y=7;y<19;y++)text(2,y,"                            ");
  text(4,8,mode==3?"30 FLOORS! WELL DONE!":"NICE ADVENTURE, MIKERO!");
  text(5,10,"FLOOR");number(12,10,depth,2);text(16,10,"/ 30");
  text(5,12,"SCORE");number(14,12,score,5);
  text(5,14,"BEST");number(14,14,high_score,5);
  text(5,15,"BEST RUN FLOOR");number(21,15,record_floor,2);
  text(5,17,"SPACE: TRY AGAIN");
 }
 present();
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
void load_floor(void) {
 u16 n;u8 t,i;
 anim_lock=1;
 variant=(seed+depth*13)%120;
 MEM(0x7000)=2+variant/4;
 vsrc=(const u8*)(0x8000+(u16)(variant&3)*4096);
 for(n=0;n<4096;n++)map[n]=vsrc[n];
 for(n=0;n<512;n++)seen[n]=0;
 enemy_count=0;
 for(n=0;n<4096;n++) {
  t=map[n];
  if(t>=32 && t<=36){
   i=enemy_count++;
   ex[i]=n&63;ey[i]=n>>6;et[i]=t-32+SLIME;eh[i]=2+(t-32)*2+depth/2;
   if(t==36){if(depth==30){et[i]=BOSS;eh[i]=24;}else{et[i]=KNIGHT;eh[i]=5+depth;}}
   map[n]=FLOOR;
  }
  if(t==CROWN && depth<30)map[n]=STAIRS;
 }
 px=5;py=5;foodclock=0;
 if(food<250)food=250;
 graphics();say(theme());sfx(40);
}
void new_game(void) {
 seed=(u8)rng;depth=1;hp=24;maxhp=24;level=1;xp=0;attack=3;potions=3;gold=0;
 score=0;music_pos=0;music_age=0;music_volume=0;music_write();
 food=400;mode=1;turns=0;turn_count=0;kill_count=0;heal_count=0;damage_count=0;
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
   say(et[i]==BOSS?"THE WARDEN STRIKES!":"AN ENEMY HITS YOU!");hurt(n);continue;
  }
  if(!visible(ex[i],ey[i]))continue;
  if(et[i]==SLIME && (turns&1))continue;
  if(et[i]==KNIGHT && (turns%3)==0)continue;
  nx=ex[i];ny=ey[i];
  if(dx && (!dy || (random8()&1)))nx+=ex[i]<px?1:-1;
  else if(dy)ny+=ey[i]<py?1:-1;
  n=tile(nx,ny);j=enemy_at(nx,ny);
  if(n!=WALL && n!=SHRINE && j==255 && (nx!=px || ny!=py)){ex[i]=nx;ey[i]=ny;}
 }
}
void tick_turn(void) {
 turns++;turn_count++;enemy_turn();
 if(mode!=1)return;
 if(food) {food--;if(++foodclock==14){foodclock=0;if(hp<maxhp)hp++;}}
 else {say("STARVING! FIND SOME FOOD.");hurt(1);}
 dirty=1;
}
void fight(u8 i) {
 u8 dmg=attack+(random8()&1);
 hit_x=120+(ex[i]-px)*16;hit_y=87+(ey[i]-py)*16;
 sfx(80);say("PAW PUNCH! PON!");
 if(eh[i]<=dmg) {
  eh[i]=0;kill_count++;add_score(et[i]==BOSS?200:20+(et[i]-SLIME)*10);xp+=et[i]==BOSS?12:2;gold+=gold<250?1:0;
  say("POOF! +XP +GOLD");
  if(et[i]==BOSS)say("KING: POOF! CLAIM THE CROWN!");
  if(xp>=5+level*3){xp=0;if(level<15){level++;maxhp+=2;attack++;}hp=maxhp;say("LEVEL UP! HEALTH RESTORED.");sfx(24);}
 }else eh[i]-=dmg;
 tick_turn();
 if(!eh[i] && mode==1){effect_kind=4;effect_age=32;}
}
void move_player(i8 dx,i8 dy) {
 u8 nx=px+dx,ny=py+dy,t=tile(nx,ny),i=enemy_at(nx,ny);
 if(t==WALL){say("A WALL BLOCKS THE WAY.");return;}
 if(i!=255){fight(i);return;}
 if(t==SHRINE){
  if(gold>=5 && hp<maxhp){gold-=5;hp=maxhp;say("KEEPER: YOUR LIGHT IS RESTORED.");sfx(30);}
  else say("KEEPER: FULL HEAL FOR 5 GOLD.");return;
 }
 px=nx;py=ny;walk_timer=16;music_step();say(theme());
 if(t==POTION){if(potions<99)potions++;put(px,py,FLOOR);say("POTION FOUND. Z TO DRINK.");sfx(35);}
 if(t==GOLD){add_score(25);gold=gold<246?gold+5:250;put(px,py,FLOOR);say("FIVE GOLD PIECES FOUND.");sfx(48);}
 if(t==CHEST){add_score(100);gold=gold<241?gold+10:250;if(potions<99)potions++;put(px,py,FLOOR);say("CHEST: 10 GOLD AND A POTION!");sfx(20);}
 if(t==FOOD){food+=100;if(food>999)food=999;put(px,py,FLOOR);say("FRESH RATIONS. +100 FOOD");sfx(55);}
 if(t==TRAP){put(px,py,FLOOR);say("SPIKES! YOU LOSE 3 HEALTH.");hurt(3);}
 if(t==STAIRS){add_score(200);depth++;load_floor();return;}
 if(t==CROWN){
  for(i=0;i<enemy_count;i++)if(et[i]==BOSS && eh[i]){say("MEET THE SLIME KING FIRST!");tick_turn();return;}
  add_score(3000);finish_run(3);say("ALL 30 FLOORS! WELL DONE!");sfx(16);return;
 }
 if(mode==1)tick_turn();
}
void heal(void) {
 if(!potions){say("NO POTIONS LEFT.");return;}
 if(hp==maxhp){say("YOUR HEALTH IS ALREADY FULL.");return;}
 potions--;heal_count++;hp+=16;if(hp>maxhp)hp=maxhp;say("POTION: 16 HEALTH RESTORED.");sfx(32);tick_turn();
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
 text(6,17,"SPACE / FIRE TO BEGIN");text(2,19,"30 FLOORS. YOUR BEST ADVENTURE");text(2,20,"MOVE TO ATTACK. Z/FIRE2 HEAL");text(4,23,"WALK A LITTLE. FIND A LOT.");present();
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
 ld a,#7
 out (0xa0),a
 in a,(0xa2)
 and #0xc0
 or #0x3c
 ld (_psg_mix),a
 ei
 ret
 __endasm;
}
void main(void) {
 hardware();music_volume=0;music_write();rng=0xace1;depth=0;graphics();
 title();
 install_animation();
 for(;;) {
  frame();if(sound_left && !--sound_left)silence();music_tick();input_read();
  input=keys?10:trigger?9:joy;
  if(mode==0){random8();if(input==9 && prev_input!=9){new_game();draw();}}
  else if(mode>=2){if(!input)repeat=0;if(input==9 && prev_input!=9){new_game();draw();}}
  else {
   if(!input)repeat=0;
   if(input && (input!=prev_input || !repeat)) {
    repeat=9;
    if(input==1)move_player(0,-1);if(input==3)move_player(1,0);if(input==5)move_player(0,1);if(input==7)move_player(-1,0);
    if(input==9){say("YOU WAIT AND LISTEN.");tick_turn();}
    if(input==10)heal();
   }else if(repeat)repeat--;
   if(dirty)draw();
  }
  prev_input=input;
 }
}
