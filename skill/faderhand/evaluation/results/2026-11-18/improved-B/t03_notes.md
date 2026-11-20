# T03: Atlanta trap loop (C# minor, 140 BPM, 8 bars)

**File:** `t03_trap.mid`. It has three named tracks: Drums (ch 10), 808 (ch 2, GM hint Synth Bass 2) and Lead (ch 3, GM hint glockenspiel/bell). It runs 480 PPQ in 4/4, with one `Loop` marker.

## What it is
- **Harmony:** one chord every two bars: C#m, A, F#m, then G# (major, with B# as the leading tone) for the turnaround. The 808 and the lead carry the harmony, and there is no chord track.
- **Drums (programmed feel, on the grid):**
  - Clap and snare layered on beat 3 of every bar, so the backbeat is half-time.
  - Two to four kicks a bar. Beat 1 is fixed, and the other kicks move between steps 3, 6, 7, 10, 11, 13 and 14 from bar to bar.
  - Hats run 8ths in bars 1–2 and 16ths from bar 3 on. Bar 7 has a gap in its 16ths (a stutter).
  - Five rolls, all with rising velocity:
    - 32nds into the next bar (bars 2 and 6)
    - 16th triplets into beat 3 (bars 3 and 7)
    - a 32nd-triplet roll in bar 8 that turns the loop around
  - Open hats in bars 4 and 8 mark the 4-bar points.
  - Hat velocity sits in shallow tiers (96/86/80), the way programmed trap hats do.
- **808:**
  - Every kick has an 808 note under it, and the 808 adds notes of its own between the kicks: 4.75 notes a bar, 63% of them on a kick.
  - Octave pops make up about 30% of the moves.
  - 12 chosen notes overlap the next note, so a synth in legato or portamento mode glides into it (1.6 slides a bar). The rest are gated at about 0.97.
  - Roots stay between C#1 and G#2 (MIDI 25–45).
- **Lead:**
  - Built on a 4-note cell, E5–D#5–C#5–G#4, played in the gaps and detached (gate 0.65).
  - Bar 3 repeats the cell with one change: it lands on A4 for the A chord.
  - The even bars answer upward.
  - Bars 5–8 sequence the cell up and resolve onto B#4 and D#5 over G#.
  - Range is 13 semitones, and phrases are about 4 notes with rests between them.

## Why
- **Sketch round:** three directions were sketched and measured, and their files are in `work/`.
  - **A, "bounce":** lead in the gaps, an 808 with octave pops, 8th/16th hats with mixed rolls.
  - **B, "half-time menace":** long 808s, triplet hats, a low flute lead.
  - **C, "call-and-response":** the lead plays only where the 808 rests.
- **Why A won:**
  - B measured as a kick with pitch: 2.4 808 notes a bar, 90% of them on a kick. One of its rolls was flat.
  - C's lead had no recognisable cell.
  - A's only failure was too many slides (3.4 a bar), because every 808 note overlapped the next. I changed it so only chosen notes overlap.
- The movement comes from the pattern, the rolls and the 808, not from timing. That matches how programmed trap is made: about 90% of notes sit exactly on the grid and timing jitter is 0 ms.

## How it was checked
- `midi_check.py --genre trap`: 0 REVISE.
  - Half-time backbeat 1.0.
  - Rolls 0.62 a bar, all rising.
  - 808 on kick 0.63.
  - Kicks with an 808 1.0.
  - 808 notes 4.75 a bar.
  - Slides 1.62 a bar.
  - Lead range 13, phrase length 4.
  - On-grid share 0.895, jitter 0 ms.
- Bars 1, 2, 4 and 8 were dumped and read back. Every bar is different (bar uniqueness 1.0).
- **Not heard:** nothing was rendered or listened to (no DAW in this run). Two things depend on the synth:
  - the 808 glides need portamento or legato on the 808 patch;
  - the lead was written for a short bell or pluck.
