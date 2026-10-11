.module video
.globl _video_install,_video_live,_camera_x,_camera_y,_old_keyi
.globl _old_hook,_frame_tick,_anim_div,_effect_age,_anim_clock
.globl _anim_isr,_anim_done
.globl _mode,_music_age,_music_pos,_music_frag,_music_volume,_music_period,_sound_left
.globl _music_step,_music_reset,_beep,_sfx_kind,_sfx_next,_psg_mix
.area _CODE
_video_install::
 di
 ld hl,#0xfd9a
 ld de,#_old_keyi
 ld bc,#5
 ldir
 ld a,#0xc3
 ld (0xfd9a),a
 ld hl,#line_irq
 ld (0xfd9b),hl
 ld hl,#0xfd9f
 ld de,#_old_hook
 ld bc,#5
 ldir
 ld a,#0xc3
 ld (0xfd9f),a
 ld hl,#_anim_isr
 ld (0xfda0),hl
 ei
 ret
line_irq:
 push af
 ld a,#1
 out (0x99),a
 ld a,#0x8f
 out (0x99),a
 in a,(0x99)
 bit 0,a
 jr z,line_done
 ld a,(_video_live)
 or a
 jr z,line_done
 ; Blank during the scroll/page transition to hide mixed scanlines.
 ld a,#0xa2
 out (0x99),a
 ld a,#0x81
 out (0x99),a
 ld a,#6
 out (0x99),a
 ld a,#0x80
 out (0x99),a
 xor a
 out (0x99),a
 ld a,#0x97
 out (0x99),a
 ld a,#0x3f
 out (0x99),a
 ld a,#0x82
 out (0x99),a
 xor a
 out (0x99),a
 ld a,#0x99
 out (0x99),a
 xor a
 out (0x99),a
 ld a,#0x9a
 out (0x99),a
 xor a
 out (0x99),a
 ld a,#0x9b
 out (0x99),a
 ld a,#0x0a
 out (0x99),a
 ld a,#0x88
 out (0x99),a
 ld a,#0xe2
 out (0x99),a
 ld a,#0x81
 out (0x99),a
line_done:
 xor a
 out (0x99),a
 ld a,#0x8f
 out (0x99),a
 pop af
 jp _old_keyi
_anim_isr::
 push af
 push bc
 push de
 push hl
 push ix
 push iy
 call _old_hook
 ld hl,#_frame_tick
 inc (hl)
 ld a,(_video_live)
 or a
 jr z,no_scroll
 ld a,#0x1f
 out (0x99),a
 ld a,#0x82
 out (0x99),a
 ld a,(_camera_y)
 out (0x99),a
 ld a,#0x97
 out (0x99),a
 ld a,(_camera_y)
 add a,#143
 out (0x99),a
 ld a,#0x93
 out (0x99),a
 ld a,#0x16
 out (0x99),a
 ld a,#0x80
 out (0x99),a
 ld a,#2
 out (0x99),a
 ld a,#0x99
 out (0x99),a
 ld a,(_camera_x)
 add a,#7
 rrca
 rrca
 rrca
 and #31
 out (0x99),a
 ld a,#0x9a
 out (0x99),a
 ld a,(_camera_x)
 neg
 and #7
 out (0x99),a
 ld a,#0x9b
 out (0x99),a
 ld a,#8
 out (0x99),a
 ld a,#0x88
 out (0x99),a
no_scroll:
 ld hl,#_anim_clock
 inc (hl)
 ld a,(_anim_div)
 inc a
 ld (_anim_div),a
 and #1
 jr nz,_anim_done
 call sfx_tick
 call music_tick
 ld a,(_effect_age)
 or a
 jr z,_anim_done
 dec a
 ld (_effect_age),a
_anim_done::
 pop iy
 pop ix
 pop hl
 pop de
 pop bc
 pop af
 ret

; PSG B carries the melody; C follows in a moving harmony.
; Only a real action starts a fragment. No queue can play on after stopping.
_music_reset::
 di
 ld a,#9
 out (0xa0),a
 xor a
 out (0xa1),a
 ld a,#10
 out (0xa0),a
 xor a
 out (0xa1),a
 ld c,#0
 ld a,#0x0e
 call fm_write
 xor a
 ld (_music_pos),a
 ld (_music_age),a
 ld (_music_frag),a
 call music_render
 ei
 ret
_music_step::
 di
 call music_silent
 ld a,(_music_pos)
 ld (_music_frag),a
 inc a
 and #63
 ld (_music_pos),a
 ld a,#8
 ld (_music_age),a
 call music_render
 ei
 ret
music_tick:
 ld a,(_mode)
 cp #1
 jr z,music_running
 xor a
 ld (_music_age),a
 jr music_render
music_running:
 ld a,(_music_age)
 or a
 ret z
 dec a
 ld (_music_age),a
music_render:
 ld a,(_music_age)
 or a
 jp z,music_silent
 ld b,a
 ld a,#8
 sub b
 ld e,a
 ld d,#0
 ld hl,#music_soft_envelope
 ld a,(_music_frag)
 cp #16
 jr c,music_check_triplet
 cp #48
 jr c,music_envelope_ready
music_check_triplet:
 and #7
 cp #1
 jr nz,music_envelope_ready
 ld hl,#music_triplet_envelope
music_envelope_ready:
 add hl,de
 ld a,(hl)
 ld b,a
 ld a,(_sound_left)
 or a
 ld a,b
 jr z,music_volume_ready
 cp #6
 jr c,music_volume_ready
 ld a,#5
music_volume_ready:
 ld (_music_volume),a
 ld a,(_music_frag)
 add a,a
 ld e,a
 ld d,#0
 ld hl,#fm_melody
 add hl,de
 ld a,#0x10
 ld c,(hl)
 call fm_write
 inc hl
 ld b,(hl)
 ld a,#0x20
 call fm_key
 ld a,#0x30
 ld b,#0xc0
 call fm_volume
 ld a,(_music_frag)
 add a,a
 ld e,a
 ld d,#0
 ld hl,#fm_harmony
 add hl,de
 ld a,#0x11
 ld c,(hl)
 call fm_write
 inc hl
 ld b,(hl)
 ld a,#0x21
 call fm_key
 ld a,#0x31
 ld b,#0x44
 call fm_volume
 ld a,(_music_frag)
 add a,a
 ld e,a
 ld d,#0
 ld hl,#fm_bass
 add hl,de
 ld a,#0x12
 ld c,(hl)
 call fm_write
 inc hl
 ld b,(hl)
 ld a,#0x22
 call fm_key
 ld a,#0x32
 ld b,#0xe5
 jp fm_volume
music_silent:
 xor a
 ld (_music_volume),a
 ld c,a
 ld a,#0x20
 call fm_write
 ld a,#0x21
 call fm_write
 ld a,#0x22
 call fm_write
 ld c,#0xcf
 ld a,#0x30
 call fm_write
 ld c,#0x4f
 ld a,#0x31
 call fm_write
 ld c,#0xef
 ld a,#0x32
 jp fm_write
fm_key:
 push af
 ld a,(_music_volume)
 or a
 ld c,b
 jr z,fm_key_ready
 set 4,c
fm_key_ready:
 pop af
 jp fm_write
fm_volume:
 push af
 ld a,(_music_volume)
 or a
 jr z,fm_muted
 ld c,a
 ld a,#9
 sub c
 ld c,a
 ld a,b
 and #15
 add a,c
 cp #15
 jr c,fm_vol_ready
fm_muted:
 ld a,#15
fm_vol_ready:
 ld c,a
 ld a,b
 and #0xf0
 or c
 ld c,a
 pop af
 jp fm_write
; Z80-safe OPLL address/data delays; no turbo R timer dependency.
fm_write:
 out (0x7c),a
 nop
 nop
 nop
 ld a,c
 out (0x7d),a
 push bc
 ld b,#7
fm_delay:
 djnz fm_delay
 pop bc
 ret
; +6 PSG steps (table maximum 9 -> 15), preserving exact silence.
psg_volume_gain:
 or a
 ret z
 add a,#6
 ret
; Four short units per bar. Repeated attacks preserve the march's triplet.
; Historical upper melody D5/E5/F#5; the held E is re-articulated at a turn.
; 64 action units: march motif, original running variation, return.
music_notes:
.dw 191,191,170,170,152,191,170,170,191,191,170,170,152,191,170,170,226,191,170,191,214,226,214,191,214,226,254,226,214,191,170,152,170,191,170,152,143,152,143,128,143,152,170,191,214,170,191,191,191,191,170,170,152,191,170,170,152,152,143,143,128,152,143,191
music_harmony_notes:
.dw 226,226,214,214,191,226,214,214,226,226,214,214,191,226,214,214,285,226,214,226,254,285,254,226,254,285,303,285,254,226,214,191,214,226,214,191,170,191,170,152,170,191,214,226,254,214,226,226,226,226,214,214,191,226,214,214,191,191,170,170,152,191,170,226
music_soft_envelope:
.db 8,5,2,0,0,0,0,0
music_triplet_envelope:
.db 8,0,8,0,8,2,0,0

; A-channel effects have their own pitch and amplitude envelopes.
_beep::
 di
 ld a,(_sfx_next)
 ld (_sfx_kind),a
 ld a,#8
 ld (_sound_left),a
 ld a,#7
 out (0xa0),a
 ld a,(_psg_mix)
 out (0xa1),a
 call sfx_render
 ei
 ret
sfx_tick:
 ld a,(_sound_left)
 or a
 ret z
 dec a
 ld (_sound_left),a
sfx_render:
 ld a,(_sound_left)
 or a
 jr z,sfx_silent
 ld b,a
 ld a,#8
 sub b
 ld e,a
 ld a,(_sfx_kind)
 add a,a
 add a,a
 add a,a
 add a,e
 ld e,a
 ld d,#0
 ld hl,#sfx_volumes
 add hl,de
 ld c,(hl)
 ld hl,#sfx_periods
 sla e
 rl d
 add hl,de
 ld b,(hl)
 inc hl
 ld e,(hl)
 xor a
 out (0xa0),a
 ld a,b
 out (0xa1),a
 ld a,#1
 out (0xa0),a
 ld a,e
 out (0xa1),a
 jr sfx_volume
sfx_silent:
 ld c,#0
sfx_volume:
 ld a,#8
 out (0xa0),a
 ld a,c
 call psg_volume_gain
 out (0xa1),a
 ret
sfx_periods:
.dw 160,220,320,450,450,450,450,450
.dw 143,143,113,113,95,95,71,71
.dw 170,170,143,143,113,113,113,113
.dw 214,214,170,170,214,214,214,214
.dw 300,340,390,440,440,440,440,440
.dw 191,191,152,152,128,128,95,95
.dw 285,285,226,226,191,191,191,191
.dw 191,191,152,152,128,128,95,95
sfx_volumes:
.db 9,7,4,1,0,0,0,0
.db 8,3,8,3,7,3,6,0
.db 8,3,8,3,7,4,2,0
.db 7,5,7,5,4,3,1,0
.db 6,5,3,2,0,0,0,0
.db 8,3,8,3,8,3,7,0
.db 7,3,7,3,6,4,2,0
.db 8,3,8,3,8,3,7,0


; Rendering-only precomputed Bresenham rays; gameplay visibility is unchanged.
.globl _view_visible,_view_origin
_view_visible::
 ld l,a
 ld h,#0
 add hl,hl
 ld de,#view_rays
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 ld a,(hl)
 inc hl
 cp #255
 jr z,view_blocked
 or a
 jr z,view_clear
 ld b,a
view_ray_loop:
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc hl
 push hl
 ld hl,(_view_origin)
 add hl,de
 ld a,(hl)
 pop hl
 cp #1
 jr z,view_blocked
 djnz view_ray_loop
view_clear:
 ld a,#1
 ret
view_blocked:
 xor a
 ret
view_rays:
.dw view_ray_0,view_ray_1,view_ray_2,view_ray_3,view_ray_4,view_ray_5,view_ray_6,view_ray_7,view_ray_8,view_ray_9,view_ray_10,view_ray_11,view_ray_12,view_ray_13,view_ray_14,view_ray_15,view_ray_16,view_ray_17,view_ray_18,view_ray_19,view_ray_20,view_ray_21,view_ray_22,view_ray_23,view_ray_24,view_ray_25,view_ray_26,view_ray_27,view_ray_28,view_ray_29,view_ray_30,view_ray_31,view_ray_32,view_ray_33,view_ray_34,view_ray_35,view_ray_36,view_ray_37,view_ray_38,view_ray_39,view_ray_40,view_ray_41,view_ray_42,view_ray_43,view_ray_44,view_ray_45,view_ray_46,view_ray_47,view_ray_48,view_ray_49,view_ray_50,view_ray_51,view_ray_52,view_ray_53,view_ray_54,view_ray_55,view_ray_56,view_ray_57,view_ray_58,view_ray_59,view_ray_60,view_ray_61,view_ray_62,view_ray_63,view_ray_64,view_ray_65,view_ray_66,view_ray_67,view_ray_68,view_ray_69,view_ray_70,view_ray_71,view_ray_72,view_ray_73,view_ray_74,view_ray_75,view_ray_76,view_ray_77,view_ray_78,view_ray_79,view_ray_80,view_ray_81,view_ray_82,view_ray_83,view_ray_84,view_ray_85,view_ray_86,view_ray_87,view_ray_88,view_ray_89,view_ray_90,view_ray_91,view_ray_92,view_ray_93,view_ray_94,view_ray_95,view_ray_96,view_ray_97,view_ray_98,view_ray_99,view_ray_100,view_ray_101,view_ray_102,view_ray_103,view_ray_104,view_ray_105,view_ray_106,view_ray_107,view_ray_108,view_ray_109,view_ray_110,view_ray_111,view_ray_112,view_ray_113,view_ray_114,view_ray_115,view_ray_116,view_ray_117,view_ray_118,view_ray_119,view_ray_120,view_ray_121,view_ray_122,view_ray_123,view_ray_124,view_ray_125,view_ray_126,view_ray_127,view_ray_128,view_ray_129,view_ray_130,view_ray_131,view_ray_132,view_ray_133,view_ray_134
view_ray_0:
.db 255
view_ray_1:
.db 255
view_ray_2:
.db 4
.dw 65471,65406,65405,65340
view_ray_3:
.db 3
.dw 65471,65406,65341
view_ray_4:
.db 3
.dw 65471,65406,65342
view_ray_5:
.db 3
.dw 65471,65407,65342
view_ray_6:
.db 3
.dw 65472,65407,65343
view_ray_7:
.db 3
.dw 65472,65408,65344
view_ray_8:
.db 3
.dw 65472,65409,65345
view_ray_9:
.db 3
.dw 65473,65409,65346
view_ray_10:
.db 3
.dw 65473,65410,65346
view_ray_11:
.db 3
.dw 65473,65410,65347
view_ray_12:
.db 4
.dw 65473,65410,65411,65348
view_ray_13:
.db 255
view_ray_14:
.db 255
view_ray_15:
.db 255
view_ray_16:
.db 5
.dw 65471,65470,65405,65404,65339
view_ray_17:
.db 4
.dw 65471,65470,65405,65404
view_ray_18:
.db 3
.dw 65471,65406,65405
view_ray_19:
.db 2
.dw 65471,65406
view_ray_20:
.db 2
.dw 65471,65407
view_ray_21:
.db 2
.dw 65472,65407
view_ray_22:
.db 2
.dw 65472,65408
view_ray_23:
.db 2
.dw 65472,65409
view_ray_24:
.db 2
.dw 65473,65409
view_ray_25:
.db 2
.dw 65473,65410
view_ray_26:
.db 3
.dw 65473,65410,65411
view_ray_27:
.db 4
.dw 65473,65474,65411,65412
view_ray_28:
.db 5
.dw 65473,65474,65411,65412,65349
view_ray_29:
.db 255
view_ray_30:
.db 6
.dw 65535,65470,65469,65468,65467,65402
view_ray_31:
.db 5
.dw 65535,65470,65469,65468,65403
view_ray_32:
.db 4
.dw 65535,65470,65469,65404
view_ray_33:
.db 3
.dw 65471,65470,65405
view_ray_34:
.db 2
.dw 65471,65470
view_ray_35:
.db 1
.dw 65471
view_ray_36:
.db 1
.dw 65471
view_ray_37:
.db 1
.dw 65472
view_ray_38:
.db 1
.dw 65473
view_ray_39:
.db 1
.dw 65473
view_ray_40:
.db 2
.dw 65473,65474
view_ray_41:
.db 3
.dw 65473,65474,65411
view_ray_42:
.db 4
.dw 1,65474,65475,65412
view_ray_43:
.db 5
.dw 1,65474,65475,65476,65413
view_ray_44:
.db 6
.dw 1,65474,65475,65476,65477,65414
view_ray_45:
.db 6
.dw 65535,65534,65533,65468,65467,65466
view_ray_46:
.db 5
.dw 65535,65534,65469,65468,65467
view_ray_47:
.db 4
.dw 65535,65534,65469,65468
view_ray_48:
.db 3
.dw 65535,65470,65469
view_ray_49:
.db 2
.dw 65535,65470
view_ray_50:
.db 1
.dw 65471
view_ray_51:
.db 0
view_ray_52:
.db 0
view_ray_53:
.db 0
view_ray_54:
.db 1
.dw 65473
view_ray_55:
.db 2
.dw 1,65474
view_ray_56:
.db 3
.dw 1,65474,65475
view_ray_57:
.db 4
.dw 1,2,65475,65476
view_ray_58:
.db 5
.dw 1,2,65475,65476,65477
view_ray_59:
.db 6
.dw 1,2,3,65476,65477,65478
view_ray_60:
.db 6
.dw 65535,65534,65533,65532,65531,65530
view_ray_61:
.db 5
.dw 65535,65534,65533,65532,65531
view_ray_62:
.db 4
.dw 65535,65534,65533,65532
view_ray_63:
.db 3
.dw 65535,65534,65533
view_ray_64:
.db 2
.dw 65535,65534
view_ray_65:
.db 1
.dw 65535
view_ray_66:
.db 0
view_ray_67:
.db 0
view_ray_68:
.db 0
view_ray_69:
.db 1
.dw 1
view_ray_70:
.db 2
.dw 1,2
view_ray_71:
.db 3
.dw 1,2,3
view_ray_72:
.db 4
.dw 1,2,3,4
view_ray_73:
.db 5
.dw 1,2,3,4,5
view_ray_74:
.db 6
.dw 1,2,3,4,5,6
view_ray_75:
.db 6
.dw 65535,65534,65533,60,59,58
view_ray_76:
.db 5
.dw 65535,65534,61,60,59
view_ray_77:
.db 4
.dw 65535,65534,61,60
view_ray_78:
.db 3
.dw 65535,62,61
view_ray_79:
.db 2
.dw 65535,62
view_ray_80:
.db 1
.dw 63
view_ray_81:
.db 0
view_ray_82:
.db 0
view_ray_83:
.db 0
view_ray_84:
.db 1
.dw 65
view_ray_85:
.db 2
.dw 1,66
view_ray_86:
.db 3
.dw 1,66,67
view_ray_87:
.db 4
.dw 1,2,67,68
view_ray_88:
.db 5
.dw 1,2,67,68,69
view_ray_89:
.db 6
.dw 1,2,3,68,69,70
view_ray_90:
.db 6
.dw 65535,62,61,60,59,122
view_ray_91:
.db 5
.dw 65535,62,61,60,123
view_ray_92:
.db 4
.dw 65535,62,61,124
view_ray_93:
.db 3
.dw 63,62,125
view_ray_94:
.db 2
.dw 63,62
view_ray_95:
.db 1
.dw 63
view_ray_96:
.db 1
.dw 63
view_ray_97:
.db 1
.dw 64
view_ray_98:
.db 1
.dw 65
view_ray_99:
.db 1
.dw 65
view_ray_100:
.db 2
.dw 65,66
view_ray_101:
.db 3
.dw 65,66,131
view_ray_102:
.db 4
.dw 1,66,67,132
view_ray_103:
.db 5
.dw 1,66,67,68,133
view_ray_104:
.db 6
.dw 1,66,67,68,69,134
view_ray_105:
.db 255
view_ray_106:
.db 5
.dw 63,62,125,124,187
view_ray_107:
.db 4
.dw 63,62,125,124
view_ray_108:
.db 3
.dw 63,126,125
view_ray_109:
.db 2
.dw 63,126
view_ray_110:
.db 2
.dw 63,127
view_ray_111:
.db 2
.dw 64,127
view_ray_112:
.db 2
.dw 64,128
view_ray_113:
.db 2
.dw 64,129
view_ray_114:
.db 2
.dw 65,129
view_ray_115:
.db 2
.dw 65,130
view_ray_116:
.db 3
.dw 65,130,131
view_ray_117:
.db 4
.dw 65,66,131,132
view_ray_118:
.db 5
.dw 65,66,131,132,197
view_ray_119:
.db 255
view_ray_120:
.db 255
view_ray_121:
.db 255
view_ray_122:
.db 4
.dw 63,126,125,188
view_ray_123:
.db 3
.dw 63,126,189
view_ray_124:
.db 3
.dw 63,126,190
view_ray_125:
.db 3
.dw 63,127,190
view_ray_126:
.db 3
.dw 64,127,191
view_ray_127:
.db 3
.dw 64,128,192
view_ray_128:
.db 3
.dw 64,129,193
view_ray_129:
.db 3
.dw 65,129,194
view_ray_130:
.db 3
.dw 65,130,194
view_ray_131:
.db 3
.dw 65,130,195
view_ray_132:
.db 4
.dw 65,130,131,196
view_ray_133:
.db 255
view_ray_134:
.db 255
; Native name-table renderer. Same rays and explored bits as the C renderer.
; Bounds are checked before map reads; IX/IY hold output streams.
.globl _render_view,_render_x,_render_y,_render_cell,_render_cols,_render_rows,_render_map
.globl _map,_seen,_sight,_screen,_px,_py
_render_view::
 push ix
 push iy
 ld ix,#_screen+97
 ld iy,#_sight
 ld hl,(_view_origin)
 ld de,#-263
 add hl,de
 ld (_render_map),hl
 ld a,(_py)
 sub #4
 ld (_render_y),a
 xor a
 ld (_render_cell),a
 ld a,#9
 ld (_render_rows),a
render_row:
 ld a,(_px)
 sub #7
 ld (_render_x),a
 ld a,#15
 ld (_render_cols),a
render_cell_loop:
 ld 0(iy),#0
 ld a,(_render_y)
 cp #64
 jr nc,render_dark
 ld a,(_render_x)
 cp #64
 jr nc,render_dark
 ld a,(_render_cell)
 call _view_visible
 or a
 jr z,render_hidden
 call render_seen_address
 ld a,(hl)
 or c
 ld (hl),a
 ld 0(iy),#1
 ld hl,(_render_map)
 ld a,(hl)
 jr render_store
render_hidden:
 call render_seen_address
 ld a,(hl)
 and c
 jr z,render_dark
 ld hl,(_render_map)
 ld a,(hl)
 cp #1
 ld a,#17
 jr z,render_store
 inc a
 jr render_store
render_dark:
 ld a,#16
render_store:
 add a,a
 add a,a
 add a,#128
 ld 0(ix),a
 inc a
 ld 1(ix),a
 inc a
 ld 32(ix),a
 inc a
 ld 33(ix),a
 inc ix
 inc ix
 inc iy
 ld hl,(_render_map)
 inc hl
 ld (_render_map),hl
 ld hl,#_render_x
 inc (hl)
 ld hl,#_render_cell
 inc (hl)
 ld hl,#_render_cols
 dec (hl)
 jp nz,render_cell_loop
 ld de,#34
 add ix,de
 ld hl,(_render_map)
 ld de,#49
 add hl,de
 ld (_render_map),hl
 ld hl,#_render_y
 inc (hl)
 ld hl,#_render_rows
 dec (hl)
 jp nz,render_row
 pop iy
 pop ix
 ret
render_seen_address:
 ld hl,(_render_map)
 ld de,#_map
 or a
 sbc hl,de
 ld a,l
 and #7
 ld e,a
 ld d,#0
 push hl
 ld hl,#render_bits
 add hl,de
 ld c,(hl)
 pop hl
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 ld de,#_seen
 add hl,de
 ret
render_bits:
.db 1,2,4,8,16,32,64,128

fm_melody:
.db 130,9,130,9,178,9,178,9,229,9,130,9,178,9,178,9,130,9,130,9,178,9,178,9,229,9,130,9,178,9,178,9,70,9,130,9,178,9,130,9,89,9,70,9,89,9,130,9,89,9,70,9,34,9,70,9,89,9,130,9,178,9,229,9,178,9,130,9,178,9,229,9,2,11,229,9,2,11,32,11,2,11,229,9,178,9,130,9,89,9,178,9,130,9,130,9,130,9,130,9,178,9,178,9,229,9,130,9,178,9,178,9,229,9,229,9,2,11,2,11,32,11,229,9,2,11,130,9

fm_harmony:
.db 70,9,70,9,89,9,89,9,130,9,70,9,89,9,89,9,70,9,70,9,89,9,89,9,130,9,70,9,89,9,89,9,3,9,70,9,89,9,70,9,34,9,3,9,34,9,70,9,34,9,3,9,243,8,3,9,34,9,70,9,89,9,130,9,89,9,70,9,89,9,130,9,178,9,130,9,178,9,229,9,178,9,130,9,89,9,70,9,34,9,89,9,70,9,70,9,70,9,70,9,89,9,89,9,130,9,70,9,89,9,89,9,130,9,130,9,178,9,178,9,229,9,130,9,178,9,70,9

fm_bass:
.db 163,8,163,8,172,8,172,8,193,8,163,8,172,8,172,8,163,8,163,8,172,8,172,8,193,8,163,8,172,8,172,8,129,8,163,8,172,8,163,8,145,8,129,8,145,8,163,8,145,8,129,8,122,8,129,8,145,8,163,8,172,8,193,8,172,8,163,8,172,8,193,8,217,8,193,8,217,8,243,8,217,8,193,8,172,8,163,8,145,8,172,8,163,8,163,8,163,8,163,8,172,8,172,8,193,8,163,8,172,8,172,8,193,8,193,8,217,8,217,8,243,8,193,8,217,8,163,8
