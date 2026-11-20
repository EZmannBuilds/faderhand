# T03: trap loop, notes

**File:** `t03_trap.mid`. 8 bars, 140 BPM, 4/4, G minor. Tracks: `Drums` (ch 10), `808` (ch 1), `Lead` (ch 2).
**Script:** `scripts/t03.py`.

## What it is

- **Harmony.** Implied by the 808 and the lead: Gm (bars 1–2) → Eb (3) → D (4), then Gm (5–6) → Eb (7) → D (8). That is about one change every two bars, which is how trap moves.
- **Drums.** Programmed, quantized and in velocity tiers, because trap is a programmed genre (DRUMS_AND_GROOVE §1).
  - Snare and clap together on beat 3 of every bar (half-time).
  - The kick anchors beat 1, and its second and third hits move from bar to bar: steps 7/10, 3/10, 6/11/14 and so on.
  - Hats are 8ths, with 16th passages and open hats on the "&".
  - Four rolls in 8 bars (bars 2, 4, 6 and 8). Each one rises in velocity into the next strong beat. Three types: 32nds, 16th triplets in bar 4, and 32nd triplets into the loop point in bar 8.
  - Bar 4 adds a snare pickup into the second half.
  - Bar 8 drops the kick after beat 2 and adds a rising 32nd snare figure, so the loop restart lands.
  - Crashes fall on bars 1 and 5.
- **808.** Locked to the kick first: every kick has an 808 under it, and 90% of the 808 notes land on a kick (LOW_END §1, "lock first").
  - Movement comes from octave jumps (G1↔G2, D2↔D1, Eb1↔Eb2) and from slides.
  - Slides are written as overlapping notes (about one per bar), not pitch bend. Two examples: an F1 pickup slides down into Eb in bar 3, and the F#1 leading tone slides up into G in bar 5.
  - The range is D1–G2. Set the synth to legato/portamento with high sustain, so slid notes don't fade (vital/README "Traps").
- **Lead.** Bell or pluck, gate about 0.7 (detached), range F#4–G5 (13 semitones).
  - The hook is a 3-note neighbour cell, D–Eb–D. Bar 2 repeats it with one change (it climbs to F). Bar 3 peaks on G5 and steps down to the maj7 of Eb. Bar 4 answers, falling to the F#4 leading tone.
  - Bar 5 states the cell exactly, for recognition.
  - Bar 6 fragments it and adds a new tag. Bar 7 sequences it up a step. Bar 8 answers again and leaves the loop open on the dominant.
  - There is a rest in every bar.

## How it was chosen (sketch round, unrendered)

I wrote three 4-bar sketches that differ by mechanism. They are in `sketches/t03_sketch_*.mid`, and the record is in `sketches/sketch_rounds.json`.

- **A, locked:** strong hook and lock, but 0 slides.
- **B, bounce:** pickups and slides, but 5.75 slides per bar and a 48-note arp instead of a hook.
- **C, space:** no rolls, 2 808 notes per bar.

I recombined A's hook, kick plan and lock with B's slide pickups and triplet roll type. These decisions were made by the director provisionally, from measurements and reasoning. Nothing was heard.

## Checks

`midi_check.py --genre trap` gives **0 REVISE**:
- half-time 1.0
- rolls 0.5 per bar, all rising
- 808 notes on kicks 0.90, kicks with 808 1.0
- 3.6 808 notes per bar, 1.0 slide per bar
- lead range 13, 4 notes per phrase
- grid share 0.91, jitter 6.0

The jitter figure comes from the triplet rolls, which sit off the 16th grid on purpose. Read back bars 1, 4 and 8 note by note.

**Not done:** no render and no listening, because no DAW or synth is connected. Sounds are unassigned (General MIDI placeholders), so nothing about timbre or balance is verified.
