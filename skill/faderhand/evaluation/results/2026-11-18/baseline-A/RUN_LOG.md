# Run log: baseline-A

**Skill under test:** the user's separate music skills in `_evals/baseline-skill/`: ai-music-studio, wavread and
faderhand-docs.
**Tasks:** `_evals/eval-pack/TASKS.md`, T01–T10.
**Tools:** no MCP, Ableton, Faderhand or WavRead tools were called. All MIDI was written with Python and mido, and
every script is in `scripts/`.

## Skill files read
Paths are relative to `<evals>/baseline-skill/`.

- **Entry files:**
  - `ai-music-studio/SKILL.md`
  - `wavread/SKILL.md`
  - `faderhand-docs/README.md`, `faderhand-docs/TOOLS.md`, `faderhand-docs/TOOL-REFERENCE.md`
- **Routed from the Music Director:**
  - `ai-music-studio/music-director/SKILL.md` (full)
  - `ai-music-studio/midi-builder/SKILL.md` (full)
  - `ai-music-studio/performance-director/SKILL.md` (full)
  - `ai-music-studio/shared/HUMAN_PERFORMANCE_SCHEMA.md` (full)
  - `ai-music-studio/shared/RHYTHM_SYSTEMS/MICROTIMING_AND_GROOVE.md` (full)
  - `ai-music-studio/shared/VIRTUAL_INSTRUMENT_GUIDE/DRUM_KIT.md` (kit cards excerpt; physical constraints through
    "What the Performance Director needs")
  - `ai-music-studio/composer/SKILL.md` (harmony, melody, motif, bass, rhythm, originality, expectation, hooks,
    high-density electronic writing, vocal handoff, melody-variety gate)
  - `ai-music-studio/arranger/SKILL.md` (section role, energy, contrast audit, repetition and development,
    transitions)
  - `ai-music-studio/shared/QUALITY_GATE.md` (first 80 lines)
- **For T07, Vital:**
  - `ai-music-studio/shared/SYNTH_WORKSHOP/FIELD_TEST.md`
  - `ai-music-studio/shared/SYNTH_WORKSHOP/AUTOMATION_GUIDE.md`
  - a grep of the whole skill folder for "vital" and "detune", and of `producer/SKILL.md` for synth and workshop
    pointers
- **For T08, Faderhand:**
  - `faderhand-docs/UNITS.md`
  - `faderhand-docs/CAPABILITY-MATRIX.md` (lines 1–60)
  - `faderhand-docs/REFERENCE-LOM-TECHNIQUES.md`
  - a grep of `ai-music-studio/daw-adapters` for the automation target format
- `ai-music-studio/profiles/`: listed only. It holds no local profile, just the README and an example.

## Per task: what I produced and how I checked it
| Task | Output | How I checked it |
|---|---|---|
| T01 | `t01_answers.json` | `scripts/t01_analyze.py` computes the answers from the file. Tempo comes from µs per beat (92.0). Bars come from the last note-off (16). Roles come from track content. Swing comes from the off-16th hat offset: 139/240 = 58%, present from bar 9. Bass on kick uses a 60-tick (1/32) window: 48 of 64. The section change is at bar 9, where the lead enters and the hats become swung 16ths. Chords come from the Keys pitch sets (Dm7, Bbmaj7, C7, A7); key is D minor |
| T02 | `t02_edited.mid` | `scripts/t02_verify.py` compares every note and meta event against the fixture. Bass bars 5–8: exactly 16 notes moved down 12 semitones, the rest identical. Drums: all original notes kept, 16 ghost snares added (pitch 38, channel 10, velocity 25–44), on the 'e' and 'a' of beats 2 and 4 in bars 1–4 only. Keys and Lead identical; tempo and time signature identical |
| T03 | `t03_trap.mid`, `t03_notes.md` | `scripts/check_midi.py`: conventions, 8 bars, melody-variety report pass, every kick doubled by the 808 |
| T04 | `t04_funk_drums.mid` | Conventions, 4 bars, four-limb check clear. The performance plan, with named models and magnitudes, is in the header of `scripts/t04_funk.py` |
| T05 | `t05_song.mid`, `t05_notes.md` | Conventions, 72 bars, 8 markers, four-limb check clear, lead melody-variety report pass. Per-section density audit in `scripts/t05_sections.py` |
| T06 | `t06_neosoul.mid` | Conventions, 8 bars, four-limb check clear. Interlock: 26 of 28 kicks doubled by bass. The other 2 fall where the bass deliberately ties over from an anticipation. 23 more bass notes sit in the kick's gaps. EP chord voicings top out at Eb4, and the EP leaves long rests, so a vocal has room |
| T07 | `t07_vital.json` | `scripts/t07_vital.py` converts each value back to its display unit: 10% detune, −6.00 dB relative to the default, 3.000 s, 375.0 ms, +25 cents |
| T08 | `t08_calls.json` | `scripts/t08_calls.py` checks every tool and argument name against the documented table in `TOOL-REFERENCE.md`: 15 calls, 0 undocumented names |
| T09 | (scored from T10) | `scripts/t09_verify.py`: chord pitches identical in every bar, lead pitch sequence identical overall and within each bar |
| T10 | `t10_revised.mid`, `t10_notes.md` | `scripts/t09_verify.py` and `scripts/check_midi.py`. Diagnosis and changes are in the notes |

The validator output for all of these is in `scripts/validation_log.txt`. Every file has 480 PPQ, a tempo and a time
signature meta event, a named track per part, and drums on MIDI channel 10.

## How I followed the skill, and where I departed from it
- **Session mode.** The Director's "just make it" exception applied: the intent locks are recorded in the notes and
  were not asked about.
  - T01: diagnosis and read-only work.
  - T02 and T10: REVISE on the user's material. Protected material was read from the fixture, never retyped.
  - All other tasks: CREATE.
- **No sketch round.** The skill's default for a new composition is three rendered sketches judged by the user. I
  skipped it because nothing could be rendered and the user had locked the brief. Instead I weighed alternatives
  in-run; T03's notes show this.
- **Performance plans.** Every performed part uses named timing models from `HUMAN_PERFORMANCE_SCHEMA.md` §3, with
  magnitudes in percent of a beat. Each magnitude is labelled "set, not measured" where the pack has no corpus for
  the style.
  - There is no "random humanize". The only spread is a tightness SD of 0.5–1.5% of a beat. It is seeded, so every
    file is reproducible.
  - The T03 trap timing is deliberately on the grid. The skill treats exact timing as a style, not a defect.
- **No plugin audit, calibration or render verification.** There was no DAW, so no instruments could be checked.
  - The General MIDI (GM) program changes are placeholders, and every instrument is unmeasured.
  - Nothing claims how anything sounds. The skill says a text model reasoning about notes is not listening.
- **Not done:**
  - `FILE_NAMING.md` was not applied, because the tasks fix the file names.
  - No diversity-ledger row was written: there is no profile or output root.
  - No `_DAW_Notes.txt` sidecars; the requested `.md` notes take their place.
- **Diversity across tasks.** Each piece has its own key, tempo, harmonic mechanism, kick/bass relation and feel:
  - T03: F harmonic minor, half-time trap, grid timing.
  - T04: funk 16ths with a laid-back backbeat.
  - T05: G minor, 60% swing, boom-bap form.
  - T06: Eb major, IV–iii–ii–V, 57% swing, an interlocking bass.

## What I could not do, or could not verify
- **T07 is mostly unverified.** The skill documents only one of the five mappings: reverb decay as log2 seconds, in
  `FIELD_TEST.md`.
  - The other four come from my recollection of Vital's parameter table, not from the skill, and were not checked
    against an installed Vital.
  - The unison-detune mapping is the least certain. If Vital applies the detune percentage per side rather than as a
    total spread, the answer is sqrt(5) = 2.236 instead of sqrt(10) = 3.162. The `basis` field says so.
- **T08 automation target format is assumed.** The docs show the target object only for the mixer
  (`{"mixer": "volume"}`), and say device targets come from `list_automatable_parameters`.
  - I used `{"device": "Auto Filter", "parameter": "Frequency"}` and put a `list_automatable_parameters` call first,
    to get the real object.
  - Arrangement automation can only be recorded in real time (`record_arrangement_automation`); it cannot be drawn.
  - The Faderhand docs say to suggest a backup before editing a Set. The runner rules forbade questions, so that step
    is not in the call list.
- **Truth-file exposure.** While first inspecting the fixtures, a `head -c 300` command printed the start of
  `fixtures/comprehension.truth.json` and `fixtures/flawed.truth.json`.
  - That showed tempo, meter, key, bars, roles, swing, the bass counts and the change bar for T01, and part of the
    protected chord list for T10.
  - My T01 answers were computed from the MIDI by `scripts/t01_analyze.py`. The chord names were not in the exposed
    part. T10 reads its protected material from `flawed.mid`.
  - I opened neither truth file again, and never opened `make_fixtures.py`.
- **No listening, rendering or analysis of any kind.** That covers sound quality, mix balance, and whether the T10
  revision "sounds performed".
