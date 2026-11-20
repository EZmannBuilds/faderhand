"""Build blind A/B pairs from two runs: a note-level text dump for an agent judge, WAV renders for human listening.

Usage: python3 blind_pairs.py <runX> <runY> <out_dir> [--render <render_midi binary>] [--seed N]
For each composition task (T03, T04, T05, T06, T10) the two outputs are shuffled into "A" and "B". The key is
written to <out_dir>/KEY.json, which judges must not read. The dump lists, per track, each bar's notes as
step:pitch:velocity(+ms offset), with no file names, scripts or notes from the run.
"""
import json, os, random, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.path.join(HERE, "..", "tools", "corpus"),):
    sys.path.insert(0, os.path.abspath(cand))
import midi_lib  # noqa: E402
import analyze  # noqa: E402

TASKS = {"T03": "t03_trap.mid", "T04": "t04_funk_drums.mid", "T05": "t05_song.mid", "T06": "t06_neosoul.mid", "T10": "t10_revised.mid"}
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def pname(p):
    return f"{NAMES[p % 12]}{p // 12 - 1}"


def dump(path, max_bars=200):
    s = midi_lib.read(path)
    g = analyze.Grid(s)
    out = [f"tempo {s.bpm:.1f} BPM, meter {s.meter[0]}/{s.meter[1]}, {len(s.notes)} notes"]
    import mido
    marks = []
    for tr in mido.MidiFile(path).tracks:
        t = 0
        for m in tr:
            t += m.time
            if m.is_meta and m.type == "marker":
                marks.append(f"bar {g.bar_of(t) + 1}: {m.text}")
    if marks:
        out.append("markers: " + "; ".join(marks))
    by = {}
    for n in s.notes:
        key = (n.track, n.channel)
        by.setdefault(key, []).append(n)
    for (t, ch), ns in sorted(by.items()):
        name = s.track_names.get(t, f"track {t}")
        out.append(f"\n## {name} (channel {ch + 1}{', drums' if ch == 9 else ''})")
        bars = {}
        for n in ns:
            bars.setdefault(g.bar_of(n.start), []).append(n)
        for b in sorted(bars)[:max_bars]:
            cells = []
            for n in bars[b]:
                off = round(g.offset(n.start) * g.ms16)
                dur = (n.end - n.start) / g.s16
                p = str(n.pitch) if ch == 9 else pname(n.pitch)
                cells.append(f"{g.pos(n.start)}:{p}:{n.velocity}{'' if off == 0 else f'{off:+d}ms'}{'' if ch == 9 else f'/{dur:.1f}'}")
            out.append(f"bar {b + 1}: " + " ".join(cells))
    return "\n".join(out)


def main():
    x, y, out = sys.argv[1], sys.argv[2], sys.argv[3]
    render = sys.argv[sys.argv.index("--render") + 1] if "--render" in sys.argv else None
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 1
    rnd = random.Random(seed)
    os.makedirs(out, exist_ok=True)
    key = {}
    for task, fn in TASKS.items():
        pair = [("X", os.path.join(x, fn)), ("Y", os.path.join(y, fn))]
        rnd.shuffle(pair)
        key[task] = {"A": pair[0][0], "B": pair[1][0], "X": x, "Y": y}
        for label, (_, path) in zip("AB", pair):
            if not os.path.exists(path):
                continue
            open(os.path.join(out, f"{task}_{label}.txt"), "w").write(dump(path))
            if render:
                subprocess.run([render, path, os.path.join(out, f"{task}_{label}.wav")], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    json.dump(key, open(os.path.join(out, "KEY.json"), "w"), indent=1)
    print("pairs written to", out)


if __name__ == "__main__":
    main()
