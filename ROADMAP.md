# Roadmap

Planned, **not implemented**. What exists today, and how well it's tested, is in `docs/CAPABILITY-MATRIX.md`.

| Item | Notes |
|---|---|
| Export single-track stems | `export_audio` renders the Main only: background control can't open the Rendered Track pop-up. Today: `record_tracks_audio` records per-part stems in one real-time pass |
| Groove editing | `Clip.quantize` and groove pool access exist in the LOM; not wrapped yet |
| MPE note expression | Per-note pitch bend, slide and pressure. Velocity, chance, velocity range, release velocity and mute are done (`get_clip_notes`, `set_note_expression`) |
| Windows install and testing | The code is plain Python, but nothing has been tested on Windows and there's no install script |
| Better plugin discovery | Browser search and a portable inventory that doesn't depend on one machine |
| Better automation editing | Curve tension has no effect on Live 12.4; Arrangement lanes can only be recorded, not drawn |
| Presets and effect-chain management | Save and recall chains and rack presets (rack presets can't be saved through the API) |
| Packaged installation | A pip/uvx package and an installer for the Remote Script |
| Project-state inspection | A fuller, faster snapshot of a Set |
| More MCP clients | Only Claude Code has been tested |
| Other devices' sidechains | Glue, Gate, Auto Filter and Multiband sidechain inputs are untested |
| Take lanes and comping | The LOM calls exist on 12.4; untested |
