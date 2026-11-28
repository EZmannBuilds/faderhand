"""get_clip_notes and set_note_expression, offline: the note selection, the velocity math, and the write with its
read-back, against a fake clip that behaves like Live's note API (get_all_notes_extended returns fresh copies each
call; apply_note_modifications writes attributes back by note_id). The same commands in Live:
tests/test_note_expression.py."""
import copy
import importlib.util
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_spec = importlib.util.spec_from_file_location("faderhand_ext", os.path.join(ROOT, "remote_script", "Faderhand", "ext.py"))
ext = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ext)

FIELDS = ("pitch", "start_time", "duration", "velocity", "mute", "probability", "velocity_deviation",
          "release_velocity")


class Note(object):
    def __init__(self, note_id, pitch, start, duration=0.25, velocity=100.0):
        self.note_id, self.pitch, self.start_time, self.duration = note_id, pitch, start, duration
        self.velocity, self.mute, self.probability = float(velocity), False, 1.0
        self.velocity_deviation, self.release_velocity = 0.0, 64.0


class Clip(object):
    is_audio_clip = False
    name = "Drums"
    length = 4.0

    def __init__(self, notes):
        self._notes = dict((n.note_id, n) for n in notes)
        self.applied = 0

    def get_all_notes_extended(self):
        return [copy.copy(n) for n in sorted(self._notes.values(), key=lambda n: (n.start_time, n.pitch))]

    def apply_note_modifications(self, notes):
        self.applied += 1
        for n in notes:
            dst = self._notes[n.note_id]
            for f in FIELDS:
                setattr(dst, f, getattr(n, f))


class DeafClip(Clip):
    """Accepts the call but keeps every velocity as it was: the read-back must catch it."""

    def apply_note_modifications(self, notes):
        self.applied += 1
        for n in notes:
            dst = self._notes[n.note_id]
            for f in FIELDS:
                if f != "velocity":
                    setattr(dst, f, getattr(n, f))


class Slot(object):
    def __init__(self, clip):
        self.clip = clip


class Track(object):
    name = "Drums"

    def __init__(self, clip):
        self.clip_slots = [Slot(clip)]
        self.arrangement_clips = []


class Song(object):
    signature_numerator = 4
    signature_denominator = 4


class CS(object):
    def __init__(self, clip):
        self._song, self._t = Song(), Track(clip)

    def _track(self, ref):
        return self._t

    def _ref(self, t):
        return "track:0"


def drums():
    """One bar of 4/4: closed hats (42) on every 16th at velocity 100, kicks (36) on each beat at 120."""
    notes = [Note(i + 1, 42, i * 0.25) for i in range(16)]
    notes += [Note(100 + b, 36, float(b), 0.5, 120) for b in range(4)]
    return Clip(notes)


def by_pitch(clip, pitch):
    return [n for n in clip.get_all_notes_extended() if n.pitch == pitch]


def test_get_clip_notes_filters():
    cs = CS(drums())
    get = lambda **k: ext.cmd_get_clip_notes(cs, "Drums", slot=0, **k)
    assert get()["matched"] == 20
    assert get(pitch=42)["matched"] == 16
    assert get(pitch=[36, 42])["matched"] == 20
    assert get(pitch_range=[30, 40])["matched"] == 4
    assert get(pitch=42, every=1)["matched"] == 4                      # hats on the beat
    assert get(pitch=42, every=0.5, offset=0.25)["matched"] == 8       # the off-beat 16ths
    assert get(start="1.2.1", end="1.3.1")["matched"] == 5             # beat 2: four hats and a kick
    r = get(pitch=42, limit=3)
    assert r["truncated"] and len(r["notes"]) == 3
    assert [n["start"] for n in get(pitch=42)["notes"]] == [i * 0.25 for i in range(16)]


def test_summary_reads_the_accents():
    cs = CS(drums())
    s = ext.cmd_get_clip_notes(cs, "Drums", slot=0, pitch=42)["summary"]
    assert s["count"] == 16 and s["velocity_min"] == s["velocity_max"] == 100.0 and s["distinct_velocities"] == 1
    assert [row[0] for row in s["velocity_by_16th"]] == list(range(1, 17))
    assert s["muted"] == 0 and s["below_full_chance"] == 0


def test_grouped_hat_accents_3_3_2():
    """The drill lesson's grouped hats: accents on the 1st, 4th and 7th 16th of each group of 8."""
    clip = drums()
    cs = CS(clip)
    r = ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=42, velocity_pattern=[110, 70, 70, 110, 70, 70, 105, 75])
    assert r["written"] and r["matched"] == 16 and r["changed"] == 16 and clip.applied == 1
    got = [n.velocity for n in by_pitch(clip, 42)]
    assert got == [110, 70, 70, 110, 70, 70, 105, 75] * 2
    steps = dict((k, v) for k, v, _ in ext.cmd_get_clip_notes(cs, "Drums", slot=0, pitch=42)["summary"]["velocity_by_16th"])
    assert steps[1] == steps[4] == 110 and steps[7] == 105
    assert [n.velocity for n in by_pitch(clip, 36)] == [120] * 4      # the kicks were not selected


def test_pattern_steps_once_per_onset():
    """Notes that start together (a kick and a hat on the beat) share one pattern step."""
    clip = drums()
    ext.cmd_set_note_expression(CS(clip), "Drums", slot=0, velocity_pattern=[127, 60])
    notes = clip.get_all_notes_extended()
    at0 = [n.velocity for n in notes if n.start_time == 0.0]
    assert at0 == [127, 127]
    assert [n.velocity for n in notes if n.start_time == 0.25] == [60]
    assert [n.velocity for n in notes if n.start_time == 0.5] == [127]   # the third onset: back to step 1


def test_ramp_scale_add_and_clamp():
    clip = drums()
    cs = CS(clip)
    ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=42, velocity_ramp=[40, 115])
    v = [n.velocity for n in by_pitch(clip, 42)]
    assert v[0] == 40 and v[-1] == 115 and v == sorted(v)
    r = ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=36, velocity_scale=1.5)
    assert r["clamped"] == 4 and [n.velocity for n in by_pitch(clip, 36)] == [127] * 4
    r = ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=36, velocity_add=-127)   # 127 - 127 = 0: kept at 1
    assert r["clamped"] == 4 and [n.velocity for n in by_pitch(clip, 36)] == [1] * 4
    ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=36, velocity=100, velocity_add=-10)
    assert [n.velocity for n in by_pitch(clip, 36)] == [90] * 4        # base, then add


def test_humanize_is_repeatable_and_bounded():
    a, b, c = drums(), drums(), drums()
    for clip, seed in ((a, 7), (b, 7), (c, 8)):
        ext.cmd_set_note_expression(CS(clip), "Drums", slot=0, pitch=42, humanize=12, seed=seed)
    va, vb, vc = ([n.velocity for n in by_pitch(x, 42)] for x in (a, b, c))
    assert va == vb and va != vc
    assert all(88 <= x <= 112 for x in va) and len(set(va)) > 1


def test_chance_range_release_and_mute():
    clip = drums()
    cs = CS(clip)
    ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=42, every=0.5, offset=0.25, probability=0.5,
                                velocity_deviation=-20, release_velocity=30)
    off = [n for n in by_pitch(clip, 42) if (n.start_time / 0.25) % 2 == 1]
    on = [n for n in by_pitch(clip, 42) if (n.start_time / 0.25) % 2 == 0]
    assert all(n.probability == 0.5 and n.velocity_deviation == -20 and n.release_velocity == 30 for n in off)
    assert all(n.probability == 1.0 and n.velocity_deviation == 0 for n in on)
    assert ext.cmd_get_clip_notes(cs, "Drums", slot=0, pitch=42)["summary"]["below_full_chance"] == 8
    ids = [n.note_id for n in by_pitch(clip, 36)][:2]
    ext.cmd_set_note_expression(cs, "Drums", slot=0, ids=ids, mute=True)
    assert [n.mute for n in by_pitch(clip, 36)] == [True, True, False, False]


def test_nothing_moves():
    clip = drums()
    where = [(n.note_id, n.pitch, n.start_time, n.duration) for n in clip.get_all_notes_extended()]
    ext.cmd_set_note_expression(CS(clip), "Drums", slot=0, velocity_pattern=[90, 60, 75], humanize=5, probability=0.9)
    assert [(n.note_id, n.pitch, n.start_time, n.duration) for n in clip.get_all_notes_extended()] == where


def test_dry_run_and_unchanged_write_nothing():
    clip = drums()
    cs = CS(clip)
    r = ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=42, velocity=64, dry_run=True)
    assert r["dry_run"] and not r["written"] and r["changed"] == 16 and clip.applied == 0
    assert r["notes"][0]["before"] == {"velocity": 100.0} and r["notes"][0]["after"] == {"velocity": 64.0}
    assert all(n.velocity == 100 for n in by_pitch(clip, 42))
    r = ext.cmd_set_note_expression(cs, "Drums", slot=0, pitch=42, velocity=100)
    assert r["changed"] == 0 and r["unchanged"] == 16 and not r["written"] and clip.applied == 0


def test_read_back_catches_a_write_that_did_not_land():
    clip = DeafClip(drums().get_all_notes_extended())
    with pytest.raises(ext.ToolError, match="read back different"):
        ext.cmd_set_note_expression(CS(clip), "Drums", slot=0, pitch=42, velocity=64)


@pytest.mark.parametrize("kwargs, message", [
    ({"velocity": 90, "velocity_pattern": [90]}, "one of velocity"),
    ({}, "nothing to change"),
    ({"pitch": 99, "velocity": 90}, "no notes matched"),
    ({"velocity": 0}, "outside 1..127"),
    ({"velocity_pattern": []}, "list of velocities"),
    ({"velocity_ramp": [60]}, r"\[from, to\]"),
    ({"probability": 1.5}, "outside 0..1"),
    ({"release_velocity": 200}, "outside 0..127"),
    ({"pitch_range": [60, 40], "velocity": 90}, "above high"),
    ({"every": 0, "velocity": 90}, "more than 0"),
    ({"start": 2, "end": 1, "velocity": 90}, "must be before"),
])
def test_bad_requests_write_nothing(kwargs, message):
    clip = drums()
    with pytest.raises(ext.ToolError, match=message):
        ext.cmd_set_note_expression(CS(clip), "Drums", slot=0, **kwargs)
    assert clip.applied == 0


def test_audio_clips_are_refused():
    clip = drums()
    clip.is_audio_clip = True
    with pytest.raises(ext.ToolError, match="audio clip"):
        ext.cmd_get_clip_notes(CS(clip), "Drums", slot=0)
