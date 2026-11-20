# T10: revision of `fixtures/flawed.mid`, notes

**File:** `t10_revised.mid`. 8 bars, 96 BPM (unchanged), 4/4. Tracks: `Drums` (ch 10), `Bass`, `Keys`, `Lead`.
**Script:** `scripts/t10.py`.

## What was wrong (measured with `midi_check.py`, and by reading the notes)

- **Every note was velocity 100.** There was 1 distinct velocity in the file.
- **Every note sat exactly on the grid.** Grid share was 1.0 and jitter 0.
- **No bar developed.**
  - The lead played the same 8-note bar 8 times (lead bar uniqueness 0.125).
  - The drums played one bar 8 times (0.125), with no ghosts, no fills and no hat dynamics.
  - The chords were whole-note blocks at a single velocity.
- **The bass flammed the low end.** All 24 bass notes sat a 16th *after* a kick (0% of bass notes on a kick, 0% of kicks with a bass note). The parts were also all the same length, and each 2-bar bass figure repeated unchanged.

## Protected material, and how it was kept

- **What was protected:**
  - the chord pitches of every bar: Am | Am | F | F | G | G | Em | Em, as written in `Keys`;
  - the lead's 64-pitch sequence: 76 74 72 74 76 79 76 74, eight times.
- **How the script keeps them.** It reads both from the fixture itself; nothing is retyped. Then it builds the new parts and reads the written file back.
- **Two assertions on the read-back file:**
  1. each bar's Keys pitch set equals the original's;
  2. the Lead pitch sequence, in onset order, equals the original 64 pitches.
- **Bar lines.** Both pass. A third check confirms that no lead note crossed a bar line: lead and chord placements are only ever *late*, so no downbeat slips into the previous bar.

## What changed (DRUMS_AND_GROOVE, ARRANGEMENT_AND_REVISION §5 order: velocity, then timing, then length, then variation)

- **Drums: rewritten as a played part.**
  - Hats are in tiers by position (beat > "&" > 16th), with variation inside each tier. Snare backbeat is 8.5 ms behind the hats. Light 16th swing (54.5%), 5 ms jitter.
  - The arc across the 8 bars:
    - bars 1–2: 8th hats and kick, soft;
    - bars 3–4: 16th pickups and the first ghost notes, then a snare pickup in bar 4 into the second half;
    - bar 5: a crash, and 16th hats from here on;
    - bars 6–7: open hats on the "&"; bar 7 has the busiest kick;
    - bar 8: a snare-and-tom fill into the loop.
  - The kick anchors beat 1, and its second hit moves between bars.
- **Bass.**
  - Re-locked to the kicks: 71% of bass notes on a kick, 100% of kicks with a bass note.
  - Chromatic or step approaches into every chord change (G→F, F#→G, F#–F→E, G#→A at the loop).
  - Octave or fifth pops in bars 4 and 6, and more activity in the second half.
  - No overlaps.
- **Keys: same pitches, new rhythm and touch.**
  - Bars 1–2 are held. Bars 3–4 re-attack once. Bars 5–7 comp (2–4 short hits). Bar 8 holds, then a soft re-attack.
  - Each chord is rolled bottom to top (9 ms per note), sits 6–14 ms behind the beat, and the top voice is a little louder.
  - Every hit stays inside its own bar, so each bar's pitch set is exactly the original's.
- **Lead: same 64 pitches in the same order. Placement, length and dynamics develop.**
  - Bars 1–4 are mp. Bars 5–7 are louder. Bar 8 eases off.
  - The first note and the high G are accented.
  - Bar 2 is detached, with a breath before bar 3.
  - Bar 3 anticipates beat 3 by a 16th. Bar 4 pulls its tail back. Bar 6 re-spaces two notes. Bar 7 is the most syncopated, with the peak note pushed a 16th early. Each of these moves is at most one 16th.
  - All notes are laid back by 2–12 ms, with the original overlap removed (monophonic).
- **Voice leading.** One parallel fifth between the bass and the top voice in bar 7 came from my new bass line. I fixed it by changing one approach note (G→F#). Parallel fifths are now 0.

## How it was checked

**`midi_check.py`: before and after.**

| Measure | flawed | revised |
|---|---|---|
| distinct velocities | 1 | 79 |
| grid share | 1.0 | 0.12 |
| drum jitter (ms) | 0 | 5.0 |
| hat / snare velocity SD | 0 / 0 | 17.6 / 28.8 |
| snare behind hats (ms) | 0 | 8.5 |
| bass notes on kicks / kicks with bass | 0 / 0 | 0.71 / 1.0 |
| bar uniqueness (all / drums / bass / lead) | 0.5 / 0.125 / 0.5 / 0.125 | 1.0 / 1.0 / 1.0 / 0.625 |
| lead velocity SD | 0 | 9.1 |
| parallel fifths per 100 moves | n/a | 0.0 |

- `--genre rock` (the closest played-backbeat target): 0 REVISE.
- `--genre generic`: 0 REVISE.
- The protected-material assertions pass, and I read back bars 1, 5 and 8.

**Not done:** no render and no listening.
