# T05: Boom-bap / lo-fi instrumental. Notes

**File:** `t05_song.mid`. 72 bars (about 3:16), 88 BPM, 4/4, G minor, 480 PPQ. Section starts are marked with MIDI
marker meta events. Tracks: Drums (channel 10), Perc Shaker (channel 10), Bass (channel 2), Keys (channel 3), Lead
(channel 4).

## Form

| Section | Bars | Function | What is new or removed |
|---|---|---|---|
| Intro | 1–4 | establish | Rhodes alone. Hats and a rim click enter in bar 3, and a kick plus snare pickup comes in bar 4 |
| Verse 1 | 5–20 | groove; room for a rapper | Full kit, bass and Rhodes stabs. The lead stays silent until a pickup in bar 20 |
| Hook 1 | 21–28 | reveal the hook | Moves to the relative major (Cm9–F13–Bbmaj9–Ebmaj7/D7alt). Adds the flute hook, a crash, a 16th shaker, busier comping and open hats |
| Verse 2 | 29–44 | develop | Ghost snares and bass pickups. The keys anticipate the D7. The flute answers at the ends of phrases and builds into the hook |
| Hook 2 | 45–52 | restate | Same hook melody, plus a 16th hat lift and bass octave pops |
| Bridge | 53–60 | strip down, then rebuild | New harmony (Abmaj7#11–Gm9–Fm9–Bb13–Ebmaj9–Am7b5–Abmaj7–D7). Half-time drums and held chords for 4 bars, then quarter-note comping and a tom fill. The lead plays the hook motif slower, in long notes |
| Hook 3 | 61–68 | climax | The hook's second half is varied, with a 16th turn, a new peak at Bb5, and keys a little louder |
| Outro | 69–72 | release | The drums thin out and stop. A last flute fragment holds D5 while the tempo slows (final ritard) |

## Harmony and material
- **Verse loop:** Gm9 | Cm9 | Ebmaj9 | D7(b9). Rootless Rhodes voicings between Bb2 and A3, voice-led by step.
- **Hook:** a ii–V–I lift into Bb. The motif is D–Eb–D–Bb: a neighbour tone, then a falling third. The four hook
  phrases all differ, and phrase 3 restates the call and climbs to G5.
- **Bridge:** opens on the bII colour, Abmaj7#11, then walks home to D7.
- **Bass:** follows the kick, with a fifth on the 'and' of 3 and a chromatic approach into each chord change. It walks
  D–F#–A–C on the D7 bars, plays one long root per bar in the half-time bridge, and holds the final chord.

## Performance
- **Every value here is set for this style, not measured.**
- **Shared swing:** 16th swing, with offbeat 16ths at 60% of the 8th, applied to every part.
- **Section offsets:** kick 0 (the anchor), snare +2% of a beat (a lazy backbeat), bass +1%, keys +1.5%, lead +1%.
- **Timing spread:** tightness SD of 0.8–1.0% of a beat. A pink-noise tempo drift adds at most ±0.5%.
- **Rhodes:** voices are slightly staggered by velocity, the way a hammer action plays.
- **Flute:** velocity and expression (CC11) rise to each phrase's peak and fall after it. Each phrase ends with a
  breath.
- **Ending:** the tempo slows over the last 8 beats along a parabolic curve, from 88 to 74 BPM.

## Checks (`scripts/validation_log.txt`)
- **File:** 480 PPQ, tempo and time signature present, 8 markers, every track named, both drum tracks on channel 10,
  no pitched track on channel 10, no hanging notes.
- **Four limbs:** the kit passes. The shaker is a second player's overdub on its own track.
- **Lead melody variety:** pass. 17 lines, 14 distinct rhythms, commonest rhythm 12% of lines, 4% repeated pitches,
  and a breath at every line end.
- **Contrast audit:** notes per bar change by section (`scripts/t05_sections.py`).
  - Drums: 5 in the intro, 14 in verse 1, 18 in hook 1, 20 in hooks 2–3, 11 in the bridge, 6 in the outro.
  - Keys: 4, 8, 16, 10 and 4 respectively for intro, verse, hook, bridge and outro.
- Not listened to. There was no render, so nothing here claims how the mix balances or how it sounds.
