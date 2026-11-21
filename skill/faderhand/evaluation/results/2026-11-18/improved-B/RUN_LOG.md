# Run log: improved-B (Faderhand Music skill, eval pack v1, T01–T10)

**Mode:** DO IT, with a locked intent ("just make it, no questions"). I asked nothing.
- No user profile exists (`modules/studio/profiles/local/` is empty), so the output location came from the runner.
- No DAW was open. I called no Ableton, Faderhand, WavRead or other MCP tools.
- MIDI was written with Python and mido. All scripts are in `scripts/`.

## Skill files read
Paths are relative to `improved-repo/skill/faderhand-music/` unless marked otherwise.

**Entry and routing**
- `SKILL.md` (entry and routing table)
- `modules/studio/SKILL.md`
- `modules/studio/music-director/SKILL.md` (lines 1–330: session start, plan gate, "just make it" mode, routing rules)

**Knowledge**
- `modules/knowledge/GENERATION_RULES.md`
- `modules/knowledge/TARGETS.md`
- `modules/knowledge/DRUMS_AND_GROOVE.md`
- `modules/knowledge/LOW_END_808_AND_BASS.md`
- `modules/knowledge/MELODY_LINES_AND_DEVELOPMENT.md`
- `modules/knowledge/ARRANGEMENT_AND_REVISION.md`
- a local findings file from a source pending licence clearance (`local/`, never shipped; removed from the skill on 2026-11-21): local-only numbers, used for trap 808 and hat decisions and not quoted in any deliverable

**Studio protocols and specialists**
- `modules/studio/shared/SKETCH_ROUND_PROTOCOL.md`
- `modules/studio/shared/MIDI_EXPORT_SCHEMA.md`
- `modules/studio/midi-builder/SKILL.md` (lines 102–215 and 335–370: verification, GM percussion rule)
- `modules/studio/performance-director/SKILL.md` (lines 100–152: timing models)

**DAW and Vital**
- `modules/daw-faderhand/README.md`
- `modules/vital/README.md`
- `improved-repo/docs/TOOL-REFERENCE.md`, plus a grep of `improved-repo/docs/TOOLS.md` for units

**Tools: read and run**
- `tools/midi_check.py`: read, then run on every MIDI file
- `tools/kb_search.py`: run for each genre and role. The sections it returned were the knowledge pages above.
- `tools/corpus/analyze.py`: only `chord_features`, to understand why rolled chords measured as 2 voices

Directory listings only: `modules/studio/shared/SYNTH_WORKSHOP/` (grepped for volume and default) and `modules/studio/profiles/local/`.

## Process applied to every composition task
The skill's loop is: sketch 2–3 directions that differ by mechanism, measure them with `midi_check.py`, then KEEP, REVISE, RECOMBINE or REJECT.

- The sketches are in `work/t0X_sketch_{A,B,C}.mid`.
- The decisions are recorded in `work/sketch_rounds.json`, marked unrendered: the basis is measured or inferred, and the decider is director_provisional.
- After building, every file went through:
  - `midi_check.py` for its genre;
  - `scripts/verify.py`, which checks for type 1, 480 PPQ, tempo and time-signature events, named tracks, drums on ch 10 only, no pitched part on ch 10, and notes on every track;
  - a bar-by-bar read-back of chosen bars.
- **Nothing was rendered or listened to.** Every judgment is from measurement or reading the notes.

## Per task

**T01: `t01_answers.json`**
- Measured from the fixture by `scripts/t01_t02.py`, cross-checked with `midi_check.py --json`.
- Answers:
  - tempo 92, meter 4/4, key D minor, 16 bars
  - roles: Drums = drums, Bass = bass, Keys = chords, Lead = melody
  - swing 57.9: off-16th hats sit 139/240 ticks into each 8th; the analyser also gives 57.9
  - bass onsets 64, of which 48 are within 1/32 of a kick
  - the new section starts at bar 9 (the lead enters and the hats go to swung 16ths)
  - chords: Dm7, Bbmaj7, C7, A7
- The key was checked from the pitch-class weights and the A7 (C#) dominant.

**T02: `t02_edited.mid`**
- Edited at the message level from a copy of the fixture.
- Bass notes that start in bars 5–8 go down 12. Both the note-on and the note-off move, including bar 8's last note, whose note-off falls on the bar-9 line.
- 16 ghost snares were added (pitch 38, ch 10, length 60 ticks, on the exact 16th grid) on the "e" and "a" of beats 2 and 4 in bars 1–4. Velocities vary from 26 to 45, and the "a" before the next beat is usually louder.
- How I checked it: a diff script rebuilt the expected note list from the fixture plus exactly these edits and compared it with the output.
  - Problems: none.
  - Meta events, track names, track order, track lengths and tempo are all identical.

**T03: `t03_trap.mid`, `t03_notes.md`**
- C# minor, 8 bars, programmed feel.
- The sketch round kept A ("bounce") after one revision: the 808 slides were cut from 3.4 to 1.6 a bar by overlapping only chosen notes.
- `midi_check --genre trap`: 0 REVISE. Details are in the notes.

**T04: `t04_funk_drums.mid`**
- 4 bars at 100 BPM. Sketches: A (16th hats, ghost-rich), B (8th hats with open barks), C (linear).
- **Kept A, revised for a session-drummer feel:**
  - jitter raised to about 13 ms local
  - wider in-tier hat variation, with 15% of 16ths jumping a tier
  - tom fill in bar 4, foot hat on 2 and 4 in the fill bar
- `midi_check --genre funk`: 0 REVISE.

  | Measure | Value |
  |---|---|
  | swing | 54.6 |
  | ghosts | 3.5 a bar |
  | on-grid share | 0.22 |
  | jitter | 12.9 ms |
  | hat structure | 0.69 |
  | hat SD | 14.8 |
  | snare SD | 33.5 |
  | snare behind the hats | 11.6 ms |

- Every bar differs.

**T05: `t05_song.mid`, `t05_notes.md`**
- F minor, 60 bars (about 2:44), with markers for Intro, Verse 1, Hook, Verse 2, Bridge, Hook 2 and Outro.
- The sketch round kept A and took B's busier bass for the hooks only.
- Parallel fifths measured in the sketch were traced to one voicing and fixed: 13 per 100 moves in the sketch, 1.0 per 100 in the song.
- `--genre boom-bap` and `--genre lofi`: 0 REVISE. 6 of the 8-bar boundaries change, against a target of 3 or more.

**T06: `t06_neosoul.mid`**
- 84 BPM in Eb, 8 bars: Abmaj9, Gm11, Fm9, Bb13sus–Bb13, then Abmaj9, Gm11, Cm9, Fm9–Bb7b9.
- **Tracks:** Drums, Bass, EP Chords and Fill.
- **Sketches:**
  - A (pocket lock) kept and revised.
  - B (Dilla drag with offbeat stabs) rejected.
  - C (busy melodic bass) rejected: bass on kick 0.25.
- **The interlock:**
  - Kick and bass share beat 1, the "a" of 2 and the "&" of 3: 61% of bass notes are on a kick, and 96% of kicks have a bass note.
  - The other bass notes are chromatic or step approaches that answer the snare (bass stepwise share 0.475).
- **Room for a vocal:**
  - Rootless 4-voice voicings between MIDI 53 and 72, at most 2 attacks a bar.
  - The fill plays only in bars 4 and 8 (beats 3–4, and beats 2–4), above the chords.
- Side-stick backbeat in bars 1–4, snare in bars 5–8, and a tom pickup in bar 8.
- **Revision:**
  - Rolled chords measured as 2 voices, because the analyser groups exact onsets. Each chord now has one onset and is voiced by velocity.
  - Note tails were trimmed to exactly 8 bars.
- `midi_check --genre neo-soul`: 0 REVISE.
  - swing 60.5, ghosts 2.1 a bar, chord voices 4
  - on-grid share 0.27, jitter 6 ms
  - snare 16.5 ms behind the hats, hat structure 0.73

**T07: `t07_vital.json`**
- Values from the calibrated units in `modules/vital/README.md`:

  | Parameter | Value | How |
  |---|---|---|
  | `unison_detune` | 1.143 | 20/17.5 |
  | `volume` | 4612 | interpolated in log(value) between 5473 (0 dB, the default) and 4400 (-7.65 dB) |
  | `reverb_decay_time` | 1.585 | log2(3) |
  | `delay_frequency` | 1.415 | log2(1/0.375) |
  | `osc_1_tune` | 0.25 | semitones |

- `basis` gives the source of each value.
- **Not verified in Vital:** the README says the units were measured on Vital 1.0.7.

**T08: `t08_calls.json`**
- 18 ordered calls. Tool names and argument names come from `daw-faderhand/README.md` recipes and `docs/TOOL-REFERENCE.md`, and a script checked every tool and argument against the reference (0 unknown). The calls, in order:

| Step | Calls |
|---|---|
| Safety first | `tooling_info`, `get_set_identity`, `write_status`, `list_tracks` |
| Plate return | `create_return_track(name="Plate")`, `load_effect_on_return_track(ret="Plate", effect="Reverb")`, then read back with `get_return_track_devices` |
| Keys send | `set_track_send(track="Keys", send="Plate", db=-14)`, then read back with `get_track_sends` |
| Bass sidechain | `load_effect(track="Bass", effect="Compressor")`, `set_sidechain(track="Bass", device="Compressor", source="Kick", on=true, params={...})`, then read back with `inspect_device_sidechain` |
| Lead filter sweep | `load_effect(track="Lead", effect="Auto Filter")`, `list_automatable_parameters(track="Lead")`, `record_arrangement_automation(track="Lead", target={"device": "Auto Filter", "parameter": "Frequency"}, points=[17.1.1 = 300 Hz, 25.1.1 = 8000 Hz], units="display")`, then read back with `param_state` |
| Final checks | `list_return_tracks`, `validate_routing` |

- The skill's two Faderhand rules shaped this list:
  - Arrangement automation can't be drawn through the API, so it is recorded in real time.
  - Every write is read back. No authorisation code was invented.

**T09/T10: `t10_revised.mid`, `t10_notes.md`**
- **Protected material:**
  - Keys pitches and the lead pitch sequence were read from the fixture.
  - Only their timing, length and velocity changed, and no protected onset moves before its own bar line.
  - Proof script result: Keys pitches identical per bar (24 notes in, 24 out), lead sequence identical per bar and overall (64 in, 64 out): `True`.
- **What changed:** drums and bass rewritten. The bass now locks to the kick instead of flamming it a 16th late, and the arrangement builds from bar 5 with fills in bars 4 and 8.
- `midi_check --genre rock`: 6 REVISE before, 0 after. Before-and-after numbers are in the notes.

## What I could not do or did not verify
- **No rendering or listening (no DAW or renderer in this run).** The sketch rounds were judged on measurements and reading the notes, so every KEEP is provisional and waits for a listen.
- **Synth settings are assumed, not checked:**
  - the 808 slides assume portamento or legato on the 808 patch;
  - the GM program numbers are only hints.
- **No instrument audit:** no instruments were assigned, since there was no DAW.
- **T07 values:** taken from the skill's calibration table, not checked against a Vital install.
- **T08:** not executed, as instructed.
- **midi_check limitation:** it groups chords by exact onset, so rolled chords measure as fewer voices. I chose simultaneous chord onsets in T05 and T06; T10's keys keep a small roll.
- **Bar boundaries:** some drum, bass and keys notes land a few ms before a bar line (played feel), so a strict per-bar bucketing puts them in the previous bar. T10's protected notes were kept strictly inside their bars.
- **Working files:** the sketches and the sketch-round record are kept in `work/`. They are not deliverables.
