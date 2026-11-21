"""Sound-role audition measurements on synthetic stems: a fast and a slow attack, a long tail, a silent note,
and a lead buried under a loud context."""
import importlib.util, os, sys

import numpy as np
import soundfile as sf
import mido

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, 'skill', 'faderhand', 'tools')
spec = importlib.util.spec_from_file_location('audition', os.path.join(TOOLS, 'audition.py'))
au = importlib.util.module_from_spec(spec)
spec.loader.exec_module(au)

SR, BPM = 44100, 120          # one beat = 0.5 s
NOTES = [(0.0, 0.4, 69), (1.0, 0.4, 72), (2.0, 0.4, 76), (3.0, 0.4, 20)]   # beats; the last is out of range


def write_midi(path):
    mf = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage('track_name', name='Lead', time=0))
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM), time=0))
    ev = []
    for s, d, p in NOTES:
        ev += [(int(s * 480), 'note_on', p), (int((s + d) * 480), 'note_off', p)]
    t = 0
    for at, kind, p in sorted(ev):
        tr.append(mido.Message(kind, note=p, velocity=90, time=at - t))
        t = at
    mf.save(path)


def render(attack_s, release_s, skip_top=True):
    x = np.zeros(int(2.5 * SR))
    for s, d, p in NOTES:
        if skip_top and p < 30:
            continue
        a, n = int(s * 0.5 * SR), int((d * 0.5 + release_s) * SR)
        t = np.arange(n) / SR
        env = np.minimum(1, t / max(attack_s, 1e-4))
        off = d * 0.5
        env = np.where(t > off, env * np.exp(-(t - off) / max(release_s / 4, 1e-3)), env)
        x[a:a + n] += 0.3 * env * np.sin(2 * np.pi * 440 * 2 ** ((p - 69) / 12) * t)
    return x


def test_attack_tail_and_reach(tmp_path):
    mid = str(tmp_path / 'song.mid')
    write_midi(mid)
    fast, slow = str(tmp_path / 'fast.wav'), str(tmp_path / 'slow.wav')
    sf.write(fast, render(0.002, 0.05), SR)
    sf.write(slow, render(0.15, 0.6), SR)
    f = au.measure(fast, mid, 'Lead')
    s = au.measure(slow, mid, 'Lead')
    assert f['articulation']['rise_ms_median'] < 20
    assert s['articulation']['rise_ms_median'] > 80
    assert s['articulation']['slow_share'] > f['articulation']['slow_share']
    assert s['tail']['tail_ms_median'] > f['tail']['tail_ms_median']
    assert f['reach']['silent_notes'] == 1 and f['reach']['silent_pitches'] == [20]


def test_in_context_audibility(tmp_path):
    mid = str(tmp_path / 'song.mid')
    write_midi(mid)
    lead = str(tmp_path / 'lead.wav')
    sf.write(lead, render(0.002, 0.05), SR)
    rng = np.random.default_rng(0)
    quiet, loud = str(tmp_path / 'quiet.wav'), str(tmp_path / 'loud.wav')
    sf.write(quiet, 0.001 * rng.standard_normal(int(2.5 * SR)), SR)
    sf.write(loud, 0.5 * rng.standard_normal(int(2.5 * SR)), SR)
    a = au.measure(lead, mid, 'Lead', [quiet])
    b = au.measure(lead, mid, 'Lead', [loud])
    assert a['in_context']['audible_share'] > 0.9
    assert b['in_context']['audible_share'] < a['in_context']['audible_share']
    m = {'song': 's', 'part': 'Lead', 'candidates': [{'name': 'fast', 'measure': a}, {'name': 'buried', 'measure': b}]}
    assert 'audible_share' in au.table(m)
