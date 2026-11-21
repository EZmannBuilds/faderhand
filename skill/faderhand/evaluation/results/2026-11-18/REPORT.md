# Evaluation, 2026-11-18: current skills vs. the Faderhand skill

The same model (Claude Opus 5.5 as subagents), the same ten tasks (`../../TASKS.md`), the same prompt
(`runner_prompt_template.md`) and the same tools, with no DAW, renderer or MCP tools. Only the skill changed.
Two runs per arm.

| Arm | What the runner was given |
|---|---|
| **baseline** | The current separate skills: ai-music-studio (repo `3bdb0ab` plus its three newer installed files), wavread (`c19ad49`) and Faderhand's docs |
| **improved (v1)** | The merged Faderhand skill as first written (commit `19f8b51`) |
| **improved (v2)** | v1 with four guidance fixes made after judge round 1: tighter drum jitter, a hat-velocity floor, 808 "lock first", and outlier warnings (the commit after `830bdff`) |

Runners never saw the scorer, the answer keys or the corpus. One baseline runner accidentally saw the first 300
characters of the answer keys through `head` (it says so in `baseline-A/RUN_LOG.md`), so its T01 is suspect.
The keys were removed from the runners' pack before any improved run.

## Objective checks (`score.py`, 67 checks)

| Task | base A | base B | v1 A | v1 B | v2 A | v2 B |
|---|---|---|---|---|---|---|
| T01 comprehension | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| T02 editing | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| T03 trap | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| T04 funk feel vs held-out human drumming | 3/8 | 3/8 | 6/8 | 5/8 | 5/8 | 6/8 |
| T05 arrangement | 6/7 | 6/7 | 7/7 | 7/7 | 7/7 | 7/7 |
| T06 interaction | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 |
| T07 Vital units | 4/5 | 4/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| T08 Faderhand plan | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| T09 preservation | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| T10 revision | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 | 6/6 |
| **Total** | **60** | **60** | **65** | **63** | **64** | **65** |

Where the arms differ:
- **T04 funk feel.**
  - Baseline hats were near-perfect tiers: velocity structure 0.88–0.90, where held-out human drummers sit at
    0.16–0.76. Its timing was tight (3–6 ms).
  - Both improved versions sit inside the human ranges for hat structure and hat timing.
  - v2 fails two timing-spread checks on purpose: it chose a tighter take after the judge (below).
- **T05 fills:** a fill or drop came before 3 of 7 section changes in the baseline, and 3–5 of 6 in the
  improved runs.
- **T07 Vital:** both baselines gave a wrong `unison_detune` (3.16 and 4.47, from the old cents^0.5 assumption).
  Every improved run gave 1.143, from the merged calibration.
- **T10:** improved v1 B let the bass drift off the kick (51%). The revision guidance and `midi_check` were
  fixed for v2.

**Caveat:** the improved skill's `midi_check.py` uses the same analyser as the scorer, so the improved runs can
aim at what is scored. The reference ranges are held-out human data, not arbitrary targets, but read these gains
together with the blind judging below.

Descriptive measures (not pass/fail):
- **Trap 808s:**
  - Baseline 808s landed on a kick 90–100% of the time; improved runs 63–64% (v1) and kick-locked again in v2.
  - Octave-jump share: baseline 0.07–0.14, improved 0.30–0.32.
- **Funk backbeat:** about 6 ms behind the hats in the baseline, 11–13 ms in the improved runs. The human data
  says about 10.
- **Neo-soul parallel fifths:** baseline B had 14.3 per 100 moves; every improved run had 0.

## Blind A/B judging (agent judge reading note dumps; `judge-v1/`, `judge-v2/`)

A fresh agent judged each round. It saw only the briefs and the shuffled A/B note dumps; the keys were sealed.
It scored groove, genre authenticity, development, interplay and musicality from 1 to 10 and named a preferred
version.

| Round | Improved wins | Baseline wins | Mean scores, improved vs baseline |
|---|---|---|---|
| 1: v1 vs baseline | 4 | **6** | groove 6.9 vs 7.2 · genre 7.3 vs 7.6 · development 7.0 vs 6.9 · interplay 7.1 vs 7.8 · musicality 6.9 vs 7.3 |
| 2: v2 vs baseline | 5 | 5 | groove 6.8 vs 6.6 · genre 7.3 vs 7.3 · development 6.8 vs 6.8 · interplay 7.3 vs 7.4 · musicality **7.1 vs 6.8** |

**Round 1 had a bug:** its dumps cut T05 off at bar 48, and round 2 fixed it. Round 1's T05 verdicts still
went to the improved runs.

The pattern held across both rounds:

| Task | Round 1 | Round 2 |
|---|---|---|
| T05 full song | improved 2–0 | improved 2–0 |
| T10 revision | 1–1 | improved 2–0 |
| T06 neo-soul | baseline 1–1 | 1–1 |
| T03 trap | **baseline 2–0** | **baseline 2–0** |
| T04 funk drums | **baseline 2–0** | **baseline 2–0** |

What the judge said, in short:
- **Improved wins:**
  - Songs change texture section by section (walking bass and offbeat stabs in verse 2, a half-time bridge with
    new harmony).
  - Revisions build an arc (held chords that turn into stabs, hats that double at bar 5).
  - Baseline songs had copy-pasted velocities and an EDM-style snare riser in a boom-bap bridge.
- **Baseline wins:**
  - Trap loops change kick and hat patterns almost every bar, and the lead develops toward a peak. The improved
    loops followed "short, repeated hook cells" and sparse rolls too literally.
  - In funk, the baseline kept hats on the grid with a late snare. The improved runs put hats 10–24 ms *ahead*
    of an on-grid snare. That relative placement matches the human data, but it reads as rushing hats against
    other parts on the grid.
  - v1 also had hats down at velocity 14–16 and ±40 ms scatter. v2 fixed that.

## What this shows, and what it doesn't

- **Shown:**
  - The merged skill carries knowledge the separate skills didn't: Vital units and Faderhand recipes.
  - It makes drum feel measurably closer to human performances.
  - It produces full songs and revisions that a blind reader preferred 4 times out of 4 (round 2).
- **Not shown:**
  - Better trap loops or better funk drum programming. A blind reader preferred the baseline every time (4 of 4
    each).
  - Two specific next fixes:
    - trap: ask for bar-by-bar kick and hat variation and a lead that builds, not just short cells;
    - played grooves: anchor the hats near the grid, and express the pocket as a late snare and late
      off-16ths rather than early hats.
- **Human listening (the user, 2026-11-18):** an overall listen to both packs: "Round two definitely sounds
  better. I really like all of them. There could be a few changes, but as of now, it sounds pretty good." That is a
  verdict on round 2 against round 1. No per-pair A/B picks were made, so it doesn't yet separate the baseline from
  the improved skill within a pair.
- **Before that, not measured at all:** listening. The judge reads notes. 20 WAV pairs per round are in
  `<evals>/blind/listen` and `blind2/listen`, with keys in a separate folder. They are a
  neutral General MIDI render for blind A/B listening.
- **Not tested in Live:** T08 checks the Faderhand plan against the tool schemas only.
