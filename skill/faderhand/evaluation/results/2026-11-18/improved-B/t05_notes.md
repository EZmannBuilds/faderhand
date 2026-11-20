# T05: boom-bap / lo-fi instrumental (F minor, 88 BPM, 60 bars, about 2:44)

**File:** `t05_song.mid`. It has four named tracks: Drums (ch 10), Bass (ch 2), Keys (ch 3, Rhodes hint) and Lead (ch 4, flute hint). Each section starts with a MIDI marker.

## Section map
At every boundary at least two things change.

| Bars | Section | What changes |
|---|---|---|
| 1–8 | **Intro** | Bars 1–4: keys alone, soft. Bars 5–8: hats, a rim backbeat and a soft kick come in. Bar 8 has a snare pickup and a C2–E1 bass pickup. |
| 9–24 | **Verse 1** | The full beat starts (snare, ghosts, kick variations, a crash on 9) and the bass comes in. The keys hold and re-strike. There's no lead, which leaves room for a rapper. Small turnaround in bar 16, tom fill in bar 24. |
| 25–32 | **Hook** | New progression (Dbmaj9, Eb6, Cm9, Fm9, then Gm7b5–C7b9 into Fm9). The lead hook comes in. Hats go to 16ths with open hats, there's a crash, an extra kick on step 3 and a busier, syncopated bass. Fill in bar 32. |
| 33–40 | **Verse 2** | The verse chords come back. The lead drops out except for answering fragments in bars 36 and 40. Different kick patterns (steps 6 and 11), and the hats go back to 8ths. |
| 41–48 | **Bridge** | Half-time drums (snare on 3) with quarter-note hats. The keys switch from held chords to broken 8th-note arpeggios. Long bass notes. New chords: Gbmaj7 (Neapolitan colour), Fm9, Dbmaj9, Gm7b5–C7b9. Bar 48 is a 16th-note snare build. |
| 49–56 | **Hook 2** | Crash. The first four bars play the hook exactly. Bars 53–56 develop it: the cell goes up to F5–Eb5–C5, the answer climbs, and it ends open on Ab4. Everything is a little louder. |
| 57–60 | **Outro** | The drums thin out to hats, kick and rim, then stop at bar 59. The lead plays the cell once more, and the piece ends on a held Fm9. |

## Musical choices
- **Harmony:**
  - Rootless 7th and 9th voicings between MIDI 52 and 72, an octave or more above the bass (median gap 19 semitones).
  - The verse loop is Fm9, Bbm9, Eb9, Abmaj9, Dbmaj9, Bbm9, Gm7b5, C7b9.
- **Lead hook:**
  - A 3-note falling cell, C5–Bb4–Ab4.
  - It's repeated a step lower, then leapt up to Eb5 and recovered by step. The fourth bar answers and resolves to F4.
  - Range is 13 semitones (E4 to F5). 63% of the moves are steps, every leap is recovered, and 73% of notes are chord tones.
- **Bass:**
  - Sparse roots that land with the kick (63% on a kick).
  - Chromatic walk-ups or a drop from the fifth into chord changes, every second bar.
- **Feel (hybrid boom-bap):**
  - 58% swing on the 16ths in every part.
  - The snare sits about 15 ms behind the hats.
  - Timing jitter about 5 ms.
  - Hats in three velocity tiers with variation inside each tier.
  - About one ghost snare a bar.

## Sketch round
Three 8-bar verse-into-hook excerpts were sketched and measured; their files are in `work/`.

- **A (kept):** held Rhodes, sparse bass that locks to the kick, a flute-like hook.
- **B:** chopped offbeat stabs over a syncopated bass. With the swung hats that made three syncopated parts at once. Only its busier bass was kept, and only for the hooks.
- **C:** a walking bass. It locked badly to the kick (0.25 on kick) and walked by arpeggio rather than by step (stepwise share 0.0).

The excerpt for A measured 13 parallel fifths per 100 moves. I traced them to a Dbmaj9 voicing with the 5th on top moving to Bbm9, revoiced it, and the full song now measures 1.0 per 100.

## How it was checked
- `midi_check.py --genre boom-bap` and `--genre lofi`: 0 REVISE.
  - swing 58.1
  - backbeat 0.76 (the bridge's half-time is deliberate)
  - ghosts 1.1 a bar
  - on-grid share 0.286, jitter 5.2 ms
  - hat structure 0.52, snare 15 ms late
  - bass stepwise share 0.215
- Arrangement: 6 of the 8-bar block boundaries change (density CV 0.39), against a target of 3 or more.
- Read back: bars 8, 9, 25, 36, 41, 48, 49, 53 and 57, plus the marker list. Every track has notes, drums are on ch 10 only, and the file is 60 bars long.
- **Not heard:** nothing was rendered or listened to. Notes that land a few ms before a bar line belong musically to the next bar.
