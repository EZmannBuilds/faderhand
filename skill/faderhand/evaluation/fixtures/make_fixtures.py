"""Build the evaluation fixtures (original material written for these tests; safe to ship).

F1  "comprehension.mid": 16 bars, 92 BPM, 4/4, D minor, swung 16ths (58%), four tracks:
    Drums (ch10), Bass, Keys (chords), Lead. Bars 1-8 are a verse texture, bars 9-16 a fuller hook
    (lead enters at bar 9, hats double). Ground truth is written to comprehension.truth.json.
F2  "flawed.mid": 8 bars, 96 BPM: every velocity 100, everything on the grid, the same bar eight
    times, bass a 16th late against every kick. Protected material: the chord pitches and the hook
    melody pitches (listed in flawed.truth.json).

Usage: python3 make_fixtures.py <out_dir>   (needs mido)
"""
import json, os, sys
import mido

PPQ = 480
S16 = PPQ // 4


def swing(tick, amount=0.58):
    # delay odd 16ths so a pair of 16ths splits amount : 1-amount of an 8th
    pos = tick % (2 * S16)
    if pos == S16:
        return tick - S16 + int(2 * S16 * amount)
    return tick


def write(path, tracks, bpm, meter=(4, 4)):
    mf = mido.MidiFile(ticks_per_beat=PPQ)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=meter[0], denominator=meter[1], time=0))
    mf.tracks.append(meta)
    for name, ch, notes in tracks:
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name=name, time=0))
        ev = []
        for start, dur, pitch, vel in notes:
            ev.append((start, 1, pitch, vel))
            ev.append((start + dur, 0, pitch, 0))
        ev.sort(key=lambda e: (e[0], e[1]))
        t = 0
        for at, on, pitch, vel in ev:
            tr.append(mido.Message("note_on" if on else "note_off", channel=ch, note=pitch, velocity=vel, time=at - t))
            t = at
        mf.tracks.append(tr)
    mf.save(path)


def f1(out):
    bar = 4 * PPQ
    drums, bass, keys, lead = [], [], [], []
    kick_steps = [0, 6, 10]          # 16th steps in the bar
    chords = [[50, 53, 57, 60], [46, 50, 53, 57], [48, 52, 55, 58], [45, 49, 52, 55]]  # Dm7 Bbmaj7 C7 A7
    roots = [38, 34, 36, 33]
    bass_steps = [0, 6, 10, 14]      # three on kicks, one pickup on step 14
    hook = [(0, 69, 2), (2, 72, 2), (4, 74, 4), (10, 72, 2), (12, 69, 4)]
    for b in range(16):
        b0 = b * bar
        hook_section = b >= 8
        for s in kick_steps:
            drums.append((swing(b0 + s * S16), S16, 36, 110 if s == 0 else 96))
        for s in (4, 12):
            drums.append((b0 + s * S16, S16, 38, 112))
        hat_steps = range(16) if hook_section else range(0, 16, 2)
        for s in hat_steps:
            v = 92 if s % 4 == 0 else (70 if s % 2 == 0 else 52)
            drums.append((swing(b0 + s * S16), S16 // 2, 42, v))
        ci = b % 4
        for s in bass_steps:
            p = roots[ci] if s != 14 else roots[(ci + 1) % 4] + 1
            bass.append((swing(b0 + s * S16), S16 * (3 if s == 0 else 2), p, 100))
        for p in chords[ci]:
            keys.append((b0, bar - S16, p, 72))
        if hook_section:
            for s, p, d in hook:
                lead.append((swing(b0 + s * S16), d * S16, p - (0 if b % 2 == 0 else 2), 95))
    write(os.path.join(out, "comprehension.mid"),
          [("Drums", 9, drums), ("Bass", 0, bass), ("Keys", 1, keys), ("Lead", 2, lead)], 92)
    truth = {
        "tempo_bpm": 92, "meter": "4/4", "key": "D minor", "bars": 16,
        "roles": {"Drums": "drums", "Bass": "bass", "Keys": "chords", "Lead": "melody"},
        "swing_percent": 58,
        "bass_onsets_total": 64, "bass_onsets_on_kick": 48,
        "arrangement_change_bar": 9,
        "hook_change": "lead enters and hats go from 8ths to 16ths",
        "chords": ["Dm7", "Bbmaj7", "C7", "A7"],
    }
    json.dump(truth, open(os.path.join(out, "comprehension.truth.json"), "w"), indent=1)


def f2(out):
    bar = 4 * PPQ
    drums, bass, keys, lead = [], [], [], []
    chords = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]]  # Am F G Em, one per bar pair
    roots = [45, 41, 43, 40]
    hook = [(0, 76), (2, 74), (3, 72), (4, 74), (8, 76), (10, 79), (12, 76), (14, 74)]
    for b in range(8):
        b0 = b * bar
        for s in (0, 8, 10):
            drums.append((b0 + s * S16, S16, 36, 100))
        for s in (4, 12):
            drums.append((b0 + s * S16, S16, 38, 100))
        for s in range(0, 16, 2):
            drums.append((b0 + s * S16, S16 // 2, 42, 100))
        ci = (b // 2) % 4
        for s in (0, 8, 10):
            bass.append((b0 + (s + 1) * S16, S16, roots[ci], 100))   # a 16th late against each kick
        for p in chords[ci]:
            keys.append((b0, bar, p, 100))
        for s, p in hook:
            lead.append((b0 + s * S16, S16 * 2, p, 100))
    write(os.path.join(out, "flawed.mid"),
          [("Drums", 9, drums), ("Bass", 0, bass), ("Keys", 1, keys), ("Lead", 2, lead)], 96)
    truth = {"protected_chord_pitches_by_bar": [sorted(chords[(b // 2) % 4]) for b in range(8)],
             "protected_hook_pitch_sequence": [p for _, p in hook],
             "bars": 8, "tempo_bpm": 96}
    json.dump(truth, open(os.path.join(out, "flawed.truth.json"), "w"), indent=1)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out, exist_ok=True)
    f1(out)
    f2(out)
    print("fixtures written to", out)
