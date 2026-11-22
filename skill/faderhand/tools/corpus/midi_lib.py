"""Small, dependency-light MIDI reader for corpus analysis (needs `mido`).

Reads a Standard MIDI File into a flat list of notes with ticks and seconds, plus the
tempo map, time signatures, controller and pitch-bend counts. Nothing here executes
or trusts file content beyond parsing it.
"""
from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, field

import mido

DRUM_CHANNEL = 9  # MIDI channel 10, zero-based


@dataclass
class Note:
    track: int
    channel: int
    pitch: int
    velocity: int
    start: int  # ticks
    end: int    # ticks
    start_s: float = 0.0
    end_s: float = 0.0


@dataclass
class Song:
    path: str
    ppq: int
    notes: list
    tempos: list            # [(tick, microseconds_per_beat)]
    time_sigs: list         # [(tick, numerator, denominator)]
    track_names: dict       # track index -> name
    programs: dict          # (track, channel) -> program
    cc_counts: dict = field(default_factory=dict)  # controller number -> count
    pitchbend_count: int = 0
    length_ticks: int = 0

    @property
    def bpm(self) -> float:
        return mido.tempo2bpm(self.tempos[0][1]) if self.tempos else 120.0

    @property
    def meter(self) -> tuple:
        return (self.time_sigs[0][1], self.time_sigs[0][2]) if self.time_sigs else (4, 4)

    def bar_ticks(self) -> int:
        num, den = self.meter
        return int(self.ppq * num * 4 / den)


def read(path: str) -> Song:
    mf = mido.MidiFile(path, clip=True)
    ppq = mf.ticks_per_beat or 480
    notes, tempos, sigs, names, programs, cc = [], [], [], {}, {}, {}
    pb = 0
    length = 0
    for ti, track in enumerate(mf.tracks):
        t = 0
        open_notes = {}
        for msg in track:
            t += msg.time
            if msg.is_meta:
                if msg.type == "set_tempo":
                    tempos.append((t, msg.tempo))
                elif msg.type == "time_signature":
                    sigs.append((t, msg.numerator, msg.denominator))
                elif msg.type == "track_name" and msg.name.strip():
                    names[ti] = msg.name.strip()
                continue
            if msg.type == "note_on" and msg.velocity > 0:
                open_notes.setdefault((msg.channel, msg.note), []).append((t, msg.velocity))
            elif msg.type in ("note_off", "note_on"):
                stack = open_notes.get((msg.channel, msg.note))
                if stack:
                    st, vel = stack.pop(0)
                    notes.append(Note(ti, msg.channel, msg.note, vel, st, max(t, st + 1)))
            elif msg.type == "control_change":
                cc[msg.control] = cc.get(msg.control, 0) + 1
            elif msg.type == "pitchwheel":
                pb += 1
            elif msg.type == "program_change":
                programs.setdefault((ti, msg.channel), msg.program)
        for (ch, p), stack in open_notes.items():
            for st, vel in stack:
                notes.append(Note(ti, ch, p, vel, st, st + ppq // 4))
        length = max(length, t)
    tempos.sort()
    sigs.sort()
    if not tempos or tempos[0][0] > 0:
        tempos.insert(0, (0, 500000))
    _seconds(notes, tempos, ppq)
    notes.sort(key=lambda n: (n.start, n.pitch))
    return Song(path, ppq, notes, tempos, sigs, names, programs, cc, pb, length)


def _seconds(notes, tempos, ppq):
    # cumulative seconds at each tempo change
    ticks = [t for t, _ in tempos]
    secs = [0.0]
    for i in range(1, len(tempos)):
        dt = tempos[i][0] - tempos[i - 1][0]
        secs.append(secs[-1] + dt * tempos[i - 1][1] / 1e6 / ppq)

    def conv(tick):
        i = bisect.bisect_right(ticks, tick) - 1
        return secs[i] + (tick - ticks[i]) * tempos[i][1] / 1e6 / ppq

    for n in notes:
        n.start_s = conv(n.start)
        n.end_s = conv(n.end)


def content_hashes(song: Song) -> tuple:
    """(exact musical hash, transposition-invariant hash), both on a 1/16 grid, ignoring velocity."""
    step = max(1, song.ppq // 4)
    pitched = [n for n in song.notes if n.channel != DRUM_CHANNEL]
    events = sorted((round(n.start / step), n.pitch, n.channel == DRUM_CHANNEL) for n in song.notes)
    exact = hashlib.sha1(repr(events).encode()).hexdigest()[:16]
    base = min((n.pitch for n in pitched), default=0)
    inv = sorted((round(n.start / step), (n.pitch - base) if n.channel != DRUM_CHANNEL else 1000 + n.pitch)
                 for n in song.notes)
    if inv:
        t0 = inv[0][0]
        inv = [(a - t0, b) for a, b in inv]
    trans = hashlib.sha1(repr(inv).encode()).hexdigest()[:16]
    return exact, trans
