# T10 – revision of `flawed.mid` (T09 protection included)

**File:** `t10_revised.mid`. It has the same four parts (`Drums` on ch 10, `Bass`, `Keys`, `Lead`), the same
tempo (96 BPM), 4/4 and 480 PPQ.

## What was wrong (diagnosis, measured)
- **Every note at velocity 100.** That's 1 distinct velocity across all 216 notes. `midi_check.py` flags it
  (REVISE): flat velocity is the most common machine tell.
- **Everything exactly on the grid.** No placement, no swing, and the snare isn't behind the hats.
- **Nothing develops.** The drums repeat one bar 8 times (bar-pattern uniqueness 0.12). So does the lead
  (0.12), with identical rhythm, length and dynamics every bar. Bass and keys only change when the chord
  changes.
- **The bass fights the kick.** All 24 bass notes sit on off-16ths (steps 1, 9, 11), and none land with a
  kick (`midi_check` WARN: 0% on kick). That smears the low end and gives the groove no anchor.
- **The lead's durations overlap.** The 2nd note of each bar runs into the 3rd. The note before the rest is
  the same length every time.

## Protected (listed before editing)
- **Keys:** the pitch set of every bar. Am (57-60-64) in bars 1–2, F (53-57-60) in 3–4, G (55-59-62) in 5–6,
  Em (52-55-59) in 7–8.
- **Lead:** the hook's pitch sequence, E-D-C-D-E-G-E-D eight times (64 notes).
- **Also kept:** tempo, meter and track names.

## What I changed (in the skill's order: velocity, timing, duration, then variation)
1. **Keys:**
   - Same pitches, played and rolled bottom-up by 6–12 ms, a little behind the beat. They never cross back
     over the bar line, so each bar's pitch set stays in its bar.
   - A dynamic arc over the 8 bars, with the top voice a little louder.
   - The rhythm develops:
     - bars 1 and 3: held statement;
     - bars 2 and 4: a re-strike on the "&" of 3;
     - bars 5–6: a comping pulse on 1, the "&" of 2 and the "&" of 3;
     - bar 7: a busier pulse at the peak;
     - bar 8: it breathes before the loop.
2. **Lead:**
   - The same 64 pitches in the same order.
   - Velocity is shaped inside the phrase (the downbeat E and the peak G strongest, passing C and D
     lighter) and across the 8 bars: it rises from mp to a peak in bar 7, then falls back.
   - Timing sits slightly behind the beat, with off-16ths a little late, and never before its own bar line.
   - Durations: the overlap is fixed. The slurred D-C stay legato, and the note before the rest grows from
     short (bars 1–4) to long (bars 5–8).
   - Small rhythm placements in the second half and at phrase ends:
     - bar 4 and bar 8: the last D comes a 16th early and is held to the bar line, like a phrase-end rhyme;
     - bar 6: the peak G is anticipated by a 16th;
     - bar 7: the E anticipates beat 3.

     Bars 1–3 and 5 keep the original rhythm, so the hook is stated before it is varied.
3. **Drums:** rewritten as a played pocket. These measurements are from `midi_check.py`:
   - snare 12 ms behind the hats; light 16th swing (55.7%); jitter about 4.7 ms; no note more than 22 ms
     off its position;
   - hats in three velocity tiers with variation;
   - ghost notes that change from bar to bar.

   Development:
   - bars 1–4: 8th hats, and the kick moves between 0/10 and 0/7/10;
   - bar 4: an open hat and a snare pickup;
   - bar 5: a crash, then 16th hats and open hats in bars 6–7, with louder backbeats;
   - bar 8: a tom fill back to the top.
4. **Bass:**
   - Rewritten on the same chord roots (A, F, G, E). It's locked to the kick: notes shared with a kick take
     the kick's real timing.
   - Approach notes at the end of bars 2–8 (bar 1 stays sparse):

     | Bar | Approach |
     |---|---|
     | 2 | G→F |
     | 3 | C→F |
     | 4 | F#→G |
     | 5 | A→G |
     | 6 | F→E |
     | 7 | G→E |
     | 8 | G#→A, back to the top of the loop |
   - An octave pop in bar 4, and it gets busier and louder in bars 5–8.

## How I checked it
- **`t10_verify.py` (protected-material diff):** Keys pitch sets per bar are **identical**. The Lead pitch
  sequence is **identical** (64 notes, same order). Tempo and part names are unchanged.
- **`midi_check.py`:**
  - The original gets 1 REVISE (flat velocities) and 1 WARN (bass 0% on kick).
  - The revision gets **0 REVISE** with `--genre hiphop-live` (closest live-feel profile at 96 BPM) and
    with `generic`.
  - Revised numbers: backbeat 1.0; swing 55.7; ghosts 1.5 a bar; grid share 0.11; hat structure 0.77;
    hat SD 14.8; snare SD 30.7; snare 12.1 ms behind the hats.
- **Variation (bar-pattern uniqueness, before → after):**

  | Part | Before | After |
  |---|---|---|
  | Drums | 0.12 | 1.0 |
  | Bass | 0.5 | 1.0 |
  | Keys | 0.5 | 0.88 |
  | Lead | 0.12 | 0.5 |

  The lead stays repetitive on purpose, because its pitches are protected.
- **Distinct velocities, before → after:**

  | Part | Before | After |
  |---|---|---|
  | Lead | 1 | 33 |
  | Keys | 1 | 25 |
  | Bass | 1 | 20 |
  | Drums | 1 | 70 |

- **Counterpoint:** no parallel fifths between the outer voices (`p5_find.py`).
- **Read back:** dumped the lead in bars 1, 4, 6 and 8. The first note of bar 1 starts at tick 12, after the
  bar line, and the moved notes sit where intended.
- **Not heard:** nothing was rendered or listened to. These are measurements and a note-by-note read only.
