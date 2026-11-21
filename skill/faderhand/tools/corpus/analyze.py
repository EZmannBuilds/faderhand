"""Per-file musical features for the corpus (measurements, not interpretations).

Usage: uv run --no-project --with mido python -I analyze.py <corpus_root> [--sample-pdmx N] [--workers 2]
Reads _inventory/inventory.jsonl, analyses approved and pending files (held-out files too, flagged), skips
duplicates, unreadable files and Zynthion's FL per-drum splits, and writes _features/features.jsonl.

Grid conventions: a "step" is a 16th note; positions are steps from the bar start; timing offsets are measured
against the nearest 16th in milliseconds and as a fraction of a 16th. Velocities are MIDI 1-127.
"""
import argparse, json, math, os, random, statistics as st, sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midi_lib  # noqa: E402

KICK = {35, 36}
SNARE = {37, 38, 40}
CLAP = {39}
CHH = {42, 44}
OHH = {46}
RIDE = {51, 53, 59}
CRASH = {49, 52, 55, 57}
TOMS = {41, 43, 45, 47, 48, 50}
DRUM_CLASS = [("kick", KICK), ("snare", SNARE), ("clap", CLAP), ("hat_closed", CHH), ("hat_open", OHH),
              ("ride", RIDE), ("crash", CRASH), ("tom", TOMS)]
KS_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KS_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def dclass(p):
    for name, s in DRUM_CLASS:
        if p in s:
            return name
    return "perc"


def q(x, n=3):
    return round(x, n) if isinstance(x, float) else x


def pct(vals, p):
    if not vals:
        return None
    v = sorted(vals)
    k = (len(v) - 1) * p
    f = math.floor(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def key_estimate(notes):
    w = [0.0] * 12
    for n in notes:
        w[n.pitch % 12] += (n.end - n.start)
    if sum(w) == 0:
        return None
    best = None
    for tonic in range(12):
        for mode, prof in (("major", KS_MAJOR), ("minor", KS_MINOR)):
            rot = [prof[(i - tonic) % 12] for i in range(12)]
            mw, mp = sum(w) / 12, sum(rot) / 12
            num = sum((a - mw) * (b - mp) for a, b in zip(w, rot))
            den = math.sqrt(sum((a - mw) ** 2 for a in w) * sum((b - mp) ** 2 for b in rot))
            r = num / den if den else 0
            if not best or r > best[0]:
                best = (r, tonic, mode)
    return {"tonic": NAMES[best[1]], "mode": best[2], "r": q(best[0])}


class Grid:
    def __init__(self, song):
        self.s16 = song.ppq / 4
        self.bar = song.bar_ticks()
        self.steps = max(1, round(self.bar / self.s16))
        self.ms16 = 60000 / song.bpm / 4

    def step(self, tick):
        return round(tick / self.s16)

    def pos(self, tick):
        return self.step(tick) % self.steps

    def bar_of(self, tick):
        return int(tick // self.bar)

    def offset(self, tick):
        """signed offset from the nearest 16th, as a fraction of a 16th"""
        return (tick - self.step(tick) * self.s16) / self.s16


def onsets(notes):
    return sorted({n.start for n in notes})


def drums_features(notes, g):
    out = {"n": len(notes)}
    by = defaultdict(list)
    for n in notes:
        by[dclass(n.pitch)].append(n)
    bars = max(1, g.bar_of(max(n.start for n in notes)) + 1)
    out["bars"] = bars
    inst = {}
    for name, ns in by.items():
        hist = [0] * g.steps
        vel = defaultdict(list)
        offs = []
        for n in ns:
            p = g.pos(n.start)
            hist[p] += 1
            vel[p].append(n.velocity)
            offs.append(g.offset(n.start))
        vels = [n.velocity for n in ns]
        # systematic placement per grid position vs residual jitter
        offpos = defaultdict(list)
        for n in ns:
            offpos[g.pos(n.start)].append(g.offset(n.start))
        resid = [o - st.mean(v) for v in offpos.values() if len(v) >= 2 for o in v]
        allv = [n.velocity for n in ns]
        tv = st.pvariance(allv) if len(allv) > 1 else 0
        vstruct = (sum(len(v) * (st.mean(v) - st.mean(allv)) ** 2 for v in vel.values()) / len(allv) / tv) if tv else None
        # local jitter: differences between successive hits at the same grid position (drift removed)
        seqpos = defaultdict(list)
        for n in sorted(ns, key=lambda n: n.start):
            seqpos[g.pos(n.start)].append(g.offset(n.start))
        diffs = [b - a for v in seqpos.values() for a, b in zip(v, v[1:])]
        inst[name] = {
            "jitter_local_ms": q(st.pstdev(diffs) / math.sqrt(2) * g.ms16, 2) if len(diffs) > 2 else None,
            "jitter_ms": q(st.pstdev(resid) * g.ms16, 2) if len(resid) > 2 else None,
            "placement_ms": {str(k): q(st.mean(v) * g.ms16, 1) for k, v in sorted(offpos.items()) if len(v) >= 2},
            "vel_structure": q(vstruct) if vstruct is not None else None,
            "per_bar": q(len(ns) / bars, 2),
            "pos_hist": [q(h / bars, 3) for h in hist],
            "vel_by_pos": [q(st.mean(vel[i]), 1) if vel[i] else None for i in range(g.steps)],
            "vel_mean": q(st.mean(vels), 1), "vel_sd": q(st.pstdev(vels), 1),
            "vel_p10": pct(vels, .1), "vel_p90": pct(vels, .9),
            "timing_sd_ms": q(st.pstdev(offs) * g.ms16, 2) if len(offs) > 1 else 0.0,
            "timing_mean_ms": q(st.mean(offs) * g.ms16, 2),
        }
    out["instruments"] = inst
    # swing: odd 16ths' delay vs even 16ths (hats/ride first, then everything)
    src = by.get("hat_closed") or by.get("ride") or notes
    even = [g.offset(n.start) for n in src if g.step(n.start) % 2 == 0]
    odd = [g.offset(n.start) for n in src if g.step(n.start) % 2 == 1]
    if len(odd) >= 4:
        d = st.mean(odd) - (st.mean(even) if even else 0)
        out["swing_percent_16"] = q(50 + 50 * d, 1)
    # ghost notes: snare hits below half the backbeat velocity
    sn = by.get("snare", [])
    if sn:
        bb = [n.velocity for n in sn if g.pos(n.start) in (4, 12)] or [max(n.velocity for n in sn)]
        accent = st.median(bb)
        ghosts = [n for n in sn if n.velocity < 0.6 * accent]
        out["snare_ghost_fraction"] = q(len(ghosts) / len(sn))
        out["snare_ghost_per_bar"] = q(len(ghosts) / bars, 2)
        gp = Counter(g.pos(n.start) for n in ghosts)
        out["ghost_positions"] = {str(k): v for k, v in gp.most_common(6)}
        out["backbeat_velocity"] = accent
    # backbeat placement, bar by bar: a bar "has 2 and 4" when snare/clap hits land on both steps 4 and 12;
    # it is "half-time" when beat 3 (step 8) is hit and neither 2 nor 4 is
    bb_notes = by.get("snare", []) + by.get("clap", [])
    if bb_notes and g.steps == 16:
        loud = st.median(n.velocity for n in bb_notes)
        hits = defaultdict(set)
        for n in bb_notes:
            if n.velocity >= 0.8 * loud:
                hits[g.bar_of(n.start)].add(g.pos(n.start))
        out["backbeat_2_4"] = q(sum(1 for b in range(bars) if {4, 12} <= hits.get(b, set())) / bars)
        out["backbeat_3"] = q(sum(1 for b in range(bars) if 8 in hits.get(b, set()) and not ({4, 12} & hits.get(b, set()))) / bars)
    # hat rolls: runs of >=3 hat onsets closer than a 16th
    hats = sorted(by.get("hat_closed", []) + by.get("hat_open", []), key=lambda n: n.start)
    rolls, run = [], [hats[0]] if hats else []
    for a, b in zip(hats, hats[1:]):
        if 0 < b.start - a.start < g.s16 * 0.9:
            run.append(b)
        else:
            if len(run) >= 3:
                rolls.append(run)
            run = [b]
    if len(run) >= 3:
        rolls.append(run)
    if hats:
        out["hat_rolls_per_bar"] = q(len(rolls) / bars, 2)
        kinds = Counter()
        where = Counter()
        vshape = Counter()
        for r in rolls:
            ioi = st.median(b.start - a.start for a, b in zip(r, r[1:])) / g.s16
            kinds["32nd" if abs(ioi - .5) < .08 else "16th-triplet" if abs(ioi - 2 / 3) < .08 else
                  "32nd-triplet" if abs(ioi - 1 / 3) < .06 else "64th" if ioi < .3 else "other"] += 1
            where[g.pos(r[0].start) // 4 + 1] += 1
            v0, v1 = r[0].velocity, r[-1].velocity
            vshape["rising" if v1 > v0 + 8 else "falling" if v1 < v0 - 8 else "flat"] += 1
        out["hat_roll_kinds"] = dict(kinds)
        out["hat_roll_start_beat"] = {str(k): v for k, v in where.items()}
        out["hat_roll_velocity_shape"] = dict(vshape)
        # hat accent pattern: mean velocity on beats, 8th offbeats, 16ths
        hv = defaultdict(list)
        for n in by.get("hat_closed", []):
            p = g.pos(n.start)
            hv["beat" if p % 4 == 0 else "8th" if p % 2 == 0 else "16th"].append(n.velocity)
        out["hat_vel_by_subdivision"] = {k: q(st.mean(v), 1) for k, v in hv.items()}
    # fills: density of the last bar vs the median bar
    per_bar = Counter(g.bar_of(n.start) for n in notes)
    if bars >= 2:
        med = st.median(per_bar.get(b, 0) for b in range(bars))
        out["last_bar_density_ratio"] = q(per_bar.get(bars - 1, 0) / med if med else 0, 2)
    return out


def line_features(notes, g):
    """monophonic-ish line: melody, bass, 808, arp"""
    ns = sorted(notes, key=lambda n: (n.start, -n.pitch))
    top = []
    for n in ns:  # skyline for melodies, lowest note for bass is handled by caller ordering
        if top and n.start == top[-1].start:
            continue
        top.append(n)
    pitches = [n.pitch for n in top]
    ivs = [b - a for a, b in zip(pitches, pitches[1:])]
    absiv = [abs(i) for i in ivs]
    bars = max(1, g.bar_of(max(n.start for n in top)) + 1)
    durs = [(n.end - n.start) / g.s16 for n in top]
    iois = [(b.start - a.start) / g.s16 for a, b in zip(top, top[1:])]
    gates = [d / i for d, i in zip(durs, iois) if i > 0]
    dirs = [1 if i > 0 else -1 for i in ivs if i != 0]
    changes = sum(1 for a, b in zip(dirs, dirs[1:]) if a != b)
    pos = Counter(g.pos(n.start) for n in top)
    # phrases: split at rests of a beat or more
    phrases, cur = [], 1
    for a, b in zip(top, top[1:]):
        if b.start - a.end >= 4 * g.s16:
            phrases.append(cur)
            cur = 1
        else:
            cur += 1
    phrases.append(cur)
    vels = [n.velocity for n in top]
    overl = sum(1 for a, b in zip(top, top[1:]) if b.start < a.end and b.pitch != a.pitch)
    # bar-to-bar repetition of the pitch/rhythm pattern
    bar_pat = defaultdict(list)
    for n in top:
        bar_pat[g.bar_of(n.start)].append((g.pos(n.start), n.pitch))
    pats = [tuple(v) for _, v in sorted(bar_pat.items())]
    uniq = len(set(pats))
    out = {
        "n": len(top), "per_bar": q(len(top) / bars, 2), "bars": bars,
        "pitch_median": st.median(pitches), "pitch_p10": pct(pitches, .1), "pitch_p90": pct(pitches, .9),
        "range": max(pitches) - min(pitches),
        "interval_hist": {str(k): v for k, v in sorted(Counter(max(-12, min(12, i)) for i in ivs).items())},
        "step_ratio": q(sum(1 for i in absiv if 0 < i <= 2) / len(absiv)) if absiv else None,
        "leap_ratio": q(sum(1 for i in absiv if i >= 5) / len(absiv)) if absiv else None,
        "repeat_ratio": q(sum(1 for i in absiv if i == 0) / len(absiv)) if absiv else None,
        "octave_jump_ratio": q(sum(1 for i in absiv if i == 12) / len(absiv)) if absiv else None,
        "contour_change_rate": q(changes / max(1, len(dirs) - 1)) if len(dirs) > 1 else None,
        "leap_recovery": None,
        "dur_hist_16ths": {str(k): v for k, v in Counter(min(16, round(d)) for d in durs).most_common(6)},
        "gate_median": q(st.median(gates)) if gates else None,
        "pos_hist": [q(pos[i] / bars, 3) for i in range(g.steps)],
        "offbeat_ratio": q(sum(v for p, v in pos.items() if p % 2 == 1) / len(top)),
        "phrase_notes_median": st.median(phrases), "phrases": len(phrases),
        "vel_mean": q(st.mean(vels), 1), "vel_sd": q(st.pstdev(vels), 1),
        "legato_overlaps_per_bar": q(overl / bars, 2),
        "bar_pattern_uniqueness": q(uniq / len(pats)) if pats else None,
        "timing_sd_ms": q(st.pstdev([g.offset(n.start) for n in top]) * g.ms16, 2) if len(top) > 1 else 0.0,
    }
    # leap recovery: after a leap of >=5, does the next move go the other way by a smaller step?
    rec, tot = 0, 0
    for a, b in zip(ivs, ivs[1:]):
        if abs(a) >= 5:
            tot += 1
            if b != 0 and (a > 0) != (b > 0) and abs(b) < abs(a):
                rec += 1
    out["leap_recovery"] = q(rec / tot) if tot else None
    return out


def arp_features(notes, g):
    f = line_features(notes, g)
    ns = sorted(notes, key=lambda n: n.start)
    ivs = [b.pitch - a.pitch for a, b in zip(ns, ns[1:])]
    up = sum(1 for i in ivs if i > 0)
    down = sum(1 for i in ivs if i < 0)
    f["direction"] = "up" if up > 2 * down else "down" if down > 2 * up else "up-down/other"
    iois = [(b.start - a.start) / g.s16 for a, b in zip(ns, ns[1:]) if b.start > a.start]
    f["rate_16ths"] = q(st.median(iois)) if iois else None
    # cycle length: smallest k where the interval sequence repeats
    cyc = None
    for k in range(2, 17):
        if len(ivs) > 2 * k and all(ivs[i] == ivs[i + k] for i in range(len(ivs) - k)):
            cyc = k
            break
    f["cycle_notes"] = cyc
    f["span"] = max(n.pitch for n in ns) - min(n.pitch for n in ns)
    return f


def chord_features(notes, g):
    by = defaultdict(list)
    for n in notes:  # notes within a 16th of each other form one chord (rolled or strummed chords count)
        by[g.step(n.start)].append(n.pitch)
    stacks = [sorted(v) for _, v in sorted(by.items()) if len(v) >= 2]
    if not stacks:
        return {"n": len(notes)}
    spans = [s[-1] - s[0] for s in stacks]
    moves = []
    for a, b in zip(stacks, stacks[1:]):
        m = sum(min(abs(x - y) for y in b) for x in a) / len(a)
        if set(a) != set(b):
            moves.append(m)
    bars = max(1, g.bar_of(max(n.start for n in notes)) + 1)
    changes = sum(1 for a, b in zip(stacks, stacks[1:]) if set(x % 12 for x in a) != set(x % 12 for x in b))
    return {"n": len(notes), "voices_median": st.median(len(s) for s in stacks), "span_median": st.median(spans),
            "bottom_median": st.median(s[0] for s in stacks), "voice_motion_median": q(st.median(moves)) if moves else None,
            "changes_per_bar": q(changes / bars, 2), "per_bar": q(len(stacks) / bars, 2)}


def classify(notes, hint):
    if hint:
        return hint
    pitches = [n.pitch for n in notes]
    by = Counter(n.start for n in notes)
    poly = st.mean(by.values())
    med = st.median(pitches)
    if poly >= 2.2:
        return "chords"
    if med < 50:
        return "bass"
    iois = sorted({n.start for n in notes})
    gaps = [b - a for a, b in zip(iois, iois[1:])]
    if len(gaps) > 8 and st.pstdev(gaps) < 0.15 * st.mean(gaps) and len(set(p % 12 for p in pitches)) <= 6:
        return "arp"
    return "melody"


def interplay(parts, g):
    """kick/bass lock, register spacing, call-and-response, two-voice motion"""
    out = {}
    kicks = sorted(n.start for n in parts.get("drums", []) if n.pitch in KICK)
    lows = parts.get("bass") or parts.get("808")
    tol = g.s16 / 2
    if kicks and lows:
        bon = onsets(lows)
        import bisect
        def near(t, arr):
            i = bisect.bisect_left(arr, t)
            return any(0 <= j < len(arr) and abs(arr[j] - t) <= tol for j in (i - 1, i))
        out["bass_on_kick"] = q(sum(near(t, kicks) for t in bon) / len(bon))
        out["kick_with_bass"] = q(sum(near(t, bon) for t in kicks) / len(kicks))
        sn = sorted(n.start for n in parts["drums"] if n.pitch in SNARE | CLAP and n.velocity >= 70)
        if sn:
            out["bass_on_snare"] = q(sum(near(t, sn) for t in bon) / len(bon))
    mel = parts.get("melody")
    if mel and parts.get("drums"):
        steps = Counter(g.step(n.start) for n in mel)
        dsteps = {g.step(n.start) for n in parts["drums"] if n.pitch in KICK | SNARE | CLAP}
        out["melody_on_kick_or_snare"] = q(sum(v for s, v in steps.items() if s in dsteps) / max(1, len(mel)))
    if mel and parts.get("chords"):
        cb = defaultdict(set)
        for n in parts["chords"]:
            for b in range(g.step(n.start), g.step(n.end)):
                cb[b].add(n.pitch % 12)
        tones = [n.pitch % 12 in cb.get(g.step(n.start), set()) for n in mel if cb.get(g.step(n.start))]
        if tones:
            out["melody_chord_tone_ratio"] = q(sum(tones) / len(tones))
        # space: fraction of melody notes that start while no chord attack happens in the same 16th
        catt = {g.step(n.start) for n in parts["chords"]}
        out["melody_avoids_chord_attacks"] = q(sum(g.step(n.start) not in catt for n in mel) / len(mel))
    if lows and parts.get("chords"):
        cs = defaultdict(list)
        for n in parts["chords"]:
            cs[n.start].append(n.pitch)
        bots = [min(v) for v in cs.values()]
        out["chord_bottom_minus_bass_median"] = q(st.median(bots) - st.median(n.pitch for n in lows), 1)
    return out


def counterpoint(tracks, g):
    """outer voices where at least two distinct pitches sound: contrary motion, parallel fifths,
    octave doubling, rhythmic complement between tracks"""
    by = defaultdict(list)
    for n in tracks:
        by[g.step(n.start)].append(n.pitch)
    steps = [s for s in sorted(by) if max(by[s]) - min(by[s]) > 0]
    if len(steps) < 16:
        return {}
    top = [max(by[s]) for s in steps]
    bot = [min(by[s]) for s in steps]
    con = sim = obl = p5 = 0
    dbl = sum(1 for t, b in zip(top, bot) if (t - b) % 12 == 0)
    for i in range(1, len(steps)):
        dt, db = top[i] - top[i - 1], bot[i] - bot[i - 1]
        if dt == 0 and db == 0:
            continue
        if dt == 0 or db == 0:
            obl += 1
        elif (dt > 0) != (db > 0):
            con += 1
        else:
            sim += 1
            if (top[i - 1] - bot[i - 1]) % 12 == 7 and (top[i] - bot[i]) % 12 == 7:
                p5 += 1
    tot = max(1, con + sim + obl)
    att = defaultdict(set)
    for n in tracks:
        att[g.step(n.start)].add(n.track)
    multi = len({n.track for n in tracks}) > 1
    single = sum(1 for v in att.values() if len(v) == 1)
    return {"contrary": q(con / tot), "similar": q(sim / tot), "oblique": q(obl / tot),
            "parallel_fifths_per_100_moves": q(100 * p5 / tot, 2), "outer_octave_doubling": q(dbl / len(steps)),
            "single_track_attack_ratio": q(single / len(att)) if multi else None}


def arrangement(notes, g, nbars):
    if nbars < 24:
        return {}
    dens = Counter(g.bar_of(n.start) for n in notes)
    tr = defaultdict(set)
    vel = defaultdict(list)
    for n in notes:
        b = g.bar_of(n.start)
        tr[b].add((n.track, n.channel))
        vel[b].append(n.velocity)
    curve = [dens.get(b, 0) for b in range(nbars)]
    layers = [len(tr.get(b, ())) for b in range(nbars)]
    # 8-bar block summaries and change points
    blocks = []
    for b in range(0, nbars, 8):
        seg = curve[b:b + 8]
        blocks.append({"bar": b + 1, "density": q(st.mean(seg), 1), "layers": q(st.mean(layers[b:b + 8]), 1),
                       "vel": q(st.mean([v for x in range(b, b + 8) for v in vel.get(x, [])]) if any(vel.get(x) for x in range(b, b + 8)) else 0, 1)})
    changes = sum(1 for a, b in zip(blocks, blocks[1:]) if abs(a["density"] - b["density"]) > 0.25 * max(1, a["density"]) or a["layers"] != b["layers"])
    mx = max(curve) or 1
    return {"bars": nbars, "blocks": blocks, "block_changes": changes, "density_cv": q(st.pstdev(curve) / (st.mean(curve) or 1)),
            "peak_block": max(blocks, key=lambda x: x["density"])["bar"], "quiet_bars_ratio": q(sum(1 for c in curve if c < 0.3 * mx) / nbars)}


def analyse(args):
    root, row = args
    path = os.path.join(root, row["rel"])
    try:
        s = midi_lib.read(path)
    except Exception as e:  # noqa: BLE001
        return {"rel": row["rel"], "error": str(e)[:200]}
    if not s.notes:
        return {"rel": row["rel"], "error": "no notes"}
    g = Grid(s)
    hint_role = None
    meta = row.get("meta", {})
    if row["source"] == "groove":
        hint_role = "drums"
    elif row["source"] == "zynthion":
        r = meta.get("role", "")
        hint_role = {"drums": "drums", "drum-fill": "drums", "808+drums": None, "hi-hat": "drums",
                     "808": "808", "bass": "bass", "melody": "melody", "arp": "arp"}.get(r)
    # group by (track, channel)
    groups = defaultdict(list)
    for n in s.notes:
        groups[(n.track, n.channel)].append(n)
    parts = defaultdict(list)
    roles = {}
    for (t, ch), ns in groups.items():
        if ch == midi_lib.DRUM_CHANNEL or hint_role == "drums":
            role = "drums"
        else:
            name = s.track_names.get(t, "").lower()
            nh = ("bass" if "bass" in name or "808" in name else "chords" if "chord" in name or "pad" in name or "keys" in name
                  else "arp" if "arp" in name else None)
            role = hint_role if hint_role and hint_role != "drums" else nh or classify(ns, None)
        roles[f"{t}:{ch}"] = role
        parts[role].extend(ns)
    nbars = max(1, g.bar_of(max(n.start for n in s.notes)) + 1)
    rec = {"rel": row["rel"], "source": row["source"], "status": row["status"], "holdout": row["holdout"],
           "meta": meta, "bpm": q(s.bpm, 2), "meter": f"{s.meter[0]}/{s.meter[1]}", "ppq": s.ppq, "bars": nbars,
           "roles": roles, "cc": {str(k): v for k, v in s.cc_counts.items()}, "pitchbends": s.pitchbend_count,
           "quantized_share": q(sum(1 for n in s.notes if abs(g.offset(n.start)) < 0.02) / len(s.notes))}
    pitched = [n for n in s.notes if n.channel != midi_lib.DRUM_CHANNEL and roles.get(f"{n.track}:{n.channel}") != "drums"]
    if pitched:
        rec["key"] = key_estimate(pitched)
    feats = {}
    for role, ns in parts.items():
        if role == "drums":
            feats[role] = drums_features(ns, g)
        elif role in ("bass", "808"):
            feats[role] = line_features(sorted(ns, key=lambda n: (n.start, n.pitch)), g)
        elif role == "arp":
            feats[role] = arp_features(ns, g)
        elif role == "chords":
            feats[role] = chord_features(ns, g)
        else:
            feats[role] = line_features(ns, g)
    rec["features"] = feats
    # Zynthion's 808 files come with a matching "- Drums.mid": measure the 808 against that kick.
    if row["source"] == "zynthion" and row["rel"].endswith(" - 808.mid"):
        sib = os.path.join(root, row["rel"][: -len(" - 808.mid")] + " - Drums.mid")
        if os.path.exists(sib):
            try:
                ds = midi_lib.read(sib)
                if ds.ppq == s.ppq:
                    parts["drums"] = ds.notes
                    rec["paired_drums"] = os.path.basename(sib)
            except Exception:  # noqa: BLE001
                pass
    rec["interplay"] = interplay(parts, g)
    if row["source"] in ("mutopia", "pdmx") and pitched:
        rec["counterpoint"] = counterpoint(pitched, g)
    rec["arrangement"] = arrangement(s.notes, g, nbars)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--sample-pdmx", type=int, default=4000)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(os.path.join(a.root, "_inventory", "inventory.jsonl"))]
    keep = []
    pdmx = []
    for r in rows:
        if not r.get("readable") or r.get("duplicate_of") or r.get("same_music_as") or r.get("transposition_of"):
            continue
        if r["source"] == "zynthion" and r["meta"].get("fl_split"):
            continue
        if r["status"].startswith("excluded"):
            continue
        (pdmx if r["source"] == "pdmx" else keep).append(r)
    random.seed(7)
    # stratify PDMX: keep the held-out ones in proportion, prefer rated and multi-track scores
    pdmx.sort(key=lambda r: (r["meta"].get("rating") in ("", "NA", "0", "0.0"), random.random()))
    keep += pdmx[: a.sample_pdmx]
    out = os.path.join(a.root, "_features")
    os.makedirs(out, exist_ok=True)
    n = 0
    with ProcessPoolExecutor(max_workers=min(2, a.workers)) as ex, open(os.path.join(out, "features.jsonl"), "w") as f:
        for rec in ex.map(analyse, [(a.root, r) for r in keep], chunksize=20):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print("analysed", n, "files")


if __name__ == "__main__":
    main()
