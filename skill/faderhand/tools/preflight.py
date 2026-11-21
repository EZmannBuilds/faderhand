"""Acoustic preflight: what a plan has to know before it relies on silence or adds a gesture, and the check afterwards
that the silence (or the entrance) really happened. Built after the Song A A/B/C test, where every planned note
change landed but the planned gaps still sounded (the stab samplers ignored note-off).

usage:
  uv run -q --no-project --with mido --with numpy --with soundfile python preflight.py set <file.als> [--json]
  uv run -q --no-project --with mido --with numpy --with soundfile python preflight.py gestures <song.mid> [--drums Drums] [--json]
  uv run -q --no-project --with mido --with numpy --with soundfile python preflight.py occupancy <stem.wav> <song.mid> <track[,track...]> [--pitches 36,38] [--json]

set        Reads a CLOSED .als (never one Live has open and unsaved). Per MIDI track: the instrument, and for Sampler and
           Simpler the volume envelope's loop mode (Trigger = note-off ignored: every hit plays its whole sample), the
           release time and the voice count; per track and return, reverb decay and delay feedback; the sends that are
           up. Flags what can keep sounding after the notes stop.
gestures   From the MIDI (GM drum notes): which bars already hold a fill (>= 1.3x the median hits per bar, or 3+
           snare or tom hits on different 16ths of the last beat) or a drop (<= 0.4x after a fuller bar), so a plan doesn't add a fill on
           top of one or a drop inside one.
occupancy  From a rendered stem and the notes that should be playing in it: per beat, "audible without notes" (no
           note sounding, or within 0.75 s of one ending, yet the stem is above -50 dBFS RMS: a tail, a held voice, a
           stuck note or bleed) and "notes without sound" (a note sounding, stem below -70 dBFS). The stem must be
           rendered from bar 1 at the MIDI's tempo.
Exit 0 always; read the flags. The numbers are evidence for a plan, not a verdict on the music.
"""
import gzip, json, os, re, statistics as st, sys
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'corpus'))

LOOP_MODES = {0: 'none', 1: 'loop', 2: 'beat', 3: 'sync', 4: 'trigger'}
SAMPLERS = ('MultiSampler', 'OriginalSimpler')
INSTRUMENT_TAGS = SAMPLERS + ('InstrumentVector', 'UltraAnalog', 'StringStudio', 'Collision', 'Operator', 'Drift',
                             'Meld', 'LoungeLizard', 'Tension', 'InstrumentGroupDevice', 'DrumGroupDevice',
                             'PluginDevice', 'AuPluginDevice')


def _manual(el, tag):
    x = el.find(tag)
    if x is None:
        return None
    m = x.find('Manual')
    return m.get('Value') if m is not None else x.get('Value')


def _name(tr):
    n = tr.find('Name/EffectiveName')
    return n.get('Value') if n is not None else '?'


def _effects(devs):
    out = []
    for d in devs:
        if d.tag == 'Reverb':
            dt = _manual(d, 'DecayTime')
            out.append({'device': 'Reverb', 'decay_s': round(float(dt) / 1000, 2) if dt else None})
        elif d.tag in ('Delay', 'PingPongDelay', 'FilterDelay', 'Echo'):
            fb = _manual(d, 'Feedback')
            out.append({'device': d.tag, 'feedback': round(float(fb), 2) if fb else None})
        elif d.tag == 'HybridReverb':
            out.append({'device': 'HybridReverb', 'decay_s': None})
    return out


def inspect_set(path):
    root = ET.fromstring(gzip.open(path).read())
    returns = []
    for rt in root.iter('ReturnTrack'):
        devs = rt.find('DeviceChain/DeviceChain/Devices')
        returns.append({'name': _name(rt), 'effects': _effects(list(devs) if devs is not None else [])})
    tracks, flags = [], []
    for tr in root.iter('MidiTrack'):
        name = _name(tr)
        devs = tr.find('DeviceChain/DeviceChain/Devices')
        devs = list(devs) if devs is not None else []
        spk = tr.find('DeviceChain/Mixer/Speaker/Manual')
        row = {'track': name, 'on': (spk.get('Value') == 'true') if spk is not None else None, 'instrument': None,
               'effects': _effects(devs), 'sends_up': []}
        for d in devs:
            if d.tag in INSTRUMENT_TAGS:
                user = d.find('UserName')
                row['instrument'] = {'type': d.tag, 'name': (user.get('Value') if user is not None else '') or d.tag}
                if d.tag in SAMPLERS:
                    env = d.find('VolumeAndPan/Envelope')
                    g = d.find('Globals')
                    lm = int(_manual(env, 'LoopMode')) if env is not None and _manual(env, 'LoopMode') else None
                    rel = float(_manual(env, 'ReleaseTime')) if env is not None and _manual(env, 'ReleaseTime') else None
                    row['instrument'].update({'loop_mode': LOOP_MODES.get(lm, lm), 'release_ms': rel,
                                              'voices': int(_manual(g, 'NumVoices')) if g is not None and _manual(g, 'NumVoices') else None})
                    if lm == 4:
                        flags.append(f'{name}: Sampler envelope in Trigger mode: note-off is ignored, every hit plays its '
                                     'whole sample; a planned gap will hold the last notes until they die')
                    if rel and rel > 1500:
                        flags.append(f'{name}: release {rel / 1000:.1f} s: notes ring on after note-off')
                break
        for e in row['effects']:
            if e.get('decay_s') and e['decay_s'] > 2.0:
                flags.append(f"{name}: {e['device']} decay {e['decay_s']} s on the track")
            if e.get('feedback') and e['feedback'] > 0.5:
                flags.append(f"{name}: {e['device']} feedback {e['feedback']}: repeats outlast the notes")
        sends = tr.find('DeviceChain/Mixer/Sends')
        for i, s in enumerate(list(sends) if sends is not None else []):
            m = s.find('Send/Manual')
            if m is not None and float(m.get('Value')) > 0.01 and i < len(returns):   # about -40 dB
                row['sends_up'].append(returns[i]['name'])
                for e in returns[i]['effects']:
                    if e.get('decay_s') and e['decay_s'] > 2.0:
                        flags.append(f"{name}: sends to {returns[i]['name']} ({e['device']} {e['decay_s']} s): gaps carry its tail")
        tracks.append(row)
    return {'set': os.path.basename(path), 'tracks': tracks, 'returns': returns, 'flags': flags}


def gestures(midi_path, drums='Drums'):
    import midi_lib
    song = midi_lib.read(midi_path)
    bar = song.bar_ticks()
    tid = [t for t, n in song.track_names.items() if n == drums]
    hits = Counter(n.start // bar for n in song.notes if n.track in tid)
    nbars = max((n.end for n in song.notes), default=0) // bar + 1
    per = [hits.get(b, 0) for b in range(nbars)]
    played = [c for c in per if c]
    med = st.median(played) if played else 0
    # a fill is a busier bar, or a last beat with snare or tom hits on 3+ different 16ths (GM 37-40 snares, 41-50 toms): many fills swap
    # hats for a snare run and keep the hit count
    slots = {(n.start // bar, round((n.start % bar) / (song.ppq / 4))) for n in song.notes
             if n.track in tid and 37 <= n.pitch <= 50 and n.pitch not in (42, 44, 46)
             and (n.start % bar) >= bar * 3 // 4 - song.ppq // 16}
    roll = Counter(b for b, _ in slots)   # distinct 16th positions, so a snare and a clap together count once
    fills = [b + 1 for b, c in enumerate(per) if med and (c >= 1.3 * med or roll.get(b, 0) >= 3)]
    drops = [b + 1 for b, c in enumerate(per) if med and c <= 0.4 * med and b > 0 and per[b - 1] > 0.4 * med]
    return {'midi': os.path.basename(midi_path), 'drum_track': drums, 'median_hits_per_bar': med,
            'fill_bars': fills, 'drop_bars': drops, 'hits_per_bar': per}


def occupancy(stem, midi_path, track, pitches=None, tail_s=0.75, loud_db=-50.0, quiet_db=-70.0):
    import numpy as np, soundfile as sf, midi_lib
    song = midi_lib.read(midi_path)
    want = set(track.split(','))   # several tracks for a stem rendered from layers soloed together
    tid = [t for t, n in song.track_names.items() if n in want]
    notes = [n for n in song.notes if n.track in tid and (not pitches or n.pitch in pitches)]
    x, sr = sf.read(stem, always_2d=True)
    m = x.mean(1)
    spb = 60.0 / song.bpm
    nbeats = int(len(m) / sr / spb)
    spans = sorted((n.start_s, n.end_s) for n in notes)
    tails, silent = [], []
    for k in range(nbeats):
        t0, t1 = k * spb, (k + 1) * spb
        seg = m[int(t0 * sr):int(t1 * sr)]
        if not len(seg):
            break
        db = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12)
        sounding = any(a < t1 and b + tail_s > t0 for a, b in spans)
        playing = any(a < t1 and b > t0 for a, b in spans)
        if not sounding and db > loud_db:
            tails.append({'beat': k + 1, 'bar': k // 4 + 1, 'db': round(db, 1)})
        if playing and db < quiet_db:
            silent.append({'beat': k + 1, 'bar': k // 4 + 1, 'db': round(db, 1)})
    flags = []
    if tails:
        flags.append(f'{len(tails)} beats audible with no note sounding (first at bar {tails[0]["bar"]}): tails, held '
                     'voices or bleed; a planned gap is not silent')
    if silent:
        flags.append(f'{len(silent)} beats with notes but no sound (first at bar {silent[0]["bar"]})')
    return {'stem': os.path.basename(stem), 'track': track, 'notes': len(notes), 'beats': nbeats,
            'audible_without_notes': tails, 'notes_without_sound': silent, 'flags': flags}


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 0
    cmd, as_json = argv[1], '--json' in argv
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    if cmd == 'set':
        r = inspect_set(argv[2])
    elif cmd == 'gestures':
        r = gestures(argv[2], opt('--drums', 'Drums'))
    elif cmd == 'occupancy':
        p = opt('--pitches')
        r = occupancy(argv[2], argv[3], argv[4], {int(v) for v in p.split(',')} if p else None)
    else:
        print(__doc__)
        return 0
    if as_json:
        print(json.dumps(r, indent=1))
        return 0
    if cmd == 'set':
        for t in r['tracks']:
            i = t['instrument'] or {}
            extra = ''.join(f", {k} {i[k]}" for k in ('loop_mode', 'release_ms', 'voices') if i.get(k) is not None)
            print(f"{t['track']:<22} {i.get('name', '-')}{extra}" + (' (muted)' if t['on'] is False else '') + (f"; sends to {', '.join(t['sends_up'])}" if t['sends_up'] else ''))
    elif cmd == 'gestures':
        print(f"median {r['median_hits_per_bar']} drum hits per bar; fills in bars {r['fill_bars']}; drops in bars {r['drop_bars']}")
    else:
        print(f"{r['stem']}: {r['notes']} notes on {r['track']}, {r['beats']} beats checked")
    for f in r.get('flags', []):
        print('  FLAG', f)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
