# Music Production Blueprint (v0, schema_version 0.1 and 0.2)

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

## Added in 0.2 (all optional; 0.1 blueprints stay valid)

- **`sections[].role_states`:** what each role is doing in the section, not just whether it's present.
  - The state is full, reduced, featured or silent.
  - `active_layers` picks which of a role's tracks play (a three-track stab can thin to its pizzicato alone).
  - Each state also carries a behavior, a reason and a basis.
- **`sections[].events`:** timed events inside a section, such as fills, dropouts, stops, entrances, exits and
  pre-transitions. Each has a bar position, a length in beats, the roles and layers involved, and the section it
  prepares.
- **`sections[].energy_strategy`:** how the energy changes: rhythm, density, register, dynamics and texture, each up,
  down or the same. This makes the energy number something an executor can act on.
- **`sections[].relationships`:** rules that apply only in that section.
- **`preservation`:** what must not change in a revision: sound, motif, rhythm, groove, harmony, passage or level.
  Each item is frozen or may vary, and a frozen item that had to change records its exception.
- **`basis`** on sections, role states, events and relationships: observed (measured), inferred (a reading of intent)
  or proposed (a planned change). It keeps measured facts apart from guesses.

## What the validator checks

- **Errors:**
  - a reference to a role that doesn't exist;
  - duplicate ids;
  - overlapping sections, or a section that runs past the song;
  - a layer of a missing track;
  - an execution need Faderhand doesn't offer;
  - (0.2) a role state that contradicts the active roles, a layer that isn't one of that role's tracks, an event
    outside its section or naming unknown roles or tracks, and preservation naming unknown roles, tracks or
    sections.
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
