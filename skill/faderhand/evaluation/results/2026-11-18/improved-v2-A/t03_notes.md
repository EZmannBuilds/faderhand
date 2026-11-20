# T03 – Atlanta trap loop (8 bars, 140 BPM, G minor)

**File:** `t03_trap.mid`. Tracks: `Drums` (ch 10), `808`, `Lead`. 480 PPQ, tempo and 4/4 in track 0.

## Intent (locked, "just make it")
Dark minor trap at 140, programmed feel. Harmony moves slowly, one chord per 2 bars:
Gm | Eb | Cm | D. The D is the harmonic-minor V, so the loop pulls back to Gm.

## Sketch round (unrendered, so the decisions are provisional)
I built three 8-bar versions that differ by mechanism and measured each with `midi_check.py --genre trap`.
The files are in `scripts/sketches/`.
- **A – bounce + call-and-response bell.** Kick moves every bar, the 808 is locked to it with octave jumps,
  and a short detached bell cell gets an answer. 0 REVISE.
- **B – 8th-triplet arp over an 8th-hat bed**, with an 808 that slides on every pickup. 2 REVISE: the arp
  never breathes (45-note phrases), and there are too many slides (3.9 a bar), which smears the low end.
- **C – sustained pad-lead over a busy, fully locked 4-kick pattern.** Passes, but the lead is a held line,
  not a trap topline, and the dense kick takes the bounce out.

**Kept: A.** It is the only one where the drums, 808 and lead each carry the genre's mechanism: half-time
backbeat, rolls as gestures, a kick-locked 808 that moves by pitch, and a short detached hook. This choice
comes from the measurements plus reasoning. Nobody has listened to it.

## What's in it, and why
- **Drums (programmed, quantized, fixed tiers):**
  - Clap and snare layered on beat 3 in every bar (half-time).
  - Hats: an 8th bed with 16th pairs, in three shallow tiers (100/88/76). Bar 5 switches to straight 16ths
    for lift.
  - Rolls about every other bar, always rising in velocity and landing on a strong beat:
    - bar 2: 32nds on beat 4;
    - bar 4: 16th-triplets on beat 4;
    - bar 6: a 32nd-triplet into a 32nd run into the beat-3 clap;
    - bar 8: a long 32nd-triplet then 32nd build into the loop.
  - Open hats on the "&" of 4 in bars 3 and 7.
  - The kick changes every bar: 0/10, 0/6/11, 0/3/10, 0/7/10/13 and so on. Bar 4 adds a snare pickup.
  - Bar 8 drops the kick after beat 2 so the roll reads.
- **808:**
  - Every kick has an 808 note (kick_with_low 1.0). Movement comes from octave jumps on the second or third
    kick of the bar.
  - Four pickups between kicks, each overlapping the next note so a legato or portamento 808 glides: F→Eb,
    Bb→C, B→D (leading tone), A→D.
  - The notes hold to the next note (gate about 1). The roots stay in MIDI 26–39, so the fundamental sits
    under about 80 Hz.
  - Bar 8: the 808 jumps up an octave, then stops on beat 4 under the roll (a drop).
  - Sound note: use a sine or slightly driven 808 with high sustain. Legato doesn't restart a decaying
    envelope.
- **Lead (bell or pluck, G4–A5, range 14 semitones):**
  - A 4-note cell (D-F-D-C, rhythm 0/3/6/7 in 16ths) with a falling reply.
  - Restated over Eb with one change (the leap reaches G5).
  - Sequenced up over Cm (Eb-G-Eb-D).
  - The 4th statement over D answers the first three (F#-A-F#-E), then falls chromatically E-Eb-D into the
    loop.
  - Notes are detached (gate about 0.6), with a rest every bar. The median phrase is 4 notes.
- **Originality:** written from scratch for this brief. No melody, bassline or drum pattern was taken from
  a reference or a known song.

## Checks
- `midi_check.py --genre trap` on the final file: **0 REVISE**.
  - half-time 1.0; rolls 0.5 a bar, all rising;
  - 808 on kick 0.85; kick with 808 1.0; 808 notes 3.4 a bar; slides 1.9 a bar;
  - lead range 14; phrase 4 notes; grid share 0.88; jitter 0.
- Read back bars 1, 4 and 8 of the 808 and lead (note dump): the slides overlap, the drop stops at beat 4,
  and the lead rests every bar.
- **Not heard:** nothing was rendered or listened to. No DAW or renderer was used. Next step: render on a
  real 808 with glide on, and check that the slides and the bar-8 drop land.
