---
name: faderhand
version: 0.7.0-dev
description: One music skill for composing, arranging, producing, sound design, mixing, analysis and DAW control. Writes and edits MIDI in any genre with corpus-measured groove, 808, melody and arrangement rules and a measure-and-revise loop; drives Ableton Live 12 through Faderhand (mixer, returns, sends, routing, devices, racks, sidechain, automation, recording); designs Vital patches with calibrated units; reads WavRead analysis reports. Use for any music task, with or without a DAW.
---

# Faderhand

One entry point for every music task. Inside, it routes to modules. Load only the module a task needs.
Resolve every path relative to this folder.

## Route the task

| The task is about… | Open | Then |
|---|---|---|
| Writing, continuing, arranging or diagnosing music; lyrics; any creative brief | `modules/studio/SKILL.md` → its **Music Director** | The Director locks intent and routes to its fifteen specialists |
| Writing or editing **MIDI** (any part, any genre) | `modules/knowledge/GENERATION_RULES.md`, then `tools/kb_search.py` for the genre and role | Measure every file with `tools/midi_check.py` and revise before calling it done |
| Groove, feel, humanising, drums | `modules/knowledge/DRUMS_AND_GROOVE.md` | `midi_check.py --genre …` |
| 808s, basslines, kick and bass lock | `modules/knowledge/LOW_END_808_AND_BASS.md` | |
| Melody, hooks, arps, counterpoint, development | `modules/knowledge/MELODY_LINES_AND_DEVELOPMENT.md` | |
| Song form, sections, part interplay, revising | `modules/knowledge/ARRANGEMENT_AND_REVISION.md` | |
| **Ableton Live:** mixer, returns, sends, buses, routing, devices, racks, sidechain, automation, recording, render | `modules/daw-faderhand/README.md` | Faderhand's tools (`tooling_info` first) |
| **Vital:** patches, preset values, synthesis | `modules/vital/README.md` → `modules/studio/shared/SYNTH_WORKSHOP/` | Use the calibrated units, not guesses |
| **WavRead:** operating the app, reading a report, comparing mixes | `modules/wavread/SKILL.md` | WavRead measures. It never decides whether music is good. |
| Mixing decisions | `modules/studio/mix-engineer/SKILL.md` | Act in Live through Faderhand; check renders with WavRead |
| FL Studio, Pro Tools, other DAWs | `modules/studio/daw-adapters/` | Check the capability matrix before promising an operation |

Several modules often apply. A beat for a Live Set uses the Director, the knowledge rules, `midi_check.py`,
Faderhand and, to check it, WavRead.

## Rules that hold everywhere

1. **User profile:** load it if one exists (`modules/studio/profiles/local/`). Nothing personal is ever
   written into skill files.
2. **Audit before you promise:**
   - Check which tools are actually connected (Faderhand, AbletonMCP, WavRead) and which instruments are
     installed (`modules/studio/plugin-auditor/`).
   - Don't assume a DAW, plugin or tool can do something it hasn't shown it can.
3. **Explore before committing:** for composition tasks, sketch 2–3 directions that differ by mechanism, compare
   them, and build the strongest or a combination (`modules/studio/shared/SKETCH_ROUND_PROTOCOL.md`).
4. **Measure, read back, revise:**
   - A rendered file or written MIDI is not a finished task.
   - Run `midi_check.py`, read back protected material, render and listen when possible, then revise the cause.
   - Report what was and wasn't heard.
5. **Learn principles, not tunes:**
   - The knowledge library holds distributions from a licensed corpus.
   - Never reproduce a melody, bassline or pattern from a reference or from memory of a known song.
6. **Faderhand safety:** say which saved Set is open before editing, suggest a copy for real songs, and read
   every write back. There is no per-song or per-conversation authorisation code; don't invent one.
7. **Provenance:** third-party MIDI never goes into an output, a commit or this skill. Numbers in
   `modules/knowledge/local/` are local only.

## Tools in this skill

```
uv run -q --no-project --with mido python tools/midi_check.py <file.mid> --genre <genre>   # measure and get revisions
python3 tools/kb_search.py "<genre> <role> <question>"                                     # retrieve knowledge sections
modules/studio/tools/check_all.py --profile <yaml>                                         # the studio's release checks
modules/evaluation/score.py <run_dir>                                                      # score an evaluation run
```
