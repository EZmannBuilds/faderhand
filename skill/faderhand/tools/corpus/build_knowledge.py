"""Aggregate _features/features.jsonl into compact statistics for the skill, and held-out reference ranges.

Usage: python3 -I build_knowledge.py <corpus_root> <skill_knowledge_dir>
Writes:
  <knowledge>/stats/*.json          from approved sources (Groove, Mutopia, PDMX): may ship
  <knowledge>/local/*.json          from pending sources (Zynthion): local only, never shipped (gitignored)
  <corpus_root>/_evals/refs.json    p10..p90 ranges from HELD-OUT files only, for evaluation/score.py
Only aggregate numbers (medians, ranges, counts, histograms) are written: no notes, no per-file patterns.
"""
import json, os, sys
from collections import Counter, defaultdict


def pct(vals, p):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    k = (len(v) - 1) * p
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return round(v[f] + (v[c] - v[f]) * (k - f), 3)


def dist(vals):
    v = [x for x in vals if x is not None]
    return {"median": pct(v, .5), "p10": pct(v, .1), "p90": pct(v, .9), "n": len(v)} if v else None


def mean_hist(hists):
    hs = [h for h in hists if h]
    if not hs:
        return None
    L = max(len(h) for h in hs)
    return [round(sum((h[i] if i < len(h) and h[i] is not None else 0) for h in hs) / len(hs), 3) for i in range(L)]


def counter_sum(dicts):
    c = Counter()
    for d in dicts:
        c.update(d or {})
    return dict(c.most_common())


def drums_block(recs):
    d = [r["features"]["drums"] for r in recs if "drums" in r["features"]]
    out = {"files": len(d), "bpm": dist([r["bpm"] for r in recs]), "quantized_share": dist([r["quantized_share"] for r in recs])}
    for inst in ("kick", "snare", "clap", "hat_closed", "hat_open", "ride"):
        I = [x["instruments"][inst] for x in d if inst in x["instruments"]]
        if len(I) < 3:
            continue
        pl = defaultdict(list)
        for x in I:
            for k, v in (x.get("placement_ms") or {}).items():
                pl[k].append(v)
        out[inst] = {
            "present_in": round(len(I) / len(d), 3),
            "hits_per_bar": dist([x["per_bar"] for x in I]),
            "position_rate": mean_hist([x["pos_hist"] for x in I]),
            "velocity_by_position": mean_hist([[v if v is not None else 0 for v in x["vel_by_pos"]] for x in I]),
            "velocity_sd": dist([x["vel_sd"] for x in I]),
            "velocity_structure": dist([x.get("vel_structure") for x in I]),
            "jitter_local_ms": dist([x.get("jitter_local_ms") for x in I]),
            "placement_ms_by_position": {k: dist(v) for k, v in sorted(pl.items(), key=lambda kv: int(kv[0])) if len(v) >= 3},
        }
    out["swing_percent_16"] = dist([x.get("swing_percent_16") for x in d])
    out["snare_ghost_per_bar"] = dist([x.get("snare_ghost_per_bar") for x in d])
    out["ghost_positions"] = counter_sum([x.get("ghost_positions") for x in d])
    out["backbeat_2_4"] = dist([x.get("backbeat_2_4") for x in d])
    out["backbeat_3"] = dist([x.get("backbeat_3") for x in d])
    out["hat_rolls_per_bar"] = dist([x.get("hat_rolls_per_bar") for x in d])
    out["hat_roll_kinds"] = counter_sum([x.get("hat_roll_kinds") for x in d])
    out["hat_roll_start_beat"] = counter_sum([x.get("hat_roll_start_beat") for x in d])
    out["hat_roll_velocity_shape"] = counter_sum([x.get("hat_roll_velocity_shape") for x in d])
    hv = [x.get("hat_vel_by_subdivision") or {} for x in d]
    out["hat_velocity_by_subdivision"] = {k: dist([h.get(k) for h in hv]) for k in ("beat", "8th", "16th")}
    return out


LINE_KEYS = ["per_bar", "pitch_median", "range", "step_ratio", "leap_ratio", "repeat_ratio", "octave_jump_ratio",
             "contour_change_rate", "leap_recovery", "gate_median", "offbeat_ratio", "phrase_notes_median",
             "vel_sd", "legato_overlaps_per_bar", "bar_pattern_uniqueness", "timing_sd_ms"]


def line_block(fs, extra=()):
    out = {"files": len(fs)}
    for k in list(LINE_KEYS) + list(extra):
        out[k] = dist([f.get(k) for f in fs])
    out["interval_hist"] = counter_sum([f.get("interval_hist") for f in fs])
    out["duration_16ths"] = counter_sum([f.get("dur_hist_16ths") for f in fs])
    out["position_rate"] = mean_hist([f.get("pos_hist") for f in fs if f.get("pos_hist") and len(f["pos_hist"]) == 16])
    if "direction" in extra or any("direction" in f for f in fs):
        out["direction"] = dict(Counter(f.get("direction") for f in fs))
    return out


def main(root, kdir):
    rows = [json.loads(l) for l in open(os.path.join(root, "_features", "features.jsonl"))]
    rows = [r for r in rows if "error" not in r]
    train = [r for r in rows if not r["holdout"]]
    held = [r for r in rows if r["holdout"]]
    os.makedirs(os.path.join(kdir, "stats"), exist_ok=True)
    os.makedirs(os.path.join(kdir, "local"), exist_ok=True)

    # ---------- Groove (CC BY 4.0): human drumming by style, beats and fills separately
    gro = defaultdict(list)
    for r in train:
        if r["source"] == "groove":
            gro[(r["meta"]["style"].split("/")[0], r["meta"]["beat_type"])].append(r)
    groove = {f"{s}/{b}": drums_block(v) for (s, b), v in sorted(gro.items()) if len(v) >= 8}
    json.dump({"source": "Groove MIDI Dataset v1.0.0 (Google LLC, CC BY 4.0), held-out test split excluded",
               "unit_notes": "positions are 16th steps 0-15; placement and jitter in ms; velocity 1-127",
               "styles": groove}, open(os.path.join(kdir, "stats", "groove_drums_by_style.json"), "w"), indent=1)

    # ---------- Mutopia + PDMX (public domain / CC): melody, bass, counterpoint, arrangement
    def cls_key(r):
        if r["source"] == "mutopia":
            return "mutopia:" + r["meta"]["why_selected"].split(":")[0]
        if r["meta"].get("is_original"):
            return "pdmx:original"
        return "pdmx:" + "-".join(r["meta"].get("genres") or ["NA"])
    cg = defaultdict(list)
    for r in train:
        if r["source"] in ("mutopia", "pdmx"):
            cg[cls_key(r)].append(r)
    classical = {}
    for k, rs in sorted(cg.items()):
        if len(rs) < 4:
            continue
        mel = [r["features"]["melody"] for r in rs if "melody" in r["features"]]
        bas = [r["features"]["bass"] for r in rs if "bass" in r["features"]]
        cp = [r.get("counterpoint") or {} for r in rs]
        ar = [r["arrangement"] for r in rs if r.get("arrangement")]
        classical[k] = {
            "files": len(rs),
            "melody": line_block(mel) if len(mel) >= 3 else None,
            "bass": line_block(bas) if len(bas) >= 3 else None,
            "counterpoint": {m: dist([c.get(m) for c in cp]) for m in ("contrary", "similar", "oblique", "parallel_fifths_per_100_moves", "outer_octave_doubling", "single_track_attack_ratio")},
            "arrangement": {"density_cv": dist([a.get("density_cv") for a in ar]),
                            "changes_per_8_bars": dist([a["block_changes"] / max(1, len(a["blocks"]) - 1) for a in ar]),
                            "quiet_bars_ratio": dist([a.get("quiet_bars_ratio") for a in ar])},
            "melody_chord_tone_ratio": dist([r["interplay"].get("melody_chord_tone_ratio") for r in rs]),
        }
    json.dump({"source": "Mutopia Project selection (PD / CC BY / CC BY-SA, see PROVENANCE.md) and PDMX approved subset (PD mark / CC0)",
               "groups": classical}, open(os.path.join(kdir, "stats", "classical_lines_counterpoint.json"), "w"), indent=1)

    # ---------- Zynthion (pending clearance): local only
    Z = [r for r in train if r["source"] == "zynthion"]
    zd = defaultdict(list)
    for r in Z:
        if "drums" in r["features"] and r["meta"]["role"] in ("drums", "hi-hat"):
            key = r["meta"]["genre"].lower()
            zd[("fills/" if r["meta"]["pack"] == "drum-fills-midi" else "") + key].append(r)
    z_drums = {k: drums_block(v) for k, v in sorted(zd.items())}
    z808 = [r for r in Z if "808" in r["features"]]
    z_808 = line_block([r["features"]["808"] for r in z808]) if z808 else None
    if z_808:
        z_808["bass_on_kick"] = dist([r["interplay"].get("bass_on_kick") for r in z808])
        z_808["kick_with_bass"] = dist([r["interplay"].get("kick_with_bass") for r in z808])
        z_808["pitchbend_events"] = dist([r["pitchbends"] for r in z808])
    zr = {}
    for role, pack in (("bass", "bass-midi"), ("melody", "melody-midi"), ("arp", "arp-midi")):
        g = defaultdict(list)
        for r in Z:
            if r["meta"]["pack"] == pack and role in r["features"]:
                g[r["meta"]["genre"].lower()].append(r["features"][role])
        zr[role] = {k: line_block(v, ("rate_16ths", "cycle_notes", "span") if role == "arp" else ()) for k, v in sorted(g.items())}
    cb = [r for r in Z if r["meta"]["role"] == "chords-and-bass"]
    zcb = defaultdict(list)
    for r in cb:
        zcb[r["meta"]["genre"]].append(r)
    z_cb = {k: {"files": len(v), "chord_bottom_minus_bass": dist([r["interplay"].get("chord_bottom_minus_bass_median") for r in v]),
                "bass": line_block([r["features"]["bass"] for r in v if "bass" in r["features"]]),
                "chords_changes_per_bar": dist([r["features"].get("chords", {}).get("changes_per_bar") for r in v]),
                "chord_voices": dist([r["features"].get("chords", {}).get("voices_median") for r in v]),
                "voice_motion": dist([r["features"].get("chords", {}).get("voice_motion_median") for r in v])} for k, v in zcb.items()}
    json.dump({"source": "Zynthion free MIDI packs (royalty-free music licence; PENDING clearance for skill use). LOCAL ONLY: do not commit, ship or quote outside this machine.",
               "drums_by_genre": z_drums, "808_with_paired_drums": z_808, "lines_by_genre": zr, "genre_pack_bass_and_chords": z_cb},
              open(os.path.join(kdir, "local", "zynthion_stats.json"), "w"), indent=1)

    # ---------- held-out reference ranges for scoring
    def rng(vals, lo=.1, hi=.9):
        v = [x for x in vals if x is not None]
        return [pct(v, lo), pct(v, hi)] if len(v) >= 3 else None
    import statistics as st  # noqa: F401
    funk = [r for r in held if r["source"] == "groove" and r["meta"]["style"].startswith(("funk", "soul", "hiphop", "neworleans")) and r["meta"]["beat_type"] == "beat"]
    fd = [r["features"]["drums"] for r in funk]
    gi = lambda inst, k: [x["instruments"].get(inst, {}).get(k) for x in fd]
    refs = {"funk": {"files": len(funk),
                     "snare_timing_sd_ms": rng(gi("snare", "timing_sd_ms")), "hat_timing_sd_ms": rng(gi("hat_closed", "timing_sd_ms")),
                     "kick_timing_sd_ms": rng(gi("kick", "timing_sd_ms")), "quantized_share": rng([r["quantized_share"] for r in funk]),
                     "snare_ghost_per_bar": rng([x.get("snare_ghost_per_bar") for x in fd]),
                     "hat_position_structure": rng(gi("hat_closed", "vel_structure")),
                     "hat_vel_sd": rng(gi("hat_closed", "vel_sd")), "snare_vel_sd": rng(gi("snare", "vel_sd"))}}
    trap_d = [r for r in held if r["source"] == "zynthion" and "drums" in r["features"] and r["meta"]["genre"].lower() in ("trap", "drill") and r["meta"]["pack"] != "drum-fills-midi"]
    trap_b = [r for r in held if r["source"] == "zynthion" and "808" in r["features"]]
    td = [r["features"]["drums"] for r in trap_d]
    refs["trap"] = {"files": len(trap_d) + len(trap_b),
                    "backbeat_3": rng([x.get("backbeat_3") for x in td], 0, 1),
                    "hat_rolls_per_bar": rng([x.get("hat_rolls_per_bar") for x in td], 0, 1),
                    "hat_position_structure": rng([x["instruments"].get("hat_closed", {}).get("vel_structure") for x in td], 0, 1),
                    "bass_on_kick": rng([r["interplay"].get("bass_on_kick") for r in trap_b], 0, 1),
                    "808_per_bar": rng([r["features"]["808"]["per_bar"] for r in trap_b], 0, 1)}
    # widen any degenerate (single-value) range a little so a reference isn't a point
    for g in refs.values():
        for k, v in list(g.items()):
            if isinstance(v, list) and v[0] is not None and v[0] == v[1]:
                g[k] = [round(v[0] * 0.8, 3), round(v[1] * 1.2 + 0.05, 3)]
    os.makedirs(os.path.join(root, "_evals"), exist_ok=True)
    json.dump(refs, open(os.path.join(root, "_evals", "refs.json"), "w"), indent=1)
    print("groove styles", len(groove), "| classical groups", len(classical), "| zynthion drum groups", len(z_drums))
    print(json.dumps(refs, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
