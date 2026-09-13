.module animation
.globl _install_animation,_anim_isr,_anim_done,_effect_patterns
.globl _old_hook,_anim_lock,_anim_div,_anim_clock,_anim_pose,_anim_oldpose
.globl _anim_oldphase,_anim_theme,_anim_updates,_walk_timer,_effect_kind,_effect_age
.globl _anim_ptr,_anim_target,_anim_size,_anim_banks,_anim_item,_anim_sat
.globl _mode,_hit_x,_hit_y,_music_age
.area _CODE
_install_animation::
 di
 ld hl,#0xfd9f
 ld de,#_old_hook
 ld bc,#5
 ldir
 ld a,#0xc3
 ld (0xfd9f),a
 ld hl,#_anim_isr
 ld (0xfda0),hl
 xor a
 ld (0xfda2),a
 ld (0xfda3),a
 ld a,#255
 ld (_anim_oldpose),a
 ld (_anim_oldphase),a
 ei
 ret

; BIOS H.TIMI callback: all registers preserved, ROM data reads protected
; by anim_lock. Never calls C or touches gameplay RNG / turns / HP.
_anim_isr::
 push af
 push bc
 push de
 push hl
 push ix
 push iy
 call _old_hook
 ld a,(_anim_lock)
 or a
 jp nz,_anim_done
 ld a,(_anim_div)
 inc a
 ld (_anim_div),a
 and #1
 jp nz,_anim_done
 ld a,(_music_age)
 or a
 jr z,music_age_done
 dec a
 ld (_music_age),a
music_age_done:
 ld a,(_mode)
 cp #2
 jr c,anim_active
 ld a,#208
 ld (_anim_sat),a
 ld hl,#_anim_sat
 ld de,#0x1b00
 ld b,#1
 call anim_upload
 jp _anim_done
anim_active:
 ld a,#1
 ld (0x7000),a
 ld hl,#_anim_clock
 inc (hl)
 ld hl,(_anim_updates)
 inc hl
 ld (_anim_updates),hl
 ld a,(_walk_timer)
 or a
 jr z,pose_idle
 dec a
 ld (_walk_timer),a
 ld a,(_anim_clock)
 rrca
 rrca
 and #3
 add a,#4
 jr pose_ready
pose_idle:
 ld a,(_anim_clock)
 rrca
 rrca
 rrca
 rrca
 and #3
pose_ready:
 ld (_anim_pose),a
environment:
 ld a,(_anim_clock)
 rrca
 rrca
 and #7
 ld b,a
 ld a,(_anim_oldphase)
 cp b
 jr z,enemies
 ld a,b
 ld (_anim_oldphase),a
 ld l,a
 ld h,#0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld a,(_anim_theme)
 add a,a
 add a,a
 add a,#0x95
 ld d,a
 ld e,#0
 add hl,de
 ld de,#0x0400
 ld a,#64
 ld (_anim_size),a
 call anim_copy_three
enemies:
 ld a,(_anim_clock)
 and #3
 add a,#0xb5
 ld h,a
 ld a,(_anim_clock)
 and #12
 rlca
 rlca
 rlca
 rlca
 ld l,a
 ld a,(_anim_clock)
 and #3
 rlca
 rlca
 rlca
 rlca
 rlca
 add a,#0x60
 ld e,a
 ld d,#5
 ld a,#32
 ld (_anim_size),a
 call anim_copy_three
items:
 ld a,(_anim_clock)
 and #1
 jr z,finish_visuals
 ld a,(_anim_item)
 inc a
 cp #7
 jr c,item_ok
 xor a
item_ok:
 ld (_anim_item),a
 ld e,a
 ld d,#0
 ld hl,#item_types
 add hl,de
 ld l,(hl)
 ld h,#0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld de,#0x0400
 add hl,de
 ex de,hl
 ld a,(_anim_item)
 add a,#0xb9
 ld h,a
 ld a,(_anim_clock)
 rrca
 and #12
 rlca
 rlca
 rlca
 rlca
 ld l,a
 call anim_copy_three
finish_visuals:
 call animate_cat
 call anim_sprites
_anim_done::
 pop iy
 pop ix
 pop hl
 pop de
 pop bc
 pop af
 ret

; HL source, DE VRAM address, B bytes. Each data write is >=30 T states
; apart, including active display; no unsafe OTIR burst is used.
anim_upload:
 ld a,e
 out (0x99),a
 ld a,d
 or #0x40
 out (0x99),a
 ld c,#0x98
anim_upload_loop:
 outi
 nop
 jp nz,anim_upload_loop
 ret

; A logical tile rewrite changes every on-screen occurrence, in all three
; SCREEN 2 thirds. Contiguous pattern bytes followed by color bytes.
anim_copy_three:
 ld (_anim_ptr),hl
 ld (_anim_target),de
 ld a,#3
 ld (_anim_banks),a
copy_loop:
 ld hl,(_anim_ptr)
 ld de,(_anim_target)
 ld a,(_anim_size)
 ld b,a
 call anim_upload
 ld de,(_anim_target)
 ld a,d
 add a,#0x20
 ld d,a
 ld a,(_anim_size)
 ld b,a
 call anim_upload
 ld hl,(_anim_target)
 ld de,#0x0800
 add hl,de
 ld (_anim_target),hl
 ld hl,#_anim_banks
 dec (hl)
 jr nz,copy_loop
 ret

animate_cat:
 ld a,(_anim_pose)
 ld b,a
 ld a,(_anim_oldpose)
 cp b
 ret z
 ld a,b
 ld (_anim_oldpose),a
 ld l,a
 ld h,#0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld de,#0x9000
 add hl,de
 ld de,#0x0d40
 ld b,#32
 call anim_upload
 ld de,#0x2d40
 ld b,#32
 call anim_upload
 ld a,(_anim_pose)
 ld l,a
 ld h,#0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld d,h
 ld e,l
 add hl,hl
 add hl,de
 ld de,#0x9200
 add hl,de
 ld de,#0x3800
 ld b,#96
 call anim_upload
 ret

anim_sprites:
 ld hl,#_anim_sat
 ld a,(_mode)
 or a
 ld d,#87
 ld e,#120
 jr nz,cat_location
 ld d,#79
 ld e,#104
cat_location:
 ld b,#3
 ld c,#0
cat_loop:
 ld (hl),d
 inc hl
 ld (hl),e
 inc hl
 ld (hl),c
 inc hl
 ld a,c
 or a
 ld a,#15
 jr z,cat_color
 ld a,c
 cp #4
 ld a,#3
 jr z,cat_color
 ld a,#10
cat_color:
 ld (hl),a
 inc hl
 inc c
 inc c
 inc c
 inc c
 djnz cat_loop
 ld a,(_mode)
 or a
 jr nz,effect_sprite
 jp ambient
effect_sprite:
 ld a,(_effect_age)
 or a
 jr z,no_effect
 dec a
 ld (_effect_age),a
 ld a,(_effect_kind)
 cp #4
 jr z,effect_hit
 cp #1
 jr nz,effect_center
effect_hit:
 ld a,(_hit_y)
 ld (hl),a
 inc hl
 ld a,(_hit_x)
 ld (hl),a
 jr effect_pattern
effect_center:
 ld (hl),#87
 inc hl
 ld (hl),#120
effect_pattern:
 inc hl
 ld a,(_effect_kind)
 cp #4
 jr nz,normal_effect_pattern
 ld a,(_effect_age)
 cp #16
 jr nc,paw_before_smoke
 and #12
 ld b,a
 ld a,#72
 sub b
 jr effect_pattern_ready
paw_before_smoke:
 and #12
 ld b,a
 ld a,#24
 sub b
 jr effect_pattern_ready
normal_effect_pattern:
 ld a,(_effect_age)
 and #12
 ld b,a
 ld a,#24
 sub b
 ld b,a
 ld a,(_effect_kind)
 cp #1
 ld a,b
 jr z,effect_pattern_ready
 add a,#16
effect_pattern_ready:
 ld (hl),a
 inc hl
 ld a,(_effect_kind)
 cp #3
 ld a,#9
 jr z,effect_color
 ld a,#15
effect_color:
 ld (hl),a
 inc hl
 jr finish_game_sat
no_effect:
 ld (hl),#217
 inc hl
 ld (hl),#0
 inc hl
 ld (hl),#12
 inc hl
 ld (hl),#15
 inc hl
finish_game_sat:
 ld (hl),#208
 ld b,#17
 jp send_sat
ambient:
 ld de,#ambient_positions
 ld b,#6
ambient_loop:
 ld a,(de)
 ld (hl),a
 inc hl
 inc de
 ld a,(_anim_clock)
 and #15
 ld c,a
 ld a,(de)
 add a,c
 ld (hl),a
 inc hl
 inc de
 push de
 ld a,(_anim_theme)
 and #3
 add a,a
 add a,a
 add a,#44
 ld (hl),a
 inc hl
 ld a,(_anim_theme)
 ld e,a
 ld d,#0
 push hl
 ld hl,#ambient_colors
 add hl,de
 ld a,(hl)
 pop hl
 ld (hl),a
 inc hl
 pop de
 djnz ambient_loop
 ld (hl),#208
 ld b,#37
send_sat:
 ld hl,#_anim_sat
 ld de,#0x1b00
 jp anim_upload
item_types:
.db 2,3,4,5,6,7,9
ambient_positions:
.db 26,32,46,184,66,64,110,168,130,24,150,208
ambient_colors:
.db 10,13,7,15,9,10,7,13
.include "visual_data.inc"
