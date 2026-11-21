"""Sound-role audition: measure how candidate sounds perform one part, alone and in the mix.

The same MIDI part is rendered through several candidate instruments (one stem per candidate). For each stem this
measures what can be decided technically. Whether a sound is *right* stays a listening decision.

- articulation: per note, the time from note-on to 70% of the note's peak, against the written note length
  (a sample that takes most of a short note to speak can't play that part)
- tail: how long a note keeps sounding after its note-off, on notes followed by a gap
- reach: notes that make no sound (out of the sample's range, or too soft a layer)
- colour: spectral centroid and the share of energy in four bands (a lead living under 250 Hz fights the bass)
- in context (optional, with the other stems of the song): the candidate is level-matched to a target loudness and
  mixed with the context; "audible share" is the part of its energy in time-frequency cells where it is no more
  than 6 dB under the rest of the mix, "low clash" is the part below 250 Hz where the context is also loud

usage:
  audition.py measure <stem.wav> <song.mid> <part name> [--context a.wav,b.wav] [--target-lufs -17.5]
                      [--region start_s,end_s] [--json]
  audition.py table <manifest.json>      # print the candidates' measurements side by side
A manifest is {"song": ..., "part": ..., "role": {...}, "candidates": [{"name", "source", "stem", "measure": {...}}]}.
Needs numpy and soundfile; pyloudnorm for loudness when it is installed (falls back to RMS dBFS).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'corpus'))

BANDS = ((0, 250), (250, 800), (800, 3000), (3000, 24000))
BAND_NAMES = ('low', 'low_mid', 'mid', 'high')


def _load(path):
    import numpy as np, soundfile as sf
    x, sr = sf.read(path, always_2d=True, dtype='float64')
    return x, sr


def loudness(x, sr):
    import numpy as np
    try:
        import pyloudnorm as pyln
        v = pyln.Meter(sr).integrated_loudness(x)
        if np.isfinite(v):
            return float(v)
    except Exception:
        pass
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def notes_of(midi_path, part):
    import midi_lib
    song = midi_lib.read(midi_path)
    want = set(part.split(','))
    tid = [t for t, n in song.track_names.items() if n in want]
    ns = sorted((n.start_s, n.end_s, n.pitch, n.velocity) for n in song.notes if n.track in tid)
    if not ns:
        raise SystemExit(f'no notes for part {part!r} in {midi_path}')
    return ns


def _env(m, sr, win_s=0.005):
    import numpy as np
    w = max(1, int(win_s * sr))
    return np.sqrt(np.convolve(m ** 2, np.ones(w) / w, 'same'))


def articulation(m, sr, notes):
    """Per note with its onset clear of the previous note's sound: rise time to 70% of the note's peak."""
    import numpy as np
    env = _env(m, sr)
    rises, ratios = [], []
    for i, (s, e, p, v) in enumerate(notes):
        a = int(s * sr)
        L = int(min(e - s, 0.6) * sr)
        if L < int(0.03 * sr) or a + L > len(env):
            continue
        before = env[max(0, a - int(0.01 * sr)):a].mean() if a > 0 else 0.0
        seg = env[a:a + L]
        pk = seg.max()
        if pk < 1e-4 or before > 0.5 * pk:        # silent, or still ringing from the last note: not measurable
            continue
        k = int(np.argmax(seg > before + 0.7 * (pk - before)))
        rises.append(k / sr * 1000)
        ratios.append(k / L)
    if not rises:
        return {'notes_measured': 0}
    r, q = np.array(rises), np.array(ratios)
    return {'notes_measured': len(r), 'rise_ms_median': round(float(np.median(r)), 1),
            'rise_ms_p90': round(float(np.percentile(r, 90)), 1),
            'rise_share_of_note_median': round(float(np.median(q)), 2),
            'slow_share': round(float(np.mean(q > 0.4)), 2)}


def tails(m, sr, notes, drop_db=20.0, min_gap_s=0.3):
    """For notes followed by a gap: ms after note-off until the level falls drop_db under the note's peak."""
    import numpy as np
    env = _env(m, sr, 0.01)
    out = []
    starts = [n[0] for n in notes]
    for i, (s, e, p, v) in enumerate(notes):
        nxt = min([t for t in starts if t > s + 1e-6] or [len(m) / sr])
        if any(a <= e < b for a, b, *_ in notes if a > s):   # another note sounds through this note-off
            continue
        if nxt - e < min_gap_s:
            continue
        a, b, c = int(s * sr), int(e * sr), int(nxt * sr)
        pk = env[a:b].max() if b > a else 0
        if pk < 1e-4:
            continue
        thr = pk * 10 ** (-drop_db / 20)
        after = env[b:c]
        below = np.nonzero(after < thr)[0]
        out.append((below[0] if len(below) else len(after)) / sr * 1000)
    if not out:
        return {'notes_measured': 0}
    return {'notes_measured': len(out), 'tail_ms_median': round(float(np.median(out))),
            'tail_ms_p90': round(float(np.percentile(out, 90)))}


def reach(m, sr, notes, quiet_db=-60.0):
    """Notes whose first 150 ms stay under quiet_db: the sample doesn't cover that pitch or velocity."""
    import numpy as np
    silent = []
    for s, e, p, v in notes:
        seg = m[int(s * sr):int((s + min(0.15, e - s + 0.05)) * sr)]
        if len(seg) and 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12) < quiet_db:
            silent.append(p)
    ps = [n[2] for n in notes]
    return {'notes': len(notes), 'pitch_range': [min(ps), max(ps)], 'silent_notes': len(silent),
            'silent_pitches': sorted(set(silent))[:24]}


def _spec(m, sr, n=4096, hop=2048):
    import numpy as np
    if len(m) < n:
        m = np.pad(m, (0, n - len(m)))
    frames = np.lib.stride_tricks.sliding_window_view(m, n)[::hop] * np.hanning(n)
    return np.abs(np.fft.rfft(frames, axis=1)) ** 2, np.fft.rfftfreq(n, 1 / sr)


def colour(m, sr):
    import numpy as np
    S, f = _spec(m, sr)
    tot = S.sum() + 1e-20
    out = {'centroid_hz': round(float((S.sum(0) * f).sum() / tot))}
    for name, (lo, hi) in zip(BAND_NAMES, BANDS):
        out[f'share_{name}'] = round(float(S[:, (f >= lo) & (f < hi)].sum() / tot), 3)
    return out


def in_context(m, ctx, sr, margin_db=6.0):
    """m and ctx mono, already at their mix levels. Energy-weighted audibility of m against ctx."""
    import numpy as np
    L = min(len(m), len(ctx))
    S, f = _spec(m[:L], sr)
    C, _ = _spec(ctx[:L], sr)
    # 1/3-octave-ish bands so one bin's leakage doesn't decide anything
    edges = np.geomspace(40, min(16000, sr / 2 - 1), 28)
    idx = np.digitize(f, edges)
    Sb = np.stack([S[:, idx == k].sum(1) for k in range(1, len(edges))], 1)
    Cb = np.stack([C[:, idx == k].sum(1) for k in range(1, len(edges))], 1)
    tot = Sb.sum() + 1e-20
    audible = Sb >= Cb * 10 ** (-margin_db / 10)
    low = edges[1:] <= 250
    low_loud = (Cb[:, low] >= Sb[:, low] * 10 ** (-margin_db / 10))
    return {'audible_share': round(float(Sb[audible].sum() / tot), 3),
            'low_clash_share': round(float(Sb[:, low][low_loud].sum() / tot), 3)}


def measure(stem, midi_path, part, context=(), target_lufs=None, region=None):
    import numpy as np
    x, sr = _load(stem)
    notes = notes_of(midi_path, part)
    if region:
        a, b = region
        x = x[int(a * sr):int(b * sr)]
        notes = [(s - a, e - a, p, v) for s, e, p, v in notes if a <= s < b]
    m = x.mean(1)
    lu = loudness(x, sr)
    out = {'stem': os.path.basename(stem), 'part': part, 'loudness_lufs': round(lu, 1),
           'peak_dbfs': round(float(20 * np.log10(np.abs(x).max() + 1e-12)), 1),
           'articulation': articulation(m, sr, notes), 'tail': tails(m, sr, notes), 'reach': reach(m, sr, notes),
           'colour': colour(m, sr)}
    if context:
        g = 10 ** (((target_lufs if target_lufs is not None else lu) - lu) / 20)
        ctx = None
        for c in context:
            y, sr2 = _load(c)
            if sr2 != sr:
                raise SystemExit(f'sample rate mismatch: {c}')
            if region:
                y = y[int(region[0] * sr):int(region[1] * sr)]
            y = y.mean(1)
            if ctx is None:
                ctx = y
            else:
                n = min(len(ctx), len(y))
                ctx = ctx[:n] + y[:n]
        out['gain_to_target_db'] = round(20 * np.log10(g), 2)
        out['in_context'] = in_context(m * g, ctx, sr)
    return out


ROWS = (('loudness_lufs', None), ('rise_ms_median', 'articulation'), ('rise_share_of_note_median', 'articulation'),
        ('slow_share', 'articulation'), ('tail_ms_median', 'tail'), ('silent_notes', 'reach'),
        ('centroid_hz', 'colour'), ('share_low', 'colour'), ('share_low_mid', 'colour'),
        ('audible_share', 'in_context'), ('low_clash_share', 'in_context'))


def table(manifest):
    cands = manifest['candidates']
    w = max(len(c['name']) for c in cands)
    lines = [f"{manifest.get('song', '')} {manifest.get('part', '')}"]
    lines.append(' ' * 26 + '  '.join(c['name'].ljust(w)[:w] for c in cands))
    for key, grp in ROWS:
        vals = []
        for c in cands:
            d = c.get('measure', {})
            v = (d.get(grp) or {}).get(key) if grp else d.get(key)
            vals.append(('-' if v is None else str(v)).ljust(w)[:w])
        lines.append(key.ljust(26) + '  '.join(vals))
    return '\n'.join(lines)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 0
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    if argv[1] == 'measure':
        ctx = [c for c in (opt('--context') or '').split(',') if c]
        reg = opt('--region')
        r = measure(argv[2], argv[3], argv[4], ctx, float(opt('--target-lufs')) if opt('--target-lufs') else None,
                    tuple(float(v) for v in reg.split(',')) if reg else None)
        print(json.dumps(r, indent=1))
    elif argv[1] == 'table':
        print(table(json.load(open(argv[2]))))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
