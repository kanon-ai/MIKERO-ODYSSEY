/* SCREEN 5: page 0 circular world, page 1 stationary UI, page 2 atlas.
   HMMM copies only changed cells. V9958 registers move the world itself. */
u8 camera_x,camera_y,video_live,video_scene,video_busy,last_anim;
u8 cache[256],ui_cache[768],command[15],sat2[33],sprite_colors[128];
u8 vbank,csx,csy,cdx,cdy,cw,ch;
u16 csy16,cdy16;
u8 old_keyi[5];
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
  for(y=0;y<9;y++)for(x=0;x<16;x++){
   wx=px+x-7;wy=py+y-4;k=((wy&15)<<4)|(wx&15);
   if(x==15)t=DARK;
   else {p=(u16)(y*2+3)*32+x*2+1;t=(screen[p]-128)>>2;if(x==7 && y==4)t=(scroll_under[0]-128)>>2;}
   t=pose_tile(t);if(cache[k]!=t){cache[k]=t;bitmap_tile(t,wx*16,wy*16);}
  }
  /* Bottom panel: same stats/messages/keys, independent of the world. */
  for(y=0;y<6;y++)for(x=0;x<32;x++){
   p=(u16)(y==0?2:y==1?0:y==2?1:y==3?21:y==4?22:23)*32+x;t=screen[p];
   if(y==0 || y==3)t=x==0?117:x==31?118:116;
   else if(x==0 || x==31)t=x==0?120:121;
   else if(y==1 && (x==9 || x==19 || x==27))t=119;
   if(ui_cache[(u16)y*32+x]!=t){ui_cache[(u16)y*32+x]=t;glyph(t,x*8,y<3?144+y*8:y==3?172:y==4?182:196);}
  }
  /* Extend the side rails across the spaced footer rows. */
  command[4]=1;command[5]=0;command[6]=168;command[7]=1;
  command[8]=1;command[9]=0;command[10]=40;command[11]=0;
  command[12]=3;command[13]=0;command[14]=0x80;send_command();
  command[4]=255;send_command();
  /* Close the frame with four pixels below the key legend. */
  command[4]=0;command[5]=0;command[6]=207;command[7]=1;
  command[8]=0;command[9]=1;command[10]=1;command[11]=0;
  command[12]=0x33;command[13]=0;command[14]=0xc0;send_command();
  wait_vdp();tx=px*16-120;ty=py*16-64;
  if(video_scene!=1){camera_x=tx;camera_y=ty;video_scene=1;video_live=1;}
  else if(scroll_dx || scroll_dy){
   for(n=0;n<8;n++){camera_x+=scroll_dx*2;camera_y+=scroll_dy*2;frame();video_sprites();}
  }
  camera_x=tx;camera_y=ty;video_live=1;video_sprites();
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
