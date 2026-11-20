# T03: Atlanta trap loop. Notes

**File:** `t03_trap.mid`. 8 bars, 140 BPM, 4/4, F minor, with E natural (harmonic minor) on the C bars. 480 PPQ.
Tracks: Kick, Clap, Hi-Hat and Open Hat (all on channel 10), 808 (channel 2), Lead (channel 3).

## Intent lock (the brief was locked: "just make it")
- Genre: Atlanta trap with a half-time feel, played by a strong producer and not a template.
- Key: F minor. Implied harmony is Fm, Fm, Db, C, then Fm, Fm, Db, C. The bass and the lead carry it; there is no chord track.
- Deliverable: an instrumental loop that repeats cleanly.

## What I did and why
- **Half-time backbeat.** The clap, with a snare layered under it, lands on beat 3 of every bar. Soft pickups come
  before bar 5 (a snare) and before bar 7 (an off-clap). Bar 8 ends with a rising 16th clap roll back to the top.
- **The hats are the main source of variation.** They play 8th notes underneath. Every bar uses a different roll rate:
  1/16 triplet, 1/32, 1/8-triplet bounce, and 16ths. Each roll gets louder or softer as a shaped ramp, not at one
  velocity. Quarter-note hats are accented over the off-8ths. Under rolls and the clap fill the hats thin out. Five
  open hats ring and get choked by the next closed hat.
- **The kick and the 808 share one rhythm.** Every kick has an 808 note on it (26 of 26), plus 3 extra 808 notes in
  the gaps. The kick drops out on beat 4 of bar 4 so the hat roll carries the lift into bar 5. It also drops out on
  beats 3–4 of bar 8 for the clap fill.
- **The 808 slides with intent.** Glides are written as note overlaps (40 ticks), with portamento on (CC65) and a
  short portamento time (CC5). The pitch-bend range is declared as 12 semitones (RPN 0). Moves include an octave slide
  F1–F2, a C2–C3–C2 jump in bar 4, and a dive from C3 to the leading tone E1. That E1 resolves to F1 when the loop
  restarts.
- **The lead is call and answer over 2-bar phrases.** Bars 1–2 are the call. Bars 3–4 answer over Db–C. Bars 5–6
  restate the call but reach a new peak, F5, through the leading tone E5. Bars 7–8 climb an F–Ab–C–Db arpeggio, hold
  C5, and end with a pickup back to the top.
  - Its melody-variety report passes: 5 lines, 5 distinct rhythms, 5 distinct line lengths, no repeated pitches, and
    every line boundary carries a rest of at least one beat.
  - It uses a music box from General MIDI (GM) as a placeholder for a dark bell or pluck. It plays detached, at
    velocities that rise and fall over each phrase and peak on each phrase's high note.
- **Timing is on the grid on purpose.** That is the genre's aesthetic for programmed drums
  (`realism_target: deliberately_mechanical`, timing only). The expression comes from velocity design, roll shapes,
  note lengths and 808 slides, and all of it is written explicitly. Nothing is randomised.

## Alternatives I considered (chose 1)
1. **(Chosen)** Hat rolls and 808 slides carry the motion, with a sparse bell call and answer.
2. A straight-16th hat bed with a dense counter-melody. Rejected: it fills the space the 808 needs.
3. A flute-led loop with triplet flows. Rejected: it pulls toward a more recent sub-style than the brief asks for.

## Checks
- `scripts/check_midi.py`: 480 PPQ, tempo and time signature present, every track named, drums on channel 10, no
  pitched track on channel 10, no hanging notes, length 8 bars.
- Bass–kick interlock: every kick has an 808 note on it.
- Lead melody-variety report: pass.
- Not listened to. No DAW or render was available, so nothing here claims how it sounds.
