# T10: Revision of `fixtures/flawed.mid`. Notes

**File:** `t10_revised.mid`. Same tempo (96 BPM), meter (4/4), length (8 bars), track names and channels. I read the
protected material from the fixture rather than retyping it.

## What was wrong (diagnosis, upstream first)
1. **No development.** The lead plays the same 1-bar hook 8 times. Drums and bass repeat one bar 8 times, and nothing
   enters, leaves or builds.
2. **Bass and kick never meet.** Every bass note sits exactly one 16th after a kick (0 of 24 bass notes on a kick). That
   makes 24 flams against the kick. The bass is also all 16th-note stubs with no line between chords.
3. **Flat dynamics.** Every note in every track is velocity 100: hats, snare, chords and melody alike.
4. **The lead overlaps itself.** In 16 places the D overlaps the following C (240 + 240 ticks against an onset at
   360), which smears a monophonic lead. The notes are otherwise uniform 8ths with no phrase ends.
5. **Grid-exact block playing.** Chords start exactly on the bar line, every voice at the same instant. The drums have
   no ghost notes, fills, open hats or crash.

## What I changed
- **Keys (protected pitches).**
  - Same pitches, one attack per chord tone per bar. No onset is earlier than its bar line.
  - Dynamic arc by bar: 50, 48, 58, 56, 68, 64, 76, 62.
  - Top voice is 8 louder and sounds first. Lower voices follow 6–12 ticks later (chord asynchrony from velocity).
  - Bars 5–6 are shortened to a dotted half, so the new bass riff speaks there.
- **Lead (protected pitch sequence).**
  - Same 64 pitches in the same order, each bar keeping its own 8 notes.
  - Placement moves by at most a 16th and stays inside the bar. In bars 3, 6 and 7 the beat-3 group is anticipated by
    a 16th, a motif transformation (rhythmic displacement) that makes the repeats develop.
  - Overlaps removed (16 → 0). Inner notes are detached, and the end of each beat-2 group is held as a breath.
  - 8-bar arc from mp to ff in bar 7, then a settle in bar 8. The peak G is accented, passing 16ths are lighter, and
    the last group of bar 8 eases back.
- **Drums (rewritten).**
  - Bars 1–2: cross-stick and light hats.
  - Bars 3–4: full snare, ghost notes, an extra kick, and a drag into bar 5.
  - Bars 5–7: crash, 16th hat pickups, more ghosts, an open hat closed by the pedal, and an extra kick in bar 6.
  - Bar 8: hats stop for a flammed snare-and-tom fill.
  - Hat timing follows a 16th placement pattern, set rather than measured: e +1.0, & −0.5, a +0.8% of a beat. The
    snare lies back +1%, and the kick is the anchor.
  - Four-limb check: clear.
- **Bass (rewritten).**
  - Locks with every kick (23 of 23), and adds 12 notes in the gaps.
  - Long roots in bars 1–2, then fifths and approach notes: G2 into F, F#2 into G, F2 into E, and G#2 back to A at the
    loop.
  - Riff with octave pops in bars 5–6, then the strongest bars in 7–8.
  - Velocity follows the same 8-bar arc.

## How I checked it (`scripts/t09_verify.py`, `scripts/check_midi.py`)
- Chord pitches per bar match the fixture exactly (24 notes before and after).
- The lead pitch sequence matches overall and within each bar (64 notes).
- Largest lead onset move: 120 ticks (one 16th).
- Lead overlaps: 16 before, 0 after.
- Velocities: the original used only velocity 100. After revision, drums use 56 distinct values, bass 25, keys 18,
  lead 34.
- Bass–kick: 0% of bass notes on a kick before; 100% of kicks doubled by bass after.
- The file passes the MIDI checks: 480 PPQ, tempo and time signature present, named tracks, drums on channel 10.
- Not listened to. Whether it now "sounds performed" needs a listener and a render.
