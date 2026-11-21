"""Measure a MIDI file against what the corpus shows for its genre, and say what to revise.

Usage:
  uv run -q --no-project --with mido python tools/midi_check.py song.mid --genre trap [--json]
  genres: trap, drill, boom-bap, hiphop-live, funk, soul, neo-soul, rnb, lofi, house, techno, afro,
          rock, jazz, latin, classical, orchestral, pop, generic

It reads the tracks, guesses each part's role (drums on channel 10; names such as "808", "bass", "keys",
"lead" win over guesses), measures them with the corpus analyser, and compares the numbers with target
ranges. The ranges come from TARGETS.md beside this file: Groove MIDI (human drumming, CC BY 4.0), Mutopia and
PDMX (public domain / CC) and, for programmed electronic and trap patterns, aggregate statistics from
packs whose numbers stay on this machine.

A PASS means a number sits where the reference material sits. It does not mean the music is good, and a
deliberate choice outside a range is fine when the brief asks for it: say so in the notes.
"""
import argparse, json, os, statistics as st, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "corpus"))
import midi_lib  # noqa: E402
import analyze  # noqa: E402

# Target ranges (lo, hi). None = no check. See TARGETS.md beside this file for where every number comes from.
LIVE = {  # human-played drum feel (Groove MIDI, beats, 10th-90th percentile, rounded)
    "quantized_share": (0.0, 0.3), "drum_jitter_ms": (3, 12), "hat_vel_structure": (0.2, 0.8),
    "hat_vel_sd": (8, 27), "snare_vel_sd": (12, 45), "snare_behind_hats_ms": (2, 25),
}
PROGRAMMED = {"quantized_share": (0.6, 1.0), "drum_jitter_ms": (0, 6)}
GENRES = {
    "trap": {"tempo": (128, 160), "half_time": True, "hat_rolls_per_bar": (0.25, 1.5), "low_on_kick": (0.35, 1.0),
             "kick_with_low": (0.8, 1.0), "low_per_bar": (2.5, 6.5), "low_glide_per_bar": (0.5, 3.0), "lead_range": (5, 16),
             "lead_phrase_notes": (3, 12), **PROGRAMMED},
    "drill": {"tempo": (136, 146), "half_time": True, "hat_rolls_per_bar": (0.25, 1.5), "roll_kind": "triplet",
              "low_on_kick": (0.3, 1.0), "kick_with_low": (0.8, 1.0), "low_per_bar": (3.5, 6.5), "low_glide_per_bar": (1.0, 3.0),
              "low_octave_jump": (0.25, 0.6), **PROGRAMMED},
    "boom-bap": {"tempo": (80, 98), "backbeat_2_4": (0.6, 1.0), "swing": (52, 62), "ghost_per_bar": (0.5, 4), **LIVE},
    "hiphop-live": {"tempo": (70, 100), "backbeat_2_4": (0.6, 1.0), "swing": (50, 61), "ghost_per_bar": (0.5, 5), **LIVE},
    "funk": {"tempo": (85, 120), "backbeat_2_4": (0.6, 1.0), "swing": (51, 74), "ghost_per_bar": (1.5, 7), **LIVE},
    "soul": {"tempo": (80, 120), "backbeat_2_4": (0.6, 1.0), "swing": (55, 77), "ghost_per_bar": (1, 5), **LIVE},
    "neo-soul": {"tempo": (70, 100), "backbeat_2_4": (0.6, 1.0), "swing": (54, 68), "ghost_per_bar": (1, 5), "low_on_kick": (0.35, 0.9),
                 "kick_with_low": (0.5, 1.0), "low_step_ratio": (0.12, 0.6), "chord_voices": (4, 7), **LIVE},
    "rnb": {"tempo": (60, 110), "low_step_ratio": (0.12, 0.6), "chord_voices": (3, 7)},
    "lofi": {"tempo": (70, 92), "backbeat_2_4": (0.6, 1.0), "swing": (52, 66), "low_step_ratio": (0.1, 0.6)},
    "house": {"tempo": (118, 128), "four_floor": True, **PROGRAMMED},
    "techno": {"tempo": (124, 150), "four_floor": True, "low_offbeat": (0.3, 1.0), **PROGRAMMED},
    "afro": {"tempo": (100, 125)},
    "rock": {"tempo": (80, 150), "backbeat_2_4": (0.6, 1.0), **LIVE},
    "jazz": {"swing": (55, 77), **LIVE},
    "latin": {**LIVE},
    "pop": {},
    "classical": {"lead_step_ratio": (0.3, 0.65), "lead_leap_recovery": (0.3, 0.7), "contrary": (0.2, 0.55), "parallel_fifths": (0, 2.0)},
    "orchestral": {"lead_step_ratio": (0.3, 0.65), "contrary": (0.15, 0.55), "parallel_fifths": (0, 2.0)},
    "generic": {},
}
GENERIC = {"bar_uniqueness_min": 0.3, "random_velocity_max_sd_without_structure": 10}


def role_of(song, t, ch, notes):
    if ch == 9:
        return "drums"
    name = song.track_names.get(t, "").lower()
    if "808" in name:
        return "808"
    for key, role in (("bass", "bass"), ("sub", "bass"), ("arp", "arp"), ("pad", "chords"), ("chord", "chords"), ("keys", "chords"),
                      ("piano", "chords"), ("rhodes", "chords"), ("ep", "chords"), ("lead", "melody"), ("melod", "melody"),
                      ("hook", "melody"), ("vocal", "melody"), ("fill", "melody"), ("drum", "drums"), ("perc", "drums")):
        if key in name:
            return role
    return analyze.classify(notes, None)


def measure(path):
    s = midi_lib.read(path)
    g = analyze.Grid(s)
    parts = defaultdict(list)
    groups = defaultdict(list)
    for n in s.notes:
        groups[(n.track, n.channel)].append(n)
    roles = {}
    for (t, ch), ns in groups.items():
        r = role_of(s, t, ch, ns)
        roles[s.track_names.get(t, f"track {t}")] = r
        parts[r].extend(ns)
    low = parts.get("808") or parts.get("bass")
    m = {"tempo": round(s.bpm, 1), "meter": f"{s.meter[0]}/{s.meter[1]}", "roles": roles,
         "bars": g.bar_of(max(n.end for n in s.notes) - 1) + 1 if s.notes else 0}
    m["quantized_share"] = round(sum(1 for n in s.notes if abs(g.offset(n.start)) < 0.02) / max(1, len(s.notes)), 3)
    if parts.get("drums"):
        d = analyze.drums_features(parts["drums"], g)
        inst = d["instruments"]
        hat = inst.get("hat_closed") or inst.get("ride") or {}
        sn = inst.get("snare") or inst.get("clap") or {}
        jit = [x.get("jitter_local_ms") for x in inst.values() if x.get("jitter_local_ms") is not None]
        m.update({"backbeat_2_4": d.get("backbeat_2_4"), "backbeat_3": d.get("backbeat_3"), "swing": d.get("swing_percent_16"),
                  "ghost_per_bar": d.get("snare_ghost_per_bar"), "hat_rolls_per_bar": d.get("hat_rolls_per_bar"),
                  "roll_kinds": d.get("hat_roll_kinds"), "roll_velocity_shape": d.get("hat_roll_velocity_shape"),
                  "hat_vel_structure": hat.get("vel_structure"), "hat_vel_sd": hat.get("vel_sd"), "snare_vel_sd": sn.get("vel_sd"),
                  "drum_jitter_ms": round(st.median(jit), 1) if jit else None})
        hp, sp = hat.get("placement_ms") or {}, sn.get("placement_ms") or {}
        bb = [sp[k] for k in ("4", "12") if k in sp]
        hb = [hp[k] for k in ("4", "12", "0", "8") if k in hp]
        if bb and hb:
            m["snare_behind_hats_ms"] = round(st.mean(bb) - st.mean(hb), 1)
        kick = inst.get("kick") or {}
        ph = kick.get("pos_hist") or []
        hats = [n for n in parts["drums"] if n.pitch in analyze.CHH | analyze.OHH]
        m["hat_min_velocity"] = min((n.velocity for n in hats), default=None)
        # largest deviation from each position's own average placement (swing and laid-back placement don't count)
        bypos = defaultdict(list)
        for n in parts["drums"]:
            bypos[(n.pitch, g.pos(n.start))].append(g.offset(n.start))
        m["max_offset_ms"] = round(max(abs(o - st.mean(v)) for v in bypos.values() for o in v) * g.ms16, 1)
        m["four_floor"] = len(ph) == 16 and all(ph[i] >= 0.75 for i in (0, 4, 8, 12))
        m["drum_bar_uniqueness"] = analyze.line_features(parts["drums"], g).get("bar_pattern_uniqueness")
    if low:
        lf = analyze.line_features(sorted(low, key=lambda n: (n.start, n.pitch)), g)
        m.update({"low_per_bar": lf["per_bar"], "low_glide_per_bar": round(lf["legato_overlaps_per_bar"] + min(2.0, s.pitchbend_count / max(1, lf["bars"]) / 8), 2),
                  "low_octave_jump": lf["octave_jump_ratio"], "low_step_ratio": lf["step_ratio"], "low_offbeat": lf["offbeat_ratio"],
                  "low_bar_uniqueness": lf["bar_pattern_uniqueness"], "low_vel_sd": lf["vel_sd"]})
        if s.pitchbend_count:
            m["pitchbend_events"] = s.pitchbend_count
    ip = analyze.interplay({"drums": parts.get("drums", []), "bass": low or [], "melody": parts.get("melody", []),
                            "chords": parts.get("chords", [])}, g)
    m["low_on_kick"] = ip.get("bass_on_kick")
    m["kick_with_low"] = ip.get("kick_with_bass")
    m["melody_chord_tone_ratio"] = ip.get("melody_chord_tone_ratio")
    m["chord_bottom_minus_bass"] = ip.get("chord_bottom_minus_bass_median")
    lead = parts.get("melody")
    if lead:
        lf = analyze.line_features(lead, g)
        m.update({"lead_range": lf["range"], "lead_step_ratio": lf["step_ratio"], "lead_leap_recovery": lf["leap_recovery"],
                  "lead_phrase_notes": lf["phrase_notes_median"], "lead_bar_uniqueness": lf["bar_pattern_uniqueness"],
                  "lead_vel_sd": lf["vel_sd"]})
    if parts.get("chords"):
        c = analyze.chord_features(parts["chords"], g)
        m["chord_voices"] = c.get("voices_median")
        m["chord_top_median"] = None
    pitched = [n for r, ns in parts.items() if r != "drums" for n in ns]
    if pitched:
        cp = analyze.counterpoint(pitched, g)
        m["contrary"] = cp.get("contrary")
        m["parallel_fifths"] = cp.get("parallel_fifths_per_100_moves")
    # whole-file repetition and velocity sanity
    bars = defaultdict(list)
    for n in s.notes:
        bars[g.bar_of(n.start)].append((n.track, n.pitch, g.pos(n.start)))
    sig = [tuple(sorted(v)) for _, v in sorted(bars.items())]
    m["bar_uniqueness"] = round(len(set(sig)) / max(1, len(sig)), 3)
    vels = [n.velocity for n in s.notes]
    m["velocity_sd"] = round(st.pstdev(vels), 1) if len(vels) > 1 else 0
    m["distinct_velocities"] = len(set(vels))
    if s.notes and len(sig) >= 24:
        arr = analyze.arrangement(s.notes, g, len(sig))
        m["arrangement_block_changes"] = arr.get("block_changes")
        m["density_cv"] = arr.get("density_cv")
    return m


def verdicts(m, genre):
    t = GENRES.get(genre, {})
    out = []

    def rng(key, label, advice):
        if key not in t or m.get(key) is None:
            return
        lo, hi = t[key]
        v = m[key]
        ok = lo <= v <= hi
        out.append(("PASS" if ok else "REVISE", f"{label}: {v} (target {lo}-{hi})", None if ok else advice))

    rng("tempo", "tempo", "set the tempo the genre lives at, or say why not")
    if t.get("half_time"):
        v = m.get("backbeat_3")
        ok = v is not None and v >= 0.6
        out.append(("PASS" if ok else "REVISE", f"half-time backbeat on beat 3: {v}", None if ok else "put the snare/clap on beat 3 of each bar (half-time), not on 2 and 4"))
    if t.get("four_floor"):
        ok = m.get("four_floor")
        out.append(("PASS" if ok else "REVISE", f"four-on-the-floor kick: {ok}", None if ok else "kick on every quarter note"))
    rng("backbeat_2_4", "backbeat on 2 and 4", "accent the snare on beats 2 and 4")
    rng("swing", "16th swing %", "move the off-16ths later (swing) by the target amount; keep it consistent per instrument")
    rng("ghost_per_bar", "ghost snares per bar", "add quiet snare notes (25-55 velocity) mostly on the 'a' of 2 and 4 and the 'e' of 3")
    rng("hat_rolls_per_bar", "hat rolls per bar", "add 32nd or triplet hat rolls, mostly leading into beat 3 or the next bar, with rising velocity")
    if t.get("roll_kind") == "triplet" and m.get("roll_kinds"):
        ok = any("triplet" in k for k in m["roll_kinds"])
        out.append(("PASS" if ok else "REVISE", f"roll subdivisions: {m['roll_kinds']}", None if ok else "drill rolls are mostly 16th or 32nd triplets"))
    if m.get("roll_velocity_shape") and "hat_rolls_per_bar" in t:
        shp = m["roll_velocity_shape"]
        ok = shp.get("rising", 0) >= sum(shp.values()) / 2
        out.append(("PASS" if ok else "WARN", f"roll velocity shape: {shp}", None if ok else "ramp roll velocities up into the target beat; flat rolls sound like a stuck note"))
    rng("low_on_kick", "share of 808/bass notes that land on a kick", "anchor the low end on the kicks, then add pickups between them")
    rng("kick_with_low", "share of kicks with an 808/bass note", "give (nearly) every kick a low note")
    rng("low_per_bar", "808/bass notes per bar", "change the 808/bass density toward the target")
    rng("low_glide_per_bar", "808 slides per bar (overlapping notes or bends)", "overlap consecutive 808 notes (portamento/legato) for slides")
    rng("low_octave_jump", "808 octave-jump share", "use octave jumps on the 808 more (drill) or less")
    rng("low_step_ratio", "bass stepwise share", "walk the bass: approach chord roots by step or chromatic neighbour")
    rng("low_offbeat", "bass off-16th share", "move bass notes to the offbeats")
    rng("chord_voices", "chord voices", "voice chords with 4+ notes (7ths, 9ths) in a mid register")
    rng("lead_range", "lead range (semitones)", "keep the hook inside about an octave; widen or narrow it")
    rng("lead_phrase_notes", "notes per lead phrase", "shorter phrases with rests between them")
    rng("lead_step_ratio", "melody stepwise share", "more steps, fewer leaps (or the reverse)")
    rng("lead_leap_recovery", "leaps recovered by step the other way", "after a leap of a 4th or more, move back by step")
    rng("contrary", "outer voices in contrary motion", "move bass and top line in opposite directions more often")
    rng("parallel_fifths", "parallel fifths per 100 moves", "remove parallel fifths between the outer voices")
    for key, label, adv in (("quantized_share", "share of notes exactly on the grid", "for a played feel, move notes off the grid by a few ms; for programmed genres, quantize"),
                            ("drum_jitter_ms", "drum timing jitter (ms)", "set timing variation to the target: consistent per-position placement plus small jitter"),
                            ("hat_vel_structure", "hat velocity follows the beat (0-1)", "accent hats by position: beats loudest, offbeat 8ths middle, 16ths quietest; then vary a little"),
                            ("hat_vel_sd", "hat velocity spread", "widen or narrow hat velocity spread"),
                            ("snare_vel_sd", "snare velocity spread", "backbeats loud, ghosts quiet"),
                            ("snare_behind_hats_ms", "snare backbeat later than the hats (ms)", "place the backbeat a few ms behind the hats for a laid-back pocket")):
        rng(key, label, adv)
    # generic checks for every genre
    if "low_on_kick" not in t and m.get("low_on_kick") is not None and m["low_on_kick"] < 0.3:
        out.append(("WARN", f"only {m['low_on_kick']:.0%} of bass notes land with a kick", "unless the style is deliberately independent (walking, offbeat), lock more bass onsets to the kicks"))
    if m.get("distinct_velocities", 0) <= 2 and m.get("velocity_sd", 0) < 3:
        out.append(("REVISE", f"velocities are flat ({m['distinct_velocities']} distinct)", "shape velocity by role and position; flat velocity is the most common machine tell"))
    if m.get("hat_min_velocity") is not None and m["hat_min_velocity"] < 25:
        out.append(("WARN", f"quietest hat velocity {m['hat_min_velocity']}", "keep hats at about 30 or more; very quiet hats vanish on most samplers"))
    if m.get("max_offset_ms") is not None and m["max_offset_ms"] > 30 and "drum_jitter_ms" in t and t["drum_jitter_ms"][1] > 6:
        out.append(("WARN", f"a drum note sits {m['max_offset_ms']} ms away from where that drum usually plays that position", "keep single notes within about 25 ms of their position's usual placement unless it's a deliberate flam or drag"))
    hvs = m.get("hat_vel_structure")
    if hvs is not None and hvs < 0.15 and (m.get("hat_vel_sd") or 0) > 10:
        out.append(("REVISE", f"hat velocity looks random (structure {hvs})", "replace random velocity with a position accent pattern plus small variation"))
    if m.get("bar_uniqueness") is not None and m["bars"] >= 4 and m["bar_uniqueness"] < GENERIC["bar_uniqueness_min"]:
        out.append(("REVISE", f"only {m['bar_uniqueness']:.0%} of bars differ", "vary every 2nd or 4th bar: a fill, a dropped kick, a hat roll, a bass pickup, a melodic answer"))
    if m.get("bars", 0) >= 24 and (m.get("arrangement_block_changes") or 0) < 3:
        out.append(("REVISE", f"arrangement barely changes ({m.get('arrangement_block_changes')} changes between 8-bar blocks)", "change layers, density or register at section boundaries"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("midi")
    ap.add_argument("--genre", default="generic", choices=sorted(GENRES))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    m = measure(a.midi)
    v = verdicts(m, a.genre)
    if a.json:
        print(json.dumps({"measures": m, "verdicts": v}, indent=1, default=str))
        return
    print(f"{os.path.basename(a.midi)}  genre={a.genre}  tempo={m['tempo']}  meter={m['meter']}  bars={m['bars']}")
    print("roles:", m["roles"])
    for status, msg, adv in v:
        print(f"  [{status}] {msg}" + (f"\n          -> {adv}" if adv else ""))
    n = sum(1 for s, *_ in v if s == "REVISE")
    print(f"{n} to revise. Measurements are evidence for revision, not a verdict on the music: listen too.")


if __name__ == "__main__":
    main()
