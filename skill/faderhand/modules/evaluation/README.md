# Evaluation

A benchmark for the music skill: the same ten tasks, the same model, the same tools and the same prompt, with
only the skill changed between arms.

## Files

| File | What it does |
|---|---|
| `TASKS.md` | Ten tasks, one per capability (comprehension, editing, genre composition, human timing, arrangement, part interaction, Vital, DAW automation, preservation, revision) |
| `fixtures/` | Original MIDI written for the tests (`make_fixtures.py`), with answer keys (`*.truth.json`). **Runners get a copy without the answer keys or the generator.** |
| `score.py` | Objective checks on a run's output folder. Writes `SCORES.json`. |
| `blind_pairs.py` | Shuffles two runs' outputs into anonymous A/B pairs: a note dump for an agent judge, and WAVs for human listening |
| `render/render_midi.swift` | Offline render through macOS's built-in General MIDI bank, for blind listening (neutral sketch sound) |
| `results/` | Each comparison's scores, the generated MIDI, run logs, judge verdicts and the blind-listening pack |

## How a comparison runs

1. Copy `TASKS.md` and the fixtures **without** `*.truth.json` and `make_fixtures.py` into an eval pack.
2. Freeze each skill under test as a snapshot. Runners must not see `modules/evaluation/`.
3. Give each runner the identical prompt (`results/*/runner_prompt.md`); only the skill path differs. Runners may
   not read the corpus, the web or anything outside the skill, the pack and their output folder.
4. Run at least two runs per arm.
5. Score each run:
   `uv run -q --no-project --with mido python score.py <run> --refs <refs.json> --server ../../../../server/ableton_tooling_server.py`
6. Build blind pairs and have a separate judge rate them without the key. Then **listen** to the WAV pairs
   blind (the human check this benchmark can't automate).

## What the checks can and can't show

- **Reference ranges come from held-out files only:** the Groove test split for funk, soul and hip-hop feel.
  The trap ranges are conventions, because too few held-out trap files survived dedup.
- **The improved skill's `midi_check.py` uses the same analyser as `score.py`.** An improved run can therefore
  "aim at" what is scored. The ranges are real-world distributions, not arbitrary targets, but read objective
  gains together with the blind judge and, above all, listening.
- **T07 tests whether the Vital calibration was merged.** The baseline skill didn't contain those units.
- Passing every check says the file is idiomatic in measurable ways. It doesn't say it's good music.
