# Research entity backgrounds

Each **entity type** (backyard observatory, university lab, national observatory, …) maps to a small **EntityModifier** record: a name, short description, and a handful of numeric multipliers. These effects are intentionally **tiny** so the game stays about telescopes and discovery, not min-maxing spreadsheets.

- **Python is canonical.** The static HTML UI and the Godot frontend mirror the same rules client-side for responsiveness; if anything disagrees with the CLI, trust Python.

## Modifier summary

| Entity type | Modifier name | Main effect |
|-------------|----------------|-------------|
| `backyard_observatory` | Backyard Persistence | Cheaper **ground_optical** and **improved_ground** tier costs |
| `university_lab` | Peer Review Engine | **+10%** milestone RP |
| `national_observatory` | Institutional Survey Machine | **+10%** survey completion RP |
| `private_institute` | Flexible Funding | **+5%** discovery RP |
| `orbital_consortium` | Launch Infrastructure | Cheaper costs from **space_optical** onward (`tier_index` ≥ 3) |
| `ai_research_bureau` | Pattern Classifier | **+0.05** confidence when already detectable (never creates detections from zero) |
| `citizen_science_network` | Many Eyes | **+1** survey progress step per qualifying discovery (capped at goal) |
| `occult_sky_society` | The Stars Whisper Back | **+10%** RP on **speculative** surveys and milestones |
| `corporate_research_division` | Procurement Department from Hell | **−5%** upgrade costs, **−5%** milestone RP |
| `custom` | Custom Charter | **No** mechanical modifier |

Unknown or future entity strings fall back to the same neutral profile as **custom**.

## Where it applies (Python)

- **Discovery RP** — after the usual confidence and first-type bonuses, multiplied by `discovery_rp_multiplier`, rounded, minimum **1 RP** when a payout would already occur.
- **Confidence** — after the normal physics/signal gates, if confidence **> 0**, add `confidence_bonus` and clamp to **1.0**.
- **Tier costs** — `upgrade_cost_multiplier` × optional `early_optical_upgrade_cost_multiplier` (ground optical tiers only) × optional `space_upgrade_cost_multiplier` (space track tiers). Displayed **effective** cost matches what `unlock_tier` charges.
- **Survey completion RP** — `survey_rp_multiplier`, with an extra **×1.1** when both the survey and the entity are speculative (`occult_sky_society`).
- **Survey progress** — each new qualifying discovery increments progress by **1 + survey_progress_bonus** (citizen science: +1 step), capped at `completion_goal`.
- **Milestone RP** — `milestone_rp_multiplier`, with the same speculative **×1.1** when applicable.

## CLI & exports

- `universe game init` prints the entity type and a one-line **Background** summary.
- `universe game status` lists modifier name, description, and **effective** upgrade costs for available tiers.
- `universe game tech-tree --state …` shows **effective** RP costs.
- `universe game report` includes a **Research Entity Background** section.
- `universe game export-godot-data` writes **`entity_modifiers.json`** next to the other bundle files (manifest **schema_version 0.2.0**).
- `universe game export-ui` embeds the modifier table for the browser UI.

## Balance assumptions

Modifiers are tuned so the early game is **not trivialised**: most deltas are a few percent or a handful of RP on a path that already awards tens to hundreds of points per survey. **Corporate** is the only profile that deliberately trims milestone payouts in exchange for slightly cheaper upgrades.

Compare entity types with `universe game playtest-matrix` and `balance-report` — see [balance-playtesting.md](balance-playtesting.md).

## See also

- `src/universe/game/entity.py` — data definitions
- `docs/research-entity.md` — narrative / UX context
- `docs/game-design.md` — overall game loop
