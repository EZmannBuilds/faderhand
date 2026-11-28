# Changelog

## Unreleased

- **Knowledge pack** (`skill/faderhand/knowledge/`): seven lessons, as `LESSONS.md` and `lessons.json` (schema
  `faderhand.knowledge/1`). Two are sourced drill conventions; five are measured findings, offline and in Live:
  - Live's "808 Pure" rings on after note-off, so shorter notes make no low-end space;
  - gating and ducking the 808 solve different problems;
  - how deep to duck the 808 under the kick;
  - thinning hats makes space but costs top end;
  - printed stems give an exact wetness ground truth.

  The lessons come from a private training lab that is not part of Faderhand: only cleared lessons ship. No
  preferences, project decisions, song material, generator output or non-commercial model output. `SKILL.md` routes
  to the pack. New offline test: `tests/offline/test_knowledge_pack.py`.
- **Four commands from the development line**, now in the Remote Script's extensions (`EXT_VERSION` 0.3.0, loaded
  with `reload_extensions`, no Live restart) and the MCP server (83 tools):
  - **`find_parameter`**: every parameter with a given name on any device of a track, racks and nested racks
    included, with the address `set_device_parameter` takes.
  - **`set_parameter_by_name`**: sets that parameter wherever it is. An ambiguous name writes nothing and lists every
    match (narrow it with `prefer` or `device_name`).
  - **`cut_arrangement_range`**: empties a stretch of the Arrangement on one or more tracks, splitting the clips that
    cross its edges. It deletes, so it runs only in a disposable Set, like the other deletes.
  - **`record_tracks_audio`**: records several tracks' outputs in one real-time pass, one take per destination track.
- **MIDI velocity and expression edits** (roadmap item; `EXT_VERSION` 0.4.0, 85 tools in 13 groups):
  - **`get_clip_notes`**: a MIDI clip's notes with their ids, velocity, chance, velocity range, release velocity and
    mute, filtered by pitch, time range or grid position, with a velocity summary per 16th of the bar.
  - **`set_note_expression`**: changes those on existing notes, nothing added, removed or moved. Velocity takes one
    base (a value, a pattern cycled per onset, or a ramp), then scale, offset and a seeded humanize, kept in 1-127.
    Every changed note is read back; `dry_run` shows the plan without writing.
  - Offline: `tests/offline/test_note_expression.py` (a fake clip with Live's note API). In Live:
    `tests/test_note_expression.py`, written but not yet run.
  - The README's group counts are corrected for the commands above.

## v0.7.0-alpha.1 (2026-11-21)

Adds the Faderhand agent skill in `skill/faderhand/`. The MCP server and Remote Script are unchanged apart from the
version: still 79 tools, same port, same safety guards. `tooling_info` now reports version `0.7.0`.

- **`skill/faderhand/`: the Faderhand agent skill**, installed on its own. `SKILL.md` routes Live tasks, MIDI
  measurement, blueprint execution and Vital units.
  - Live recipes and safety rules (`daw/`) and calibrated Vital preset units (`vital/`).
  - `tools/midi_check.py` measures a MIDI file against genre ranges and lists what to revise. The ranges come from
    Groove MIDI, PDMX and Mutopia aggregates, or from documented first principles (`tools/TARGETS.md`,
    `tools/PROVENANCE.md`). Trap and drill report "no target yet": no cleared source covers them.
  - `tools/preflight.py` (checks that a planned silence or entrance really happens in the render) and
    `tools/audition.py` (measures candidate sounds for one part: articulation, tail, reach, colour and, in the mix,
    audible share).
  - Corpus tools that rebuild the aggregate numbers from the cleared sources only (`tools/corpus/`).
  - A ten-task benchmark with its scorer, blind A/B tooling and the 2026-11-18 results (`evaluation/`).
- **Music Production Blueprint v0 and 0.2** (`skill/faderhand/blueprint/`): a JSON Schema, a validator with semantic
  checks, a converter from an existing song's MIDI, and an example built on the benchmark's own fixture.
- **Tests:** 17 new offline tests (12 blueprint, 3 preflight, 2 audition); the offline suite has 53. CI now installs
  `mido` and `jsonschema`.
- **Separate skills, bundled on the website.** The AI Music Studio and WavRead skills stay in their own repositories,
  and the MIDI knowledge pages moved to the Studio. `docs/ARCHITECTURE-AND-DELIVERY-PLAN.md` has the split, the
  bundle proposal, the regression plan and the next phases.

## v0.6.0-alpha.1 (2026-11-14)

- **Renamed to Faderhand, for Ableton Live 12.** The control script folder and class are now `Faderhand`
  (status bar: "Faderhand: listening on port 9878"), `tooling_info` reports name `Faderhand` and version `0.6.0`,
  the MCP server id is `faderhand`, and the docs, issue-template links and security advisory URL point to
  https://github.com/EZmannBuilds/faderhand. Tool behavior, port, safety guards and the server file path
  (`server/ableton_tooling_server.py`) are unchanged.
- **Back-compat.** `tools/install_remote_script.sh` installs `Faderhand` and also updates an already existing
  `WavReadBridge` folder, so an old Control Surface slot keeps listening on 9878 (enable only one of the two).
  The server reads `FADERHAND_HOST` / `FADERHAND_PORT` first, then falls back to `WAVREAD_BRIDGE_HOST` /
  `WAVREAD_BRIDGE_PORT`. Existing `claude mcp add wavread-bridge` configs keep working until removed. The Set
  identity key (`wavread.set_id`) is unchanged so earlier Sets keep their identity.

## v0.5.0-alpha.1 (2026-11-10)

- **Approval codes removed.** Tools now edit whichever saved Set is open, with no approval step. `authorize_set`,
  `confirm_authorization`, `set_approval_mode` and `revoke_authorization` are gone (79 tools). Unsaved Sets are still
  refused, deletions still need a disposable Set, recording through transport still counts as a write, and stop
  always runs. Work on copies of Sets that matter.
- In Live (12.4.16, macOS): connection 4/4 and the delete guard 3/3 pass. The full edit suite last passed under 0.4.0.

## v0.4.0-alpha.1 (2026-11-10)

First public release, as WavRead MCP Bridge. An experimental developer preview.

- Write protection: every Live Set opens read-only, and edits need that Set to be approved. One central classifier
  covers every command; unknown commands count as writes. Approval ends on a Set switch, Save As or reload.
- Input checks: loopback-only connections, a 1 MB request cap, validated command names, parameters and audio paths.
- Edits need a one-time code that Live shows in its status bar (`authorize_set`, then `confirm_authorization`).
  Codes can be turned off after one approval (`set_approval_mode`). Untitled Sets are refused, recording through
  transport counts as a write, and an approval idles out after 30 minutes.
- The control script is named WavReadBridge; env vars `WAVREAD_BRIDGE_HOST` / `WAVREAD_BRIDGE_PORT`.
- 83 MCP tools for returns and sends, routing and audio buses, devices and parameters, racks, sidechain, automation,
  clips and recording, Arrangement editing, and metering.
- Offline test suite in CI; end-to-end tests in Live 12.4.16 on macOS.
