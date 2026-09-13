"""Check story messages and their gameplay outcomes in controlled MSX1 scenes."""
from pathlib import Path
import hashlib
import json
from emulator_support import OpenMSX

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs'
ROM = OUT / 'MIKERO-ODYSSEY.rom'
S = json.loads((ROOT / 'work/build/symbols.json').read_text())
checks = []


def check(name, passed, **details):
    print(name, bool(passed), details, flush=True)
    checks.append(dict(name=name, passed=bool(passed), **details))
    assert passed, name


for standard in ('ntsc', 'pal'):
    with OpenMSX(standard, work=ROOT / 'work') as e:
        e.load_rom(ROM, 'ASCII16')
        e.run_for(5)

        def get(name, size=1):
            return e.read_symbol(S, name, size)

        def put(name, value, size=1):
            e.write_block('memory', S[name], value.to_bytes(size, 'little'))

        def tap(mask):
            e.command(f'keymatrixdown 8 {mask};after time 0.06 {{keymatrixup 8 {mask}}}')
            e.run_for(.8)

        def message():
            return e.read_block('memory', S['screen'] + 22 * 32, 32).decode('ascii').strip()

        def setup(kind=11, health=80):
            tiles = bytearray([1] * 4096)
            for y in range(6, 15):
                for x in range(6, 15):
                    tiles[y * 64 + x] = 0
            e.write_block('memory', S['map'], tiles)
            e.write_block('memory', S['seen'], bytes(512))
            for name, value in dict(mode=1, depth=1, px=10, py=10, hp=20, maxhp=24,
                                    level=1, xp=0, attack=3, gold=0, enemy_count=1,
                                    ex=11, ey=10, eh=health, et=kind, foodclock=0,
                                    turns=0, dirty=1, prev_input=0, repeat=0,
                                    rescue_phase=0, kill_count=0).items():
                put(name, value)
            for name, value in dict(food=400, score=0, turn_count=0).items():
                put(name, value, 2)
            e.run_for(.8)

        tap(1)
        setup()
        tap(1)
        check(standard + '-creature-contact', message() == 'A CREATURE BUMPS INTO YOU!'
              and get('hp') == 19 and get('turn_count', 2) == 1, message=message())

        setup(15)
        put('depth', 30)
        tap(1)
        check(standard + '-king-contact', message() == 'THE KING BUMPS INTO YOU!'
              and get('hp') == 16 and get('turn_count', 2) == 1, message=message())

        setup(11, 1)
        tap(128)
        check(standard + '-creature-return-reward', message() == 'POOF! +XP +GOLD'
              and get('eh') == 0 and get('score', 2) == 20 and get('xp') == 2
              and get('gold') == 1 and get('turn_count', 2) == 1, message=message())

        setup(15, 1)
        put('depth', 30)
        put('level', 15)
        tap(128)
        check(standard + '-king-return-crown-hint', message() == 'POOF! THE CROWN IS AHEAD!'
              and get('eh') == 0 and get('score', 2) == 200 and get('xp') == 12
              and get('gold') == 1 and get('mode') == 1, message=message())

        setup()
        put('enemy_count', 0)
        put('gold', 5)
        put('hp', 5)
        e.write_block('memory', S['map'] + 10 * 64 + 11, bytes([7]))
        tap(128)
        check(standard + '-keeper-treatment', message() == 'KEEPER: ALL PATCHED UP!'
              and get('hp') == 24 and get('gold') == 0 and get('px') == 10
              and get('turn_count', 2) == 0, message=message())
        check(standard + '-key-help-visible',
              e.read_block('memory', S['screen'] + 23 * 32, 32).strip()
              == b'ARROWS:MOVE SPACE:WAIT Z:HEAL')
        check(standard + '-strict-VRAM', e.timing_violations() == 0)

data = ROM.read_bytes()
check('paw-tap-wording-present', b'PAW TAP! PON!\0' in data)
removed = [b'THE WARDEN STRIKES!', b'AN ENEMY HITS YOU!', b'PAW PUNCH! PON!',
           b'KING: POOF! CLAIM THE CROWN!', b'KEEPER: YOUR LIGHT IS RESTORED.',
           b'JUST RESTING. SEE YOU SOON!', b'MIKERO IS SAFE!']
check('old-story-messages-absent', all(text not in data for text in removed))
(OUT / 'worldview-verification.json').write_text(json.dumps(dict(
    rom_sha256=hashlib.sha256(data).hexdigest(), checks=checks,
    method='Injected RAM fixtures, actual emulated keyboard actions and displayed name-table text; NTSC/PAL MSX1 RAM32K VRAM16K; not physical hardware.'), indent=2) + '\n')
