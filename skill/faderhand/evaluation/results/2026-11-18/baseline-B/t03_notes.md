# T03: Atlanta trap loop (8 bars, 140 BPM, C minor)

**Brief, as locked:** an original 8-bar loop with kick, clap/snare, closed hats with rolls, open hat, 808 and one
melodic lead. "Just make it": no questions asked, so no sketch round. I built one idea and checked it against
the brief.

## What it is
- **Harmony (through the 808 roots and the lead):** C minor, i – i – VI – V | i – i – bII – V
  (Cm, Cm, Ab, G, Cm, Cm, Db, G). The V uses the harmonic-minor B natural and bar 7 borrows a Phrygian Db.
  Together they give the dark, slightly sinister colour the style leans on.
- **Lead (track "Lead", bell or pluck):** a 2-bar call and answer. The call is a triplet turn (G–Ab–G) that
  falls to the leading tone B. The answer sits low and leaves space. Bars 3–4 move the call up over Ab. Bar 5
  peaks on C6. Bar 6 adds a repeated-note stutter. Bar 7 bends the turn onto Db, and bar 8 ends on B so the loop
  pulls back to C. Melody-variety gate: 9 distinct phrase rhythms in 14 lines, a 21% top-rhythm share and a
  7% repeated-pitch share: **pass**.
- **Drums:** a clap on beat 3 gives a half-time backbeat; the snare is saved for pickups and the turnaround run. The kick changes in every bar of
  each 2-bar pair, and bars 5–8 vary the pair again. Bar 8 drops the kick and the 808 for a snare run that builds
  back into the loop.
- **Hats:** this part carries the style. It uses 16ths accented on the 8th, two bars of plain 8ths for space and
  a two-beat 8th-triplet switch in bar 6. The rolls are a rising 16th-triplet roll (bar 2), a falling 32nd
  "drip" (bar 4), a 32nd stutter (bar 7) and a 1/48 flutter that swells into the loop top (bar 8). Every roll
  has its own velocity ramp, so no two sound the same. The open hats sit on the off-beats where the closed hats
  stop.
- **808 (track "808"):** each note starts with a kick (28 of 28 onsets) and holds until the next one. It pops up
  an octave in bars 4 and 8. Slides are written as 30-tick legato overlaps into a new pitch, so a mono 808 patch
  with legato glide slides there. CC65/CC5 are set as a portamento hint for GM players.

## Performance decisions (Performance Director)
- Drum and 808 timing is on the grid on purpose (`realism_target: deliberately_mechanical` for timing). Trap is
  programmed music, and its feel lives in the hat vocabulary and velocity, not in a drummer's microtiming. That
  is why no timing model is applied and the imperfection list for timing is empty.
- Expression is carried by velocity: 35 distinct drum velocities, ramps inside every roll and a velocity arch on
  the lead (phrase starts accented, triplet pickups lighter, line ends softer, bars 5–6 lifted). The lead notes
  are 8% short of their written length so the pluck articulates rather than smears.
- Feasibility: at most 2 hand strikes and 1 foot strike at any moment, so a drummer could play it, although
  the style doesn't require that.

## Checks run
- 480 PPQ, 140 BPM tempo event, 4/4, C-minor key signature, markers. Named tracks Drums (channel 10), 808
  (channel 1) and Lead (channel 2). No pitched part is on channel 10. Length is 8 bars and no same-pitch notes
  overlap.
- Not checked: how it sounds. Nothing was rendered or heard. GM program numbers are stand-ins: load a real 808
  patch with glide, and a bell or pluck for the lead. Velocities are a rough MIDI mix.
