# Faderhand skill

The agent skill that ships with the Faderhand MCP server. It covers:
- driving Ableton Live through Faderhand's tools;
- measuring MIDI against measured genre ranges;
- validating and executing Music Production Blueprints;
- setting Vital patches with calibrated units.

It is one of three skills that are **installed separately and bundled together on the WavRead website**:

| Skill | Repository | Job | Licence |
|---|---|---|---|
| **Faderhand** (this one) | EZmannBuilds/faderhand, `skill/faderhand/` | the hands: DAW control, measurement, plan execution | MIT |
| **AI Music Studio** | EZmannBuilds/ai-music-studio | the musician: Music Director, 15 specialists, MIDI knowledge, technique cards (planned) | PolyForm Noncommercial 1.0.0 |
| **WavRead** | EZmannBuilds/wavread-skill | the ears: reading WavRead analysis reports | MIT |

None requires the others. Together they plan in a blueprint (Studio), execute and measure it (Faderhand), and check
the render (WavRead).

## Install (Claude Code)

```bash
ln -s "$(pwd)/skill/faderhand" ~/.claude/skills/faderhand
```

Python 3.10+ is needed. `uv run -q --no-project --with mido …` provides `mido` (and `jsonschema` for the validator).

## Layout

| Path | What it is |
|---|---|
| `SKILL.md` | Entry point and routing |
| `daw/README.md` | How to drive Live with Faderhand's tools: recipes, safety, automation targets |
| `vital/README.md` | Calibrated Vital preset units, measured by render, and traps |
| `blueprint/` | Music Production Blueprint v0: schema, validator, converter, example |
| `tools/midi_check.py` | Measure a MIDI file against a genre's ranges and list revisions |
| `tools/TARGETS.md`, `tools/PROVENANCE.md` | Where each range comes from; sources, licences and attribution |
| `tools/corpus/` | Rebuild the corpus inventory, analysis and statistics (the knowledge pages live in the Studio skill) |
| `evaluation/` | Ten-task benchmark, fixtures, objective scorer, blind A/B tooling, offline GM renderer, results |

The plan for the split, and what comes next: `docs/ARCHITECTURE-AND-DELIVERY-PLAN.md` in this repository.
