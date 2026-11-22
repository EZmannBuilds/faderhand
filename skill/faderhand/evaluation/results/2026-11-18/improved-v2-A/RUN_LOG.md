# Run log: improved-v2-A (Faderhand skill, `skill/faderhand/`)

**Setup:**
- The runner rules are in `eval-pack/TASKS.md`.
- No DAW was used, and no Ableton, Faderhand, WavRead or other MCP tools were called.
- All MIDI was written with Python and mido (`uv run -q --no-project --with mido python …`).
- Every script is in `scripts/`. The sketch-round files are in `scripts/sketches/`.
- The intent was locked as "just make it, no questions", so the skill's plan-before-build gate was recorded
  as the user's speed mode and nothing was asked.

## Skill files read
Paths are relative to `improved-v2-repo/`.

**Entry and routing**
- `skill/faderhand/SKILL.md`
- `skill/faderhand/modules/studio/SKILL.md`
- `skill/faderhand/modules/studio/music-director/SKILL.md`, these sections:
  - session start;
  - plan before you build;
  - intent lock;
  - divergent search and candidate selection;
  - similarity control;
  - MIDI deliverables;
  - deliverable modes.
- `skill/faderhand/modules/studio/shared/SKETCH_ROUND_PROTOCOL.md` (§1–6)
- `skill/faderhand/modules/studio/profiles/local/`: listed only. It holds just a README, so there is no user
  profile.

**Knowledge (MIDI writing)**
- `skill/faderhand/modules/knowledge/GENERATION_RULES.md`
- `skill/faderhand/modules/knowledge/TARGETS.md`
- `skill/faderhand/modules/knowledge/DRUMS_AND_GROOVE.md`
- `skill/faderhand/modules/knowledge/LOW_END_808_AND_BASS.md`
- `skill/faderhand/modules/knowledge/MELODY_LINES_AND_DEVELOPMENT.md`
- `skill/faderhand/modules/knowledge/ARRANGEMENT_AND_REVISION.md`
- a local findings file from a source pending licence clearance (`local/`, never shipped; removed from the skill on 2026-11-21): local-only trap and 808 numbers. I used
  them to inform choices and did not quote them in any notes.

**Tools (run and read)**
- `skill/faderhand/tools/midi_check.py`: run on every MIDI output.
- `skill/faderhand/tools/kb_search.py`: run for trap, funk, boom-bap, neo-soul and revision queries.
- `skill/faderhand/tools/corpus/analyze.py`: read only the measurement functions (drums, line, chord,
  interplay, counterpoint, arrangement), to know exactly what the checker measures. `p5_find.py` uses
  `midi_lib` and `analyze` the same way.

**DAW and Vital**
- `skill/faderhand/modules/daw-faderhand/README.md`
- `docs/TOOL-REFERENCE.md` and `docs/TOOLS.md`, which the Faderhand module points to.
- `skill/faderhand/modules/vital/README.md`
- A grep of `modules/studio/shared/SYNTH_WORKSHOP/*.md` for volume and default values found nothing extra.

**Not read:**
- `skill/faderhand/modules/evaluation/`: the scorer and blind pairs. I left it out on purpose so the run
  wasn't tuned to the scorer.
- The remaining specialist SKILL files, which these tasks didn't need.

## Tasks

### T01: MIDI comprehension → `t01_answers.json`
| Answer | Value | How it was found |
|---|---|---|
| Tempo | 92 BPM | set_tempo 652174 |
| Meter | 4/4 | time signature event |
| Key | D minor | see chords |
| Bars | 16 | read from the file |
| Roles | Drums = drums, Bass = bass, Keys = chords, Lead = melody | track contents |
| Swing | 57.9 | the off-16th hats sit 19 ticks late in bars 9–16, so 139/240 of the 8th |
| Bass onsets | 64 total, 48 on a kick (within 1/32) | kicks on steps 0, 6, 10; bass on 0, 6, 10, 14 |
| Arrangement change | bar 9 | the lead enters and the hats go to swung 16ths |
| Chords | Dm7, Bbmaj7, C7, A7 | read from the Keys voicings bar by bar; A7 is V, which gives D minor |

**Check:** `scripts/t01_comprehension.py` computes every numeric value from the file. The analyzer's swing
formula agrees.

### T02: editing → `t02_edited.mid`
**Edits:**
- Bass notes that start in bars 5–8 move down 12 semitones, and their note-offs move with them.
- 16 ghost snares (pitch 38, velocity 26–45) on steps 5, 7, 13 and 15 of bars 1–4. The "a" before each
  backbeat or downbeat is a little louder.
- All other events are copied as they were: same order, same ticks.

**Check:** `scripts/t02_verify.py` does a note-by-note diff against the fixture:
- meta events identical;
- Keys and Lead identical;
- Drums: the original 272 notes intact plus exactly the 16 ghosts;
- Bass identical apart from the 16 moved notes.

### T03: trap → `t03_trap.mid`, `t03_notes.md`
- **Sketch round:** three versions that differ by mechanism, measured with `--genre trap`.
- **Kept: A.** It has a bounce kick, an 808 locked to the kick with octave jumps and four glides, rolls on
  alternate bars that rise into their target, and a detached bell call-and-response hook. Its own 808
  drop sits in bar 8.
- **Final check:** `midi_check --genre trap` gives 0 REVISE. Read back bars 1, 4 and 8.

### T04: funk drums → `t04_funk_drums.mid`
- **Two sketches:**
  - A: 16th one-hand hats.
  - B: 8th hats with a linear kick and snare.

  Both pass. **Kept A**, because the 16ths carry the funk swing.
- **Played-feel model** (`scripts/drummer.py`):
  - placement per position: hats early, the snare 13 ms behind them, off-16ths late, which gives a swing
    of 56.9%;
  - jitter about 4 ms;
  - hats in velocity tiers with variation and a floor of 35;
  - ghosts that change every bar;
  - an open hat in bar 2, a tom fill in bar 4, and a crash on the one for the loop.
- **Check:** `midi_check --genre funk` gives 0 REVISE (ghosts 3.5 a bar, hat structure 0.67).

### T05: boom-bap song → `t05_song.mid`, `t05_notes.md`
- **Form:** 60 bars with 7 markers (Intro, Verse 1, Hook, Verse 2, Bridge, Hook 2, Outro). The section
  map came first.
- **Sketch round on the hook (3 mechanisms):**
  - A is kept for verse 1 and the hooks.
  - B's walking bass and offbeat stabs are recombined into verse 2.
  - C's texture is recombined into the bridge.
- **Checks:** `midi_check` gives 0 REVISE for both boom-bap and lofi, with 6 of 7 block boundaries
  changing.
- **Revision:** parallel fifths went from 4.7 to 0 per 100 moves. Two lead notes were rewritten and a
  voicing rule was added.
- **Read back:** markers and the boundary bars.

### T06: neo-soul → `t06_neosoul.mid`
- **Two sketches:**
  - A: kick and bass interlock with chromatic approach notes, held chords.
  - B: everything on the kick, offbeat stabs.

  B got a REVISE: 100% of the bass sat on the kick, which isn't interlock. **Kept A.**
- **What's in it:**
  - The bass takes the kick's timing where they coincide. 0.69 of bass notes land on a kick and every kick
    has a bass note.
  - Electric piano in rootless 4-voice voicings, MIDI 53–71 (under 72), 1–2 attacks a bar.
  - A short `Fill` track at the end of each 4-bar phrase, in the gaps where a vocal would breathe.
- **Check:** `midi_check --genre neo-soul` gives 0 REVISE (swing 57.9, no parallel fifths). I read back the
  EP voicings and revoiced the B7 as B7(b9b13) to avoid a D/D# clash.

### T07: Vital → `t07_vital.json`
All values come from the calibrated table in `modules/vital/README.md`:

| Parameter | Value | Calculation |
|---|---|---|
| unison_detune | 1.143 | 20/17.5 |
| volume | 4612 | -6 dB from the 5473 = 0 dB default, interpolated in log(value) |
| reverb_decay_time | 1.585 | log2 3 |
| delay_frequency | 1.415 | log2(1/0.375) |
| osc_1_tune | 0.25 | semitones |

The `basis` key gives the source in one line. **Caveat:** the README says 5473 is about 0 dB. I treated
that as Vital's default volume. The README calibrates against Vital 1.0.7.

### T08: Faderhand plan → `t08_calls.json`
**The 14 calls, in order:**
1. `tooling_info`, `get_set_identity` and `list_tracks`. The skill's safety rule is handshake first, then
   confirm which saved Set is open.
2. `create_return_track(name="Plate")`
3. `load_effect_on_return_track(ret="Plate", effect="Reverb")`
4. `set_track_send(track="Keys", send="Plate", db=-14)`, then `get_track_sends` to read it back.
5. `load_effect(track="Bass", effect="Compressor")`
6. `set_sidechain(track="Bass", device="Compressor", source="Kick", on=True, params={…})`, then
   `inspect_device_sidechain`.
7. `load_effect(track="Lead", effect="Auto Filter")`
8. `list_automatable_parameters(track="Lead")`
9. `record_arrangement_automation(track="Lead", target={"device": "Auto Filter", "parameter": "Frequency"},
   points=[17.1.1 = 300 Hz, 25.1.1 = 8000 Hz], units="display")`, then `param_state`.

**Check:** a script confirmed that every tool name and argument name appears in `docs/TOOL-REFERENCE.md`.
Arrangement automation can't be drawn through the API, so the module's documented route is
`record_arrangement_automation`, which records in real time.

### T09 and T10: preservation and revision → `t10_revised.mid`, `t10_notes.md`
**Diagnosis:**
- one velocity across the whole file;
- everything on the grid;
- the drums and lead identical in every bar;
- the bass entirely off the kick;
- the lead's note lengths overlapping.

**Protected:** the Keys pitch set of every bar and the Lead's 64-note pitch sequence.

**Changes:**
- **Keys and lead:** velocity, timing kept inside each bar, durations, and a few small rhythm placements in
  bars 4 and 6–8.
- **Drums and bass:** rewritten. The drums form a played pocket that builds; the bass is kick-locked with
  approach notes.

**Checks:**
- `scripts/t10_verify.py` proves the Keys pitch sets per bar and the Lead pitch sequence are identical.
- `midi_check`: the original gets 1 REVISE and 1 WARN; the revision gets 0 REVISE with both `hiphop-live`
  and `generic`.
- No parallel fifths.

### Runner-rule check (all MIDI files)
`scripts/final_check.py` confirms every MIDI file has:
- 480 PPQ, a tempo event and a time signature;
- named part tracks;
- drums on channel 10 only, and pitched parts never on channel 10;
- a whole number of bars (T03 initially ended 10 ticks short; it was fixed by padding the conductor track);
- markers in T05.

## What I could not do
- **Render or listen:**
  - There was no DAW or renderer, and MCP tools were off-limits.
  - So I couldn't run the skill's render/listen step, the WavRead analysis or the Faderhand read-back.
  - The sketch-round decisions are therefore marked **unrendered and provisional**, decided on
    measurements plus reasoning (`measured` and `inferred` in the skill's terms), not on listening.
- **Plugin audit and user profile:**
  - There was no plugin or instrument audit (`plugin-auditor`): no instruments are known.
  - The program numbers in the files are General MIDI placeholders.
  - There was no user profile, so I used the task's file names, not the studio naming system.
- **T08:** the calls were not executed, as the task asked. The Faderhand read-back values (what Live
  reports after each write) are therefore unknown.
- **T07:** the volume default is an assumption, explained above.
