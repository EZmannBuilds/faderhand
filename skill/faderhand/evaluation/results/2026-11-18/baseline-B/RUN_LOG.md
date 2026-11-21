# RUN_LOG: baseline-B (baseline skills: ai-music-studio + wavread + faderhand-docs)

All outputs are in this folder and every script is in `scripts/`. Every script was run with
`uv run -q --no-project --with mido python <script>` from inside `scripts/`. No MCP tools were called (no Ableton,
Faderhand or WavRead). Nothing was read outside the skill folder, the eval pack and this folder. In the eval
pack, only `TASKS.md`, `fixtures/comprehension.mid` and `fixtures/flawed.mid` were opened. The `*.truth.json`
files and `make_fixtures.py` were **not** read, because they would give the answers away.

## Skill files read
Entry files:
- `baseline-skill/ai-music-studio/SKILL.md`, which routes to the Music Director
- `baseline-skill/wavread/SKILL.md`. Not used further: no task involved audio analysis or WavRead.
- `baseline-skill/faderhand-docs/README.md`, `TOOLS.md`, `TOOL-REFERENCE.md`

Routed from the Music Director and the specialists, as each task needed them:
- `ai-music-studio/music-director/SKILL.md`: session modes, "plan before you build" (the "just make it"
  exception), the production order, MIDI deliverable checks and DAW execution rules
- `ai-music-studio/midi-builder/SKILL.md`, `shared/MIDI_EXPORT_SCHEMA.md`: GM channel-10 rule, verification
  output, the `unperformed` rule and range reporting
- `ai-music-studio/performance-director/SKILL.md`, `shared/HUMAN_PERFORMANCE_SCHEMA.md`: named timing models
  with magnitudes, no randomness, the imperfection causes and the feasibility report
- `ai-music-studio/composer/SKILL.md`: harmony and melody workflow, motif transformation and the
  melody-variety gate
- `ai-music-studio/shared/RHYTHM_SYSTEMS/MICROTIMING_AND_GROOVE.md`: swing as a tempo function, natural
  magnitude as a ceiling, marker parts and corpus naming
- `ai-music-studio/shared/VIRTUAL_INSTRUMENT_GUIDE/DRUM_KIT.md` (behaviour, physical constraints and
  programming sections): the four-limb rule, ghost layers, hi-hat microtiming (Räsänen 2015), rudiments and flams
- `ai-music-studio/shared/SYNTH_WORKSHOP/FIELD_TEST.md`, `AUTOMATION_GUIDE.md`, and the Vital lines of
  `shared/FREE_INSTRUMENTS.md` and `shared/SYNTH_WORKSHOP/*` (found by search) for T07
- `ai-music-studio/daw-adapters/ABLETON_LIVE.md` (integration stack, plus the automation, sidechain and devices
  sections) and `shared/DAW_ADAPTER_CONTRACT.md` (sections 1–5) for T08
- `faderhand-docs/UNITS.md`, plus the Vital, automation and sidechain rows of `faderhand-docs/CAPABILITY-MATRIX.md`
  and `REFERENCE-LOM-TECHNIQUES.md` (found by search)

Not loaded, as unneeded for these briefs: the Creative Lab and sketch round (intent was locked, so the round was
skipped and recorded as skipped), the Plugin Auditor (no DAW and no instruments to audit), vocal and lyric
skills, the Mix Engineer and the research files.

## How the skill's rules were applied across tasks
- **Session:** there is no user profile in `profiles/`. The runner gave the output location, so nothing else
  was asked. The mode is "just make it": this is recorded as the mode, and the intent-lock and sketch-round
  gates were skipped as the Director allows. The deliverable mode is instrumental.
- **Plugin audit and render verification:** not possible here, because there is no DAW and no instruments.
  Every track uses a GM stand-in program and is labelled unmeasured. Nothing was rendered or heard, so no
  output claims to sound a certain way; claims are measured from the MIDI or reasoned.
- **Performance:** every timing deviation comes from a named model with a stated magnitude: `swing_ratio`,
  `section_offset`, `chord_asynchrony` (derived from velocity), and a seeded `drift_1f` applied last and
  smallest. All are labelled *set, not measured* wherever the pack has no corpus for the style. No random
  humanising is used. Trap (T03) is declared deliberately mechanical in timing.
- **MIDI Builder checks:** `scripts/midilib.py: verify()` and `scripts/verify_all.py`. These check 480 PPQ, the
  tempo and time-signature meta events, that every note track is named, drums on channel 10, no pitched part on
  channel 10, no zero-length or same-pitch overlapping notes, the length in bars, and the four-limb drum rule (no
  more than 2 hands and 2 feet within 12 ticks). The final sweep reports **no problems on any file**.

## Tasks

### T01: MIDI comprehension → `t01_answers.json`
- **Method:** `scripts/t01.py` measures the file. Tempo comes from the tempo event (652174 µs = 92 BPM) and
  the meter from the time signature. Bars are counted from the last note-off (16). Chords are named from each
  Keys bar's pitch-class set: Dm7, Bbmaj7, C7, A7 (a 4-bar cycle, asserted for all 16 bars). The key is
  D minor, reasoned from the Dm7 tonic, the A7 dominant with its C# leading tone and the lead's D-minor pitches.
- **Swing:** the 16th hats (bars 9–16) land at tick 139 of each 240-tick 8th, so the long note's share is
  57.9%. Bars 1–8 have straight 8ths and no 16ths.
- **Bass and kick:** 64 bass onsets, 48 of them within 1/32 of a kick (kicks on 1 and the "and" of 2 and 3; bass
  on 1 and the "and" of 2, 3 and 4).
- **Arrangement change:** bar 9, where the lead enters and the swung 16th hats start. Roles were assigned from
  channel, register and polyphony.
- **Limit:** the key is a reasoned judgment, not computed by a key-finding algorithm.

### T02: editing → `t02_edited.mid`
- **Method:** `scripts/t02.py` copies the file event by event. In the Bass track, each note-on is paired with
  its note-off, and both are moved -12 only when the onset falls in bars 5–8. That includes the bar-8 note whose
  note-off lands on bar 9's downbeat.
- **Ghosts:** 16 notes (pitch 38) on the "e" and "a" of beats 2 and 4 in bars 1–4. Velocities run 28–43,
  alternating like a hand and lifting slightly toward bar 4.
- **Check:** `scripts/check_t02.py` compares the edit with the original. The conductor, Keys and Lead tracks
  are identical. The Bass is identical except for the 16 transposed notes. The Drums keep all 272 original
  notes, and the only additions are the 16 ghosts at the right positions and velocities. Track lengths and the
  file duration are unchanged.
- **Flagged, not changed (MIDI Builder range rule):** the transposed bars 5–8 reach A0–Eb1 (MIDI 21–27). That
  is below a 4-string bass's low E (28) and needs an extended-range bass or a synth bass. The brief asked for
  exactly this, so it was done and is reported here.

### T03: Atlanta trap → `t03_trap.mid`, `t03_notes.md`
- **What it is:** C minor at 140 BPM, i–i–VI–V | i–i–bII–V. Drums have a half-time clap, a kick that varies
  each bar, 16th hats and four different rolls (16th-triplet, 32nd, 32nd stutter, 1/48 flutter), each with its
  own velocity ramp, plus open hats and a turnaround snare run. The 808 locks to the kick (28 of 28 onsets),
  with octave pops and glides written as legato overlaps. The bell/pluck lead uses a triplet-turn motif that is
  transformed over 8 bars.
- **Checks:** the verifier is clean. Melody-variety gate: pass (9 rhythms in 14 lines, a 21% top share and 7%
  repeated pitches). The first build put a clap, a snare layer and a hat at one instant (3 hands). The snare
  layer was removed, so the clap carries the backbeat.

### T04: funk drums → `t04_funk_drums.mid`
- **What it is:** 4 bars at 100 BPM with kick, a laid-back backbeat with one flammed backbeat, swung ghost
  strokes, one-handed 16th hats with a 2-bar amplitude pattern, open hats closed by the foot (pedal hat),
  a crash on the downbeat and a snare-to-tom fill in bar 4.
- **Plan:** written in the header of `scripts/t04_funk.py`: realism target, models, magnitudes, imperfection
  causes and feasibility.
- **Checks:** clean, with at most 2 hands and 2 feet at any moment. The hat stops during the fill and at the
  crash. Deviation from the straight 16th grid averages 7.5 ms with an 18.8 ms maximum: 12 ms of swing plus
  the backbeat offset, about 3% of the beat, at the natural ceiling.

### T05: complete arrangement → `t05_song.mid`, `t05_notes.md`
- **What it is:** 56 bars at 88 BPM in Db major: Intro 4, Verse 8, Hook 8, Verse 8, Hook 8, Bridge 8,
  Hook 8, Outro 4, each marked with a marker meta event. It has Drums, Bass, Keys (Rhodes) and Lead (vibes),
  with distinct verse, hook and bridge harmony, a hook motif developed across the song, and section-level
  density and dynamics.
- **Checks:** clean (8 markers, 56 bars). Melody-variety gate: pass. Bass onsets on a kick: 159 of 219.
  Section density rises from intro (5 drum notes per bar) to hooks (about 22), dips in the bridge (10.6) and
  thins in the outro.
- **Fixes:** the first build had duplicate snare hits where a fill met a ghost stroke, and 3 hands at once
  where a tambourine met a fill. Both were fixed at the source.

### T06: instrumental interaction → `t06_neosoul.mid`
- **What it is:** 8 bars at 84 BPM in D major: Gmaj9, F#m9, Em9, A13sus, then Gmaj9, F#m7–B7alt, Em9,
  A13sus–A13. Tracks are Drums, Bass Guitar, Electric Piano and Guitar Fill.
- **Interlock (measured):** every kick (27 of 27) has a bass note with it. The bass adds 17 notes in the kick's
  gaps, 44 notes in total.
- **Vocal room (measured):** the Electric Piano's top note is D4 (62), with no notes above D4. It sounds about
  50% of the time and is comped sparsely. The guitar fill plays only in bar 4 (and an echo in bar 8), the
  vocal's breath points.
- **Checks:** clean. A first build had a bass approach note at Eb1 (27), below the bass's range; it now
  approaches from above. Another start time was negative, at the hats' -4 ms push on bar 1; starts are now
  clamped to 0.

### T07: Vital raw values → `t07_vital.json`
- **Values:**
  - `unison_detune` = 4.472136 (sqrt 20)
  - `volume` = 4621.2804 (−12.02 dB, against the default 5473.0404 = −6.02 dB)
  - `reverb_decay_time` = 1.584963 (log2 3 s)
  - `delay_frequency` = 1.415037 (log2 2.667 Hz = 375 ms)
  - `osc_1_tune` = 0.25
- **Check:** `scripts/t07_vital.py` converts each raw value back to display units.
- **Could not verify:** the pack documents only the reverb-decay unit (FIELD_TEST.md: 12 units of log2 seconds,
  which this matches). Its AUTOMATION_GUIDE says not to hand-guess internal units, and no Vital install or
  source was available. The other four scalings come from my knowledge of Vital's parameter table, and the
  `basis` key says so.
- **Least certain:** `unison_detune`. If Vital's display is ± cents per voice rather than the spread between
  the outermost voices, the answer is sqrt(10) = 3.162278. That alternative is in `basis`.

### T08: Faderhand plan → `t08_calls.json`
- **The plan:** 22 ordered calls.
  1. Discover and read: `tooling_info`, `write_status`, `get_set_identity`, `list_tracks`, `list_return_tracks`.
  2. Make the Plate return: `create_return_track(name="Plate")`, `load_effect_on_return_track(ret="Plate",
     effect="Reverb")`, then read back.
  3. Send: `set_track_send(track="Keys", send="Plate", db=-14)`, then read back.
  4. Sidechain: `load_effect(Bass, Compressor)`, `inspect_device_sidechain`, `set_sidechain(track="Bass",
     device="Compressor", source="Kick", on=true, params={...})`, then inspect again.
  5. Lead filter: `load_effect(Lead, Auto Filter)`, `get_device_parameters`, `list_automatable_parameters`, and
     `set_arm(Lead, false)`, because the adapter warns that an armed MIDI track records silence.
  6. Automate: `record_arrangement_automation` on Auto Filter Frequency from 300 Hz at 17.1.1 to 8 kHz at
     25.1.1, with nine points one bar apart, spaced evenly in log-frequency. Arrangement lanes can't be drawn
     through the LOM, so this is the documented route.
  7. Finish: `back_to_arrangement`, `param_state` and `validate_routing`.
- **Check:** `scripts/t08_calls.py` confirms every tool name and argument name is in `TOOL-REFERENCE.md`.
- **Undocumented assumption:** the docs show the automation `target` only for the mixer (`{"mixer": "volume"}`).
  The device target `{"device": "Auto Filter", "parameter": "Frequency"}` is my assumption, so the plan calls
  `list_automatable_parameters` first, and in a live run its returned target object would replace this one.
  Likewise, returns may show a letter prefix: if `create_return_track` reports a letter, use it for `ret` and
  `send`.

### T09 / T10: revision → `t10_revised.mid`, `t10_notes.md`
- **Diagnosis:** every bar is identical in every part; the bass sits a 16th after every kick, never on the
  downbeat; every velocity is 100; the lead has 16 overlapping notes; the chords are block chords held to the
  barline.
- **Revision:** the keys keep the same pitches and one attack per bar, now with an 8-bar dynamic arc, derived
  asynchrony and releases. The lead keeps its pitch sequence, with rhythm nudged inside the bar, overlaps
  removed, articulated lengths and phrased velocity. The bass and drums were rewritten to lock and to build:
  cross-stick, then backbeat, then crash, 16th hats and fills.
- **Checks:** `scripts/t10_revise.py` asserts that the Keys pitches match the original in every bar and that
  the Lead pitch sequence matches both overall and bar by bar (64 notes). The build fails if either changes.
  Lead overlaps went 16 → 0. Distinct bars went 1 → 8 (drums), 4 → 8 (bass) and 1 → 6 (lead). Velocity SD
  went 0 → 5.8–20.5. Grid deviation averages 4 ms (13 ms maximum), all from named models.

## What I could not do
- **Listening:** nothing was rendered or heard, and no render verification or plugin audit was possible
  without a DAW. Claims like "sounds performed" or "sounds like the genre" are reasoned from the notes, not
  listened. GM programs are stand-ins.
- **T07:** four of the five raw values could not be checked against a Vital install or source (see T07).
- **T08:** the device automation target's exact shape isn't documented. The plan reads it with
  `list_automatable_parameters` before recording.
- **Groove timing:** the funk, boom-bap and neo-soul timing magnitudes are set by style, not taken from a
  measured corpus. The pack has no corpus for these styles, and each value is labelled as set.
