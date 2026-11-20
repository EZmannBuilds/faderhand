# Architecture and delivery plan: Faderhand, AI Music Studio and WavRead

Status, 2026-11-20. This plan rescopes PR #2 into separate skills, per the owner's decision ("keep the studio skill and
Faderhand separate while bundling them on the website"). It follows the sequence agreed in planning: separate the
skills, set a composition contract, build an arrangement director, connect the knowledge, add the feedback loop, then
songwriting and composition memory. Items marked **done** are in this PR or in the Studio branch below. Items marked
**planned** are not started.

## 1. Separate skills, one bundle

| Skill | Repo | Entry | Owns | Requires |
|---|---|---|---|---|
| Faderhand | EZmannBuilds/faderhand | `skill/faderhand/SKILL.md` | DAW control, `midi_check`, blueprint schema and validator, Vital units, evaluation, corpus tools | nothing (Live + the MCP server to act) |
| AI Music Studio | EZmannBuilds/ai-music-studio | `SKILL.md` → Music Director | musical planning, 15 specialists, MIDI knowledge, genre profiles (planned), technique cards (planned), composition memory (planned) | nothing; uses Faderhand and WavRead when present |
| WavRead | EZmannBuilds/wavread-skill | `skills/wavread/SKILL.md` | interpreting analysis reports, operating the app | the WavRead app |

**Website bundle (proposal, nothing changed on the site).**
- Each skill is downloaded and versioned on its own.
- A convenience bundle lists the three at pinned versions. Proposed manifest:

```json
{"bundle": "WavRead Music Agent Bundle", "bundle_version": "2026.11-preview",
 "skills": [
  {"name": "faderhand", "repo": "EZmannBuilds/faderhand", "path": "skill/faderhand", "version": "0.7.0", "licence": "MIT"},
  {"name": "ai-music-studio", "repo": "EZmannBuilds/ai-music-studio", "path": ".", "version": "2.1-dev", "licence": "PolyForm-Noncommercial-1.0.0"},
  {"name": "wavread", "repo": "EZmannBuilds/wavread-skill", "path": "skills/wavread", "version": "1.5.6", "licence": "MIT"}],
 "notes": "Install any subset. The bundle is not one merged skill; each keeps its own licence and changelog."}
```

The Faderhand server and Remote Script install as before; the bundle covers the skills only.

## 2. Component ownership map (what stayed, moved or left PR #2)

| Was in PR #2 | Now | Status |
|---|---|---|
| `skill/faderhand/modules/studio/` (a copy of the Studio) | removed from Faderhand; the Studio stays in its own repo | **done** |
| `modules/wavread/` (a copy of the WavRead skill) | removed; it stays in wavread-skill | **done** |
| `modules/daw-faderhand/` | `skill/faderhand/daw/` | **done** |
| `modules/vital/` | `skill/faderhand/vital/` | **done** |
| `modules/knowledge/*.md`, `stats/`, `kb_search.py` | Studio repo, `shared/MIDI_KNOWLEDGE/` and `tools/kb_search.py` | **done**, in local branch `feat/midi-knowledge` (`0d025c4`), **not pushed** |
| `modules/knowledge/TARGETS.md`, `PROVENANCE.md` | `skill/faderhand/tools/` (they document the checker's ranges); PROVENANCE also copied to the Studio | **done** |
| `tools/midi_check.py`, `tools/corpus/` | stay in Faderhand | **done** |
| `modules/evaluation/` | `skill/faderhand/evaluation/` (results from 2026-11-18 kept as recorded) | **done** |
| new: `skill/faderhand/blueprint/` | schema v0, validator, converter, example; tests in `tests/offline/test_blueprint.py` | **done** |
| genre ranges inside `midi_check.py` | move to Studio-owned genre profiles that the checker reads as data; keep a default copy in Faderhand for standalone use | **planned** (phase 4) |
| Studio's installed copy ahead of its repo (3 files) | synced into the Studio branch | **done** (same branch) |

Duplicate instructions are gone:
- **The DAW recipes** live only in Faderhand's `daw/README.md`. The Studio's Ableton adapter names the "sidecar" as
  Faderhand.
- **The knowledge pages** live only in the Studio.
- **The checker** lives only in Faderhand.

## 3. Music Production Blueprint v0 (done)

- **Location and tests:** `skill/faderhand/blueprint/`, with `tests/offline/test_blueprint.py` (8 tests).
- **Design:** roles are separate from tracks, every role carries a reason, and sections carry energy, active roles,
  changes and the gesture before. Relationships carry measured values, and execution needs are checked against what
  Faderhand offers.
- **Converted reference song:** *Cold Brick* (the darkest of the three boom-bap references, with the owner's Vital
  808) is converted and validates. The blueprint stays with the song files on the owner's machine (`Notes/Cold Brick -
  Blueprint v0.json`); the repo carries only an example built on the benchmark's own original fixture.
- **What *Cold Brick*'s blueprint shows:**
  - 8 roles on 7 tracks; the stab hook is three layered tracks.
  - 83% of 808 notes land with the kick.
  - The stabs stay clear of the kick 99% of the time and the snare 85%; the piano stays clear of the stabs 96%.
  - **The arrangement weakness, measured:** kick, snare, hats, 808, stabs and piano are active in 7 of 8 sections, so
    sections change by energy and the odd added part, not by subtraction. That is the first thing the arrangement
    director has to fix.

## 4. Next phases (planned, in order)

1. **Arrangement Director v0 (Studio plans, Faderhand executes).**
   - Input: *Cold Brick*'s blueprint and brief.
   - Output: one revised blueprint that justifies every role and changes the active roles at section boundaries
     (subtraction, substitution, entries), plus the Live build of it as a scratch version. The current Set is
     untouched.
   - Compare the two versions blind, with the same brief.
   - No track-count target.
2. **Technique cards (Studio).**
   - 8–12 reviewed cards for the problems the references showed: drum/bass interaction, stab and keys tone,
     sectional contrast, melodic development, transitions.
   - Each card says when to use it, when not to, which roles it touches and how to check it.
   - The director records which cards it used. The checker receives each card's expectations as data.
3. **Feedback loop (Faderhand + WavRead + Studio).** Keep blueprints, diagnostics, renders and the owner's notes per
   version. A failed check produces a targeted revision, not a rewrite; a sound swap keeps the notes.
4. **Genre profiles as data (Studio), read by `midi_check`.**
5. **Songwriting and lyrics, and composition memory (Studio)**, both on the same blueprint contract.

## 5. Regression-test plan

Every phase must keep these passing, or explain the change:
- **Faderhand offline suite:** `tests/offline`, now 44 tests, including the blueprint tests.
- **Studio release checks:** `tools/check_all.py`, all eleven checks, privacy included.
- **The ten-task benchmark:** `skill/faderhand/evaluation/`, with the same tasks and fixtures.
  - The 2026-11-18 numbers are the baseline: objective 60/67 for the old skills and 64–65/67 for the new.
  - The blind judge tied 5–5.
  - Trap (T03) and funk drum programming (T04) are watched as regressions: the old skill won both in both rounds.
- **The three reference songs:** Dusty Keys, Late Bus and Cold Brick.
  - They are kept as fixtures, as their MIDI and blueprints on the owner's machine.
  - Each phase rebuilds at least *Cold Brick* from its blueprint and checks the stems: no silent notes, bass and 808
    pitch, and level against the mix targets.
- **Listening:** blind A/B WAV pairs for the owner (`evaluation/render/`), since agent judges read notes and can't hear.

## 6. Acceptance criteria for this PR

- [x] Faderhand's skill installs and routes on its own: no copies of the Studio or WavRead skills.
- [x] The Studio skill passes its own release checks with the knowledge added (branch `feat/midi-knowledge`).
- [x] Blueprint v0 schema, validator and converter, with tests in the offline suite.
- [x] One reference song (*Cold Brick*) expressed as a valid blueprint.
- [x] This plan: ownership map, bundle proposal, regression plan, decisions.
- [ ] The owner approves pushing the Studio branch, and the website bundle change, separately.

## 7. Decisions needed from the owner

| Decision | Default used here |
|---|---|
| Push the Studio branch `feat/midi-knowledge` (it also carries the Studio's 3 unpushed commits from October) | not pushed; waiting |
| Website bundle: separate downloads plus a convenience bundle, as above | proposal only; no site change |
| Zynthion: ask whether analysing its free packs for a skill is allowed | its numbers stay local; the trap and drill checker ranges they informed must be confirmed or replaced before a public release |
| Revisions in Live: autonomous in scratch versions, the owner promotes to the main Set | yes |
| Composition memory: per project by default, cross-project only if the owner opts in | per project |
