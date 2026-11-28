# DAW control: Faderhand for Ableton Live 12

This module is how the skill acts inside a running Live Set. Faderhand is this repository's MCP server and
control script. Its tools include `tooling_info`, `get_set_identity` and `list_tracks`. If those tools aren't
in the session, Faderhand isn't installed: say so, offer the README's install steps, and work offline (MIDI files,
plans, WavRead analysis).

**Precedence:** where `studio/daw-adapters/ABLETON_LIVE.md` describes a "sidecar Remote Script" for mixer,
returns, sends, routing, racks, sidechain and automation, **that sidecar is Faderhand.** Its notes on what plain
AbletonMCP can't do (mixer read-only, no returns) don't apply when Faderhand is connected. The adapter's notes on
clip and note editing still apply to the companion AbletonMCP server (port 9877), if that is installed too.

Reference: `../../../docs/TOOL-REFERENCE.md` (every tool and argument), `../../../docs/TOOLS.md` (units and
conventions), `../../../docs/CAPABILITY-MATRIX.md` (what is proven in Live).

## Safety (from the README; no approval codes)

- Faderhand edits whichever **saved** Set is open. Unsaved Sets are refused, and deletes only work in a disposable
  Set (a track named `__TOOLING_SCRATCH__`).
- Before editing:
  - Call `get_set_identity` and say which Set is open.
  - If it's a real song, suggest working on a copy.
  - Edit only what the user asked.
- There is **no per-conversation or per-song authorisation code**, and the skill must not invent one. The
  practical guards are the saved-Set rule, the disposable-Set rule for deletes, confirming the open Set, and
  reading every write back.
- Every write returns Live's value afterwards. Report that value, not the one you asked for.

## Recipes (tool names and arguments as the server defines them)

**Return track with reverb, and a send in dB**
```
create_return_track(name="Plate")
load_effect_on_return_track(ret="Plate", effect="Reverb")
set_track_send(track="Keys", send="Plate", db=-14)
```

**Compressor on the bass, keyed from the kick**
```
load_effect(track="Bass", effect="Compressor")
set_sidechain(track="Bass", device="Compressor", source="Kick",
              params={"Threshold": "-30 dB", "Ratio": "4", "Attack": "1 ms", "Release": "150 ms"})
```
Prove it with `capture` or `measure_levels`: ducking with the kick, none without.

**Automation**
- Targets are objects: `{"mixer": "volume"}`, `{"mixer": "pan"}`, `{"send": "A"}`, or
  `{"device": <index or name>, "parameter": "<name>"}`.
- Call `list_automatable_parameters(track=...)` to get the exact target object for a device parameter.
- Session clip envelopes are written directly:
  `set_automation_points(track, slot, target, points=[{"at": "1.1.1", "value": "300 Hz"}, ...], units="display")`
  or `set_automation_curve(...)` for shaped sweeps.
- Arrangement automation can't be drawn through the API. `record_arrangement_automation(track, target,
  points=[{"at": "17.1.1", "value": "300 Hz"}, {"at": "25.1.1", "value": "8000 Hz"}], units="display")` records it
  in real time, so it takes as long as the passage plays.

```
load_effect(track="Lead", effect="Auto Filter")
list_automatable_parameters(track="Lead")          # read the exact target for Auto Filter's Frequency
record_arrangement_automation(track="Lead", target={"device": "Auto Filter", "parameter": "Frequency"},
                              points=[{"at": "17.1.1", "value": "300 Hz"}, {"at": "25.1.1", "value": "8000 Hz"}],
                              units="display")
```

**Buses and routing:** `create_audio_bus`, `route_multiple_tracks`, `validate_routing`.
**Racks:** `create_effect_rack`, `add_rack_chain`, `set_rack_macros`.
**Render a passage to check it:** `record_track_audio` resamples the Main for N bars in real time;
`export_audio(start="9.1.1", length="8.0.0", path="/abs/folder/Name.wav")` renders the Main offline through Live's
Export window (macOS, Accessibility permission; a new path only). Then analyse the file with WavRead (the separate WavRead skill, if installed) or
`tools/audio_check.py` in this repo.

## Check what a sampler does on note-off before planning silence

Live's Sampler has a volume-envelope loop mode. In **Trigger** mode (`LoopMode` 4 in the `.als`), note-off is
ignored: every hit plays its whole sample. Some sampled-orchestra presets ship this way. A "stab" on a sustained
string patch then rings for seconds. Only the voice limit cuts it off.

While the part plays every bar, you can't hear this. But a planned dropout, stop or gap fills with the previous
hits dying away.

- **Before an arrangement plan relies on silence:** read the instrument's envelope (`get_device_parameters`, or the
  `.als`).
- **After rendering:** measure the stem inside each planned gap. Don't trust the notes alone.
- `tools/preflight.py` does both: `set` flags Trigger-mode samplers, long releases and tails on sends; `occupancy`
  lists beats that sound with no note sounding.

## Match the articulation to the note length

A sustain or legato sample can't play a fast part, even with the Sampler attack at zero. The recorded sound itself
takes time to speak, and a long release blurs one note into the next. Measured at 150 BPM:
- sustained trombones took about 130 ms to reach 70% of peak, on notes of about 220 ms;
- legato cellos took about 70 ms on 8th-note ostinato notes of about 120 ms;
- legato full strings have a 700 ms release on those same notes.

A listener heard it as instruments that "don't play fast".

For parts faster than about 8th notes at 140 BPM:
- use a staccato, spiccato or pizzicato articulation;
- or shorten the release and start sustained samples about 50–100 ms early.

To check, measure the onset rise time on the rendered stem against the written note length.
`tools/audition.py measure` does this, along with the other audition measures.

## Where MIDI notes come from

Faderhand creates Arrangement MIDI clips (`create_arrangement_midi_clip`) and edits clips. To place a MIDI file
the skill wrote:
1. Use the companion AbletonMCP (`add_notes_to_clip`) if it is installed, or ask the user to drag the `.mid` in.
2. Then read the notes back (`get_clip_notes`) and compare them with the file.

Never claim notes are in the Set without reading them back.

## Shape velocity and expression on notes already in a clip

`set_note_expression` changes velocity, chance (`probability`), velocity range (`velocity_deviation`), release
velocity and mute on existing notes. It never adds, removes or moves a note. Select notes with `pitch`,
`pitch_range`, `start`/`end`, a grid (`every`, `offset`, in beats) or `ids` from `get_clip_notes`.

**Grouped hat accents (3+3+2), then check where they landed**
```
set_note_expression(track="Drums", slot=0, pitch=42, velocity_pattern=[110, 70, 70, 110, 70, 70, 105, 75], dry_run=True)
set_note_expression(track="Drums", slot=0, pitch=42, velocity_pattern=[110, 70, 70, 110, 70, 70, 105, 75])
get_clip_notes(track="Drums", slot=0, pitch=42)      # summary.velocity_by_16th: the mean velocity at each 16th
```

**A crescendo into the drop, then a little life on the off-beat hats**
```
set_note_expression(track="Snare", arrangement_index=0, start="15.1.1", end="17.1.1", velocity_ramp=[50, 120])
set_note_expression(track="Drums", slot=0, pitch=42, every=0.5, offset=0.25, humanize=6, seed=1, probability=0.85)
```

- A velocity change is one base (`velocity`, `velocity_pattern` or `velocity_ramp`), then `velocity_scale`, then
  `velocity_add`, then `humanize`. The result is kept in 1-127, and the reply counts the notes that had to be kept.
- `humanize` with the same `seed` gives the same result, so a revision can be repeated exactly.
- `dry_run=True` shows every note's before and after without writing. Use it before a broad selection.
- Velocity changes the sound only if the instrument responds to it. Check its velocity sensitivity
  (`get_device_parameters`), then render and listen. A changed number is not a heard accent.

## Quantize, swing and grooves

`quantize_notes` moves existing notes toward a grid; the groove tools put one of Live's grooves on a clip. Both only
change timing (a groove can also change velocity): render and listen before calling the feel right.

**Tighten the hats to 16ths, half way, then swing them**
```
quantize_notes(track="Drums", slot=0, pitch=42, grid="1/16", strength=50, dry_run=True)
quantize_notes(track="Drums", slot=0, pitch=42, grid="1/16", strength=50)
quantize_notes(track="Drums", slot=0, pitch=42, grid="1/16", swing=62)
```

**Put an MPC swing on a clip**
```
list_grooves(search="mpc 16")
load_groove(name="Swing MPC 3000 16ths 57", track="Drums", slot=0)
set_groove_amount(amount=100)                    # the pool's Global Amount: at 0, no groove does anything
get_groove_pool(clips=True)                      # which clips use which groove
```

- `swing` is the MPC-style percentage: 50 is straight, about 66 is a triplet feel. Live's "Swing 16ths 66" groove
  moved off 16ths 41.7 ms late at 120 BPM: a full triplet.
- A swung or quantized note that now runs into the next note of its pitch is shortened, as Live does. The reply
  lists it under `shortened`. Notes that would land on the same spot are refused with nothing written.
- A groove changes how a clip plays, not its notes, and every clip using it follows `set_groove`. Live's API can't
  remove a clip's groove. To switch one off, set its amounts to 0 or turn the Global Amount down.
- New clips can come with a groove already assigned (seen in a Set whose pool had one). Check `get_groove_pool(clips=True)`
  before relying on straight timing.

## Amp-feedback bass

A tuned resonance fed back through distortion: the whine of an amp feeding back, tracking the bass line.

```
build_feedback_bass(track="Bass", preset="growl", key_note="E1", transpose=24, follow_slot=0)
```

- It goes after the track's instrument as one rack, "Feedback Bass (growl)": Auto Filter (Vowel) -> Saturator
  (Waveshaper) -> Spectral Resonator -> Roar (tuned feedback) -> EQ Eight (tilt) -> Limiter (-1 dB). Bypass or
  delete the rack to take it all out.
- `preset`: `subtle`, `growl` or `screaming`. `key_note` + `transpose` sets the resonance's pitch: two octaves above
  the bass (24) sits in the whine's register. Live's note names: C3 = 60.
- `follow_slot` makes the resonance follow that Session clip's notes. Without it, the resonance stays on one pitch:
  in key for a one-note part, clashing on the others. Arrangement clips can't follow (no clip envelopes in the API).
  Build and follow in a Session clip, then record it.
- `follow_notes` does the same for any pitch parameter, e.g. a Resonators note or a filter's frequency.
- The presets were measured to die away when the notes stop. Raising Roar's Feedback or Shaper 1 Amt past them can
  make the chain ring on forever (the Limiter then holds it at -1 dBFS). If a tail won't stop, lower those two.
- Listen before calling it right: the measurements show the resonance moves and doesn't run away, not that it
  sounds good on this bass.
