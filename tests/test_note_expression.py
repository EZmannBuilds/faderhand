"""get_clip_notes and set_note_expression in Live (the offline twin with the same cases on a fake clip:
tests/offline/test_note_expression.py). Proves, in a Session clip and an Arrangement clip:
  1. the notes read back as written, with Live's defaults for chance, velocity range and release velocity;
  2. a 3+3+2 accent pattern on the hats lands on the right 16ths, and the kicks are untouched;
  3. a ramp, a clamp, chance, velocity range, release velocity and mute are written and read back;
  4. a dry run writes nothing; nothing ever moves (pitch, start and length are unchanged);
  5. a request that matches no note fails and writes nothing.
It doesn't prove the sound. That was checked once by a render (2026-11-27, docs/CAPABILITY-MATRIX.md): resample the
part through a velocity-sensitive instrument and measure each 16th's peak.
usage: python3 tests/test_note_expression.py   (scratch set; results tests/results/note-expression.json)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from lt import call, Log, LiveError
from lt import authorize
authorize()   # tests run only in saved disposable Sets

RES = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RES, exist_ok=True)
log = Log(os.path.join(RES, "note-expression.json"))
call("reload_extensions")
NAME = "Tool Notes Test"
names = {t["name"]: t["ref"] for t in call("list_tracks", devices=False)}
if NAME in names:                       # a fresh track each run, so earlier edits can't leak in
    call("delete_track", track=names[NAME])
M = call("create_track", kind="midi", name=NAME)["ref"]

HATS = [[42, i * 0.25, 0.2, 100] for i in range(16)]
KICKS = [[36, float(b), 0.5, 120] for b in range(4)]
call("set_song_time", tempo=120, numerator=4, denominator=4, loop=False)
call("make_test_clip", track=M, slot=0, length=4.0, notes=HATS + KICKS, name="Notes session")
call("create_arrangement_midi_clip", track=M, at="1.1.1", length=4, notes=HATS + KICKS, name="Notes arrangement")


def where(clip):
    return sorted((n["pitch"], n["start"], n["duration"]) for n in call("get_clip_notes", track=M, **clip)["notes"])


for label, clip in (("session", {"slot": 0}), ("arrangement", {"arrangement_index": 0})):
    r = call("get_clip_notes", track=M, **clip)
    first = r["notes"][0]
    log(label + ": 20 notes read back with Live's defaults", r["total_notes"] == 20 and first["probability"] == 1.0
        and first["velocity_deviation"] == 0.0, summary=r["summary"], first=first)
    placed = where(clip)

    r = call("set_note_expression", track=M, pitch=42, velocity_pattern=[110, 70, 70, 110, 70, 70, 105, 75], **clip)
    hats = [n["velocity"] for n in call("get_clip_notes", track=M, pitch=42, **clip)["notes"]]
    kicks = [n["velocity"] for n in call("get_clip_notes", track=M, pitch=36, **clip)["notes"]]
    log(label + ": 3+3+2 hat accents", hats == [110, 70, 70, 110, 70, 70, 105, 75] * 2 and kicks == [120] * 4,
        hats=hats, kicks=kicks, result={k: r[k] for k in ("matched", "changed", "written")})

    call("set_note_expression", track=M, pitch=42, velocity_ramp=[40, 115], **clip)
    v = [n["velocity"] for n in call("get_clip_notes", track=M, pitch=42, **clip)["notes"]]
    log(label + ": ramp 40 to 115", v[0] == 40 and v[-1] == 115 and v == sorted(v), velocities=v)

    r = call("set_note_expression", track=M, pitch=36, velocity_scale=1.5, **clip)
    log(label + ": scale past 127 is kept at 127", r["clamped"] == 4, result=r["notes"][:1])

    call("set_note_expression", track=M, pitch=42, every=0.5, offset=0.25, probability=0.5, velocity_deviation=-20,
         release_velocity=30, **clip)
    off = call("get_clip_notes", track=M, pitch=42, every=0.5, offset=0.25, **clip)["notes"]
    log(label + ": chance, velocity range and release velocity on the off-beat 16ths",
        len(off) == 8 and all(n["probability"] == 0.5 and n["velocity_deviation"] == -20 and
                              n["release_velocity"] == 30 for n in off), sample=off[:2])

    ids = [n["id"] for n in call("get_clip_notes", track=M, pitch=36, **clip)["notes"]][:2]
    call("set_note_expression", track=M, ids=ids, mute=True, **clip)
    muted = [n["mute"] for n in call("get_clip_notes", track=M, pitch=36, **clip)["notes"]]
    log(label + ": mute two kicks by id", muted == [True, True, False, False], muted=muted)

    before = [n["velocity"] for n in call("get_clip_notes", track=M, pitch=42, **clip)["notes"]]
    r = call("set_note_expression", track=M, pitch=42, velocity=64, dry_run=True, **clip)
    after = [n["velocity"] for n in call("get_clip_notes", track=M, pitch=42, **clip)["notes"]]
    log(label + ": dry run writes nothing", not r["written"] and before == after, changed=r["changed"])

    try:
        call("set_note_expression", track=M, pitch=99, velocity=90, **clip)
        log(label + ": no match is refused", False)
    except LiveError as e:
        log(label + ": no match is refused", "no notes matched" in str(e), error=str(e))

    log(label + ": nothing moved", where(clip) == placed)

print("results:", os.path.join(RES, "note-expression.json"))
sys.exit(0 if all(r["ok"] for r in log.rows) else 1)
