"""quantize_notes and the groove pool in Live (offline twin: tests/offline/test_groove.py). Proves, on a fresh track:
  1. quantize: a dry run writes nothing; strength 100 puts every start on the 16th grid and keeps lengths; strength 50
     moves halfway; swing 66 puts the off 16ths at a third of a beat late; ends=True quantizes the ends too; notes
     that would collide are refused with nothing written; nothing but start and length ever changes;
  2. grooves: list_grooves finds Live's grooves and searches by words; load_groove adds one to the pool and nothing
     else; set_groove writes every amount and the base; set_groove_amount covers 0-131.25%; set_clip_groove assigns
     a groove to a clip and get_groove_pool(clips=True) reports it.
It doesn't prove the sound of a groove (that needs a render).
usage: python3 tests/test_groove.py   (scratch set; results tests/results/groove.json)
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from lt import call, Log, LiveError
from lt import authorize
authorize()   # tests run only in saved disposable Sets

RES = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RES, exist_ok=True)
log = Log(os.path.join(RES, "groove.json"))
call("reload_extensions")
NAME = "Tool Groove Test"
names = {t["name"]: t["ref"] for t in call("list_tracks", devices=False)}
if NAME in names:
    call("delete_track", track=names[NAME])
M = call("create_track", kind="midi", name=NAME)["ref"]
call("set_song_time", tempo=120, numerator=4, denominator=4, loop=False)

LATE = [0.03, 0.27, 0.49, 0.71, 1.02, 1.26, 1.52, 1.77]          # hats a little off the 16ths
NOTES = [[42, s, 0.2, 100] for s in LATE] + [[36, 0.02, 0.5, 120], [36, 1.01, 0.5, 120]]
call("create_arrangement_midi_clip", track=M, at="1.1.1", length=4, notes=NOTES, name="Quantize test")
A = {"arrangement_index": 0}


def notes(**k):
    return call("get_clip_notes", track=M, **dict(A, **k))["notes"]


def shape():
    return sorted((n["id"], n["pitch"], n["velocity"]) for n in notes())


base = shape()
r = call("quantize_notes", track=M, grid="1/16", pitch=42, dry_run=True, **A)
log("dry run plans 8 moves and writes nothing", r["changed"] == 8 and not r["written"]
    and all(abs(n["start"] - s) < 1e-4 for n, s in zip(notes(pitch=42), LATE)), report={k: r[k] for k in ("mean_off_grid_before", "largest_move")})

r = call("quantize_notes", track=M, grid="1/16", strength=50, pitch=42, **A)
half = [n["start"] for n in notes(pitch=42)]
want = [round(s + (round(s / 0.25) * 0.25 - s) / 2, 6) for s in LATE]
log("strength 50 moves halfway", all(abs(a - b) < 1e-4 for a, b in zip(half, want)), starts=half)

r = call("quantize_notes", track=M, grid="1/16", pitch=42, **A)
hats = notes(pitch=42)
log("strength 100 lands on the 16ths and keeps lengths",
    all(abs(n["start"] - i * 0.25) < 1e-4 for i, n in enumerate(hats)) and all(abs(n["duration"] - 0.2) < 1e-4 for n in hats),
    starts=[n["start"] for n in hats], mean_off_grid_after=r["mean_off_grid_after"])

r = call("quantize_notes", track=M, grid="1/16", swing=66, pitch=42, **A)
sw = [n["start"] for n in notes(pitch=42)]
want = [(i // 2) * 0.5 + (0.5 * 0.66 if i % 2 else 0.0) for i in range(8)]
short = [n["duration"] for n in notes(pitch=42)]
log("swing 66 puts the off 16ths late, and the hats that now run into the next are shortened as Live does",
    all(abs(a - b) < 1e-4 for a, b in zip(sw, want)) and sorted(r["shortened"]) == sorted(
        n["id"] for n in notes(pitch=42) if n["duration"] < 0.2 - 1e-4) and len(r["shortened"]) == 3,
    starts=sw, durations=short, shortened=r["shortened"])

r = call("quantize_notes", track=M, grid="1/8", ends=True, pitch=36, **A)
k = notes(pitch=36)
log("ends=True quantizes the ends too", all(abs(a - b) < 1e-4 for n, w in zip(k, [(0.0, 0.5), (1.0, 0.5)])
    for a, b in zip((n["start"], n["duration"]), w)),
    kicks=[(n["start"], n["duration"]) for n in k])

try:
    call("quantize_notes", track=M, grid="1/2", pitch=42, **A)
    log("colliding notes are refused", False)
except LiveError as e:
    log("colliding notes are refused", "nothing written" in str(e)
        and all(abs(a - b) < 1e-6 for a, b in zip([n["start"] for n in notes(pitch=42)], sw)),
        error=str(e)[:160])

log("only starts and lengths changed (same notes, pitches, velocities)", shape() == base)

g = call("list_grooves")
mpc = call("list_grooves", search="mpc 16")["grooves"]
log("list_grooves finds Live's grooves and searches by words", g["count"] >= 100 and len(mpc) > 0,
    count=g["count"], mpc=[x["name"] for x in mpc][:3])

before = call("get_groove_pool")
clips_before = call("get_groove_pool", clips=True)["clips"]
r = call("load_groove", name=mpc[0]["name"], folder=mpc[0]["folder"])
for _ in range(40):
    time.sleep(0.25)
    after = call("get_groove_pool")
    if after["count"] > before["count"]:
        break
new = after["grooves"][-1]
clips_after = [c for c in call("get_groove_pool", clips=True)["clips"]]
log("load_groove adds it to the pool and changes no clip", after["count"] == before["count"] + 1
    and new["name"] == mpc[0]["name"] and clips_after == clips_before, groove=new)

gi = new["index"]
r = call("set_groove", groove=gi, timing=40, random=5, velocity=-30, quantize=20, base="1/8")["after"]
log("set_groove writes every amount and the base", (r["timing"], r["random"], r["velocity"], r["quantize"], r["base"])
    == (40.0, 5.0, -30.0, 20.0, "1/8"), after=r)
call("set_groove", groove=gi, timing=100, random=0, velocity=0, quantize=0, base="1/16")

amt = call("get_groove_pool")["global_amount"]
ok = [call("set_groove_amount", amount=a)["after"] for a in (0, 131.25, 100)]
call("set_groove_amount", amount=amt * 100.0)
log("set_groove_amount covers 0 to 131.25%", ok == [0.0, 131.25, 100.0], read_back=ok)

r = call("set_clip_groove", track=M, groove=gi, **A)
mine = [c for c in call("get_groove_pool", clips=True)["clips"] if c["track"] == M]
log("set_clip_groove assigns it and the pool reports it", r["after"]["index"] == gi
    and [c["groove"] for c in mine] == [gi], clips=mine)

try:
    call("set_groove", groove=gi, timing=150)
    log("out-of-range amounts are refused", False)
except LiveError as e:
    log("out-of-range amounts are refused", "outside" in str(e), error=str(e)[:120])

print("results:", os.path.join(RES, "groove.json"))
sys.exit(0 if all(r["ok"] for r in log.rows) else 1)
