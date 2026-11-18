# Development record: the Faderhand skill

Started 2026-11-18, branch `feat/universal-music-skill` in `this repository`. Done items are marked
**done**. Items still open are marked **open**, and the ones waiting on the owner are marked **decision**.

## 1. What was in the environment

| Found | Where | State |
|---|---|---|
| AI Music Studio 2.1-dev | repo the `ai-music-studio` repository (3 commits ahead of GitHub, unpushed); installed copy its installed copy | **The installed copy had three newer files than the repo:** the Ableton adapter's Faderhand/sidecar and `export_audio` sections, the capability matrix and the changelog. The merge took the newer files. The repo itself is untouched and still lacks them. |
| WavRead agent skill 1.5.6 | the `wavread-skill` repository (c19ad49, 2026-11-10); older copies in the website repo's `docs/skill/` and the WavRead vault's "Public Agent Skill" | The newest copy, wavread-skill, was used |
| Vital knowledge | the studio's `shared/SYNTH_WORKSHOP/` (course, recipes, field test); the Vital 40 set's `Notes/Vital 40 - Calibration.json` | There was no separate Vital skill. The calibrated units were only in the Vital 40 notes, so they are folded into `modules/vital/`. |
| Faderhand 0.6.0 | this repo | 79 tools. No skill files before this work. |
| "MIDI Downloads Google group" | **a Chrome tab group** named "Midi Downloads", found by reading Chrome's saved session (no tab was touched) | Five tabs: Zynthion (drum-fills page, reached from its free-MIDI index), Mutopia, Groove MIDI Dataset, PDMX on Zenodo, Slakh |

Conflicting instructions found and resolved:
- **Mixer and routing over AbletonMCP.** The studio's adapter says the mixer is read-only over plain AbletonMCP
  and points to an unnamed "sidecar". That sidecar is Faderhand, and the Faderhand module takes precedence.
- **WavRead's related-tools page** treats the studio and the "WavRead MCP Bridge" as separate installs. A note
  now points to the modules.
- **Approval codes.** The studio's adapter already removed them, and Faderhand 0.5.0 removed them from the
  tools. The entry point forbids inventing one.

## 2. Skills integrated (done)

One entry, `SKILL.md`, routes to:
- `modules/studio/` (Music Director plus 15 specialists, unchanged apart from three pointer notes);
- `modules/wavread/`;
- `modules/daw-faderhand/` (new);
- `modules/vital/` (new);
- `modules/knowledge/` (new);
- `modules/evaluation/` (new).

The studio's own release checks pass on the merged copy: links, skills, schemas, examples, compatibility,
evidence, evals, records, routing, privacy and manifest. The privacy scan of all 457 files in the skill found
nothing personal. Faderhand's offline test suite passes: 36 tests.

## 3. Source files discovered and downloaded

Corpus folder, outside every repo: a corpus folder outside every repository. Every file's hash, licence, status and dedup result
is in `_inventory/inventory.jsonl`.

| Source | Downloaded | Usable after dedup | Licence | Status |
|---|---|---|---|---|
| Groove MIDI Dataset | 1,150 drum performances (MIDI-only zip, 3.3 MB) | 1,145 (1,017 train, 128 held out) | CC BY 4.0 | approved |
| Mutopia, curated | 60 pieces, 163 MIDI files; why each was chosen is in `tools/corpus/mutopia_picks.py` | 150 (136 / 14) | 46 Public Domain, 14 CC BY or BY-SA | approved, credited |
| PDMX | 254,035 MIDI (214 MB archive; 42 files listed but missing) | 43,154 approved; 4,000 analysed (3,805 / 195) | dataset CC BY 4.0; scores PD mark or CC0 | approved subset; 210,881 excluded (licence conflict, duplicates, or genres that may arrange copyrighted songs) |
| Zynthion | 13 packs, 2,680 files: 808 and hi-hat rolls (81), arp (138), bass (106), melody (414), drum patterns (168), drum fills (674), and the genre packs deep house (154), EDM (148), house (189), lo-fi (153), techno (154), trance (148), trap (153) | 823 after removing FL per-drum splits, duplicates and 1,009 transpositions (715 / 108) | royalty-free music licence, no redistribution | **pending clearance:** analysed locally only |
| Slakh | 0 | – | CC BY 4.0 | not downloaded: MIDI only inside a ~105 GB archive, 39 GB free |

- The Zynthion chord-progression and chords-and-scales collections were not downloaded.
- The genre packs' "Chords and bass" folders were downloaded with their packs and used only as harmonic
  context for bass analysis.
- Every Zynthion download went through its email form, with the owner's approval to use his Gmail. Each pack sends
  him a link and a marketing email.
- Nothing downloaded was ever executed. Zips and tars were extracted with path checks.

## 4. What the analysis extracted

`tools/corpus/analyze.py` measures, per file and per role:
- rhythm grid, per-position placement and jitter, and swing;
- velocity tiers and velocity structure;
- ghost notes, backbeat type, and hat rolls (kind, start beat, velocity shape);
- register, intervals, step, leap and leap recovery, contour, phrase length and gate;
- arpeggio rate, direction and cycle; chord voicing and voice motion;
- kick-to-bass/808 lock, register spacing, melody chord-tone share;
- counterpoint: contrary motion, parallel fifths, rhythmic complementarity;
- arrangement density and change across 8-bar blocks.

The findings are written up in `modules/knowledge/*.md`, each labelled Measured, Practice or Inference.
Headline findings:
- **Human drumming is placement plus jitter, and velocity is about half pattern, half variation.** Random
  humanising has neither.
- **The pocket is relative:**
  - The backbeat sits about 5–15 ms behind the hats in funk and hip-hop.
  - Off-16ths sit 15–25 ms behind the 8ths.
  - Measured swing: hip-hop 52.5, funk 56, afrobeat 58, jazz 59.5, soul 67.6, New Orleans 75.
- **Hats run in three velocity tiers:** beat, then "&", then 16ths at roughly half. Afrobeat inverts the first
  two.
- **Ghost notes:** funk 3.7 per bar against hip-hop 1.5. They sit on the "a" before and the "e" after a
  backbeat.
- **Lines:**
  - Classical and folk melodies are about 40% steps, with leaps recovered by step about 40% of the time.
  - Counterpoint runs about 45% contrary motion with essentially no parallel fifths.
  - In fugues, 60% of attack points have one voice moving: parts take turns.
- **Locally (pending):**
  - Every trap and drill kick has an 808, but only about 44% of 808 notes sit on kicks.
  - Slides are overlapping notes, not pitch bend.
  - Trap hat rolls are 32nds into beat 4, always rising. Drill rolls are triplets.

## 5. Changes to skill behaviour

- **One router** decides which module to use.
- **A generation checklist** (`GENERATION_RULES.md`) with two original worked examples.
- **A measure-and-revise loop:** `tools/midi_check.py` measures a file against its genre's measured ranges and
  lists revisions. The MIDI Builder must run it before handing over a file. A file existing doesn't make a task
  done.
- **Retrieval** (`tools/kb_search.py`) instead of loading the library.
- **Vital raw-value conversions** that were measured, not guessed.
- **A Faderhand recipe page:** returns, sends, sidechain, automation targets, arrangement automation.
- The **multiple-directions** rule is now part of the entry point (the studio already had the protocol).

## 6. Evaluation (done; mixed result)

Full report: `modules/evaluation/results/2026-11-18/REPORT.md`.
- **Objective checks:** baseline 60/67 in both runs; improved v1 65 and 63; v2 64 and 65.
  - The gains are in played-drum feel against held-out human drummers, fills at section changes, and Vital units.
- **Blind A/B agent judge:** round 1 preferred the baseline 6–4; round 2 (v2) tied 5–5, with v2 slightly ahead
  on groove and musicality.
  - The improved skill won every full song and revision in round 2.
  - The baseline won every trap loop and funk drum part in both rounds.
- **Conclusion:** the merge and the knowledge library help arrangement, revision, measurable idiom and tool
  knowledge. They do **not yet** help trap loops or programmed funk feel. Two fixes are written but not
  re-evaluated. Nothing has been listened to yet: two blind WAV packs are waiting.

## 7. Still open, or needing the owner's decision

- **decision: Zynthion clearance.** Ask Zynthion (info@zynthion.com) whether analysing its free packs to build
  a skill is allowed. Until then, `knowledge/local/` stays on this Mac. The trap and drill ranges in
  `midi_check.py` that those numbers informed must be confirmed or replaced before any public release.
- **decision: licensing of the combined skill.** The studio module is PolyForm Noncommercial and the rest is
  MIT, so the combined skill is noncommercial as shipped.
- **decision: installing it.** It isn't installed in the user's skills folder yet. Installing it next to the existing
  `ai-music-studio` and `wavread` skills would duplicate them.
- **decision: ai-music-studio's repo** still lacks the three newer files found in its installed copy (the same
  trap as on 2026-09-15). Syncing them into that repo is separate work.
- **open: listen.** Two blind A/B WAV packs need a human listener: `<corpus>/_evals/blind/listen` and
  `blind2/listen`, with keys in their `KEYS-do-not-open-until-you-have-listened` folders. Agent judging reads notes;
  it doesn't hear.
- **open: re-evaluate the two round-2 fixes** (hats anchored to the grid; bar-by-bar trap variation), with a
  third pair of runs and a judge.
- **open: in-Live tests.** The DAW evaluation (T08) checks the plan against the tool schemas. No tool was run
  in Live, because Faderhand (the former WavRead Bridge) was off limits for this session.
- **open: coverage.** No drill or UK-garage data beyond the local packs. No vocal, mix or sound data in the
  corpus. One human-drumming dataset.
