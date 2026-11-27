# Faderhand knowledge pack

Generated 2026-11-27 from a private training lab. 7 lessons.

Each lesson is either a **measured finding** (from controlled experiments where the cause of every change was known) or a **sourced convention** (from published producer interviews and guides). None is a rule. None outranks what the person you are working with hears. A confidence is a judgement, not a probability. Unless a lesson says otherwise, nobody has listened to the result yet.

How to use it: before planning or revising, read the lessons for the brief's genre and stage. Say which lesson you are applying. Measure the result the way the lesson's Faderhand line says, and report what you did not hear.

## Stage: sketch

### Drill 808: holds the root, glides as a pickup, tuned

*Sourced convention; confidence 0.60; genres: drill. Id L-d0fc16c731.*

**What was found.** The 808 holds the root, one or two notes a bar, and glides as a pickup into the next bar; slides are what make UK drill. An out-of-tune 808 alone makes a beat sound amateur.

**Technique.** Tune the 808 to the key (check its pitch in cents), one or two notes a bar, glide into the downbeat.

**Limits.** Secondary sources; slide density varies by producer.

**Sources.** Native Instruments blog; Complex (M1OnTheBeat interview); 808Melo quoted via Genius; FADER (Mike Dean, '808 on the wrong note')

*Published sources. Conventions, not rules.*

### UK/Brooklyn drill drum vocabulary

*Sourced convention; confidence 0.60; genres: drill. Id L-4e195b84f2.*

**What was found.** About 138-145 BPM felt half time. Snare or clap on beat 3; often, but not in every track, it moves over two bars (beat 3 of bar 1, beat 4 of bar 2), with ghost snares at phrase ends. Hats grouped (3+3+2) with stepped velocities and deliberate holes, straight 16ths mixed with triplet bursts, varied over a 4-bar phrase.

**Technique.** Start with the snare on beat 3 of every bar, then try the two-bar move (beat 4 in every second bar) against it and keep whichever the song wants. Group the hats with holes, vary the pattern every 4 bars.

**Limits.** Secondary sources and producer statements; conventions vary by scene and era; not a target to enforce. The two-bar snare is a variation to audition, not a requirement.

**Sources.** Native Instruments blog 'drill'; Attack Magazine 'Beat dissected: UK drill'; Tracklib (808Melo, Dior); Amped Studio; DJ Mag 'Evolving sound of UK drill'

*Published sources. Conventions, not rules.*

## Stage: arranged

### Notes are not sound: Live's '808 Pure' rings on after note-off, so shorter MIDI notes open no low-end space

*Measured finding; confidence 0.85; genres: trap, drill, hip-hop. Id L-8ab2d208b9.*

**What was found.** The preset's release outlasts every gap the shorter notes leave, so the 808 never stops. The offline lab assumed note-off means silence; for this instrument that is false.

**Technique.** Before using note length to make space, measure the instrument: play a short note and read its level 100-250 ms after note-off. If it rings on, shorten the amp release (or use a gate) and measure again.

**In Faderhand.** Run preflight.py set on the saved Set and preflight.py occupancy on the stems inside planned gaps; read the 808's release with get_device_parameters before relying on note length.

**Limits.** One preset; measured, not heard. Other 808 presets (Sampler in Trigger mode, short-release synths) differ.

*Measured on controlled renders with known causes (offline and/or in Ableton Live). Not a listening result unless it says so.*

### Shortening the 808 opens the low register but does not clear the kick

*Measured finding; confidence 0.60; genres: trap, drill. Id L-d79e9ed0a7.*

**What was found.** Gating the 808 to half its length took the low end from sounding 82% of the time to 55% and created about two low-register gaps a bar, but the kick stayed about 6.3 dB under the 808 at the hit: the overlap is at the 808 start, not its tail.

**Technique.** Two tools for two problems: gate the 808 for space in the low register, duck it (sidechain) for kick clarity. Gating by note length works only if the 808 releases at note-off: check the instrument first (see the 808 Pure lesson), and shorten its amp release or use a gate if it rings on.

**Limits.** Offline synth 808 and kick; measured, not heard. In Live with the Core Library '808 Pure' the same note lengths changed nothing: the low end sounded 100% of the time at every length.

*Measured on controlled renders with known causes (offline and/or in Ableton Live). Not a listening result unless it says so.*

### Thinning closed hats creates measurable negative space

*Measured finding; confidence 0.80; genres: trap, drill, hip-hop. Id L-5c5841b8b0.*

**What was found.** Halving the hats moved the empty-16th share from 44% to 61%; quartering it to 72%. It also removed most of the mix's air band, so space in the rhythm costs brightness unless something else carries the top.

**Technique.** For space without losing the top end: thin the hats but keep one bright element (an open hat, a shaker on the offbeat) or group the hats (3+3+2) rather than deleting evenly.

**In Faderhand.** Edit the hat clip (create_arrangement_midi_clip with fewer notes) or mute a hat layer; count the empty 16th slots in the drum stem before and after, and check the top end.

**Limits.** Even thinning only; grouped patterns with holes (the drill convention) are not tested yet. Replicated in Live (808 Core Kit): empty 16ths 0.11/0.45/0.58, air 0.12/0.08/0.04%; the kit's hats are darker, so absolute values differ.

*Measured on controlled renders with known causes (offline and/or in Ableton Live). Not a listening result unless it says so.*

## Stage: mix

### How deep to duck an 808 under the kick

*Measured finding; confidence 0.70; genres: trap, drill, 808-based hip-hop. Id L-4a0c2ef9fa.*

**What was found.** Each 3 dB of ducking gave the kick about 1.7 dB against the 808 in the 30 ms after each hit; the mix's sub share and loudness barely moved, because the dip is short.

**Technique.** Sidechain-compress the 808 from the kick for 6-9 dB of gain reduction, fast attack, release shorter than the gap to the next kick.

**In Faderhand.** set_sidechain (a Compressor on the 808, sidechained from the kick track) and set_device_parameters; then render, print the kick and 808 as stems, and compare their low bands in the 30 ms after each kick.

**Limits.** Synthetic kick and 808, one fixture, measured not heard. The perceptual sweet spot is untested: make a blind pair before treating 6-9 dB as a preference.

*Measured on controlled renders with known causes (offline and/or in Ableton Live). Not a listening result unless it says so.*

### Wetness has a ground truth from printed stems, but no mix-only measure detects a short room yet

*Measured finding; confidence 0.80; genres: all. Id L-50d11d7a0e.*

**What was found.** Stems printed post-mixer in one pass sum to the mix exactly (-143 dB residual with no send), so mix minus stems is the returns' output. The room rose 9 dB for 9 dB of send. In this mix it sat 25-34 dB under the dry signal above 300 Hz, and none of three mix-only measures moved.

**Technique.** Measure how wet a mix is from printed stems and returns (mix minus the dry stems), not from the mix alone. A mix-only dryness measure is still an open problem: test candidates against this ground truth with longer rooms and sparser parts.

**In Faderhand.** Print each part post-mixer and the mix in one recording pass; their sum then equals the mix, so the residual isolates the returns. Separate passes do not null: some synths start at a new oscillator phase every time.

**Limits.** One short room, one arrangement, quiet sends under a loud 808; measured, not heard. 'Too dry' cannot be checked from a mix yet.

*Measured on controlled renders with known causes (offline and/or in Ableton Live). Not a listening result unless it says so.*
