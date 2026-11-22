# T10 – Revision of `fixtures/flawed.mid`: notes

## What was wrong (measured and read back before editing)
| Problem | Evidence |
|---|---|
| Every velocity was 100 in every part (1 distinct value) | `midi_check.py` flagged it: "velocities are flat" |
| Everything sat exactly on the grid, with no swing, no jitter and the snare not behind the hats | Share of notes on the grid 1.0. Jitter, hat SD and snare SD were all 0 (`--genre hiphop-live`). |
| The drums repeated one bar 8 times | No ghost notes (0 per bar), no fills, no open hat, no crash at the midpoint |
| **The bass flammed the kick** | `low_on_kick` was 0.0: every bass note sat exactly a 16th after a kick (bass steps 1/9/11 against kicks 0/8/10), the low-end anti-pattern in `LOW_END_808_AND_BASS.md` §5. It also repeated one rhythm for 8 bars with no pickups. |
| The lead's notes overlapped | 16 overlaps: the 8th note on step 2 was still sounding when the 16th on step 3 began. |
| Nothing developed over the 8 bars | Same dynamics and articulation throughout |

## Protected material (T09), listed before editing
- **Keys:** the pitch set of every bar (Am Am F F G G Em Em, as written).
- **Lead:** the hook's pitch sequence (E D C D E G E D) × 8 = all 64 notes, in order.

## What I changed, in the order the skill gives (velocity, then timing, then durations, then variation)
- **Keys:**
  - The same 24 notes, one attack per pitch per bar, each kept inside its own bar.
  - The top voice is louder than the bottom.
  - Each chord is rolled bottom to top by about 4–25 ms.
  - The second bar of each chord pair is re-struck softer and released early, so it breathes.
  - The level follows a per-bar dynamic arc that builds to bar 7.
- **Lead:**
  - The same 64 pitches in the same order.
  - Velocity is a phrase arch over each two-bar phrase, with the G peak accented and the passing 16ths lighter. The overall arc peaks in bar 7.
  - It sits slightly behind the beat with small jitter, and downbeats never cross back over the barline.
  - **Slight rhythm changes:** in bars 3 and 7, beat 3 is anticipated by a 16th (a push). In bars 2 and 6, the peak is laid back a 16th.
  - **Articulation changes by section:** detached in bars 1–2, legato in 3–4, mixed in 5–6, and legato in 7–8 with the last note held.
  - The overlaps are removed: 16 before, 0 after.
- **Bass (rewritten):**
  - Roots land with the kick (`low_on_kick` 0.80, `kick_with_low` 1.0).
  - Approach notes walk into each chord change: A–E–G–F# into F, F# up into G, and a G–G#–A–G# turnaround back to Am.
  - Octave pops come in bar 5 onward. Every bar is different.
- **Drums (rewritten as a played groove that develops):**
  - **Bars 1–2:** 8th hats in velocity tiers, with the backbeat 12 ms behind the hats.
  - **Bars 3–4:** ghost notes enter. An open hat and a snare pickup fill end bar 4.
  - **Bar 5:** a crash, then 16th hats and more kicks.
  - **Bar 8:** a snare-and-tom fill that loops back to bar 1.
  - Swing is about 57%, with consistent placement per instrument plus 5–7 ms of jitter.

## How I checked it
- **`scripts/t10_verify.py`** (a diff against the original):
  - The Keys pitches of every bar are identical in all 8 bars, and no note crosses a barline.
  - The Lead pitch sequence is identical (64/64 notes), as are the Lead pitches per bar.
  - Lead overlaps went from 16 to 0.
- **`midi_check.py --genre hiphop-live`:** the original had 7 REVISE items; the revision has 0.

  | Check | Value |
  |---|---|
  | Swing | 56.7 |
  | Ghosts per bar | 1.4 |
  | Share of notes on the grid | 0.23 |
  | Drum jitter | 6.3 ms |
  | Hat velocity structure | 0.62 |
  | Snare behind the hats | 12 ms |
  | Bar uniqueness | 1.0 (from 0.5) |
  | Distinct velocities | 83 |

## Not done
- Nothing was rendered or heard (no DAW, by the runner rules). "Sounds performed" is supported by measurement only.
- The lead's pitch-and-rhythm repetition is still high (`lead_bar_uniqueness` 0.375). That is deliberate, because the hook's pitches are protected. Development comes from articulation, dynamics, the pushes and everything around the hook.
