# T03 – Atlanta trap loop: notes

**File:** `t03_trap.mid` is 8 bars at 140 BPM in C# minor, 480 PPQ. It has three tracks: `Drums` on channel 10 (kick, clap, closed and open hats), `808`, and `Lead`, a bell or pluck.
**Harmony, implied by the 808 and the lead:** C#m | C#m | A | G# | C#m | C#m | A | G#. The G# major chord in bars 4 and 8 uses the harmonic-minor B#, which pulls the loop back to the top.

## Sketch round (unrendered, compared on paper and with `midi_check.py --genre trap`)
| Sketch | Mechanism | Measured | Verdict |
|---|---|---|---|
| A: call-and-response bell | Short detached lead phrases that rest under the clap. The 808 follows the kick. | Lead steps 0.56, every leap recovered. 808 octave jumps only 0.17. 808 on the kick 0.69. | Best lead. The 808 was too kick-bound. |
| B: triplet flow | The lead is an 8th-note-triplet figure through the chord tones (trap arp rate). | Lead steps 0.31, leap recovery 0.25. | It works as an arp, but it isn't a hook. Rejected. |
| C: 808 as the melody | The lead holds long notes. The 808 moves more, with octave jumps 0.29 and 1.6 slides per bar. | Lead phrase 1 note (REVISE). | Its 808 movement is good, but its lead is weak. |

**Built:** a combination of A's lead and C's octave-jump 808 moves.

## What the loop does and why
- **Drums, programmed feel:** the notes are quantized, with two or three fixed velocity tiers. The clap is on beat 3 of every bar (half-time).
  - **Kick:** beat 1 is anchored and the second and third kicks move each bar (steps 6/11, 3/10, 6/11/14, 7/10, …).
  - **Hats:** 8ths with programmed 16th bounces.
  - **Rolls:** four rolls in 8 bars (0.5 per bar). 32nds go into bars 3 and 7, and 16th triplets lead into bar 5 and back to the top. Every roll's velocity rises (58→100).
  - **Open hats** sit on the "&" of 4 in bars 3 and 7.
  - **Bar 8 drops to quarter-note hats** before its roll, so the turnaround breathes.
- **808:**
  - Every kick has an 808 note (`kick_with_low` 1.0). Only 64% of the 808 notes land on a kick; the rest are pickups between the kicks.
  - It averages 4.9 notes a bar, with 1.6 overlap slides a bar (overlapping notes, not pitch bend).
  - Octave jumps make up 32% of its moves (C#1↔C#2, A1↔A2, G#1↔G#2).
  - The roots sit at MIDI 25–45.
- **Lead:**
  - The hook cell is E–D#–C# on dotted 8ths, then a G#–B pickup.
  - Bars 3–4 restate it a third lower over A, then arpeggiate G# major.
  - Bar 5 repeats the hook exactly.
  - Bar 6 keeps the start and lands on a new peak (G#5). Bars 7–8 answer with a descending run and a half cadence on B#.
  - Phrases rest at least a beat, usually under the clap. The range is 12 semitones and 59% of the moves are steps.

## Measured (final file, `midi_check.py --genre trap`): 0 to revise
| Check | Value |
|---|---|
| Half-time backbeat | 1.0 |
| Hat rolls per bar | 0.5, all rising |
| 808 on a kick | 0.64 |
| Kicks with an 808 | 1.0 |
| 808 notes per bar | 4.9 |
| 808 slides per bar | 1.6 |
| Lead range | 12 |
| Lead phrase median | 6 notes |
| Share of notes on the grid | 0.93 |
| Drum jitter | 0 ms |
| Bar uniqueness | 1.0 |

I also read back bar 8 as a note dump.

## Not done
- Nothing was rendered or heard. No DAW was used, as the runner rules require.
- The slides depend on the 808 patch being set to legato or portamento with high sustain (`vital/README.md`). That still needs checking in the real instrument.
