"""Objective scorer for TASKS.md outputs.

Usage: uv run --no-project --with mido python score.py <run_dir> [--refs <refs.json>] [--server <faderhand server.py>]
Prints and writes <run_dir>/SCORES.json. Every check is a measurement on the output files; none of them says
whether the music is good. `--refs` points at reference ranges built from held-out corpus files
(build_refs.py); without it the genre and feel checks use the fixed fallback ranges below.
"""
import argparse, ast, json, math, os, statistics as st, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.path.join(HERE, "..", "tools", "corpus"),):
    if os.path.exists(os.path.join(cand, "midi_lib.py")):
        sys.path.insert(0, os.path.abspath(cand))
        break
import midi_lib  # noqa: E402
import analyze  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def load(path):
    try:
        return midi_lib.read(path)
    except Exception:  # noqa: BLE001
        return None


def by_track(song):
    out = defaultdict(list)
    for n in song.notes:
        out[song.track_names.get(n.track, str(n.track))].append(n)
    return out


def check(name, ok, detail=""):
    return {"check": name, "pass": bool(ok), "detail": detail}


def within(v, lo, hi):
    return v is not None and lo <= v <= hi


def drum_parts(song):
    return [n for n in song.notes if n.channel == 9]


def pitched_parts(song):
    return [n for n in song.notes if n.channel != 9]


def position_structure(notes, g):
    """share of velocity variance explained by metric position (0 = random, 1 = fully patterned)"""
    if len(notes) < 8:
        return None
    by = defaultdict(list)
    for n in notes:
        by[g.pos(n.start)].append(n.velocity)
    allv = [n.velocity for n in notes]
    tot = st.pvariance(allv)
    if tot == 0:
        return 0.0
    between = sum(len(v) * (st.mean(v) - st.mean(allv)) ** 2 for v in by.values()) / len(allv)
    return round(between / tot, 3)


# ---------------------------------------------------------------- T01
def t01(run):
    truth = json.load(open(os.path.join(FIX, "comprehension.truth.json")))
    p = os.path.join(run, "t01_answers.json")
    if not os.path.exists(p):
        return [check("answers file exists", False)]
    a = json.load(open(p))
    norm = lambda s: str(s).lower().replace(" ", "").replace("maj7", "m7+").replace("Δ", "m7+")
    chords_ok = [norm(x) for x in a.get("chords", [])] == [norm(x) for x in truth["chords"]] or \
        [str(x).lower().replace("maj", "ma") for x in a.get("chords", [])] == ["dm7", "bbma7", "c7", "a7"]
    key = str(a.get("key", "")).lower().replace(" ", "")
    return [
        check("tempo", within(a.get("tempo_bpm"), 91, 93), a.get("tempo_bpm")),
        check("meter", a.get("meter") == "4/4", a.get("meter")),
        check("key", key in ("dminor", "dm", "dmin"), a.get("key")),
        check("bars", a.get("bars") == 16, a.get("bars")),
        check("roles", {k: str(v).lower() for k, v in (a.get("roles") or {}).items()} == truth["roles"], a.get("roles")),
        check("swing", within(a.get("swing_percent"), 55, 61), a.get("swing_percent")),
        check("bass onsets", a.get("bass_onsets_total") == 64, a.get("bass_onsets_total")),
        check("bass on kick", within(a.get("bass_onsets_on_kick"), 47, 49), a.get("bass_onsets_on_kick")),
        check("section change", a.get("arrangement_change_bar") == 9, a.get("arrangement_change_bar")),
        check("chords", chords_ok, a.get("chords")),
    ]


# ---------------------------------------------------------------- T02
def t02(run):
    p = os.path.join(run, "t02_edited.mid")
    src, out = load(os.path.join(FIX, "comprehension.mid")), load(p)
    if not out:
        return [check("edited file readable", False)]
    g = analyze.Grid(src)
    bar = g.bar
    sig = lambda n, name: (name, n.channel, n.pitch, n.start, n.end, n.velocity)
    exp = Counter()
    for name, ns in by_track(src).items():
        for n in ns:
            if name == "Bass" and 4 * bar <= n.start < 8 * bar:
                exp[(name, n.channel, n.pitch - 12, n.start, n.end, n.velocity)] += 1
            else:
                exp[sig(n, name)] += 1
    got = Counter()
    ghosts = []
    for name, ns in by_track(out).items():
        for n in ns:
            got[sig(n, name)] += 1
    missing = exp - got
    extra = got - exp
    want_steps = {5, 7, 13, 15}
    for (name, ch, pitch, start, end, vel), c in extra.items():
        if pitch == 38 and ch == 9 and 25 <= vel <= 45 and start < 4 * bar and \
                abs(analyze.Grid(out).offset(start)) < 0.26 and g.pos(start) in want_steps:
            ghosts += [start] * c
    ghost_ok = len(ghosts) == 16 and len(set(ghosts)) == 16
    unintended = sum(extra.values()) - len(ghosts)
    bass_moved = sum(1 for k in missing if k[0] == "Bass")
    tempo_ok = abs(out.bpm - src.bpm) < 0.01 and out.meter == src.meter
    return [
        check("bass bars 5-8 transposed exactly, rest of bass untouched", bass_moved == 0, f"{bass_moved} expected bass notes missing"),
        check("16 ghost snares at e/a of beats 2 and 4, bars 1-4, vel 25-45", ghost_ok, f"{len(ghosts)} found"),
        check("nothing else changed", not missing and unintended == 0, f"{sum(missing.values())} missing, {unintended} unexpected"),
        check("tempo and meter kept", tempo_ok, f"{out.bpm} {out.meter}"),
    ]


# ---------------------------------------------------------------- feature helpers
def feats(path, hint_parts=None):
    s = load(path)
    if not s:
        return None, None
    g = analyze.Grid(s)
    parts = defaultdict(list)
    for (t, ch), ns in _groups(s).items():
        name = s.track_names.get(t, "").lower()
        if ch == 9:
            role = "drums"
        elif "808" in name or "bass" in name:
            role = "bass"
        elif any(k in name for k in ("key", "chord", "pad", "rhodes", "piano", "ep")):
            role = "chords"
        elif any(k in name for k in ("lead", "melod", "fill", "hook", "vocal")):
            role = "melody"
        else:
            role = analyze.classify(ns, None)
        parts[role].extend(ns)
    return s, (g, parts)


def _groups(s):
    out = defaultdict(list)
    for n in s.notes:
        out[(n.track, n.channel)].append(n)
    return out


def ref_check(name, value, refs, key, fallback):
    lo, hi = (refs.get(key) or fallback) if refs else fallback
    return check(f"{name} in reference range [{lo}, {hi}]", within(value, lo, hi), value)


# ---------------------------------------------------------------- T03 trap
def t03(run, refs):
    s, x = feats(os.path.join(run, "t03_trap.mid"))
    if not s:
        return [check("trap file readable", False)]
    g, parts = x
    d = analyze.drums_features(parts["drums"], g) if parts.get("drums") else {}
    b = analyze.line_features(parts["bass"], g) if parts.get("bass") else {}
    ip = analyze.interplay(parts, g)
    hats = [n for n in parts.get("drums", []) if n.pitch in analyze.CHH]
    r = refs.get("trap", {}) if refs else {}
    glide = (b.get("legato_overlaps_per_bar") or 0) > 0 or s.pitchbend_count > 0
    return [
        check("tempo 140", abs(s.bpm - 140) < 0.5, s.bpm),
        check("all four parts present", all(parts.get(k) for k in ("drums", "bass", "melody")), sorted(parts)),
        ref_check("half-time backbeat share on beat 3", d.get("backbeat_3"), r, "backbeat_3", [0.6, 1.0]),
        ref_check("hat rolls per bar", d.get("hat_rolls_per_bar"), r, "hat_rolls_per_bar", [0.25, 3.0]),
        check("rolls use 32nds or triplets", any(k in (d.get("hat_roll_kinds") or {}) for k in ("32nd", "16th-triplet", "32nd-triplet")), d.get("hat_roll_kinds")),
        ref_check("808 onsets on a kick", ip.get("bass_on_kick"), r, "bass_on_kick", [0.5, 1.0]),
        ref_check("808 notes per bar", b.get("per_bar"), r, "808_per_bar", [1.5, 8.0]),
        check("808 glides or overlaps (slides)", glide, f"overlaps/bar {b.get('legato_overlaps_per_bar')}, bends {s.pitchbend_count}"),
        ref_check("hat velocity structure (variance explained by position)", position_structure(hats, g), r, "hat_position_structure", [0.25, 1.0]),
        check("drums not one bar repeated", (analyze.line_features(parts['drums'], g).get('bar_pattern_uniqueness') or 0) >= 0.25 if parts.get('drums') else False),
    ]


# ---------------------------------------------------------------- T04 funk feel
def t04(run, refs):
    s, x = feats(os.path.join(run, "t04_funk_drums.mid"))
    if not s:
        return [check("funk file readable", False)]
    g, parts = x
    d = analyze.drums_features(parts.get("drums") or s.notes, g)
    inst = d.get("instruments", {})
    hats = [n for n in s.notes if n.pitch in analyze.CHH | analyze.OHH | analyze.RIDE]
    r = refs.get("funk", {}) if refs else {}
    sn_t = (inst.get("snare") or {}).get("timing_sd_ms")
    hat_t = (inst.get("hat_closed") or inst.get("ride") or {}).get("timing_sd_ms")
    kick_t = (inst.get("kick") or {}).get("timing_sd_ms")
    qshare = sum(1 for n in s.notes if abs(g.offset(n.start)) < 0.02) / max(1, len(s.notes))
    return [
        ref_check("snare timing spread (ms)", sn_t, r, "snare_timing_sd_ms", [4, 20]),
        ref_check("hat timing spread (ms)", hat_t, r, "hat_timing_sd_ms", [4, 20]),
        ref_check("kick timing spread (ms)", kick_t, r, "kick_timing_sd_ms", [3, 20]),
        ref_check("share of notes exactly on the grid", round(qshare, 3), r, "quantized_share", [0.0, 0.25]),
        ref_check("ghost notes per bar", d.get("snare_ghost_per_bar"), r, "snare_ghost_per_bar", [1.0, 8.0]),
        ref_check("hat velocity structure", position_structure(hats, g), r, "hat_position_structure", [0.2, 1.0]),
        ref_check("hat velocity spread", (inst.get("hat_closed") or inst.get("ride") or {}).get("vel_sd"), r, "hat_vel_sd", [8, 30]),
        ref_check("snare velocity spread", (inst.get("snare") or {}).get("vel_sd"), r, "snare_vel_sd", [10, 40]),
    ]


# ---------------------------------------------------------------- T05 arrangement
def t05(run):
    p = os.path.join(run, "t05_song.mid")
    s = load(p)
    if not s:
        return [check("song file readable", False)]
    import mido
    markers = []
    for tr in mido.MidiFile(p).tracks:
        t = 0
        for m in tr:
            t += m.time
            if m.is_meta and m.type in ("marker", "cue_marker", "text") and m.type != "text" or (m.is_meta and m.type == "marker"):
                markers.append((t, m.text))
    g = analyze.Grid(s)
    nbars = g.bar_of(max(n.end for n in s.notes) - 1) + 1
    arr = analyze.arrangement(s.notes, g, nbars)
    bars = defaultdict(list)
    for n in s.notes:
        bars[g.bar_of(n.start)].append((n.track, n.pitch, g.pos(n.start), n.velocity))
    sigs = [tuple(sorted(bars.get(b, []))) for b in range(nbars)]
    exact_repeat = 1 - len(set(sigs)) / max(1, len(sigs))
    tracks_by_bar = [len({t for t, *_ in bars.get(b, [])}) for b in range(nbars)]
    # fills: drum density in the bar before each marker vs the median drum bar
    dbar = Counter(g.bar_of(n.start) for n in s.notes if n.channel == 9)
    med = st.median([dbar.get(b, 0) for b in range(nbars)]) or 1
    mbars = sorted({g.bar_of(t) for t, _ in markers if t > 0})
    fills = sum(1 for b in mbars if b >= 1 and (dbar.get(b - 1, 0) > 1.2 * med or dbar.get(b - 1, 0) < 0.5 * med))
    return [
        check("at least 48 bars", nbars >= 48, nbars),
        check("at least 5 section markers", len({txt for _, txt in markers}) >= 5, [m[1] for m in markers][:12]),
        check("arrangement changes between 8-bar blocks (>=4)", (arr.get("block_changes") or 0) >= 4, arr.get("block_changes")),
        check("layer count varies (min < max)", min(tracks_by_bar) < max(tracks_by_bar), f"{min(tracks_by_bar)}..{max(tracks_by_bar)}"),
        check("exact bar repetition below 60%", exact_repeat < 0.6, round(exact_repeat, 3)),
        check("drum fill or drop before most section changes", mbars and fills >= 0.5 * len(mbars), f"{fills}/{len(mbars)}"),
        check("density varies (CV >= 0.25)", (arr.get("density_cv") or 0) >= 0.25, arr.get("density_cv")),
    ]


# ---------------------------------------------------------------- T06 interaction
def t06(run, refs):
    s, x = feats(os.path.join(run, "t06_neosoul.mid"))
    if not s:
        return [check("neo-soul file readable", False)]
    g, parts = x
    ip = analyze.interplay(parts, g)
    ch = parts.get("chords", [])
    d = analyze.drums_features(parts["drums"], g) if parts.get("drums") else {}
    chord_top = st.median(sorted(n.pitch for n in ch)[-max(1, len(ch) // 4):]) if ch else None
    gch = analyze.Grid(s)
    stacks = Counter(gch.step(n.start) for n in ch)  # a rolled chord (notes a few ms apart) is one chord
    attacks_per_bar = len(stacks) / max(1, analyze.Grid(s).bar_of(max(n.start for n in s.notes)) + 1)
    voices = st.median(stacks.values()) if stacks else 0
    return [
        check("tempo 84", abs(s.bpm - 84) < 0.5, s.bpm),
        check("bass and kick interlock: >=40% of bass onsets on kicks", within(ip.get("bass_on_kick"), 0.4, 1.0), ip.get("bass_on_kick")),
        check("most kicks have bass with them (>=50%)", within(ip.get("kick_with_bass"), 0.5, 1.0), ip.get("kick_with_bass")),
        check("bass also moves between kicks (on-kick share <= 90%)", within(ip.get("bass_on_kick"), 0.0, 0.9), ip.get("bass_on_kick")),
        check("chord upper voices stay under the vocal (median top <= 74)", chord_top is not None and chord_top <= 74, chord_top),
        check("chords are not a wall: <= 4 attacks per bar", attacks_per_bar <= 4, round(attacks_per_bar, 2)),
        check("extended voicings (median >= 4 notes)", voices >= 4, voices),
        check("drums have ghost notes", (d.get("snare_ghost_per_bar") or 0) >= 1, d.get("snare_ghost_per_bar")),
        check("played feel: not all on the grid", sum(1 for n in s.notes if abs(g.offset(n.start)) < 0.02) / len(s.notes) < 0.5),
    ]


# ---------------------------------------------------------------- T07 Vital
def t07(run):
    p = os.path.join(run, "t07_vital.json")
    if not os.path.exists(p):
        return [check("vital answers exist", False)]
    a = json.load(open(p))
    num = lambda k: (float(a[k]) if isinstance(a.get(k), (int, float, str)) and str(a.get(k)).replace('.', '', 1).replace('-', '', 1).isdigit() else None)
    return [
        check("unison_detune 20 cents = 20/17.5", within(num("unison_detune"), 1.09, 1.20), a.get("unison_detune")),
        check("volume -6 dB ~ 4612 (log interp 4400..5473)", within(num("volume"), 4540, 4690), a.get("volume")),
        check("reverb_decay_time 3 s = log2(3)", within(num("reverb_decay_time"), 1.55, 1.62), a.get("reverb_decay_time")),
        check("delay_frequency 375 ms = log2(1/0.375)", within(num("delay_frequency"), 1.38, 1.45), a.get("delay_frequency")),
        check("osc_1_tune +25 cents = 0.25 semitones", within(num("osc_1_tune"), 0.24, 0.26), a.get("osc_1_tune")),
    ]


# ---------------------------------------------------------------- T08 Faderhand plan
def server_tools(server):
    tree = ast.parse(open(server).read())
    tools = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any((isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "tool") or getattr(d, "attr", "") == "tool"
                   for d in node.decorator_list):
                tools[node.name] = {a.arg for a in node.args.args + node.args.kwonlyargs}
    return tools


def t08(run, server):
    p = os.path.join(run, "t08_calls.json")
    if not os.path.exists(p):
        return [check("calls file exists", False)]
    calls = json.load(open(p))
    if isinstance(calls, dict):
        calls = calls.get("calls") or calls.get("tool_calls") or []
    tools = server_tools(server)
    valid = 0
    bad = []
    for c in calls:
        t, args = c.get("tool"), c.get("args") or {}
        if t in tools and set(args) <= tools[t]:
            valid += 1
        else:
            bad.append(t)
    names = [c.get("tool") for c in calls]
    blob = json.dumps(calls).lower()
    return [
        check("every call is a real tool with real argument names", calls and valid == len(calls), f"{valid}/{len(calls)} valid; bad: {bad[:5]}"),
        check("creates return Plate", "create_return_track" in names and "plate" in blob),
        check("loads Reverb on the return", "load_effect_on_return_track" in names and "reverb" in blob),
        check("sends Keys at -14 dB", "set_track_send" in names and "-14" in blob),
        check("Compressor on Bass sidechained from Kick", "set_sidechain" in names and "compressor" in blob),
        check("Auto Filter loaded and automated 300 Hz -> 8 kHz", "auto filter" in blob and any(n and "automation" in n for n in names) and ("8000" in blob or "8 khz" in blob or "8k" in blob)),
    ]


# ---------------------------------------------------------------- T09 + T10
def t09_t10(run, refs):
    p = os.path.join(run, "t10_revised.mid")
    src, out = load(os.path.join(FIX, "flawed.mid")), load(p)
    if not out:
        return [check("revised file readable", False)], [check("revised file readable", False)]
    truth = json.load(open(os.path.join(FIX, "flawed.truth.json")))
    g = analyze.Grid(out)
    tr = by_track(out)
    keys = tr.get("Keys") or [n for n in out.notes if n.channel == 1]
    lead = tr.get("Lead") or [n for n in out.notes if n.channel == 2]
    kept_bars = 0
    for b in range(8):
        pcs = sorted({n.pitch for n in keys if g.bar_of(n.start) == b})
        if pcs == truth["protected_chord_pitches_by_bar"][b]:
            kept_bars += 1
    seq_ok = 0
    for b in range(8):
        seq = [n.pitch for n in sorted((n for n in lead if g.bar_of(n.start + g.s16 // 2) == b), key=lambda n: n.start)]
        if seq == truth["protected_hook_pitch_sequence"]:
            seq_ok += 1
    t09 = [check("chord pitches kept in all 8 bars", kept_bars == 8, f"{kept_bars}/8"),
           check("hook pitch sequence kept in all 8 bars", seq_ok == 8, f"{seq_ok}/8")]
    parts = defaultdict(list)
    for n in out.notes:
        parts["drums" if n.channel == 9 else "bass" if n.channel == 0 or n in (tr.get("Bass") or []) else "other"].append(n)
    ip = analyze.interplay(parts, g)
    hats = [n for n in parts["drums"] if n.pitch in analyze.CHH | analyze.OHH]
    bars = defaultdict(list)
    for n in parts["drums"] + parts["bass"]:
        bars[g.bar_of(n.start)].append((n.pitch, g.pos(n.start)))
    uniq = len({tuple(sorted(v)) for v in bars.values()}) / max(1, len(bars))
    vels = [n.velocity for n in out.notes]
    offs = [abs(g.offset(n.start)) * g.ms16 for n in out.notes]
    t10 = [
        check("velocities no longer flat (SD >= 8)", st.pstdev(vels) >= 8, round(st.pstdev(vels), 1)),
        check("hat velocities follow the beat, not noise (structure >= 0.25)", (position_structure(hats, g) or 0) >= 0.25, position_structure(hats, g)),
        check("timing moved off the grid but stays tight (median 2-20 ms)", within(st.median(offs), 2, 20), round(st.median(offs), 1)),
        check("bass now lands with the kick (>= 60%)", (ip.get("bass_on_kick") or 0) >= 0.6, ip.get("bass_on_kick")),
        check("drums+bass develop: >= 50% distinct bars", uniq >= 0.5, round(uniq, 2)),
        check("still 8 bars at 96 BPM", abs(out.bpm - 96) < 0.5 and g.bar_of(max(n.start for n in out.notes)) + 1 == 8),
    ]
    return t09, t10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--refs")
    ap.add_argument("--server", default=os.path.join(HERE, "..", "..", "..", "server", "ableton_tooling_server.py"))
    a = ap.parse_args()
    refs = json.load(open(a.refs)) if a.refs else {}
    res = {"T01": t01(a.run), "T02": t02(a.run), "T03": t03(a.run, refs), "T04": t04(a.run, refs), "T05": t05(a.run),
           "T06": t06(a.run, refs), "T07": t07(a.run), "T08": t08(a.run, a.server)}
    res["T09"], res["T10"] = t09_t10(a.run, refs)
    summary = {k: f"{sum(c['pass'] for c in v)}/{len(v)}" for k, v in res.items()}
    total = sum(sum(c["pass"] for c in v) for v in res.values())
    n = sum(len(v) for v in res.values())
    out = {"summary": summary, "total": f"{total}/{n}", "checks": res}
    json.dump(out, open(os.path.join(a.run, "SCORES.json"), "w"), indent=1, default=str)
    print(json.dumps(summary), "total", out["total"])


if __name__ == "__main__":
    main()
