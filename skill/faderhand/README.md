# Faderhand: one music skill

One installable agent skill that combines three things:
- the **AI Music Studio** (composition, arrangement, production, mixing and finishing, with sixteen specialists);
- the **WavRead** agent skill (analysis reports, app control);
- **Faderhand** (Ableton Live control), plus calibrated **Vital** knowledge.

It adds a **MIDI knowledge library learned from a licensed corpus**, with a measure-and-revise tool. The
user sees one skill, named Faderhand like the MCP server it ships with. Inside, the modules stay separate, so each can still be updated from its own source.

## Install (Claude Code)

```bash
ln -s "$(pwd)/skill/faderhand" ~/.claude/skills/faderhand
```

Notes:
- A symlink keeps the installed skill in step with the repository. Copying works too: `cp -R`, and recopy after
  each update.
- If a user profile exists, link it into `modules/studio/profiles/local/` (see that folder's README).
- `modules/knowledge/local/` only exists on a machine that built it from the corpus. It's gitignored.
- The tools need Python 3.10+ and `mido`. `uv run -q --no-project --with mido python …` handles that.
- If `ai-music-studio` or `wavread` is also installed as a separate skill, uninstall or disable those to avoid
  two skills answering the same request.

## Layout

| Path | What it is | Source |
|---|---|---|
| `SKILL.md` | The single entry point and router | new |
| `modules/studio/` | AI Music Studio 2.1-dev: Music Director, 15 specialists, shared schemas, DAW adapters, evals, release checks | `ai-music-studio` repo at `3bdb0ab`, plus three newer files that only existed in the installed copy (`CHANGELOG.md`, `daw-adapters/ABLETON_LIVE.md`, `daw-adapters/DAW_CAPABILITY_MATRIX.json`) |
| `modules/wavread/` | WavRead agent skill 1.5.6 | `wavread-skill` repo at `c19ad49` (newer than the copy in the website repo) |
| `modules/daw-faderhand/` | How to drive Live with this repository's MCP tools | new |
| `modules/vital/` | Calibrated Vital preset units and traps, pointing to the studio's synth workshop | new, from the Vital 40 calibration renders |
| `modules/knowledge/` | Learned MIDI knowledge: guidance pages, aggregate stats, provenance | new |
| `modules/evaluation/` | Ten-task benchmark, fixtures, objective scorer, results | new |
| `tools/midi_check.py` | Measure a MIDI file against the genre's measured ranges and list revisions | new |
| `tools/kb_search.py` | Retrieve only the relevant knowledge sections | new |
| `tools/corpus/` | Rebuild the corpus inventory, analysis and statistics | new |

## Changes made while merging

- The studio's Ableton adapter describes a "sidecar Remote Script" for mixer and routing work. That sidecar is
  Faderhand, and `modules/daw-faderhand/README.md` says so and takes precedence.
- WavRead's related-tools page described the studio and the "WavRead MCP Bridge" as separate installs. A note
  now points to the modules here.
- The studio's MIDI Builder, Performance Director and Composer each gained a short pointer to the knowledge
  library and `midi_check.py`. No other specialist text changed.
- The studio's manifest lost one entry: `.github/workflows/validate.yml`, which isn't part of the merged copy.
- No approval-code workflow was reintroduced. The entry point says not to invent one.

## Licences

| Part | Licence |
|---|---|
| `modules/studio/` | **PolyForm Noncommercial 1.0.0** (its own `LICENSE`) |
| `modules/wavread/` | MIT (its own `LICENSE`) |
| Everything else in this folder | MIT, as the rest of this repository |

Because the studio module is noncommercial, **the combined skill can't be sold** while that module is in it.
That licence covers the skill's text, not music made with it.

Corpus data: see `modules/knowledge/PROVENANCE.md`.
- No third-party MIDI is included.
- Groove MIDI Dataset (CC BY 4.0, Google LLC), PDMX (CC BY 4.0) and the Mutopia Project editions listed there are
  credited.
- Numbers from Zynthion's packs are kept local until the licence question is settled.
