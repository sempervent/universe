# Balance playtesting

Deterministic autoplay instruments the telescope game loop in Python. Use it to answer pacing questions (RP income, tier unlocks, surveys, milestones, entity modifiers) without adding new mechanics.

**Python autoplay is canonical** for balance runs. Godot and the static HTML UI can export game state for manual review; they do not drive the matrix or balance report.

## Commands

### Single playtest

```bash
uv run universe game playtest \
  --scenario solar_tutorial_basic \
  --entity-type backyard_observatory \
  --seed local-sky \
  --out data/generated/playtests/solar_tutorial_basic_backyard.json
```

Optional: `--max-turns N`, `--no-events` (skip `*_events.jsonl`).

Outputs next to the run path:

- `run.json` — full `PlaytestRun` (events + `final_state` + `summary`)
- `run_events.jsonl` — one `PlaytestEvent` per line (unless `--no-events`)
- `run_summary.md` — short human summary

### Matrix

```bash
uv run universe game playtest-matrix \
  --out data/generated/playtests/matrix
```

Runs default scenarios × all non-custom entity types. Filters:

- `--scenario ID` (repeatable)
- `--entity-type TYPE` (repeatable)
- `--seed SEED`
- `--max-turns N`
- `--no-deep-field` — skip scene-001 scenarios

Writes `matrix/runs/*.json` and `matrix-summary.json`.

### Balance report

```bash
uv run universe game balance-report \
  --input data/generated/playtests/matrix \
  --out data/generated/playtests/balance-report.md
```

Accepts a single run JSON, a matrix directory, or any folder of run JSON files.

## Scenarios

| ID | Scene | Intent |
|----|-------|--------|
| `solar_tutorial_basic` | solar-system | Tutorial pacing, cheapest upgrades |
| `solar_to_space_optical` | solar-system | Reach `space_optical` from solar loop |
| `deep_field_first_contact` | scene-001 | First deep-sky detections (starts at space optics) |
| `radio_transition` | scene-001 | Radio / CMB / jets (starts at `radio`) |
| `compact_object_transition` | scene-001 | X-ray/gamma compact objects |
| `late_game_inference` | scene-001 | Weak lensing / dark matter |
| `now_scope_smoke` | scene-001 | Speculative tier smoke test |
| `solar_to_deep_field_campaign` | solar → scene-001 | Campaign greedy; auto-switch at deep-field unlock |
| `campaign_instrument_ladder` | all six campaign scenes | Full ladder pacing (`campaign_ordered` strategy) |

Strategy default: `greedy_research` (start matching survey → observe → milestones/surveys auto-claim → cheapest upgrade → set highest active tier).

### Campaign autoplay strategies

| Strategy | Behavior |
|----------|----------|
| `greedy_research` | Single-scene greedy loop |
| `campaign_greedy` | On unlock, jump to highest newly unlocked scene by catalog order |
| `campaign_ordered` | Stay in catalog order; advance only when current scene has meaningful discoveries and few easy targets remain; prefer scene-recommended surveys |

Use `campaign_instrument_ladder` with `campaign_ordered` for ladder balance reports:

```bash
uv run universe game playtest \
  --scenario campaign_instrument_ladder \
  --entity-type private_institute \
  --seed local-sky \
  --out data/generated/playtests/campaign_instrument_ladder_private.json
```

## Event types

`observe_object`, `discover_object`, `confirm_object`, `characterize_object`, `survey_started`, `survey_progressed`, `survey_completed`, `milestone_achieved`, `telescope_unlocked`, `telescope_set_active`, `blocked_upgrade`, `no_observable_targets`, `playtest_warning`.

Each event records RP before/after and `delta_research_points`.

## Reading the balance report

1. **Executive summary** — run counts and solar→space success rate.
2. **Scenario results** — per-scenario RP and tier outcomes.
3. **Entity comparison** — average RP across runs.
4. **Tier unlock timing** — turn when each tier first unlocked, by entity.
5. **Survey / milestone timing** — completion turns.
6. **RP economy** — RP curves by turn.
7. **Warnings** — stuck loops, one-turn surveys, unreachable targets.
8. **Warnings** — stuck loops, ladder-specific scene pacing.
9. **Suggested adjustments** — heuristic flags (not automatic rebalance).

Sections **7e–7g** cover campaign progression:

- **7e** — scene unlocks and visits (all campaign scenarios)
- **7f Campaign Ladder Analysis** — per-scene unlock/visit/discovery table, median first-discovery turns, visit sequences, tier unlock context, now-scope status (from `campaign_instrument_ladder` runs)
- **7g** — catalog alignment checks (recommended surveys, detectable objects at unlock tier, signal-mode fit)

### Ladder metrics (in `run.json` → `summary`)

Per scene: `unlock_turn`, `first_visit_turn`, `first_discovery_turn`, `first_confirmed_discovery_turn`, `total_discoveries`, `total_rp_earned`, `surveys_completed`, `milestones_achieved`, `turns_spent_active`, `no_rp_turns_while_active`.

Also: `scene_visit_sequence`, `tier_unlock_context` (tier → turn, active scene, RP cost).

Alignment validation: `universe.game.campaign_balance.run_campaign_alignment_checks()` (used in report §7g and `tests/test_campaign_balance.py`).

### Warning examples

- **Stuck** — no RP change for more than five consecutive turns.
- **First Light Survey turn 1** — reported as INFO when intentional tutorial pacing.
- **Follow-up RP** — see section 7b; small diminishing returns after solar exhaustion.
- **Guidance hints** — section 7c lists `solar_exhausted_deep_field_ready` when applicable.
- **Cannot reach space_optical** — solar-only loop may need more RP sources.
- **Now-scope exclusive content** — no detections tagged with now-scope tier.
- **Scene unlocked but never visited** — ladder autoplay skipped a program.
- **Scene visited but no discoveries** — scene may lack detectable objects at unlock tier.
- **First discovery late** — more than ~8 turns after unlock (configurable in `collect_ladder_warnings`).
- **Visit sequence out of order** — intermediate scene skipped when a later one was visited first.

## Frontend manual playtests

- **CLI / JSON state** — `game init`, `game observe`, etc. produce `ResearchState` JSON suitable for diffing.
- **Static HTML** — exported UI embeds scene + state; discovery log lives in-browser (optional future “Export Playtest Log”).
- **Godot** — save/export uses the same state schema; map events to `PlaytestEvent` in a future pass if needed.

## Pacing changes (post-instrumentation)

- **First Light Survey** (`local_sky_survey`): goal 8, reward 8 RP; citizen-science bonus only when `completion_goal >= 8`.
- **Follow-up observations**: capped diminishing RP per object (see `discovery.py`).
- **Guidance hints**: `game status`, `game report`, and balance report section 7c.
- **Causality Shadow** (`speculative_anomaly` in Scene 001): now-scope-only placeholder.

## Observation RP caps

Each scene caps **primary discovery RP** per `observe_scene` pass (discoveries still register; only funding is bounded). Caps live in `src/universe/game/observation_rewards.py`:

| Scene | Cap per observe |
|-------|-----------------|
| solar-system | 70 |
| scene-001 | 250 |
| radio-cmb-survey | 150 |
| stellar-remnant-field | 150 |
| cosmic-web-map | 250 |
| now-scope-anomaly-field | 400 |

Survey and milestone RP are **not** capped. Playtests record `reward_cap_applied` events; balance report §7h summarizes cap frequency.

## Assumptions

- Scenes generated in-process (`generate_solar_system`, `generate_scene_001`) with scenario seeds.
- Bootstrapped tiers in late scenarios do not spend RP.
- Same seed + scenario + entity type ⇒ identical run id and summary (deterministic).

## See also

- [discovery-loop.md](discovery-loop.md)
- [entity-backgrounds.md](entity-backgrounds.md)
- [survey-programs.md](survey-programs.md)
- [milestones.md](milestones.md)
