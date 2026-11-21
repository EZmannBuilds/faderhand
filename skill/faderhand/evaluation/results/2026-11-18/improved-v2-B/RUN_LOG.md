# Run log: improved-v2-B

**Skill:** `improved-v2-repo/skill/faderhand/` (Faderhand 0.7.0-dev). **Tasks:** `eval-pack/TASKS.md`, T01–T10.

**Date:** 2026-11-18. **Tools:** Python with mido, through `uv run`. No Ableton, Faderhand, WavRead or other MCP tools were called.

## Skill files read

All paths are relative to `improved-v2-repo/`.

### Entry and routing
- `skill/faderhand/SKILL.md`
- `skill/faderhand/modules/studio/SKILL.md`
- `skill/faderhand/modules/studio/music-director/SKILL.md`:
  - **Mode:** recorded as "just make it, no questions". The intent-lock wait was skipped, as the Director allows for that mode.
  - **Classification:** composition + midi_artifact, plus diagnosis/revision for T10.
- `skill/faderhand/modules/studio/shared/SKETCH_ROUND_PROTOCOL.md`
- `skill/faderhand/modules/studio/profiles/local/`: listed only. It holds just a README, so there is no user profile.

### MIDI knowledge
- `skill/faderhand/modules/knowledge/GENERATION_RULES.md`
- `skill/faderhand/modules/knowledge/TARGETS.md`
- `skill/faderhand/modules/knowledge/DRUMS_AND_GROOVE.md`
- `skill/faderhand/modules/knowledge/LOW_END_808_AND_BASS.md`
- `skill/faderhand/modules/knowledge/MELODY_LINES_AND_DEVELOPMENT.md`
- `skill/faderhand/modules/knowledge/ARRANGEMENT_AND_REVISION.md`
- a local findings file from a source pending licence clearance (`local/`, never shipped; removed from the skill on 2026-11-21): local-only numbers. They informed the trap design but are not quoted in any output.

### Tools
- `skill/faderhand/tools/midi_check.py`: read, and run on every MIDI output and sketch.
- `skill/faderhand/tools/kb_search.py`: read the header, and ran it once for "trap 808 hats roll lead".
- `skill/faderhand/tools/corpus/analyze.py`: only the roll-detection and `counterpoint()` parts, to locate the parallel fifths it reported. `midi_lib.py` was imported, not read.

### Vital (T07)
- `skill/faderhand/modules/vital/README.md`: the calibrated raw-unit table.
- `skill/faderhand/modules/studio/shared/SYNTH_WORKSHOP/README.md` (first part).
- A grep of the workshop `.md` files, including `FIELD_TEST.md`, for units.

### DAW (T08)
- `skill/faderhand/modules/daw-faderhand/README.md`
- `docs/TOOL-REFERENCE.md`
- A grep of `docs/TOOLS.md`

### Not read
- `skill/faderhand/modules/evaluation/` (score.py). I didn't use the scorer, so the run isn't tuned to it.

## Shared method (the skill's loop)

1. **Name the target:** genre, tempo, and played or programmed feel.
2. **Run a sketch round** that differs by mechanism (T03, T04, T05, T06). It is unrendered, and every decision is `director_provisional` on a measured + inferred basis.
3. **Build** the chosen direction.
4. **Run `midi_check.py --genre …`.** Fix every REVISE at its cause, then read back chosen bars note by note.
5. **Run a format validator** (`scripts/validate.py`) on every file. It checks:
   - 480 PPQ;
   - a tempo event and a time signature;
   - a named track per part;
   - drums on channel 10 and nothing else on 10.

**Where things are:**
- Scripts: `scripts/`
- Sketches and the round records: `sketches/` (`sketch_rounds.json`, in the protocol's §8 shape)
- Saved checker output: `checks/`

## Per task

### T01: comprehension
**Produced:** `t01_answers.json` (`scripts/t01.py`).

| Key | Answer |
|---|---|
| tempo | 92 BPM |
| meter | 4/4 |
| key | D minor |
| bars | 16 |
| roles | Drums = drums, Bass = bass, Keys = chords, Lead = melody |
| swing | 57.9% (the 16th hats sit 139/240 of the 8th) |
| bass onsets | 64 |
| bass onsets on a kick | 48 (within 1/32) |
| arrangement change | bar 9 (lead enters, 16th hats added) |
| chords | Dm7, Bbmaj7, C7, A7 |

**Checked:**
- Every number is computed from the file, not read by eye.
- `midi_check.py --json` agrees independently: tempo 92, swing 57.9, bass on kick 0.75 × 64 = 48.
- The key is confirmed by the A7 (C#) resolving to Dm7.

### T02: preserving edit
**Produced:** `t02_edited.mid` (`scripts/t02.py`).

**How:**
- The edits are made on absolute-time event lists, so every other message keeps its time, order and value.
- **Bass, bars 5–8:** each note is moved −12. The note-ons and their paired note-offs are both moved, including the off that lands exactly on bar 9.
- **Ghost snares:** 16 notes (pitch 38, velocity 26–45, varied by bar, the "a" a little louder) on steps 5, 7, 13 and 15 of bars 1–4, on the straight grid. Bars 1–4 have no swung 16ths to follow.

**Checked:** a diff against the original asserts:
- metas, track names and end-of-track are identical;
- Keys and Lead are identical;
- Bass differs only by −12 on exactly the 16 notes in bars 5–8;
- Drums keeps every original note and adds only those 16.

### T03: trap
**Produced:** `t03_trap.mid` and `t03_notes.md` (`scripts/t03.py`). 140 BPM, G minor.

**Sketch round:**
- **A, locked:** RECOMBINE. Strong hook, but 0 808 slides.
- **B, bounce:** RECOMBINE. Too many slides, and the lead is a 48-note arp.
- **C, space:** REJECT. No rolls, too few 808 notes.
- The final takes A's hook and kick lock and adds B's slide pickups and triplet roll type.

**Checked:**
- `--genre trap`: 0 REVISE. Half-time 1.0; 0.5 rolls per bar, all rising; 808 on kicks 0.90; kicks with 808 1.0; 3.6 notes per bar; 1.0 slide per bar; lead range 13; 4 notes per phrase.
- Read back bars 1, 4 and 8.

### T04: human funk drums
**Produced:** `t04_funk_drums.mid` (`scripts/t04.py`, `scripts/played.py`).

**How it's played:**
- Placement is set per instrument and position: hats and kick early, backbeat 13.6 ms behind the hats.
- 5 ms jitter, clipped, so no note sits more than 22.5 ms from its position.
- 16th swing 56.5%.
- Hats in three velocity tiers with variation inside each.
- Ghosts change from bar to bar (3.75 per bar).
- Open hats on the "&". The hats thin out before a snare-and-tom fill in bar 4.

**Sketch round:** A (16th hats, 56% swing) KEEP. B (8th hats) and C (67% shuffle, 51 ms offsets) REJECT.

**Checked:** `--genre funk`: 0 REVISE, 0 WARN. Every LIVE range passes; hat velocity structure is 0.76.

### T05: arrangement
**Produced:** `t05_song.mid` and `t05_notes.md` (`scripts/t05.py`).
- 60 bars at 88 BPM.
- Markers: Intro, Verse 1, Hook, Verse 2, Bridge, Hook 2, Outro.

**Sketch round:** run on the hook. A KEEP; B ("chop") REJECT; C (straight half-time) REJECT.

**Revised after measuring:** `scripts/p5find.py` found parallel fifths between the bass and the top voice, caused by bass walk-ups colliding with kick notes and by one octave pop. I fixed them in the bass plan: 6.45 per 100 moves went to 0.0.

**Checked:**
- `--genre boom-bap`: 0 REVISE, 0 WARN. 6 of the 8-bar boundaries change.
- `--genre lofi`: 0 REVISE.
- Read back bars 8, 25 and 41.

### T06: neo-soul interaction
**Produced:** `t06_neosoul.mid` (`scripts/t06.py`). 84 BPM, Eb major (ii–V–I–IV with a iii–VI turn).

**How the parts interact:**
- The bass guitar locks about half its notes to the kick (0.58) and approaches every change chromatically or by step (stepwise share 0.38). Every kick but one has a bass note (0.96).
- The EP plays rootless 4-voice voicings, all under MIDI 71, rolled, with at most 3 attacks a bar.
- The melodic fill appears only in bars 4 and 8, where a vocal would breathe.

**Sketch round:** A ("pocket") KEEP. B (fully locked roots) REJECT. C (busy funk) REJECT.

**Checked:**
- `--genre neo-soul`: 0 REVISE.
- **One WARN, deliberate:** "drum note 49 ms off the grid". Every flagged note is a swung off-16th. At 84 BPM, 61% swing alone puts them 39 ms late; the swing itself is consistent. I listed every note over 30 ms with `scripts/offsets.py` to confirm none is a stray.
- Read back bars 1 and 4.

### T07: Vital raw values
**Produced:** `t07_vital.json` (`scripts/t07_t08.py`).

| Parameter | Raw value | Derivation |
|---|---|---|
| `unison_detune` | 1.1429 | 20 cents / 17.5 |
| `volume` | 4612 | log interpolation between 5473 = 0 dB (default) and 4400 = −7.65 dB |
| `reverb_decay_time` | 1.585 | log2(3) |
| `delay_frequency` | 1.415 | log2(1/0.375) |
| `osc_1_tune` | 0.25 | +25 cents in semitones |

**Basis:** the skill's calibrated table in `modules/vital/README.md`, measured on Vital 1.0.7. The 4612 figure is computed, and it matches the README's own stated value.

### T08: Faderhand call plan
**Produced:** `t08_calls.json`, 16 calls, in this order:

1. `tooling_info`
2. `get_set_identity` (say which Set is open)
3. `write_status`
4. `list_tracks(devices=True)`
5. `create_return_track(name="Plate")`
6. `load_effect_on_return_track(ret="Plate", effect="Reverb")`
7. `list_return_tracks` (read back)
8. `set_track_send(track="Keys", send="Plate", db=-14)`
9. `get_track_sends(track="Keys")`
10. `load_effect(track="Bass", effect="Compressor")`
11. `set_sidechain(track="Bass", device="Compressor", source="Kick", params={...})`
12. `inspect_device_sidechain`
13. `load_effect(track="Lead", effect="Auto Filter")`
14. `list_automatable_parameters(track="Lead")`
15. `record_arrangement_automation(track="Lead", target={"device": "Auto Filter", "parameter": "Frequency"}, points=[17.1.1 → 300 Hz, 25.1.1 → 8000 Hz], units="display")`
16. `param_state`

**Checked:** every tool name and argument name was checked against `docs/TOOL-REFERENCE.md`.

**Notes on the plan:**
- The read-back calls follow the skill's rule to read every write back.
- Arrangement automation goes through `record_arrangement_automation`, because the LOM can't draw it. It records in real time, across bars 17–25.
- **Not executed**, as the task says.

### T09/T10: revision with preserved material
**Produced:** `t10_revised.mid` and `t10_notes.md` (`scripts/t10.py`).

**How the protected material is kept:**
- The chord pitch sets of every bar and the lead's 64-pitch sequence are read from the fixture itself.
- After writing, the script asserts on the read-back file that both are identical, and that no lead note crosses a bar line.

**What changed:**
- **Drums:** a played arc with fills, ghosts and a crash at bar 5.
- **Bass:** re-locked to the kicks. It had been a 16th late, with 0% of notes on a kick; now 71% are on a kick and 100% of kicks have a bass note. Approach notes lead into every change.
- **Keys:** the same pitches, re-voiced in time (rolled, laid back), developing from held chords to comping.
- **Lead:** the same pitches, developed through placement (each move at most a 16th), length and a dynamic arc.

**Checked:**
- `--genre rock` and `generic`: 0 REVISE.
- Before/after table in `t10_notes.md`: distinct velocities 1 → 79; grid share 1.0 → 0.12; bar uniqueness 0.5 → 1.0.
- One parallel fifth that my new bass introduced was found and fixed.
- Read back bars 1, 5 and 8.

## What I could not do

- **No rendering or listening.**
  - No DAW, synth or WavRead was available, and the run rules forbid those tools.
  - Every sketch round is therefore labelled unrendered, and its KEEP/REJECT decisions are provisional (measured + inferred).
  - Nothing in these outputs claims how anything sounds.
- **No instrument audit** (plugin-auditor). Parts use General MIDI note numbers, and nothing was checked against a real instrument.
- **No user profile** exists, so none was loaded.
- **The intent lock was not stated back and confirmed.** The brief locked the intent ("just make it"), which the Director allows; the mode is recorded instead.
- **T06's off-grid WARN** is left as a deliberate swing choice (explained above).
- **T08 was not executed.** That includes the `get_set_identity` safety confirmation, which would have to happen in a live session.
