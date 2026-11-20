# Evaluation tasks (v1)

Ten tasks, one per capability. A runner agent gets this file, the fixtures folder, one skill to follow and an
output folder `OUT`. Both arms of a comparison get the same file, fixtures, model and tools. Only the skill differs.
`score.py` scores each output folder objectively; `judge` prompts compare pairs blind.

Runner rules (part of the prompt):
- Treat each brief as a locked intent: the user said "just make it, no questions". Don't ask anything.
- No DAW is open. Don't call any Ableton or Faderhand tools. Write MIDI with Python and `mido`
  (`uv run -q --no-project --with mido python script.py`). Keep any script you write in `OUT/scripts/`.
- Read only the skill folder you were given, this file, the fixtures folder and `OUT`. Don't read other folders
  on this computer and don't browse the web.
- Every MIDI file: 480 PPQ, a tempo and time signature meta event, one named track per part, drums on MIDI
  channel 10. Put files exactly where each task says.

## T01 MIDI comprehension
Read `fixtures/comprehension.mid`. Write `OUT/t01_answers.json` with keys: `tempo_bpm` (number), `meter`
("n/d"), `key` (e.g. "E minor"), `bars` (int), `roles` (object: track name to one of drums, bass, chords, melody,
arp, pad, fx), `swing_percent` (the 16th-note swing as the long note's share of an 8th, 50 = straight),
`bass_onsets_total`, `bass_onsets_on_kick` (bass onsets within 1/32 of a kick onset), `arrangement_change_bar`
(the first bar of the new section), `chords` (the four-chord cycle, e.g. ["Am7", ...]).

## T02 Accurate MIDI editing and preserving material
Copy `fixtures/comprehension.mid` to `OUT/t02_edited.mid` and edit it: (a) transpose the Bass track down one
octave in bars 5–8 only; (b) add ghost snare notes (pitch 38, velocity 25–45) on the 2nd and 4th 16th of beats 2
and 4 ("e" and "a") in bars 1–4 only. Change nothing else: no other note, velocity, timing, track or tempo.

## T03 Genre composition: Atlanta trap
Compose an original 8-bar trap loop at 140 BPM in a minor key: drums (kick, snare or clap, closed hats with
rolls, open hat), an 808 bass part, and one melodic lead. Make it sound like the genre played by a strong
producer, not a template. Save `OUT/t03_trap.mid` and a short `OUT/t03_notes.md` (what you did and why).

## T04 Human timing and articulation
Write a 4-bar funk drum groove at 100 BPM, as if a session drummer played it into a MIDI kit: kick, snare
(with ghost notes), hi-hat, plus whatever else the groove needs. Save `OUT/t04_funk_drums.mid`.

## T05 Complete arrangement
Compose an original instrumental of at least 48 bars at 88 BPM in a boom-bap / lo-fi hip-hop style with an
intro, verses, a hook, a bridge and an outro: drums, bass, keys and a lead. Mark sections with MIDI marker meta
events. Save `OUT/t05_song.mid` and `OUT/t05_notes.md`.

## T06 Instrumental interaction
Compose an original 8-bar neo-soul groove at 84 BPM: drums, bass guitar, electric piano chords and a short
melodic fill. Bass and kick should interlock, and the chords should leave room for a vocal. Save
`OUT/t06_neosoul.mid`.

## T07 Sound design and Vital
Write `OUT/t07_vital.json` with the raw Vital 1.0.x preset values (not display values) for: `unison_detune`
giving 20 cents between two voices; `volume` (the master volume parameter) for -6 dB relative to the default volume;
`reverb_decay_time` for 3.0 seconds; `delay_frequency` (sync off) for a 375 ms delay; `osc_1_tune` for +25 cents.
Also a key `basis` saying in one line where each value came from.

## T08 DAW automation and effects plan
Write `OUT/t08_calls.json`: the exact ordered list of Faderhand tool calls (objects with `tool` and `args`) that
would, in an open saved Live Set with tracks "Keys", "Bass", "Kick" and "Lead": create a return track named
"Plate" with Live's Reverb on it; send Keys to it at -14 dB; put a Compressor on Bass sidechained from Kick;
automate Auto Filter frequency on Lead from 300 Hz to 8 kHz across bars 17–24 (load the Auto Filter first).
Use only tools and argument names the skill documents. Don't call the tools.

## T09 Preservation under revision
(Scored from T10's output.) The chord pitches of every bar and the hook's pitch sequence in `fixtures/flawed.mid`
are protected and must survive T10 unchanged.

## T10 Revision
`fixtures/flawed.mid` sounds machine-made and repetitive. Revise it so it sounds performed and develops over its
8 bars, while keeping the chord progression's pitches and the hook melody's pitch sequence exactly. You may
change rhythm placement slightly, velocities, durations, the drums and the bass. Save `OUT/t10_revised.mid` and
`OUT/t10_notes.md` (what was wrong, what you changed, how you checked it).
