# T05 – Boom-bap / lo-fi instrumental: notes

**File:** `t05_song.mid` is 64 bars (about 2:55) at 88 BPM in F minor, 480 PPQ. It has four tracks: `Drums` on channel 10, `Bass`, `Keys` (EP), and `Lead` (a flute-like voice). The sections are marked with MIDI marker events.

## Section map, written before the notes
At least two things change at every boundary.

| Bars | Section | Harmony (one chord a bar) | What plays | Boundary gesture in the bar before |
|---|---|---|---|---|
| 1–8 | Intro | Fm9 Dbmaj7 Bbm9 C7b9 | Bars 1–4: keys alone, getting louder. Bars 5–8: hats and rim enter. Bass enters in bar 7. | Bar 8: rising snare pickup. |
| 9–24 | Verse 1 | same | Full kit (kick, snare, swung hats, ghosts), bass roots on the kick with walk-ups, swung keys comp with a push every 4th bar | Bar 24: snare fill, hats thinned. Crash on bar 25. |
| 25–32 | Hook | Dbmaj9 Eb6 Cm7 Fm9 | The lead hook enters. The keys hold longer chords. Busier kick, an octave pop in the bass, open hats on the "&" of 4. | Bar 32: snare-tom fill, backbeat removed from beat 4. |
| 33–40 | Verse 2 | verse chords | The lead drops out except for answer phrases in bars 36 and 40. The kick drops out for a bar (37). | Bar 40: tom fill. |
| 41–48 | Bridge | Gbmaj7#11 Fm7 Ebm9 Ab13 | Half-time drums (snare on 3, quarter-note hats), whole-note keys, long bass notes, a new lead line built from the hook's intervals | Bar 48: stop-time (one hit on beat 4). Ab13 resolves to the hook's Db. |
| 49–56 | Hook | hook chords | The hook returns, pitch for pitch the same as bars 25–32 (checked). It is a little louder, with a 16th shaker for lift. | Bar 56: fill. |
| 57–64 | Outro | Fm9 Dbmaj7 Bbm9 Fm(add9) | Bars 57–60: drums, bass, keys and hook fragments. Bars 61–64: keys alone on held chords, plus one last fragment. | Ends on Fm(add9). |

## Sketch round (unrendered, the hook section, 8 bars each, `midi_check --genre boom-bap`)
| Sketch | Mechanism | Measured | Verdict |
|---|---|---|---|
| A | Swung comp keys, a stepwise flute hook, bass roots on the kick with walk-ups | Lead steps 0.62, chord tones 0.84, contrary motion 0.38, bass on the kick 0.65 | **Built** |
| B | Dusty minimal: one keys stab a bar, a vibes motif in triplets, the bass doubling the root | Lead steps 0.11, lead bar uniqueness 0.38 | Too static for a hook |
| C | A walking 8th-note bass, keys on 2 and 4, long-tone lead | Bass on the kick 0.28, lead phrase of 1 note | Loses the boom-bap kick-and-bass lock |

## Hook craft
- **The cell:** Ab–C–Bb–Ab over Dbmaj9.
- **Developed:**
  - repeated a step lower over Eb6;
  - re-rhythmed and rising over Cm7;
  - answered by a descent to F over Fm9;
  - repeated exactly in bars 5–6;
  - given a higher peak in bar 7 (the leap is recovered by step);
  - answered by a longer run in bar 8.
- **The bridge line** reuses the hook's intervals over new harmony. **The outro** keeps only the cell's first two notes (fragmentation).

## Measured (final file): 0 to revise
- **`midi_check.py --genre boom-bap`:**

  | Check | Value |
  |---|---|
  | Swing | 59.1 |
  | Backbeat on 2 and 4 | 0.70 of bars (the intro and half-time bridge are deliberate) |
  | Ghosts per bar | 0.67 |
  | Share of notes on the grid | 0.25 |
  | Drum jitter | 6 ms (a tight, hybrid take) |
  | Hat velocity structure | 0.59 |
  | Snare behind the hats | 14 ms |
  | Arrangement block changes | 6 of 7 boundaries |
  | Density CV | 0.46 |
  | Bar uniqueness | 0.94 |
- **`--genre lofi`:** also 0 to revise (bass stepwise share 0.27).
- **Voice leading:** contrary motion in the outer voices is 0.32.
  - The first build had 4.7 parallel fifths per 100 moves, from Bbm9→C7b9 with F over Bb going to G over C.
  - I revoiced C7b9 (G-Bb-Db-E), and parallel fifths dropped to 0.
- **Other revisions:**
  - Bar 48 first came out with three extra kicks. I rewrote it as a real stop-time bar.
  - Bar 7 of the hook first leapt up a 5th and then kept rising. The leap is now recovered by step.

## Not done
- Nothing was rendered or listened to (no DAW, by the runner rules). The balance, the keys' tone and whether the lo-fi texture works are unjudged.
- There is no vinyl, noise or sample layer: this is MIDI only.
