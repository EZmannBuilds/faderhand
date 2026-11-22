# Vital: synthesis and sound design

Vital (by Matt Tytel) is a free wavetable synth. This module is the skill's Vital knowledge. It has two parts:

1. **The synth workshop** in the AI Music Studio skill (`shared/SYNTH_WORKSHOP/`, when that skill is installed):
   - a course, a patch standard and recipes;
   - an automation guide and a teacher protocol;
   - a field test of building those recipes in Vital.

   Start with its `README.md`. The Producer routes there for any sound-design task.
2. **Calibrated parameter units** (below): what Vital's raw preset values mean in real units. These were
   measured by rendering a 40-patch set (Vital 1.0.7 AU, Live 12, 48 kHz) and checking each mapping against the
   render. Recheck them on another Vital version.

## Raw preset values vs. what you hear

A `.vital` preset is JSON. Its `settings` hold **raw** values, not the numbers the UI displays. When writing or
editing a preset, convert:

| Parameter | Raw value means | Measured check |
|---|---|---|
| `unison_detune` | **17.5 cents between two voices per unit, linear.** 20 cents = 20/17.5 = **1.143**. | 4.472 gave 78.2 cents. An older rule of thumb (cents^0.5) is about 4x too wide and over-detunes. |
| `volume` | About amplitude^0.25 up to the 0 dB point: **5473 ≈ 0 dB, 4400 ≈ -7.65 dB, 3364 ≈ -16 dB.** Interpolate in log(value) between these: -6 dB ≈ **4612**. Above 5473 the slope is about 80.7·log10(v/5473) dB. | 6400 and 7400 clipped a 24-bit render; don't go above 0 dB without a reason. |
| `reverb_decay_time` | **log2(seconds).** 2 s = 1.0, 3 s = log2(3) = **1.585**. | 1.0 measured 2.07 s (T30 x2). The macro span is 12 units, so a small macro amount multiplies decay a lot. |
| `delay_frequency` (sync off) | **log2(1/seconds).** 250 ms = 2.0, 375 ms = log2(1/0.375) = **1.415**. | Feedback 0.5 = -6.0 dB per repeat. |
| `osc_N_tune` | **semitones.** +25 cents = **0.25**. | 0.5 measured +50.1 cents. |
| `velocity_track` | 0.5 gave +6.1 dB from velocity 40 to 110. | |
| Oscillator level | about level² (quadratic). A modulation route acts before the square. | From the workshop field test. |
| Sample root | With sample keytrack on, MIDI 60 plays the sample at its recorded pitch: transpose = 60 - root. | Within 5–8 cents. |

## Traps

- **Vital is x86_64 only** on Apple silicon. In Live it runs under Rosetta, and many instances idle hot.
  Switch off instances a render doesn't need, and unload the set when done.
- **Legato doesn't restart a decaying envelope,** so slid 808 or bass notes fade. Use high sustain for slide
  patches.
- **A sub can pass every meter and still not carry.** Check energy above 150 Hz, and give subs and 808s a 2nd
  harmonic around -20 dB.
- **Perlin random restarts at every note** in trigger mode. Use sync mode and about 5x the route depth for slow
  drift (field test).

## With the rest of the skill

- **Role first:** the Studio's Producer (when installed) chooses the role (808, pad, pluck, lead); the workshop's recipes give the patch.
- **Load and set it in Live** with Faderhand (`../daw/`): `load_effect`/instrument loading, then
  `set_device_parameter` in display units, read back.
- **Check the result:** render it and run WavRead's analysis or the workshop's test protocol. Don't call a
  patch right from its parameters alone.
