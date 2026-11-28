"""build_feedback_bass and follow_notes in Live (offline twin: tests/offline/test_feedback_bass.py). On fresh tracks, a
saw bass (Operator) playing E1, G1, A1 and a bar of rest:
  1. build: the rack and its six devices in order, every preset setting read back, the tuning, both follow lanes
     (Spectral Resonator Freq. Hz and Roar FB Note step E3 -> G3 -> A3), and the refusals;
  2. render (skip with --no-render): each preset played from the Arrangement must die away in the rest bar (no
     runaway feedback) and peak at -1 dBFS or below; and with the resonance following the notes, the static E3
     resonance must be gone from the G bar (at least 20 dB below the static chain's).
usage: python3 tests/test_feedback_bass.py [--no-render]   (scratch set; results tests/results/feedback-bass.json)
"""
import json, math, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from lt import call, Log, LiveError
from lt import authorize
authorize()   # tests run only in saved disposable Sets

RES = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RES, exist_ok=True)
log = Log(os.path.join(RES, "feedback-bass.json"))
call("reload_extensions")
NOTES = [[40, 0, 3.5, 100], [43, 4, 3.5, 100], [45, 8, 3.5, 100]]      # E1, G1, A1, then a bar of rest
PREFIX = "Tool FB "


def clear():
    while True:
        left = [t for t in call("list_tracks", devices=False) if t["name"].startswith(PREFIX)]
        if not left:
            return
        call("delete_track", track=left[-1]["ref"])


def bass(name, arrangement=False):
    m = call("create_track", kind="midi", name=PREFIX + name)["ref"]
    call("insert_native_device", track=m, name="Operator")
    call("set_device_parameters", track=m, device="Operator", units="auto",
         values={"Osc-A Wave": "Saw 64", "Volume": "-12 dB", "Ae Release": "60 ms"})
    if arrangement:
        call("create_arrangement_midi_clip", track=m, at="1.1.1", length=16, notes=NOTES, name="Bass line")
    else:
        call("make_test_clip", track=m, slot=0, length=16.0, notes=NOTES, name="Bass line")
    return m


def number(s):
    s = str(s).strip().lower()
    m = re.match(r"^(-?[\d.]+|-inf)\s*(k?)", s)
    if not m:
        return s
    v = float("-inf") if m.group(1) == "-inf" else float(m.group(1))
    return v * (1000 if m.group(2) == "k" else 1)


def same(a, b):
    x, y = number(a), number(b)
    if isinstance(x, float) and isinstance(y, float):
        return x == y or abs(x - y) <= max(0.02 * abs(x), 0.6)
    return str(a).strip().lower() == str(b).strip().lower()


clear()
call("transport", action="stop"); call("transport", action="stop_all_clips")
call("set_song_time", tempo=120, numerator=4, denominator=4, loop=False)

# ------------------------------------------------------------------ 1. build
B = bass("build")
r = call("build_feedback_bass", track=B, preset="growl", key_note="E1", transpose=24, follow_slot=0)
log("one rack, six devices in order", r["rack"] == "Feedback Bass (growl)" and r["chain"] ==
    ["Auto Filter", "Saturator", "Spectral Resonator", "Roar", "EQ Eight", "Limiter"], chain=r["chain"])
off = [s for s in r["settings"] if not same(s["set"] if not isinstance(s["set"], float) else r["tuned_to"]["name"]
                                            if s["parameter"] == "FB Note" else s["set"], s["reads"])]
log("every preset setting reads back", not off, settings=len(r["settings"]), mismatches=off)
log("tuned to E1 + 24 = E3", r["tuned_to"] == {"midi": 64, "name": "E3"}, tuned_to=r["tuned_to"])
sr, roar = r["follow"]
log("Spectral Resonator's Freq follows the notes (E3, G3, A3)",
    [round(number(s["value"])) for s in sr["steps_read_back"]] in ([330, 392, 440], [330, 391, 439], [330, 392, 439]),
    steps=sr["steps_read_back"])
log("Roar's FB Note follows the notes", [s["value"] for s in roar["steps_read_back"]] == ["E3", "G3", "A3"],
    steps=roar["steps_read_back"])
for label, kw, needle in (("a second rack on the same track is refused", {"track": B}, "already has"),
                          ("a key outside Roar's range is refused", {"track": None, "key_note": "C5"}, "outside"),
                          ("a MIDI track with no instrument is refused", {"track": "empty"}, "no instrument")):
    if kw["track"] is None:
        kw["track"] = bass("range")
    elif kw["track"] == "empty":
        kw["track"] = call("create_track", kind="midi", name=PREFIX + "empty")["ref"]
    try:
        call("build_feedback_bass", **kw)
        log(label, False)
    except LiveError as e:
        log(label, needle in str(e), error=str(e)[:120])

if "--no-render" in sys.argv:
    print("results:", os.path.join(RES, "feedback-bass.json"))
    sys.exit(0 if all(x["ok"] for x in log.rows) else 1)

# ------------------------------------------------------------------ 2. render
ANALYSE = r'''
import json, math, sys
import numpy as np, soundfile as sf
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12.0)
out = {}
for label, path, aligned in json.loads(sys.argv[1]):
    x, sr = sf.read(path, always_2d=True); x = x.mean(axis=1)
    bars = [x[int(k * 2.0 * sr):int((k + 1) * 2.0 * sr)] for k in range(4)]
    rms = lambda a: 20 * math.log10(math.sqrt(float(np.mean(a ** 2))) + 1e-12)
    rest = 3 if aligned else int(np.argmin([rms(b[int(0.3 * sr):]) for b in bars]))
    tail = bars[rest][int(0.3 * sr):]; h = len(tail) // 2
    g = bars[(rest + 2) % 4][int(0.2 * sr):int(1.6 * sr)]           # the G1 bar comes two bars after the rest
    w = np.hanning(len(g)); X = np.abs(np.fft.rfft(g * w, 1 << 17)) * 2 / w.sum(); f = np.fft.rfftfreq(1 << 17, 1 / sr)
    e3 = 20 * math.log10(X[(f > hz(64) * 0.985) & (f < hz(64) * 1.015)].max() + 1e-12)
    out[label] = {"peak": 20 * math.log10(float(np.abs(x).max()) + 1e-12), "rest_first": rms(tail[:h]),
                  "rest_second": rms(tail[h:]), "g_bar_e3": e3}
print(json.dumps(out))
'''


def record(tracks):
    dst = [call("create_track", kind="audio", name=PREFIX + "rec %d" % i)["ref"] for i in range(len(tracks))]
    call("record_tracks_audio", takes=[{"dst": a, "source": m, "slot": 0} for m, a in zip(tracks, dst)], bars=4)
    for _ in range(120):
        time.sleep(0.5)
        st = call("record_tracks_audio_status")
        if st["done"]:
            break
    call("transport", action="stop"); call("transport", action="stop_all_clips"); call("back_to_arrangement")
    return [t["file"] for t in st["takes"]]


def analyse(rows):
    out = subprocess.run(["/opt/homebrew/bin/uv", "run", "-q", "--with", "numpy", "--with", "soundfile", "python", "-c",
                          ANALYSE, json.dumps(rows)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# 2a: each preset from the Arrangement (all takes start at bar 1; bar 4 is the rest)
ring = []
for preset in ("subtle", "growl", "screaming"):
    m = bass("ring " + preset, arrangement=True)
    call("build_feedback_bass", track=m, preset=preset, key_note="E1", transpose=24)
    ring.append((preset, m))
call("back_to_arrangement"); call("set_song_time", position="1.1.1")
files = record([m for _, m in ring])
res = analyse([[p, f, True] for (p, _), f in zip(ring, files)])
for p, v in res.items():
    decays = v["rest_second"] <= -60 or v["rest_second"] < v["rest_first"] - 20
    log("%s dies away after the notes (no runaway feedback)" % p, decays,
        rest_first_half=round(v["rest_first"], 1), rest_second_half=round(v["rest_second"], 1))
    log("%s peaks at -1 dBFS or below" % p, v["peak"] <= -0.99, peak=round(v["peak"], 2))

# 2b: growl, static against following (Session clips; each take is aligned on its own rest bar)
st_m = bass("growl static"); call("build_feedback_bass", track=st_m, preset="growl", key_note="E1", transpose=24)
fo_m = bass("growl follow"); call("build_feedback_bass", track=fo_m, preset="growl", key_note="E1", transpose=24,
                                  follow_slot=0)
call("set_song_time", position="1.1.1"); call("transport", action="play"); time.sleep(0.3)
for m in (st_m, fo_m):
    call("fire_clip", track=m, slot=0)
files = record([st_m, fo_m])
res = analyse([["static", files[0], False], ["follow", files[1], False]])
drop = res["static"]["g_bar_e3"] - res["follow"]["g_bar_e3"]
log("following the notes removes the static E3 resonance from the G bar", drop >= 20,
    static_db=round(res["static"]["g_bar_e3"], 1), follow_db=round(res["follow"]["g_bar_e3"], 1), drop_db=round(drop, 1))

print("results:", os.path.join(RES, "feedback-bass.json"))
sys.exit(0 if all(x["ok"] for x in log.rows) else 1)
