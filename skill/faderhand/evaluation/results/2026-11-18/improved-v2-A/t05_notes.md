# T05 – boom-bap / lo-fi instrumental (60 bars, 88 BPM, Eb major / C minor)

**File:** `t05_song.mid`. Tracks: `Drums` (ch 10), `Bass`, `Keys`, `Lead`. 480 PPQ. Tempo, 4/4 and section
markers are in track 0. At 88 BPM, 60 bars run about 2:44.

## Section map (written before any notes)
Each boundary changes at least two things: layers, density, register, drum pattern or harmony. Every
boundary also has a gesture in the bar before it.

| Bars | Marker | Harmony | What changes / gesture into it |
|---|---|---|---|
| 1–8 | Intro | verse loop: Fm9 – Bb13 – Ebmaj9 – Cm9 – Fm9 – Bb13 – Ebmaj9 – C7b9 | Keys alone (held, rolled). Hats and side-stick from bar 5. The lead foreshadows the hook head in bars 7–8. A snare drag on beat 4 of bar 8. |
| 9–24 | Verse 1 | verse loop ×2 | Full kit, bass enters, keys comp in a chop-like 3-hit pattern. The lead is silent for 8 bars, then gives short answers at the end of each 2-bar phrase. Hats go to 16ths in bars 17–24. A tom fill in bar 24. |
| 25–32 | Hook | Abmaj9 – Gm11 – Fm9 – Bb13sus – Abmaj9 – Gm11 – Cm9 – Bb13 | New harmony, the hook melody, open hats, a crash, held keys. A drop in bar 32 (no kick in its second half). |
| 33–40 | Verse 2 | verse loop | A walking quarter-note bass, offbeat keys stabs, a new kick pattern, and the lead as a low counter-line (Ab3–D5). The band stops on beat 3 of bar 40, then a snare drag. |
| 41–48 | Bridge | Dbmaj9 – Cm9 – Bbm9 – Eb9 ×2 (ends Eb7b9 = V of Ab) | Kick nearly gone, ride instead of hats, side-stick backbeat, a bass pedal-like root and fifth, and held keys in a higher register. The lead fragments and sequences the hook head, speeding up (diminution) in bars 47–48. A 16th snare build. |
| 49–56 | Hook 2 | hook progression | 16th hats, a busier kick, and bass with fifths and octave pops. The keys add an extra push. The hook is exact for 6 bars, then a new ending climbs to C6 and resolves on Eb5. A tom fill. |
| 57–60 | Outro | Fm9 – Bb13 – Ebmaj9 (held) | Drums thin out for 2 bars, then stop. The lead plays the hook cell in augmentation and the final Ebmaj9 rings. |

## Sketch round (unrendered, so the decisions are provisional)
Before the full build I wrote the hook (8 bars) three ways, each with the same lead, and measured each with
`midi_check.py --genre boom-bap`. The files are in `scripts/sketches/t05_hook_sketch_*.mid`.
- **A – chopped Rhodes over boom-bap.** The bass sits on the kick; open hats on the "&" of 4. 0 REVISE.
- **B – jazz-trio mechanism.** Walking quarter bass, offbeat keys stabs, and a stop on beat 3. 0 REVISE.
  It's busier under the lead.
- **C – minimal dusty.** Ride, side-stick, held chords and a pedal bass. 2 REVISE: there are no ghosts and
  the snare is flat. Too static to carry a hook.

**Decision: KEEP A as the core groove for verse 1 and the hooks, and RECOMBINE.**
- B's walking bass and offbeat stabs become the contrast for verse 2.
- C's held-chord, ride and side-stick texture becomes the bridge, where stillness is the point.

The basis is measured plus inferred. Nobody listened.

## Performance (how it is played)
- **Drums: hybrid boom-bap feel, as a played take.**
  - 16th swing 57.5%.
  - The snare sits about 12 ms behind the hats; the kick is slightly early.
  - Jitter of about 4–5 ms SD, with no note more than 24 ms from its position.
  - Hats in three velocity tiers with variation inside each tier, never under 32.
  - Ghosts (26–52) on the "a" before backbeats and the "e" after them, a different set in each bar of the
    4-bar cycle.
- **Bass:** onsets that share a kick take that kick's actual time, so the low end doesn't flam. Other notes
  swing with the hats. Walk-ups come at the end of every 2-bar phrase.
- **Keys:** rootless 4-voice voicings (3-5-7-9 colours), voice-led, kept at MIDI 53–72 under the lead,
  played slightly behind the beat and rolled bottom-up.
- **Lead:** placed a little behind the beat, off-16ths swung. Phrase peaks are louder and short notes
  lighter.

## Checks
- **`midi_check.py --genre boom-bap`: 0 REVISE.**
  - backbeat 0.91; swing 57.5; ghosts 1.1 a bar;
  - grid share 0.12; jitter 4.4 ms;
  - hat structure 0.70; hat SD 14.5; snare SD 31.4; snare 12.6 ms behind the hats.
- **`--genre lofi`: 0 REVISE.** Bass step share 0.18.
- **Arrangement:** 6 of 7 eight-bar boundaries change (at least 3 needed); density CV 0.41; bar uniqueness 0.98.
- **Low end:** 0.73 of bass onsets land on a kick, and 0.83 of kicks have a bass note.
  The chord bottom sits about 2 octaves over the bass median.
- **Counterpoint:** the first build had 4.7 parallel fifths per 100 outer-voice moves, from two causes:
  - Hook bars 1→2 and 5→6: the lead's Eb→D ran parallel to the bass's Ab→G. I changed the lead's note on
    the Gm11 bars (F5, and a Bb4 restart in bar 30).
  - Keys top voices a fifth over the bass at the bridge and hook-2 boundaries. I added a voicing rule
    against that.

  After both fixes: **0 parallel fifths**; contrary motion 0.36; lead step share 0.48; leap recovery 0.59;
  lead chord-tone share 0.76.
- **Read back:**
  - the marker text and positions;
  - the track names, tempo and meter;
  - the notes at bars 1, 8, 9, 24, 25, 41, 48, 49 and 60 (downbeats slightly early by design; bass
    downbeats ride with the kick).
- **Not heard:** nothing was rendered or listened to. These are measurements and a bar-by-bar read only.
  Worth checking by ear:
  - whether the verse-2 walking bass sits well under the low counter-line;
  - the level of the hook-2 climb to C6.
- **Originality:** all material is original to this brief. No sample, melody or pattern came from a known
  record.
