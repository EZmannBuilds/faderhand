"""delete_arrangement_clip and record_track_audio, offline, against fake Live objects. These two commands came from
the installed development line (delete by position, slot checks, added scenes, the Temp Project warning). The fakes
model only the parts of Live's API the commands touch. The same commands in Live: tests/test_arrangement_edit.py and
the recording passes in tests/test_e2e_release.py."""
import importlib.util
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_spec = importlib.util.spec_from_file_location("faderhand_ext_rec", os.path.join(ROOT, "remote_script", "Faderhand", "ext.py"))
ext = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ext)


class Routing(object):
    def __init__(self, display_name, attached_object=None):
        self.display_name, self.attached_object = display_name, attached_object


class AClip(object):
    def __init__(self, name, start, end):
        self.name, self.start_time, self.end_time = name, float(start), float(end)


class RecClip(object):
    def __init__(self, path):
        self.is_recording, self.length, self.file_path = True, 0.0, path


class Slot(object):
    def __init__(self, track, has_clip=False):
        self.track, self.has_clip, self.clip, self.fired = track, has_clip, None, []

    def fire(self, record_length=None):
        self.fired.append(record_length)
        self.clip = RecClip(self.track.record_path)
        self.has_clip = True


class Track(object):
    def __init__(self, name, midi=False, slots=8, record_path="/Music/Song Project/Samples/Recorded/take.wav"):
        self.name, self.has_midi_input, self.record_path = name, midi, record_path
        self.clip_slots = [Slot(self) for _ in range(slots)]
        self.arrangement_clips = []
        self.available_input_routing_types = []
        self.input_routing_type = Routing("No Input")
        self.input_routing_channel = Routing("Post FX")
        self.available_input_routing_channels = [Routing("Post FX"), Routing("Pre FX")]
        self.current_monitoring_state, self.arm = 1, False
        self.deleted = []

    def delete_clip(self, c):
        self.arrangement_clips.remove(c)
        self.deleted.append(c.name)


class Song(object):
    signature_numerator, signature_denominator = 4, 4

    def __init__(self, tracks):
        self.tracks, self.scenes_created = tracks, 0

    def create_scene(self, index):
        assert index == -1
        self.scenes_created += 1
        for t in self.tracks:
            t.clip_slots.append(Slot(t))


class CS(object):
    def __init__(self, tracks, scratch=True):
        self._song, self.scratch, self.queue = Song(tracks), scratch, []

    def _track(self, ref):
        for t in self._song.tracks:
            if t.name == ref:
                return t
        if isinstance(ref, int):
            return self._song.tracks[ref]
        raise ext.ToolError("no track %r" % (ref,))

    def _ref(self, t):
        return t.name

    def _require_scratch(self):
        if not self.scratch:
            raise ext.ToolError("deletes run only in a disposable Set")

    def schedule_message(self, delay, fn):
        self.queue.append(fn)

    def run_tick(self):
        fn = self.queue.pop(0)
        fn()


def arranged():
    t = Track("Arr")
    t.arrangement_clips = [AClip("A", 0, 16), AClip("B", 32, 48), AClip("C", 64, 80)]
    return t


# --------------------------------------------------------------------------------------- delete_arrangement_clip
def test_delete_by_position():
    t = arranged()
    r = ext.cmd_delete_arrangement_clip(CS([t]), "Arr", at="9.1.1")       # bar 9 = beat 32
    assert t.deleted == ["B"]
    assert r["deleted"] == {"name": "B", "start": 32.0, "end": 48.0}
    assert r["arrangement_clips"] == 2


def test_delete_by_index_still_works():
    t = arranged()
    r = ext.cmd_delete_arrangement_clip(CS([t]), "Arr", index=2)
    assert t.deleted == ["C"] and r["deleted"]["name"] == "C"


@pytest.mark.parametrize("index", [-1, 3, None])
def test_delete_refuses_a_bad_index(index):
    t = arranged()
    with pytest.raises(ext.ToolError):
        ext.cmd_delete_arrangement_clip(CS([t]), "Arr", index=index)
    assert t.deleted == []                                               # -1 no longer deletes the last clip


def test_delete_refuses_a_position_with_no_clip():
    t = arranged()
    with pytest.raises(ext.ToolError, match="no arrangement clip starting"):
        ext.cmd_delete_arrangement_clip(CS([t]), "Arr", at="2.1.1")
    assert t.deleted == []


def test_delete_needs_a_disposable_set():
    t = arranged()
    with pytest.raises(ext.ToolError, match="disposable"):
        ext.cmd_delete_arrangement_clip(CS([t], scratch=False), "Arr", at="1.1.1")
    assert t.deleted == []


# ------------------------------------------------------------------------------------------- record_track_audio
def rig(slots=8, record_path=None):
    src = Track("Bass", slots=slots)
    kw = {"record_path": record_path} if record_path else {}
    dst = Track("Render", slots=slots, **kw)
    dst.available_input_routing_types = [Routing("Resampling"), Routing("Bass", src)]
    return CS([src, dst]), src, dst


def untouched(cs, dst):
    return cs._song.scenes_created == 0 and dst.input_routing_type.display_name == "No Input" and not cs.queue


def test_slot_past_the_last_scene_adds_scenes():
    cs, src, dst = rig(slots=8)
    r = ext.cmd_record_track_audio(cs, "Render", "Bass", slot=10, bars=2)
    assert r["slot"] == 10 and r["scenes_added"] == 3
    assert cs._song.scenes_created == 3 and len(dst.clip_slots) == 11 and len(src.clip_slots) == 11
    assert dst.input_routing_type.attached_object is src


def test_slot_inside_the_scenes_adds_nothing():
    cs, src, dst = rig(slots=8)
    r = ext.cmd_record_track_audio(cs, "Render", "Bass", slot=7)
    assert r["scenes_added"] == 0 and cs._song.scenes_created == 0


@pytest.mark.parametrize("slot,msg", [(-1, "0 or more"), (8 + 16, "far past")])
def test_bad_slot_is_refused_before_any_change(slot, msg):
    cs, src, dst = rig(slots=8)
    with pytest.raises(ext.ToolError, match=msg):
        ext.cmd_record_track_audio(cs, "Render", "Bass", slot=slot)
    assert untouched(cs, dst)


def test_sixteen_scenes_past_is_the_limit():
    cs, src, dst = rig(slots=8)
    r = ext.cmd_record_track_audio(cs, "Render", "Bass", slot=8 + 15)
    assert r["scenes_added"] == 16


def test_occupied_slot_is_refused_before_routing_changes():
    cs, src, dst = rig()
    dst.clip_slots[2].has_clip = True
    with pytest.raises(ext.ToolError, match="already holds a clip"):
        ext.cmd_record_track_audio(cs, "Render", "Bass", slot=2)
    assert untouched(cs, dst)


def test_midi_track_is_refused():
    cs, src, dst = rig()
    dst.has_midi_input = True
    with pytest.raises(ext.ToolError, match="MIDI track"):
        ext.cmd_record_track_audio(cs, "Render", "Bass")


def record(path):
    cs, src, dst = rig(record_path=path)
    ext.cmd_record_track_audio(cs, "Render", "Bass", slot=0, bars=2)
    cs.run_tick()                                   # routing: arm, monitoring
    cs.run_tick()                                   # launch: fire(record_length)
    assert dst.clip_slots[0].fired == [8.0] and dst.arm
    cs.run_tick()                                   # recording has started
    dst.clip_slots[0].clip.is_recording = False     # Live stops it after record_length
    dst.clip_slots[0].clip.length = 8.0
    cs.run_tick()
    st = ext.cmd_record_track_audio_status(cs)
    assert st["done"] and st["error"] is None and not dst.arm and st["clip_length"] == 8.0
    return st


def test_take_in_the_project_has_no_warning():
    st = record("/Music/Song Project/Samples/Recorded/Render 0001.wav")
    assert "warning" not in st


@pytest.mark.parametrize("path", ["/Users/x/Music/Ableton/Live Recordings/Temp Project/Samples/Recorded/1.wav",
                                  "/Users/x/Music/Ableton/Live Recordings/2026-11-27 Project/Samples/Recorded/1.wav"])
def test_take_outside_the_project_is_flagged(path):
    st = record(path)
    assert "Save it" in st["warning"] and path in st["warning"]
