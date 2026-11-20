# Run log: improved-A

**Skill under test:** `improved-repo/skill/faderhand-music/` (entry: `SKILL.md`).
**Tasks:** `eval-pack/TASKS.md` T01–T10. Output is in this folder. Scripts are in `scripts/`. Working files (fixture dumps and sketch-round MIDI) are in `work/`.
- No Ableton, Faderhand, WavRead or other MCP tools were called. Nothing was rendered or listened to.
- Python with mido was run as `uv run -q --no-project --with mido python …`.

## Skill files read
All paths are under `<evals>/improved-repo/`.

**Entry and routing**
- `skill/faderhand-music/SKILL.md`: the entry point and its routing table.
- `skill/faderhand-music/modules/studio/SKILL.md`: the studio entry.
- `skill/faderhand-music/modules/studio/music-director/SKILL.md`, read in part:
  - Session start, Plan before you build ("just make it" means record the mode and proceed), Leave only the deliverable.
  - Intent lock, Choosing between ideas / Divergent search, Similarity control.
  - MIDI deliverables.
- `skill/faderhand-music/modules/studio/shared/SKETCH_ROUND_PROTOCOL.md`, §1–4. With no renderer, the protocol calls for a reduced round labelled **unrendered**.
- `skill/faderhand-music/modules/studio/profiles/local/`: empty, so no user profile was available.

**Knowledge library**
All under `skill/faderhand-music/modules/knowledge/`:
- `GENERATION_RULES.md`, `README.md`, `TARGETS.md`
- `DRUMS_AND_GROOVE.md`, `LOW_END_808_AND_BASS.md`
- `MELODY_LINES_AND_DEVELOPMENT.md`, `ARRANGEMENT_AND_REVISION.md`
- `local/ZYNTHION_FINDINGS.md`: local trap, 808, melody and arp numbers.

**Vital, Faderhand and docs**
- `skill/faderhand-music/modules/vital/README.md`: the calibrated raw-value table.
- `skill/faderhand-music/modules/daw-faderhand/README.md`: safety rules and recipes.
- `docs/TOOL-REFERENCE.md`: every tool and argument. `docs/TOOLS.md`: grep excerpts on units, returns and automation.
- A grep of `skill/faderhand-music/modules/studio/shared/SYNTH_WORKSHOP/*.md` for Vital raw values found nothing. A grep of the whole repo for the volume calibration found only the Vital README.

**Tools**
- `skill/faderhand-music/tools/midi_check.py`, run on every MIDI output.
- `skill/faderhand-music/tools/kb_search.py`, run for funk, trap, boom-bap and neo-soul queries. Its hits were sections I had already read in full.
- `skill/faderhand-music/tools/corpus/analyze.py`, read in part, to understand what `midi_check` measures (rolls, swing, ghosts, counterpoint, arrangement blocks).

## Per task

### T01: MIDI comprehension
- **Produced:** `t01_answers.json`.
  - 92 BPM, 4/4, D minor, 16 bars.
  - Roles: Drums → drums, Bass → bass, Keys → chords, Lead → melody.
  - Swing 57.9.
  - Bass onsets 64, of which 48 are on a kick.
  - The new section starts at bar 9.
  - Chord cycle: Dm7, Bbmaj7, C7, A7.
- **How it was checked:** `scripts/t01_analyze.py` parses the file.
  - **Swing:** every off-16th hat sits 139 of 240 ticks into its 8th, so 139/240 = 57.9%.
  - **Bass on kick:** kicks fall on steps 0/6/10 and bass on steps 0/6/10/14, so 48 of 64, within a 1/32-note tolerance.
  - **Section change:** the per-bar track and density signature first changes at bar 9, where the Lead enters and swung 16th hats appear.
  - **Chords:** identified from pitch classes.
  - **Key:** D minor follows from Dm7, A7 as V7 and the lead's pitch set. I also confirmed the fixture with `midi_check`.

### T02: Accurate editing
- **Produced:** `t02_edited.mid`, written by `scripts/t02_edit.py`, which edits the copied file in place.
  - The Bass moves down an octave only for notes starting in bars 5–8: 16 notes, including the bar-8 pickup.
  - 16 ghost snares (pitch 38) go on steps 5, 7, 13 and 15 of bars 1–4, at velocities 26–45, varied per bar.
- **How it was checked:** `scripts/t02_verify.py` diffs the edit against the original. Result: **ALL OK**.
  - Meta events are identical.
  - Keys and Lead are unchanged.
  - The only Bass changes are exactly −12, and only in bars 5–8.
  - The only Drums changes are the 16 added ghosts, all valid.
  - `midi_check` reports 0 to revise.

### T03: Trap loop
- **Produced:** `t03_trap.mid` (8 bars, 140 BPM, C# minor) and `t03_notes.md`.
- **How it was made:** I ran a three-direction sketch round, unrendered and measured with `midi_check`, with sketches in `work/sketches/t03_*.mid`. The build combines A's lead with C's octave-jump 808.
- **How it was checked:** `midi_check --genre trap` reports 0 to revise.
  - Half-time backbeat 1.0.
  - 0.5 rolls per bar, all rising.
  - 808 on a kick 0.64; kicks with an 808 1.0.
  - 1.6 slides per bar; octave jumps 0.32.
  - Lead range 12, lead steps 0.59.
- I read back bar 8. Details are in `t03_notes.md`.

### T04: Human-timing funk drums
- **Produced:** `t04_funk_drums.mid` (4 bars, 100 BPM, Drums on channel 10).
  - Kick, snare with ghosts, 16th hi-hat in three velocity tiers with variation, an open hat in bar 2, and a snare-tom fill in bar 4.
- **Sketch round** (unrendered, measured; `work/sketches/t04_*.mid`):
  - A: 16th one-hand hats.
  - B: 8th hats with denser ghosts.
  - C: linear funk.
  - **I chose A.** It came closest to the measured funk medians: ghosts 3.5 a bar against a 3.7 median, and its 16th hats make the swing measurable. C sat more on the grid and had few ghosts.
- **How it was checked:** `midi_check --genre funk` reports 0 to revise.
  - Swing 56.7.
  - Share of notes on the grid 0.16; jitter 9 ms.
  - Hat velocity structure 0.58; hat SD 15.9; snare SD 32.8.
  - Snare 12 ms behind the hats.
  - Every bar is different.
- **Revisions after the first build:**
  - The last fill notes spilled into a 5th bar, so I capped the loop at 4 bars.
  - I clamped hat velocities, because one hat came out at 101.
  - I lowered the swing setting slightly, because the placement already adds about 7 ms of lateness to the off-16ths.

### T05: Complete arrangement
- **Produced:** `t05_song.mid` and `t05_notes.md`.
  - 64 bars at 88 BPM in F minor.
  - Markers: Intro 1, Verse 1 9, Hook 25, Verse 2 33, Bridge 41, Hook 49, Outro 57.
- **How it was made:** I wrote the section map first, then ran a sketch round on the hook (A, B and C in `work/sketches/t05_hook_*.mid`). A was built.
- **How it was checked:**
  - `midi_check --genre boom-bap` and `--genre lofi` both report 0 to revise. The arrangement changes at 6 of 7 eight-bar boundaries, and density CV is 0.46.
  - `scripts/section_summary.py` reads back note counts per track every 4 bars.
  - I checked that hook 1 and hook 2 have identical lead pitches.
- **Revisions after measuring:**
  - **Parallel fifths:** they came out at 4.7 per 100 moves. I revoiced C7b9, which brought them to 0.
  - **Bar 48:** it had stray kicks, so I made it a true stop-time bar.
  - **Hook bar 7:** a leap was not recovered, so I added a step back.

### T06: Neo-soul interaction
- **Produced:** `t06_neosoul.mid` (8 bars, 84 BPM). Tracks: Drums, Bass Guitar, EP Chords, Melodic Fill.
- **Sketch round** (unrendered; `work/sketches/t06_*.mid`):
  - A: laid-back pocket. **Chosen.**
  - B: pedal bass. Two REVISE items: bass on the kick 1.0 and steps 0.09.
  - C: busy stabs with a walking bass. Bass on the kick 0.27, and three syncopated parts left no vocal space.
- **What was revised:** I revoiced the EP top line so it moves against the bass roots. Contrary motion rose from 0.21 to 0.32.
- **How it was checked:** `midi_check --genre neo-soul` reports 0 to revise.
  - Bass on the kick 0.61; kicks with bass 1.0. The bass walks with chromatic approaches (steps 0.38).
  - Chord voices 4.5, all EP notes in MIDI 53–70.
  - At most 3 EP attacks per bar. The fill plays only at the ends of bars 4 and 8.
  - Swing 62.3; snare 20 ms behind the hats; ghosts 2.6 a bar; parallel fifths 0.

### T07: Vital raw values
- **Produced:** `t07_vital.json`:
  - `unison_detune` 1.143
  - `volume` 4612
  - `reverb_decay_time` 1.585
  - `delay_frequency` 1.415
  - `osc_1_tune` 0.25
  - plus a `basis` line.
- **Source:** all values come from the calibrated table in `modules/vital/README.md`, computed in `scripts/t07_t08.py`:
  - 20/17.5 for the detune.
  - Log interpolation between 5473 (0 dB) and 4400 (−7.65 dB) for −6 dB.
  - log2(3) for the reverb decay.
  - log2(1/0.375) for the delay.
  - Semitones for the oscillator tune.
- **Assumption:** "the default volume" is the README's 0 dB point, 5473. The README doesn't say outright that this is Vital's default.

### T08: Faderhand call plan
- **Produced:** `t08_calls.json`, 16 ordered calls. Tool names and argument names come from the skill's Faderhand README recipes and `docs/TOOL-REFERENCE.md`. None were called.
  1. **Safety and identity:** `tooling_info`, `get_set_identity`, `write_status`, `list_tracks`.
  2. **Plate return:** `create_return_track(name="Plate")`, then `load_effect_on_return_track(ret="Plate", effect="Reverb")`, then the `get_return_track_devices` read-back.
  3. **Keys send:** `set_track_send(track="Keys", send="Plate", db=-14)`, then the `get_track_sends` read-back.
  4. **Sidechain:** `load_effect(Bass, Compressor)`, then `set_sidechain(track="Bass", device="Compressor", source="Kick", on=true, params={…})`, then `inspect_device_sidechain`.
  5. **Filter automation:**
     - `load_effect(Lead, "Auto Filter")`, then `list_automatable_parameters(Lead)`.
     - `record_arrangement_automation` with target `{"device":"Auto Filter","parameter":"Frequency"}`, points 17.1.1 = "300 Hz" and 25.1.1 = "8000 Hz", units "display".
     - Then a `param_state` read-back.
- **Caveat:** Arrangement automation records in real time, per the docs.

### T09 and T10: Preservation under revision
- **Produced:** `t10_revised.mid` and `t10_notes.md`.
- **How it was checked:**
  - **Protected material:** `scripts/t10_verify.py` confirms the Keys pitch set is identical in all 8 bars (no note crosses a barline). The Lead pitch sequence is identical, 64/64 in order, and the same per bar. Lead overlaps went from 16 to 0.
  - **`midi_check --genre hiphop-live`:** 7 REVISE items before, 0 after. Swing 56.7, ghosts 1.4 a bar, share of notes on the grid 0.23, jitter 6.3 ms, bar uniqueness 0.5 → 1.0, bass on the kick 0.0 → 0.8, distinct velocities 1 → 83.
  - **Deliverable rules:** `scripts/validate_all.py` checks every output MIDI for 480 PPQ, a tempo and time-signature event, named tracks, drums only on channel 10 and pitched parts off it. All pass.

## What I could not do or did not do
- **No renders or listening.** No DAW or renderer was used, by the runner rules. Every sketch round was the protocol's reduced, **unrendered** round: judged on measurements and a bar-by-bar read, never on audio. Musical quality (sound, balance, whether a groove actually feels good) is unverified. The skill says only listening decides that.
- **No user profile** existed (`modules/studio/profiles/local/` is empty). I couldn't check installed instruments (plugin audit), and the runner said to ask nothing. I added GM program numbers as stand-ins only.
- **`modules/evaluation/score.py`** is listed in the entry SKILL.md, but it isn't in the skill folder, so I didn't run it.
- **Local trap numbers:** the trap and 808 targets partly come from `local/ZYNTHION_FINDINGS.md`, which is marked local-only and pending licence clearance. I used them for this run's own MIDI only. No third-party MIDI was copied into any output.
- **T07 volume:** the value assumes the default is the README's 0 dB point (5473). Vital's real default wasn't verified, because doing so would mean opening Vital.
