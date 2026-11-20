# T10: revision of `flawed.mid` (8 bars, 96 BPM, A minor: Am – Am – F – F – G – G – Em – Em)

Mode: **REVISE** (improve what exists). **Protected:** the Keys chord pitches in every bar and the Lead's
pitch sequence (76 74 72 74 76 79 76 74, eight times).

## What was wrong (diagnosis, upstream first)
1. **Nothing developed (arrangement).** Every part played the same bar eight times: the drums, the lead and
   the bass and keys (one bar per chord). Nothing entered, left or built, and there was no fill or turnaround.
2. **The bass fought the kick (composition).** It never played a downbeat. Each bass note landed a 16th after a
   kick (on the "e" of 1, the "e" of 3 and the "a" of 3), so bass and kick read as a sloppy flam, not a groove.
3. **The dynamics were flat (performance, PD-FAKE-04).** Every note in every part had velocity 100: no accents,
   no ghost notes, no phrase shape, and hats as loud as the backbeat.
4. **The lead smeared (performance, PD-FAKE-03).** Two notes in every bar overlapped the next note (16
   overlaps), so a mono patch blurred the hook. All its notes were the same length.
5. **The chords were robotic.** They were block chords held to the barline with all voices identical, so there
   was no release and no voicing.

## What changed
- **Keys:** the same pitches, one chord per bar. They follow an 8-bar dynamic arc (they settle in bars 1–2,
  build through bar 4 and peak in bars 5–7). Each top voice is louder and arrives first, with the other voices
  trailing 0.6 ms per velocity step (`chord_asynchrony`, derived). Chords release just before the change
  (93–97% of the bar), and nothing is pushed across a barline.
- **Lead:** the same 64 pitches in the same order, and every bar keeps its own 8 notes. Bars 1–2 state the
  rhythm. Bars 3–8 nudge single notes by a 16th inside the bar: anticipations in bars 5–7 and delays in bar 4.
  That gives 6 distinct bar rhythms instead of 1. Overlaps were removed (16 → 0). Note lengths now articulate:
  short pickups, held arrivals and a held last note. Velocity is phrased: the phrase start is accented, the
  high G is the goal, passing notes are lighter and the 8-bar arc applies. The lead sits about 8 ms behind the
  drums (`section_offset`, set).
- **Bass (rewritten):** it plays on the downbeat with the kick on the chord roots (A, F, G, E). The roots are
  held in bars 1–2, then answer the kick in bars 3–4. Octave pops and passing tones lift bars 5–7, and bar 8
  walks up (E F# G G#) into the next A.
- **Drums (rewritten):** bars 1–2 have cross-stick and 8th hats. Bars 3–4 add the snare backbeat and ghost
  strokes, ending in a rising snare fill in bar 4. Bar 5 brings a crash and 16th hats; bars 5–7 add open hats
  on the "and" of 4 and more ghosts. Bar 8 ends with a tom run back to the top. Hats are accented on the beat
  with an uneven hand (`velocity_asymmetry`). The backbeat is +6 ms (laid back, set) and `drift_1f` adds 1.5–2 ms.
- **Unchanged:** tempo (96 BPM), 4/4, the track names, order and channels, and no program changes.

## How it was checked (`scripts/t10_revise.py`, run on the written file)
- Keys pitches per bar are identical to the original in all 8 bars. The Lead's pitch sequence is identical
  overall and bar by bar (64 notes). Both are asserted, and the build fails if either changes.
- Lead overlaps went from 16 to 0, with no same-pitch overlaps on any track. Four limbs are respected (at most
  2 hand strikes and 1 foot at a time), and the file is 8 bars long.
- Development: distinct bars went from 1 to 8 for the drums, 4 to 8 for the bass and 1 to 6 for the lead.
  Drum notes per bar rise 13 → 25 and settle to 21 in the turnaround bar.
- Velocity spread (SD) went from 0 to 20.5 (drums), 7.5 (bass), 7.7 (keys) and 5.8 (lead).
- Timing: deviations from the 16th grid average 4 ms with a 13 ms maximum, which is within the natural ceiling.
  Each deviation comes from a named model (`section_offset`, `drift_1f`, `chord_asynchrony`), not from random
  humanising.
- Not checked: how it sounds. Nothing was rendered or heard, so "sounds performed" is a reasoned claim, not a
  listening result.
