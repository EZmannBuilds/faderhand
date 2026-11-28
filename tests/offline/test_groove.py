"""quantize_notes and the groove pool, offline, against fakes of Live's objects: a clip with Live's note API (fresh
copies on each read, writes matched by note_id, and Live's rule that notes of one pitch can't overlap), a groove pool,
clip grooves and a browser tree. The same commands in Live: tests/test_groove.py."""
import copy
import importlib.util
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_spec = importlib.util.spec_from_file_location("faderhand_ext_groove", os.path.join(ROOT, "remote_script", "Faderhand", "ext.py"))
ext = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ext)

FIELDS = ("pitch", "start_time", "duration", "velocity", "mute", "probability", "velocity_deviation",
          "release_velocity")


class Note(object):
    def __init__(self, note_id, pitch, start, duration=0.2, velocity=100.0):
        self.note_id, self.pitch, self.start_time, self.duration = note_id, pitch, start, duration
        self.velocity, self.mute, self.probability = float(velocity), False, 1.0
        self.velocity_deviation, self.release_velocity = 0.0, 64.0


class Groove(object):
    def __init__(self, name, base=3, timing=100.0):
        self.name, self.base = name, base
        self.timing_amount, self.random_amount, self.velocity_amount, self.quantization_amount = timing, 0.0, 0.0, 0.0


class Clip(object):
    is_audio_clip = False
    name = "Hats"
    length = 4.0

    def __init__(self, notes, groove=None):
        self._notes = dict((n.note_id, n) for n in notes)
        self.applied = 0
        self._groove = groove

    @property
    def groove(self):
        return self._groove

    @groove.setter
    def groove(self, g):
        if g is None:                      # as in Live 12.4.16
            raise TypeError("did not match C++ signature")
        self._groove = g

    def get_all_notes_extended(self):
        return [copy.copy(n) for n in sorted(self._notes.values(), key=lambda n: (n.start_time, n.pitch))]

    def apply_note_modifications(self, notes):
        self.applied += 1
        for n in notes:
            dst = self._notes[n.note_id]
            for f in FIELDS:
                setattr(dst, f, getattr(n, f))
        by_pitch = {}
        for n in self._notes.values():                 # Live: a note can't run into the next one of its pitch
            by_pitch.setdefault(n.pitch, []).append(n)
        for row in by_pitch.values():
            row.sort(key=lambda n: n.start_time)
            for a, b in zip(row, row[1:]):
                if a.start_time + a.duration > b.start_time:
                    a.duration = b.start_time - a.start_time


class Slot(object):
    def __init__(self, clip):
        self.clip = clip


class Track(object):
    name = "Hats"

    def __init__(self, clip):
        self.clip_slots = [Slot(clip)]
        self.arrangement_clips = []


class Pool(object):
    def __init__(self, grooves):
        self.grooves = grooves


class Song(object):
    signature_numerator = 4
    signature_denominator = 4

    def __init__(self, track, grooves):
        self.tracks = [track]
        self.groove_pool = Pool(grooves)
        self.groove_amount = 1.0


class Item(object):
    def __init__(self, name, children=(), loadable=False):
        self.name, self.children = name, list(children)
        self.is_loadable, self.is_folder = loadable, not loadable


class Browser(object):
    def __init__(self, cs):
        self.cs, self.loaded = cs, []
        agr = lambda n: Item(n + ".agr", loadable=True)
        self.packs = Item("packs", [Item("Core Library", [Item("Grooves", [
            Item("Swing", [Item("Basic", [agr("Swing 16ths 57"), agr("Swing 8ths 57")]),
                           Item("MPC", [agr("Swing MPC 3000 16ths 54")])]),
            Item("Style", [agr("Funk Drummer 16ths")])])])])
        self.user_library = Item("user_library", [Item("Grooves", [agr("My Shuffle"), agr("Swing 16ths 57")])])

    def load_item(self, item):
        self.loaded.append(item.name)
        self.cs._song.groove_pool.grooves.append(Groove(item.name[:-4]))


class App(object):
    def __init__(self, cs):
        self.browser = Browser(cs)


class CS(object):
    def __init__(self, clip, grooves=None):
        self._t = Track(clip)
        self._song = Song(self._t, list(grooves or []))
        self._app = App(self)

    def _track(self, ref):
        return self._t

    def _ref(self, t):
        return "track:0"

    def application(self):
        return self._app


LATE = [0.03, 0.27, 0.49, 0.71, 1.02, 1.26, 1.52, 1.77]


def hats(starts=LATE, duration=0.2):
    return Clip([Note(i + 1, 42, s, duration) for i, s in enumerate(starts)])


def starts(clip, pitch=42):
    return [round(n.start_time, 6) for n in clip.get_all_notes_extended() if n.pitch == pitch]


# ---------------------------------------------------------------- grid and swing
def test_grid_values():
    cs = CS(hats())
    assert ext._grid_beats(cs, "1/16") == 0.25 and ext._grid_beats(cs, "1/8T") == pytest.approx(1 / 3)
    assert ext._grid_beats(cs, 0.25) == 0.25 and ext._grid_beats(cs, "0.5b") == 0.5
    with pytest.raises(ext.ToolError, match="note value"):
        ext._grid_beats(cs, "1/7")


def test_swung_positions():
    assert [ext._swung(k, 0.25, 50) for k in range(4)] == [0.0, 0.25, 0.5, 0.75]
    assert [round(ext._swung(k, 0.25, 66), 6) for k in range(4)] == [0.0, 0.33, 0.5, 0.83]
    assert ext._nearest_step(0.31, 0.25, 66) == pytest.approx(0.33)
    assert ext._nearest_step(0.43, 0.25, 66) == pytest.approx(0.5)


# ---------------------------------------------------------------- quantize
def test_full_and_half_strength():
    clip = hats()
    ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/16", strength=50)
    assert starts(clip) == [round(s + (round(s / 0.25) * 0.25 - s) / 2, 6) for s in LATE]
    r = ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/16")
    assert starts(clip) == [i * 0.25 for i in range(8)]
    assert r["written"] and r["mean_off_grid_after"] == 0.0
    assert all(n.duration == 0.2 for n in clip.get_all_notes_extended())


def test_swing_shortens_notes_that_run_into_the_next_as_live_does():
    clip = hats([i * 0.25 for i in range(8)])
    r = ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/16", swing=66)
    assert starts(clip) == [0.0, 0.33, 0.5, 0.83, 1.0, 1.33, 1.5, 1.83]
    short = sorted(n.note_id for n in clip.get_all_notes_extended() if n.duration < 0.2 - 1e-9)
    assert sorted(r["shortened"]) == short and len(short) == 3     # 0.33 + 0.2 runs past 0.5; the last has no next
    assert r["written"]                                            # the read-back expected the trims


def test_a_moved_note_can_shorten_one_outside_the_selection():
    clip = Clip([Note(1, 42, 0.0, 0.51), Note(2, 42, 0.52, 0.2)])  # 2 moves to 0.5 and cuts note 1 to 0.5
    r = ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/8", ids=[2])
    assert r["shortened_outside_selection"] == [1]
    assert [(n.start_time, round(n.duration, 6)) for n in clip.get_all_notes_extended()] == [(0.0, 0.5), (0.5, 0.2)]


def test_ends():
    clip = Clip([Note(1, 36, 0.02, 0.45), Note(2, 36, 1.01, 0.52)])
    ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/8", ends=True)
    assert [(n.start_time, round(n.duration, 6)) for n in clip.get_all_notes_extended()] == [(0.0, 0.5), (1.0, 0.5)]


def test_collisions_write_nothing():
    clip = hats([0.0, 0.1, 0.5])
    with pytest.raises(ext.ToolError, match="same spot"):
        ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/2")
    assert clip.applied == 0
    clip = hats([0.0, 0.1])
    with pytest.raises(ext.ToolError, match="outside the selection"):
        ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/4", ids=[2])
    assert clip.applied == 0


def test_a_dry_run_shows_collisions_instead_of_failing():
    clip = hats([0.0, 0.1, 0.5])
    r = ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/2", dry_run=True)
    assert not r["written"] and clip.applied == 0
    # "1/2" is a half note (2 beats), so all three land on 0: two pairs
    assert r["collisions"] == [{"pitch": 42, "start": 0.0, "ids": [1, 2]}, {"pitch": 42, "start": 0.0, "ids": [2, 3]}]


def test_dry_run_and_selection():
    clip = Clip([Note(i + 1, 42, s) for i, s in enumerate(LATE)] + [Note(50, 36, 0.04, 0.5)])
    r = ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/16", dry_run=True)
    assert not r["written"] and r["changed"] == 9 and clip.applied == 0
    ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, grid="1/16", pitch=42)
    assert starts(clip, 36) == [0.04]                              # the kick wasn't selected
    assert sorted((n.note_id, n.pitch, n.velocity) for n in clip.get_all_notes_extended()) == \
        sorted([(i + 1, 42, 100.0) for i in range(8)] + [(50, 36, 100.0)])


@pytest.mark.parametrize("kwargs, message", [
    ({"grid": 0}, "outside"), ({"strength": 120}, "outside 0..100"), ({"swing": 40}, "outside 50..75"),
    ({"pitch": 99}, "no notes matched"),
])
def test_bad_quantize_requests(kwargs, message):
    clip = hats()
    with pytest.raises(ext.ToolError, match=message):
        ext.cmd_quantize_notes(CS(clip), "Hats", slot=0, **kwargs)
    assert clip.applied == 0


# ---------------------------------------------------------------- groove pool
def pool_cs():
    g0, g1 = Groove("Swing 16ths 66"), Groove("Swing 8ths 52", base=1)
    clip = hats()
    clip._groove = g0
    return CS(clip, [g0, g1]), clip, g0, g1


def test_get_groove_pool():
    cs, clip, g0, g1 = pool_cs()
    r = ext.cmd_get_groove_pool(cs, clips=True)
    assert r["global_amount"] == 1.0 and r["count"] == 2
    assert [(g["name"], g["base"], g["timing"]) for g in r["grooves"]] == [("Swing 16ths 66", "1/16", 100.0),
                                                                          ("Swing 8ths 52", "1/8", 100.0)]
    assert r["clips"] == [{"slot": 0, "track": "track:0", "clip": "Hats", "groove": 0, "groove_name": "Swing 16ths 66"}]


def test_set_groove_and_amount():
    cs, clip, g0, g1 = pool_cs()
    r = ext.cmd_set_groove(cs, "Swing 8ths 52", timing=40, random=5, velocity=-30, quantize=20, base="1/16")
    assert {k: r["after"][k] for k in ("timing", "random", "velocity", "quantize", "base")} == \
        {"timing": 40.0, "random": 5.0, "velocity": -30.0, "quantize": 20.0, "base": "1/16"}
    assert g1.base == 3
    assert ext.cmd_set_groove_amount(cs, 131.25)["after"] == 131.25 and cs._song.groove_amount == 1.3125
    for bad, msg in (({"timing": 150}, "outside 0..100"), ({"velocity": -101}, "outside -100..100"),
                     ({"base": "1/12"}, "base is one of"), ({}, "nothing to change")):
        with pytest.raises(ext.ToolError, match=msg):
            ext.cmd_set_groove(cs, 1, **bad)
    with pytest.raises(ext.ToolError, match="outside"):
        ext.cmd_set_groove_amount(cs, 140)


def test_set_clip_groove():
    cs, clip, g0, g1 = pool_cs()
    r = ext.cmd_set_clip_groove(cs, "Hats", 1, slot=0)
    assert r["before"] == {"index": 0, "name": "Swing 16ths 66"} and r["after"] == {"index": 1, "name": "Swing 8ths 52"}
    assert clip.groove is g1
    with pytest.raises(ext.ToolError, match="out of range"):
        ext.cmd_set_clip_groove(cs, "Hats", 5, slot=0)
    with pytest.raises(ext.ToolError, match="empty"):
        ext.cmd_set_clip_groove(CS(hats()), "Hats", 0, slot=0)


def test_list_and_load_grooves():
    cs, clip, g0, g1 = pool_cs()
    allg = ext.cmd_list_grooves(cs)
    assert allg["count"] == 6
    assert [g["name"] for g in ext.cmd_list_grooves(cs, search="mpc 16")["grooves"]] == ["Swing MPC 3000 16ths 54"]
    assert [g["folder"] for g in ext.cmd_list_grooves(cs, search="funk")["grooves"]] == ["Style"]
    with pytest.raises(ext.ToolError, match="give folder"):
        ext.cmd_load_groove(cs, "Swing 16ths 57")                 # in Core Library and the User Library
    r = ext.cmd_load_groove(cs, "Swing 16ths 57", folder="Swing/Basic")
    assert r["pool_before"] == 2 and cs._app.browser.loaded == ["Swing 16ths 57.agr"]
    assert [g.name for g in cs._song.groove_pool.grooves][-1] == "Swing 16ths 57"
    assert clip.groove is g0                                       # loading changes no clip
    with pytest.raises(ext.ToolError, match="no groove called"):
        ext.cmd_load_groove(cs, "Nope")
