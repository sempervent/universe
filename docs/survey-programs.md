# Survey Programs

Survey programs are named research campaigns the Research Entity runs in
addition to ad-hoc observations. Each survey has a focused target list, a
goal count, prerequisite tiers/signals, and a one-time research-point
reward. Surveys are how the game expresses *medium-term direction* — they
are not instant accomplishments.

Surveys are deterministic, declarative, and scene-scoped. They never modify
scene data. They mutate only the player's `ResearchState`.

## Lifecycle

1. **LOCKED** — required telescope tiers or signal types are missing.
2. **AVAILABLE** — prerequisites met but the survey is not active.
3. **ACTIVE** — the player has chosen this as their current campaign. Only
   one survey is active at a time.
4. **COMPLETED** — the goal count has been reached. The reward is
   auto-credited the moment the goal is met.

A survey's status is dynamic; it is computed from the current state by
`survey_status(state, survey)`.

## Counting rule

A discovery counts toward the active survey if **all** of the following are true:

- `object_type` is in `target_object_types` (or the survey is speculative
  with an empty target list, e.g. `now_scope_first_light`).
- The current `scene.id` matches the survey's `scene_scope`
  (`solar_system`, `deep_field`, or `any`).
- The discovery's confidence is at least the survey's `min_confidence`
  (defaults to 0.5; the multi-messenger program requires 0.75).
- All `required_signal_types` were detected in this observation.

The same `object_id` cannot be counted twice for the same survey, so
re-observing a previously credited object does not "farm" progress.

## CLI

```bash
# List every program with status, progress, requirements
uv run universe game surveys --state data/generated/game-state.json

# (Optional) include a scene to flag scope mismatches
uv run universe game surveys --state ... --scene data/generated/solar-system/scene.json

# Activate a campaign
uv run universe game start-survey \
  --state data/generated/game-state.json \
  --survey local_sky_survey \
  --out data/generated/game-state.json

# Idempotently claim a completed survey's reward
uv run universe game claim-survey \
  --state data/generated/game-state.json \
  --survey local_sky_survey \
  --out data/generated/game-state.json
```

`game observe` automatically advances any active survey, completes it on
goal, and credits the reward. The `claim-survey` command is provided as a
safety net for legacy state files.

## Default catalogue

| ID | Name | Tier req. | Targets | Goal | Reward |
|----|------|-----------|---------|------|--------|
| `local_sky_survey` | Local Sky Survey | naked_eye | star, planet, moon | 5 | 10 |
| `planetary_census` | Planetary Census | ground_optical | planet, moon | 8 | 20 |
| `small_bodies_watch` | Small Bodies Watch | improved_ground | asteroid, comet | 2 | 20 |
| `deep_field_survey` | Deep Field Survey | space_optical | galaxy, quasar, lyman_alpha_blob | 10 | 75 |
| `radio_sky_survey` | Radio Sky Survey | radio | cmb_background, quasar, galaxy | 5 | 75 |
| `compact_object_search` | Compact Object Search | xray_gamma | black_hole, magnetar | 2 | 100 |
| `multi_messenger_event_program` | Multi-Messenger Event Program | multi_messenger | black_hole, magnetar, quasar | 3 | 175 |
| `cosmic_web_mapping` | Cosmic Web Mapping Program | dark_matter_mapper | filament, node, void | 8 | 225 |
| `dark_matter_inference_program` | Dark Matter Inference Program | dark_matter_mapper | filament, void, galaxy | 5 | 300 |
| `now_scope_first_light` ⚠ | Now-Scope First Light *(speculative)* | now_scope | (any object via now-signal) | 1 | 500 |

Speculative surveys are clearly labelled in the CLI, the report, and the UI.

## UI

The browser telescope UI exposes surveys via the **Surveys** tab in the
right column. Each card shows current status, progress, prerequisites, and
either a `Start Survey` or `Claim` button when applicable. Survey state is
persisted in `localStorage` along with the rest of the game state.

## Balance playtesting

Survey completion turn timing is recorded in autoplay runs (`survey_completed` events). Use `playtest-matrix` + `balance-report` to spot surveys that finish in one turn for all entity types. See [balance-playtesting.md](balance-playtesting.md).

Campaign scenes list `recommended_survey_ids` in the catalog; `campaign_ordered` autoplay prefers those when starting a survey. Report §7g validates that each recommended survey exists and has plausible targets in its scene.

## Limitations

- Only one active survey at a time. A "queue" is not yet supported.
- Survey scope is currently a coarse string (`solar_system` / `deep_field`
  / `any`). It is matched against `scene.id`. A scene with id
  `solar-system` is considered solar-system-scoped; everything else is
  deep-field-scoped.
- Surveys do not yet unlock other surveys directly. The `unlocks` field is
  reserved for future use.
- Entity-type bonuses (e.g. citizen-science network gets cheaper surveys)
  are not implemented yet.
