# T10: revision of `flawed.mid` (A minor, 96 BPM, 8 bars)

**File:** `t10_revised.mid`. It keeps the same four tracks, names, channels and tempo as the original. I also added two section markers.

## What was wrong
Measured with `midi_check.py --genre rock` and by reading the notes:

- **Flat velocities:** every note in every part had velocity 100 (1 distinct value).
- **Fully quantized:** on-grid share 1.0, jitter 0 ms, and the snare sat exactly with the hats.
- **Nothing developed:**
  - every drum bar was identical (drum bar uniqueness 0.125);
  - the lead played the same bar 8 times (lead bar uniqueness 0.125);
  - the bass and keys changed only when the chord did;
  - there were no fills or section gestures.
- **The bass flammed the kick:** it played a 16th after every kick (steps 1, 9, 11 against kicks on 0, 8, 10), so 0% of bass notes landed on a kick and 0% of kicks had a bass note.
- **The keys were block whole notes at the same volume as the lead.**
- **Two lead notes overlapped:** step 2 rang into step 3.

## What I changed
**Protected material: the pitches were read from the fixture, not retyped.**

- **Keys:** the same 3 notes in every bar.
  - A small bottom-up roll, and never before the bar line.
  - The top voice is louder, and the keys sit under the lead (55–75 against the lead's 72–112).
  - Bars 5–6 are half-bar chords so the G section breathes. The other bars are legato.
- **Lead:** the same 64 pitches in the same order, 8 per bar, and no note crosses a bar line. The hook stays exact in pitch; only its rhythm, phrasing and dynamics develop:

  | Bars | What the lead does |
  |---|---|
  | 1–2 | The statement as written. Bar 2's last note is held to end the phrase. |
  | 3–4 | Detached. The 5th note (and in bar 4 the peak too) moves an off-16th early, as an anticipation. |
  | 5–6 | New section, more space: off-beat entries, and bar 6 starts late. |
  | 7 | The climax. The peak (G5) comes early and is held. |
  | 8 | The cadence. Everything comes earlier and the last note rings to the end. |

  - Velocity follows a 2-bar phrase arc that peaks on G5, and the second half is louder.

**Free parts:**

- **Drums:** played pop-rock with a build.
  - Bars 1–4: 8th hats in three velocity tiers. A ghost and a 16th hat come in, then an open hat and a tom fill in bar 4.
  - Bar 5: crash, then ride 8ths for bars 5–6. Bar 7: 16th hats.
  - Bar 8: the hats thin out, then a snare-to-toms crescendo fill from beat 3.
  - The kick pattern varies across the 8 bars (5 different patterns).
  - The backbeat sits about 14 ms behind the hats, with jitter of about 7 ms.
- **Bass:** locked to the kick (51% of bass notes on a kick, 96% of kicks with a bass note).
  - Bars 1–4: roots with walk-ups into each chord change (G to A, C3–G2 into F, F#2 into G).
  - Bars 5–6: driving 8ths for the lift.
  - Bars 7–8: Em, then a walk F#2–G#2 that leads back to A.

## How I checked it
- **Protection (T09):** the script compares the revised file against the fixture.
  - Keys pitches per bar are identical (24 notes in, 24 out).
  - The lead pitch sequence is identical, per bar and overall (64 in, 64 out).
  - Result: `True`.
- **`midi_check.py --genre rock`:** 6 REVISE before, 0 after.

  | Measure | Before | After |
  |---|---|---|
  | on-grid share | 1.0 | 0.28 |
  | jitter | 0 ms | 7.1 ms |
  | snare behind the hats | 0 ms | 13.8 ms |
  | hat velocity SD | 0 | 13.8 |
  | snare velocity SD | 0 | 29 |
  | distinct velocities | 1 | 70 |
  | bar uniqueness | 0.5 | 1.0 |
  | drum and bass bar uniqueness | 0.125 / 0.5 | 1.0 |
  | lead bar uniqueness | 0.125 | 0.875 |

- **`--genre generic`:** 0 REVISE.
- **Read back:** bars 1, 5 and 8.
- **Deliberate:** parallel fifths between the outer voices measure 3.7 per 100 moves. They come from the bass doubling roots and fifths under the hook, which is normal in pop-rock and not a counterpoint error.
- **Not heard:** nothing was rendered or listened to.
