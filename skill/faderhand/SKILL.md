---
name: faderhand
version: 0.7.0-dev
description: Drive Ableton Live 12 through the Faderhand MCP tools (tracks, mixer in dB, returns and sends, routing and buses, devices and parameters, racks, sidechain, automation, Arrangement clips, recording and rendering), measure MIDI against genre ranges and list what to revise (midi_check), validate and execute Music Production Blueprints, and set Vital patches with calibrated units. Use for any hands-on Live task or MIDI measurement. Composition and arrangement planning live in the separate AI Music Studio skill.
---

# Faderhand

Faderhand is the hands: it acts inside a running Live Set, measures MIDI, and executes plans. It does not decide
what the music should be. The **AI Music Studio** skill (installed separately) plans the music. The **WavRead** skill
(also separate) reads audio analysis reports. Faderhand works with or without either of them.
Resolve every path relative to this folder.

## Route the task

| The task is about… | Open | Then |
|---|---|---|
| **Ableton Live:** mixer, returns, sends, buses, routing, devices, racks, sidechain, automation, Arrangement clips, recording, render | `daw/README.md` | Faderhand's tools (`tooling_info` first) |
| **Measuring a MIDI file**: groove, swing, ghost notes, hat tiers, kick and 808 lock, melody shape, section changes | `tools/midi_check.py` (ranges and sources: `tools/TARGETS.md`, `tools/PROVENANCE.md`) | Report every REVISE line and say which are deliberate |
| **A blueprint** to check or execute (a plan from the Studio skill, or one written here) | `blueprint/README.md` | Validate first: `blueprint/validate_blueprint.py` |
| **Before an arrangement change, and after its render:** what keeps sounding after note-off, which fills and drops already exist, whether planned gaps are really silent | `tools/preflight.py` (`set`, `gestures`, `occupancy`) | Act on every FLAG, or say why it doesn't matter |
| **Expressing an existing song as a blueprint** | `blueprint/blueprint_from_midi.py` | Validate it, then compare its measured relationships with the intent |
| **Vital:** preset values, patches | `vital/README.md` | Use the calibrated units, not guesses |
| Testing a skill change | `evaluation/README.md` | Same tasks, same model; score and compare blind |

**If the AI Music Studio skill is installed,** creative decisions go through its Music Director. Faderhand carries
them out and reports measurements back. **Without it,** do what the user asked directly. For new composition, say that
the Studio skill exists, and still measure anything you write with `midi_check.py`.

## Rules

1. **Confirm the Set.** Call `get_set_identity` and say which saved Set is open before editing. Suggest a copy for a song
   that matters. Edit only what was asked, and read every write back.
2. **No authorisation codes.** There is no per-song or per-conversation code, and you must not invent one. The guards
   are: saved Sets only, deletes only in a Set with a `__TOOLING_SCRATCH__` track, and read-back on every write.
3. **Audit before you promise.** Check which tools are connected and which instruments are installed. Measure an
   instrument before trusting it: some presets sound an octave off their written note, and some drum-kit pads ship
   20 dB down.
4. **A rendered file is not a finished task.** Render, measure (stems, `midi_check.py`, WavRead if present), fix the
   cause, and report what wasn't heard.
   **Notes are not sound:** before planning silence, run `preflight.py set` on the saved Set (a Sampler in Trigger mode
   ignores note-off). After the render, run `preflight.py occupancy` on the stems inside each planned gap.
5. **Keep musical intent through a revision.** Swapping a sound or a patch keeps the notes and roles unless the user
   asked for more.
6. **Provenance:** third-party MIDI never goes into an output, a commit or this skill.

## Tools

```
uv run -q --no-project --with mido python tools/midi_check.py <file.mid> --genre <genre>
uv run -q --no-project --with mido --with numpy --with soundfile python tools/preflight.py set|gestures|occupancy ...
uv run -q --no-project --with jsonschema python blueprint/validate_blueprint.py <blueprint.json>
uv run -q --no-project --with mido python blueprint/blueprint_from_midi.py <song.mid> <mapping.json> <out.json>
uv run -q --no-project --with mido python evaluation/score.py <run_dir> --refs <refs.json>
```
