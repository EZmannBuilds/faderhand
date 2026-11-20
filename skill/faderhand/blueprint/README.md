# Music Production Blueprint (v0)

The blueprint is the contract between the planner and the executor:
- **The AI Music Studio skill** writes blueprints: the musical decisions.
- **Faderhand** validates them and carries them out in Live: the DAW mechanics.

| File | What it is |
|---|---|
| `music_blueprint.v0.schema.json` | The JSON Schema |
| `validate_blueprint.py` | Schema plus semantic checks; exit 1 on errors |
| `blueprint_from_midi.py` | Expresses an existing song as a blueprint, from its MIDI and a mapping file |
| `examples/fixture-comprehension.*` | A worked example on the benchmark's own original fixture |

## What a blueprint says

- **`song`:** title, tempo, meter, key, length, mode.
- **`creative_direction`:** the focal element, the contrast, the mood, what to avoid, and the brief in the user's words.
- **`roles`:** musical functions, each with a reason the song needs it. **Roles are not tracks.** One track can play
  several roles (a drum track plays kick, snare, hats and transitions). One role can need several layered tracks (a
  stab hook made of a string section, a pizzicato layer and quiet brass).
- **`tracks`:** which roles each track plays, its instrument (browser URI, patch file, measured transpose, drum pad
  map), how it layers, and its effects.
- **`sections`:** bars, energy, active roles, what changed, the gesture in the bar before, and the harmony.
- **`relationships`:**
  - Each one is a rule between roles, with an optional measured value.
  - Rules: `coordinate_onsets`, `avoid_onsets`, `complement_phrase_gaps`, `call_response`, `register_separation`,
    `double`, `follow_harmony`, `contrast_rhythm`.
- **`techniques`:** technique-card ids applied to roles, with why. The cards themselves belong to the Studio skill.
- **`execution`:** the Faderhand capabilities the plan relies on, which the validator checks against what Faderhand
  offers.

## What the validator checks

- **Errors:**
  - a reference to a role that doesn't exist;
  - duplicate ids;
  - overlapping sections, or a section that runs past the song;
  - a layer of a missing track;
  - an execution need Faderhand doesn't offer.
- **Warnings:**
  - a role no track plays, or a role that's never active;
  - gaps between sections;
  - a section that changes nothing;
  - no gesture before a section change.

There is no track-count rule. A plan is judged by whether each role is justified and whether the sections develop.

## Not in v0 (planned)

- Note-level content: v0 points at a MIDI file.
- Automation curves, bus and send plans, lyric and syllable alignment, and composition-memory fingerprints. These
  extend the schema as the Studio's arrangement director, songwriting module and memory are built
  (`docs/ARCHITECTURE-AND-DELIVERY-PLAN.md`).
