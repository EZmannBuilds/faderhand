# T05: boom-bap / lo-fi instrumental, notes

**File:** `t05_song.mid`. 60 bars, 88 BPM, 4/4, C minor.
- Tracks: `Drums` (ch 10), `Bass`, `Keys` (Rhodes-style), `Lead`.
- Section markers are MIDI marker meta events in the tempo track.
- Script: `scripts/t05.py`.

## Section map (bars) and what changes at each boundary

| Section | Bars | Harmony | What happens |
|---|---|---|---|
| Intro | 1–8 | Cm9 Abmaj9 Fm9 G7b13 | Keys alone for 4 bars. Kick, hats and bass come in at bar 5, snare at 7. Bar 8 stops on beat 3 with a lead pickup. |
| Verse 1 | 9–24 | same loop | Full groove with a crash at bar 9. The lead only answers at the end of each 4-bar phrase, leaving room for a rapper. Bar 24 has a snare fill. |
| Hook | 25–32 | Ebmaj9 Abmaj9 Fm9 G7, voiced higher | The lead hook enters. Keys play 3 stabs a bar instead of held chords. Open hat on the "&" of 4, plus tambourine, a new kick family and octave pops in the bass. Bar 32 drops the kick on the last two beats. |
| Verse 2 | 33–40 | verse loop | A different kick family and 16th hats. Keys play only every other bar. A low counter-line replaces the answers. Snare fill in bar 40. |
| Bridge | 41–48 | Abmaj7 Abmaj7 Gm9 Cm9 Fm9 Fm9 Dm7b5 G7b13 | Bars 41–44: no kick and no bass, side-stick and quarter hats only. Bass and kick return at 45 with the hook cell inverted. Bar 48 is an 8-step snare crescendo. |
| Hook 2 | 49–56 | hook loop | Crash and the fullest drums. The first half is the hook exactly. The second half moves the cell up a third and climbs to F5 before coming home. |
| Outro | 57–60 | Cm9 Abmaj9 Fm9 Cm9 | Kick only on beat 1, then the drums leave. Keys and the hook's first cell end on a held Cm9. |

## Craft decisions

- **Drums: hybrid boom-bap feel.** The grid comes from the pattern, with played timing on top (DRUMS_AND_GROOVE §1, §3):
  - 16th swing 57%
  - hats on the 8ths about 12 ms early
  - backbeat snare 11 ms behind the hats
  - 5 ms jitter
  - hat velocity in tiers (beat > "&" > 16th) with variation inside each tier
  - ghost snares that change from bar to bar
- **Bass.** Roots land with the kick: 77% of bass notes are on a kick, and every kick has a bass note. Every other bar walks up or down into the next root. All notes are detached and never overlap.
- **Keys.** Rootless minor-9th voicings at MIDI 51–70, about an octave above the bass. They are rolled bottom to top, about 14 ms per note, and sit about 10 ms behind the beat.
- **Lead.**
  - The hook is Bb–G–Bb–C, repeated with one change (the leap to Eb5), then answered in bars 3–4.
  - In the second half of each hook, the cell stays and the answer develops.
  - Long notes are sung out; off-beat pickups are lighter.
- **Voice leading.** After the first check, `scripts/p5find.py` found parallel fifths between bass and top voice: two bass walk-ups collided with a kick note, and one octave pop sat a fifth under the lead. I fixed the cause in the bass plan, and parallel fifths are now 0.0 per 100 moves.

## Sketch round (unrendered)

Three 8-bar versions of the hook are in `sketches/t05_sketch_A|B|C.mid`, with the record in `sketches/sketch_rounds.json`.
- **A, "dusty" (kept).** This became the song.
- **B, "chop" (rejected).** It passes the numbers, but keys, bass and lead are all syncopated in the same lane, and it has no hook.
- **C, straight half-time (rejected).** It is a different style: no backbeat on 2 and 4, no swing and no ghosts.

## Checks

**`midi_check.py --genre boom-bap`: 0 REVISE, 0 WARN.**

| Measure | Value |
|---|---|
| backbeat on 2 and 4 | 0.85 |
| 16th swing | 57.7 |
| ghosts per bar | 1.3 |
| grid share | 0.11 |
| jitter | 4.8 ms |
| hat velocity structure | 0.59 |
| hat velocity SD | 14.2 |
| snare velocity SD | 32.5 |
| snare behind hats | 11.1 ms |
| arrangement changes at 8-bar boundaries | 6 |
| density CV | 0.37 |

`--genre lofi` also gives 0 REVISE (bass stepwise share 0.26).

I read back bars 8, 25 and 41 (intro stop, hook entry, bridge breakdown).

**Not done:** no render and no listening. Sounds are unassigned.
