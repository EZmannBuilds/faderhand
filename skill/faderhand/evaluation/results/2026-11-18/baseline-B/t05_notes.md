# T05: boom-bap / lo-fi instrumental (56 bars, 88 BPM, Db major with Bb-minor colour)

**Brief, as locked:** an original instrumental of at least 48 bars at 88 BPM. It needs an intro, verses, a hook,
a bridge and an outro, with drums, bass, keys and a lead, and the sections marked. "Just make it": no questions
asked. The sketch round was skipped because the intent was locked, so one idea was built and checked.

## Form (MIDI markers)
| Bars | Section | What changes |
|---|---|---|
| 1–4 | Intro | Rhodes alone with sustain pedal. Hats and rim fade in over bars 3–4. The lead previews the hook head at half speed. A pickup kick leads into the verse |
| 5–12 | Verse 1 | Full boom-bap kit, a bass locked to the kick and Rhodes comping that leaves room. The lead only answers at phrase ends (bars 8 and 12) |
| 13–20 | Hook 1 | New progression. The hook melody arrives. Crash, a tambourine overdub, soft swung 16th hats and busier comping and bass |
| 21–28 | Verse 2 | Same chords as Verse 1, but the drummer adds ghost strokes and kick variations, and the lead answers more often (4 answers instead of 2) |
| 29–36 | Hook 2 | The hook again. Bar 4 now runs up instead of resting, and the last bar climbs to F5 into the bridge |
| 37–44 | Bridge | The floor drops: half-time feel, rim instead of snare, and long Rhodes chords. The lead plays the hook head **inverted and augmented**. Bar 42 moves to A major (a chromatic mediant) while the lead holds G#/Ab across the change. Bars 43–44 build with snare 8ths then 16ths over a pedal bass |
| 45–52 | Hook 3 | The final hook with a new peak (bars 49–50 climb to Bb5 and A5). It ends on Db, the sus4, to set up home |
| 53–56 | Outro | Rhodes and bass resolve to Dbmaj9. The lead plays the hook head one last time. The drums stop after a final kick and soft crash at bar 55 |

## Material (Composer)
- **Verse:** Ebm9 – Ab13 – Dbmaj9 – Bbm9 (ii–V–I–vi).
- **Hook:** Gbmaj9 – F7alt – Bbm9 – Ab13sus (IV – V/vi – vi – V).
- **Bridge:** Bbm9 – Gbmaj9 – Ebm9 – F7alt – Bbm9 – **Amaj9** – Ab13sus – Ab13. The F7alt resolves deceptively
  into the hook's Gbmaj9.
- **Voicings:** rootless 4-note Rhodes voicings around middle C, voice-led by step. They sit under the lead (60–73).
- **Hook motif:** an off-beat pickup falling F–Eb–Db, answered by a chromatic descent over F7alt (A–Ab–Gb–F).
  The motif is transformed rather than replaced: augmented in the intro, echoed in the verse answers, inverted
  and augmented in the bridge, and given a new peak in Hook 3.
- **Melody-variety gate:** 17 lines, 12 distinct phrase rhythms, a 17.6% top-rhythm share and a 2% repeated-pitch
  share. Every line boundary has a rest of at least one beat: **pass**.
- **Bass:** the root lands with the kick, then syncopations and a chromatic approach note into each new root.
  159 of 219 bass onsets sit within 1/32 of a kick; the rest fill the kick's gaps.

## Performance plan (Performance Director, executed by the build script)
All values are **set for this style**. None are measured from a corpus: the pack has no boom-bap timing corpus.
- `swing_ratio`: 57:43 at the 16th (off-beat 16ths about 24 ms late). This is the sampler-swing convention of
  the style.
- `section_offset`: snare +10 ms (laid-back backbeat), ghost strokes +4 ms, bass +8 ms and lead +12 ms behind the
  kick. That follows the documented mechanism of a soloist lagging the drums; the amount is set. The kick and
  hats are the anchor.
- `chord_asynchrony`: derived from the voicing velocities. The top voice of the Rhodes is played louder and
  arrives first; the others trail by 0.6 ms per velocity step (at most about 6 ms). Pedal (CC64) is used only in
  the intro, the bridge and the outro.
- `drift_1f`: a seeded 1/f series applied last, 2 ms SD on the hats and 3 ms on the other parts.
- Dynamics: the section levels rise from intro to Hook 3 and drop in the bridge. The lead has a phrase arch
  (higher notes lean louder, long endings relax).
- Feasibility: four limbs are respected throughout (at most 2 hand strikes and 1 foot at a time). The tambourine
  is an overdub. The vibes lead is monophonic and in range (F4–Bb5).

## Checks run
- 480 PPQ, one 88 BPM tempo event, 4/4, a Db key signature and 8 section markers. Four named tracks: Drums
  (channel 10), Bass (1), Keys (2), Lead (3). No pitched part is on channel 10. The length is 56 bars, there are
  no same-pitch overlaps, and every track has notes in each section where it should play.
- Not done: rendering or listening. GM programs (Fingered Bass, Electric Piano 1, Vibraphone) are stand-ins.
  Velocities and CC values are a rough MIDI mix, and nothing was measured on a real instrument.
