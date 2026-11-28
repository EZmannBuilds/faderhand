"""build_feedback_bass and follow_notes, offline: note names, the follow steps, the presets, the parameter names
Live 12.4.16 reported for each device, follow_notes against a fake clip envelope, and the build's refusals. The
chain in Live, with its render checks: tests/test_feedback_bass.py."""
import importlib.util
import os
import sys
import types

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_spec = importlib.util.spec_from_file_location("faderhand_ext_fb", os.path.join(ROOT, "remote_script", "Faderhand", "ext.py"))
ext = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ext)

# The parameter names each device has on Live 12.4.16 (read with get_device_parameters, 2026-11-27): every name a
# preset sets must be one of these, so a typo fails here instead of in Live.
LIVE_NAMES = {
    "Auto Filter": {"Frequency", "Resonance", "Filter Morph", "Filter Type", "Morph Slope", "Circuit", "Drive",
                    "Formant"},
    "Saturator": {"Drive", "Pre Dc Filter", "Type", "Output", "Dry/Wet", "WS Drive", "WS Linearity", "WS Curve",
                  "WS Damp", "WS Period", "WS Depth"},
    "Spectral Resonator": {"Transpose", "Freq. Hz", "Note", "Decay", "High Damp", "Low Damp", "Harmonics",
                           "Dry Wet"},
    "Roar": {"Drive", "Tone Amt", "Tone Freq", "Shaper 1 On", "Shaper 1 Type", "Shaper 1 Amt", "Feedback",
             "FB Time Mode", "FB Note", "FB Freq", "Fb Gate On", "Output", "Dry/Wet"},
    "EQ Eight": {"8 Filter On A", "8 Filter Type A", "8 Frequency A", "8 Gain A", "1 Gain A", "1 Frequency A"},
    "Limiter": {"Ceiling", "Release", "Input Gain", "Output"},
}
ITEMS = {("Auto Filter", "Filter Type"): "Vowel", ("Saturator", "Type"): "Waveshaper",
         ("Roar", "FB Time Mode"): "Note", ("EQ Eight", "8 Filter Type A"): "High Shelf"}


# ---------------------------------------------------------------- note names and follow steps
@pytest.mark.parametrize("name, midi", [("E1", 40), ("C3", 60), ("F#2", 54), ("Bb0", 34), ("C-2", 0), ("b1", 47),
                                        (64, 64), (64.4, 64)])
def test_note_numbers(name, midi):
    assert ext._note_number(name) == midi


def test_bad_note_names():
    for bad in ("H2", "E", "C#", "x1", True):
        with pytest.raises(ext.ToolError, match="note"):
            ext._note_number(bad)


def notes(*rows):
    return [{"start": s, "pitch": p, "mute": m} for s, p, m in rows]


def test_follow_points():
    pts, clamped = ext._follow_points(notes((0, 40, False), (0, 52, False), (4, 43, False), (8, 45, False)), 24)
    assert pts == [(0, 64.0), (4, 67.0), (8, 69.0)] and clamped == 0
    pts, _ = ext._follow_points(notes((0, 40, False), (0, 52, False)), 0, chord="highest")
    assert pts == [(0, 52.0)]
    pts, _ = ext._follow_points(notes((1, 40, False), (2, 40, False), (3, 99, True)), 0)
    assert pts == [(0.0, 40.0), (1, 40.0)]                     # first value covers the start; muted and repeats skipped
    pts, clamped = ext._follow_points(notes((0, 80, False), (4, 10, False)), 0, lo=12, hi=84)
    assert pts == [(0, 80.0), (4, 12.0)] and clamped == 1
    pts, _ = ext._follow_points(notes((0, 40, False), (16, 43, False)), 0, end=16)
    assert pts == [(0, 40.0)]                                   # notes past the clip's end don't count
    with pytest.raises(ext.ToolError, match="no notes"):
        ext._follow_points(notes((0, 40, True)), 0)
    with pytest.raises(ext.ToolError, match="lowest or highest"):
        ext._follow_points(notes((0, 40, False)), 0, chord="middle")


# ---------------------------------------------------------------- presets
@pytest.mark.parametrize("preset", ["subtle", "growl", "screaming"])
def test_presets_use_live_names_and_cover_the_chain(preset):
    st = ext._fb_settings(preset, 64)
    assert list(st) == list(ext._FB_CHAIN)
    for dev, vals in st.items():
        unknown = set(vals) - LIVE_NAMES[dev]
        assert not unknown, (dev, unknown)
    for (dev, name), want in ITEMS.items():
        assert st[dev][name] == want
    assert st["Roar"]["FB Note"] == 64.0 and st["Spectral Resonator"]["Freq. Hz"] == "329.63 Hz"
    assert st["Limiter"]["Ceiling"] == "-1.0 dB" and st["Roar"]["Fb Gate On"] == "On"


def test_presets_stay_below_the_measured_ringing_edge():
    # Measured 2026-11-27: growl at 55 % feedback and screaming at 65 % shaper rang on after the notes stopped.
    pct = lambda v: float(v.split()[0])
    for preset in ext._FB_PRESETS:
        roar = ext._fb_settings(preset, 64)["Roar"]
        assert pct(roar["Feedback"]) <= 45 and pct(roar["Shaper 1 Amt"]) <= 45, preset


def test_overrides():
    st = ext._fb_settings("growl", 64, {"Roar": {"Feedback": "20 %"}, "Limiter": {"Ceiling": "-2 dB"}})
    assert st["Roar"]["Feedback"] == "20 %" and st["Limiter"]["Ceiling"] == "-2 dB"
    with pytest.raises(ext.ToolError, match="no device"):
        ext._fb_settings("growl", 64, {"Reverb": {"Decay": "2 s"}})
    with pytest.raises(ext.ToolError, match="preset is one of"):
        ext._fb_settings("loud", 64)


# ---------------------------------------------------------------- follow_notes against a fake clip envelope
class Param(object):
    def __init__(self, name, lo, hi, hz=False, value=0.0):
        self.name, self.original_name, self.min, self.max, self.value = name, name, lo, hi, value
        self.hz, self.is_quantized, self.is_enabled = hz, False, True

    def str_for_value(self, v):
        return ("%.0f Hz" % v) if self.hz else "note %d" % int(v)


class Env(object):
    def __init__(self):
        self.events = []

    def delete_events_in_range(self, a, b):
        self.events = [e for e in self.events if not a <= e.time <= b]

    def create_event(self, e):
        self.events.append(e)

    def value_at_time(self, t):
        past = [e for e in sorted(self.events, key=lambda e: e.time) if e.time <= t]
        return past[-1].value if past else 0.0


class Note(object):
    def __init__(self, nid, pitch, start):
        self.note_id, self.pitch, self.start_time, self.duration = nid, pitch, start, 1.0
        self.velocity, self.mute, self.probability, self.velocity_deviation, self.release_velocity = 100.0, False, 1.0, 0.0, 64.0


class Clip(object):
    is_audio_clip, name, looping, loop_end, end_marker, length = False, "Bass", True, 16.0, 16.0, 16.0

    def __init__(self, ns):
        self.ns, self.envs = ns, {}

    def get_all_notes_extended(self):
        return list(self.ns)

    def automation_envelope(self, p):
        return self.envs.get(p.name)

    def create_automation_envelope(self, p):
        return self.envs.setdefault(p.name, Env())


class Dev(object):
    def __init__(self, params):
        self.name, self.parameters = "Dev", params


class Track(object):
    name, has_midi_input = "Bass", True

    def __init__(self, clip, dev):
        self.clip_slots = [types.SimpleNamespace(clip=clip)]
        self.devices = [dev]
        self.arrangement_clips = []


class CS(object):
    def __init__(self, track):
        self._t = track
        self._song = types.SimpleNamespace(signature_numerator=4, signature_denominator=4)

    def _track(self, ref):
        return self._t

    def _ref(self, t):
        return "track:0"

    def _device(self, t, d, chain=None):
        return t.devices[0]

    def _param(self, d, name):
        return next(p for p in d.parameters if p.name == name)

    def _num(self, s):
        return float(str(s).split()[0])

    def _bisect(self, p, target):
        return target                              # this fake's raw value is its display value


@pytest.fixture(autouse=True)
def fake_live(monkeypatch):
    live = types.ModuleType("Live")
    live.Envelope = types.SimpleNamespace(EnvelopeEvent=lambda t, v: types.SimpleNamespace(time=t, value=v))
    monkeypatch.setitem(sys.modules, "Live", live)


def follow_cs():
    clip = Clip([Note(1, 40, 0.0), Note(2, 43, 4.0), Note(3, 45, 8.0)])
    dev = Dev([Param("FB Note", 12, 84), Param("Freq. Hz", 20, 20000, hz=True, value=110)])
    return CS(Track(clip, dev)), clip


def test_follow_notes_on_a_note_parameter():
    cs, clip = follow_cs()
    r = ext.cmd_follow_notes(cs, 0, 0, {"device": 0, "parameter": "FB Note"}, transpose=24)
    assert r["kind"] == "note" and r["steps"] == 3
    env = clip.envs["FB Note"]
    assert [env.value_at_time(t) for t in (0.5, 4.5, 8.5, 15.0)] == [64.0, 67.0, 69.0, 69.0]


def test_follow_notes_on_a_frequency_parameter():
    cs, clip = follow_cs()
    r = ext.cmd_follow_notes(cs, 0, 0, {"device": 0, "parameter": "Freq. Hz"}, transpose=24)
    assert r["kind"] == "hz"
    env = clip.envs["Freq. Hz"]
    assert [round(env.value_at_time(t), 2) for t in (0.5, 4.5, 8.5)] == [329.63, 392.0, 440.0]


# ---------------------------------------------------------------- the build's refusals (nothing is inserted)
class BuildTrack(object):
    def __init__(self, devices, midi=True):
        self.name, self.has_midi_input = "Bass", midi
        self.devices = devices
        self.inserted = []

    def insert_device(self, name):
        self.inserted.append(name)
        raise AssertionError("a refused build must not insert anything")


def build_cs(track):
    cs = CS(Track(Clip([]), Dev([])))
    cs._t = track
    return cs


@pytest.mark.parametrize("devices, midi, kwargs, message", [
    ([types.SimpleNamespace(name="Operator", type=1), types.SimpleNamespace(name="Feedback Bass (growl)", type=2)],
     True, {}, "already has a Feedback Bass rack"),
    ([types.SimpleNamespace(name="Arpeggiator", type=4)], True, {}, "no instrument"),
    ([types.SimpleNamespace(name="Operator", type=1)], True, {"key_note": "C5"}, "outside Roar's FB Note range"),
    ([types.SimpleNamespace(name="Operator", type=1)], True, {"preset": "loud"}, "preset is one of"),
])
def test_build_refusals(devices, midi, kwargs, message):
    t = BuildTrack(devices, midi)
    with pytest.raises(ext.ToolError, match=message):
        ext.cmd_build_feedback_bass(build_cs(t), 0, **kwargs)
    assert t.inserted == []
