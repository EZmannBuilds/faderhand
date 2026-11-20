# Where the ranges in `tools/midi_check.py` come from

| Check | Range | Basis |
|---|---|---|
| Played feel: share of notes exactly on the grid | 0–0.3 | Measured, Groove beats: quantized share p90 is 0.10–0.19 per style. A generous ceiling. |
| Played feel: drum jitter (ms) | 3–12 | Groove's local jitter medians are 16–26 ms, but they include drift in long takes. v2 (2026-11-18) narrowed the range after a blind judge marked looser grooves as sloppy. This is an inference; check it by listening. |
| Played feel: hat velocity structure | 0.2–0.8 | Measured, Groove: hats p10–p90 about 0.11–0.98 for rock and 0.17–0.56 for funk. Range set around the funk, hip-hop and soul medians. |
| Hat velocity SD | 8–27 | Measured, Groove held-out funk, soul and hip-hop beats: p10–p90 8.6–27. |
| Snare velocity SD | 12–45 | Measured, Groove: snare SD medians of 23–36. |
| Snare later than hats (ms) | 2–25 | Measured, Groove funk and hip-hop: backbeat about 5–15 ms after the hats (medians). |
| Swing per style | boom-bap 52–62, hip-hop live 50–61, funk 51–74, soul 55–77, neo-soul 54–68, jazz 55–77 | Measured, Groove 16th swing p10–p90 per style. Neo-soul and boom-bap are set from the hip-hop and soul data (inference). |
| Ghost snares per bar | funk 1.5–7, soul 1–5, boom-bap 0.5–4 | Measured, Groove medians (funk 3.7, soul 2.2, hip-hop 1.5) with spread. |
| Backbeat on 2 and 4 | ≥ 0.6 of bars | Measured, Groove beats: medians 0.61–0.75. |
| Programmed feel: grid share ≥ 0.6, jitter ≤ 6 ms | | Practice. Also matches the local programmed packs. |
| Trap and drill: half-time backbeat, rolls 0.25–1.5 per bar, low notes on kicks 0.35–1.0 (v2: a fully locked 808 is allowed), kicks with a low note ≥ 0.8, 808 notes per bar 2.5–6.5, slides 0.5–3 per bar, drill octave jumps 0.25–0.6, drill rolls triplet | | **Practice, informed by local pending-clearance numbers** (the Studio skill's `shared/MIDI_KNOWLEDGE/local/ZYNTHION_FINDINGS.md`, local only). Confirm or replace them before a public release. |
| House and techno four-on-the-floor; techno bass off-16th share ≥ 0.3 | | Practice (also matches local packs). |
| Classical: melody stepwise share 0.3–0.65, leap recovery 0.3–0.7, contrary motion 0.2–0.55, parallel fifths ≤ 2 per 100 moves | | Measured, PDMX classical and Mutopia: step 0.39 (0.17–0.61), recovery 0.40, contrary 0.36 (0.19–0.50), parallel fifths median 0. |
| Generic: bar uniqueness ≥ 0.3; flat velocities; random hat velocity (structure under 0.15 with SD over 10) | | Inference from the measured distributions: no human take or published pattern sits there. |
