# Transient observation events

Deterministic **turn-window** events add time-domain astronomy without a real-time scheduler or calendar UI.

## Model

- **Catalog:** `src/universe/game/transients.py` — fixed definitions (`TransientEventDefinition`).
- **State:** `ResearchState.transient_events` — per-event `TransientEventState` (active, discovered, expired, reward claimed).
- **Rules:** An event is *active* when `start_turn <= turn < start_turn + duration_turns` and the player is in the matching campaign scene. Observation requires the minimum telescope tier and at least one required signal type.

Transient RP is **separate** from per-pass discovery RP caps (see `observation_rewards.py`).

## CLI

```bash
uv run universe game transients --state data/generated/game-state.json --scene solar-system

uv run universe game observe-transient \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --event solar_flare_001 \
  --out data/generated/game-state.json
```

`game status` and `game report` list active, upcoming, expired, and observed events for the active scene.

## Catalog (summary)

| ID | Scene | Window (turns) | Tier | RP |
|----|-------|----------------|------|-----|
| solar_flare_001 | solar-system | 2–5 | ground_optical | 15 |
| comet_brightening_001 | solar-system | 3–8 | improved_ground | 18 |
| quasar_outburst_001 | scene-001 | 6–13 | space_optical | 60 |
| magnetar_flare_001 | stellar-remnant-field | 8–12 | xray_gamma | 100 |
| gravitational_wave_candidate_001 | stellar-remnant-field | 12–17 | gravitational_wave | 130 |
| lensing_anomaly_001 | cosmic-web-map | 18–29 | dark_matter_mapper | 180 |
| neutrino_burst_001 | stellar-remnant-field | 20–24 | neutrino_cosmic_ray | 150 |
| causality_echo_001 | now-scope-anomaly-field | 30–49 | now_scope | 320 (speculative) |

## Playtests

Autoplay (`campaign_ordered`) observes available transients after each `observe_scene` pass. Balance report **§7i** summarizes observed/missed events and transient RP.

## Frontends

- **HTML:** Transients tab in exported telescope UI.
- **Godot:** `transient_events.json` in the data bundle; `TransientEngine.gd` mirrors core rules.
- **Unreal:** No transient gameplay (Scene 001 cinematic only).
