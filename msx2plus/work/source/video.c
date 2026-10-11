/* SCREEN 5: page 0 circular world, page 1 stationary UI, page 2 atlas.
   HMMM copies only changed cells. V9958 registers move the world itself. */
u8 camera_x,camera_y,video_live,video_scene,video_busy,last_anim;
u8 cache[256],ui_cache[768],command[15],sat2[33],sprite_colors[128];
u8 vbank,csx,csy,cdx,cdy,cw,ch;
u16 csy16,cdy16;
u8 old_keyi[5];
/* Actor changes are committed only after the camera reaches its new cell. */
u8 actor_count,actor_cells[144],actor_tiles[144];
const u8 tile_base[32]={0,1,2,56,4,5,60,52,8,9,10,32,36,40,44,48,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31};
void video_install(void);
void video_sprites(void);
void vr(u8 r,u8 v){reg_num=r;reg_val=v;regwrite();}
void wait_vdp(void) __naked {
 __asm
001$:
 di
 ld a,#2
 out (0x99),a
 ld a,#0x8f
 out (0x99),a
 in a,(0x99)
 push af
 xor a
 out (0x99),a
 ld a,#0x8f
 out (0x99),a
 pop af
 ei
 and #1
 jr nz,001$
 ret
 __endasm;
}
void send_command(void) __naked {
 __asm
 call _wait_vdp
 di
 ld a,#32
 out (0x99),a
 ld a,#0x91
 out (0x99),a
 ld hl,#_command
 ld b,#15
 ld c,#0x9b
 otir
 ei
 ret
 __endasm;
}
void blit(void){
 command[0]=csx;command[1]=0;command[2]=(u8)csy16;command[3]=csy16>>8;
 command[4]=cdx;command[5]=0;command[6]=(u8)cdy16;command[7]=cdy16>>8;
 command[8]=cw;command[9]=0;command[10]=ch;command[11]=0;
 command[12]=0;command[13]=0;command[14]=0xd0;send_command();
}
void bitmap_upload(void) __naked {
 __asm
 di
 ld a,(_vbank)
 out (0x99),a
 ld a,#0x8e
 out (0x99),a
 ld hl,(_vaddr)
 ld a,l
 out (0x99),a
 ld a,h
 and #0x3f
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
void glyph(u8 c,u8 x,u8 y){
 if(rescue_pending && c>=128){
  u8 t=(c-128)>>2;
  if(t==7 || t==27 || t==28)c=100+(t==7?0:t==27?4:8)+(c&3);
 }
 if(c<128){csx=(c&31)*8;csy16=544+(u16)(c>>5)*8;}
 else {u8 t=(c-128)>>2;csx=(t&15)*16+(c&1)*8;csy16=512+(u16)(t>>4)*16+((c>>1)&1)*8;}
 cdx=x;cdy16=256+y;cw=8;ch=8;blit();
}
void bitmap_tile(u8 t,u8 x,u8 y){csx=(t&15)*16;csy16=t<32?512+(u16)(t>>4)*16:576+(u16)((t-32)>>4)*16;cdx=x;cdy16=y;cw=16;ch=16;blit();}
void video_clear(void){
 u16 i;for(i=0;i<256;i++)cache[i]=255;for(i=0;i<768;i++)ui_cache[i]=255;
 command[0]=command[1]=command[2]=command[3]=command[4]=command[5]=command[6]=command[7]=0;
 command[8]=0;command[9]=1;command[10]=0;command[11]=2;command[12]=0;command[13]=0;command[14]=0xc0;send_command();wait_vdp();
}
void graphics(void){
 u8 i;video_live=0;video_busy=1;anim_lock=1;anim_theme=depth?(depth-1)%8:0;
 vr(0,6);vr(7,0);vr(1,0xa2);vr(2,0x3f);vr(8,0x0a);vr(23,0);vr(25,0);vr(26,0);vr(27,0);
 MEM(0x7000)=1;vbank=4;vaddr=0;vsrc=(const u8*)0x8000;vlen=16384;bitmap_upload();
 vbank=5;vaddr=0x3800;vsrc=(const u8*)0xb000;vlen=832;bitmap_upload();
 vsrc=(const u8*)(0xb340+(u16)anim_theme*32);vr(16,0);
 for(i=0;i<32;i++){reg_val=vsrc[i];__asm
ld a,(_reg_val)
out (0x9a),a
__endasm;}
 for(i=0;i<128;i++)sprite_colors[i]=i<96?(i<16?2:i<32?5:i<48?7:i<64?9:i<80?10:15):15;
 vbank=5;vaddr=0x3400;vsrc=sprite_colors;vlen=128;bitmap_upload();
 vr(5,0xec);vr(11,2);vr(6,0x2f);video_clear();video_busy=0;
 vr(1,0xe2);MEM(0xf3e0)=0xe2; /* BIOS mirror: 16x16 sprites */
 anim_lock=0;
}
u8 pose_tile(u8 t){
 u8 f=(frame_tick>>3)&3;
 if(t>=11 && t<=15)return 32+(t-11)*4+f;
 if(t==7)return 52+f;if(t==3)return 56+f;if(t==6)return 60+f;return t;
}
void animate_world(void){
 u16 i;u8 f=(frame_tick>>3)&3,t;
 if(last_anim==f)return;last_anim=f;
 for(i=0;i<256;i++)if(cache[i]>=32 && cache[i]<64){t=(cache[i]&252)|f;cache[i]=t;bitmap_tile(t,(i&15)*16,(i>>4)*16);}
 wait_vdp();
}
void present(void){
 u8 x,y,t,wx,wy,k,n,tx,ty;u16 p;
 video_busy=1;
 if(mode==1 && !rescue_pending && !ending_pending){
  actor_count=0;
  {
   const u8 *cell=screen+97;
   u8 f=(frame_tick>>3)&3,old,base;
   u8 moving=video_scene==1 && (scroll_dx || scroll_dy);
   wy=py-4;
   for(y=0;y<9;y++,wy++,cell+=32){
    wx=px-7;k=((wy&15)<<4)|(wx&15);
    for(x=0;x<16;x++,wx++,cell+=2){
     t=x==15?DARK:(*cell-128)>>2;
     if(x==7 && y==4)t=(scroll_under[0]-128)>>2;
     base=tile_base[t];t=base>=32?base+f:base;old=cache[k];
     if(old!=t){
      if(moving && ((t>=32 && t<52) || (old>=32 && old<52))){
       actor_cells[actor_count]=k;actor_tiles[actor_count++]=t;
      }else{cache[k]=t;bitmap_tile(t,wx<<4,wy<<4);}
     }
     k=(k&240)|((k+1)&15);
    }
   }
  }
  /* Only the changing rows need a per-cell cache scan. */
  {
   const u8 *row;
   u8 *saved;
   u8 fresh=ui_cache[0]==255,dy;
   for(y=0;y<6;y++){
    if(!fresh && (y==0 || y==3 || y==5))continue;
    row=screen+(u16)(y==0?2:y==1?0:y==2?1:y==3?21:y==4?22:23)*32;
    saved=ui_cache+(u16)y*32;
    dy=y<3?144+y*8:y==3?172:y==4?182:196;
    for(x=0;x<32;x++,saved++){
     t=*row++;
     if(y==0 || y==3)t=x==0?117:x==31?118:116;
     else if(x==0 || x==31)t=x==0?120:121;
     else if(y==1 && (x==9 || x==19 || x==27))t=119;
     if(*saved!=t){*saved=t;glyph(t,x<<3,dy);}
    }
   }
   if(fresh){
    /* The rails and bottom rule persist until video_clear(). */
    command[4]=1;command[5]=0;command[6]=168;command[7]=1;
    command[8]=1;command[9]=0;command[10]=40;command[11]=0;
    command[12]=3;command[13]=0;command[14]=0x80;send_command();
    command[4]=255;send_command();
    command[4]=0;command[5]=0;command[6]=207;command[7]=1;
    command[8]=0;command[9]=1;command[10]=1;command[11]=0;
    command[12]=0x33;command[13]=0;command[14]=0xc0;send_command();
   }
  }
  wait_vdp();tx=px*16-120;ty=py*16-64;
  if(video_scene!=1){camera_x=tx;camera_y=ty;video_scene=1;video_live=1;}
  else if(scroll_dx || scroll_dy){
   for(n=0;n<2;n++){camera_x+=scroll_dx*8;camera_y+=scroll_dy*8;frame();video_sprites();}
  }
  camera_x=tx;camera_y=ty;video_live=1;video_sprites();
  for(n=0;n<actor_count;n++){
   k=actor_cells[n];t=actor_tiles[n];cache[k]=t;bitmap_tile(t,k<<4,k&240);
  }
  wait_vdp();
 }else{
  if(video_scene==1){
   for(p=0;p<768;p++)ui_cache[p]=255;
   /* Non-game screens use 192 rows; remove the extended footer. */
   command[4]=0;command[5]=0;command[6]=192;command[7]=1;
   command[8]=0;command[9]=1;command[10]=20;command[11]=0;
   command[12]=0;command[13]=0;command[14]=0xc0;send_command();wait_vdp();
  }
  video_live=0;video_scene=0;vr(0,6);vr(2,0x3f);vr(8,0x0a);vr(23,0);vr(25,0);vr(26,0);vr(27,0);
  for(y=0;y<24;y++)for(x=0;x<32;x++){p=(u16)y*32+x;t=screen[p];if(ui_cache[p]!=t){ui_cache[p]=t;glyph(t,x*8,y*8);}}
  wait_vdp();
 }
 video_busy=0;scroll_dx=0;scroll_dy=0;screen_count++;dirty=0;
}
void video_sprites(void){
 u8 i,pose=(frame_tick>>3)&3;
 for(i=0;i<6;i++){sat2[i*4]=camera_y+63;sat2[i*4+1]=120;sat2[i*4+2]=pose*24+i*4;sat2[i*4+3]=0;}
 if(effect_age){sat2[24]=camera_y+(effect_kind==1 || effect_kind==4?hit_y-24:64);sat2[25]=effect_kind==1 || effect_kind==4?hit_x:120;sat2[26]=effect_kind==4 && effect_age<20?100:96;sat2[27]=0;sat2[28]=216;}
 else sat2[24]=216;
 vbank=5;vaddr=0x3600;vsrc=sat2;vlen=29;bitmap_upload();
}
