# Campaign scene progression

The campaign layer coordinates **which observation scene** the player is working in. It is not a story engine — only a small catalog, unlock rules, and an active scene pointer.

## Scene catalog

Python source: `src/universe/game/scenes.py`

| Scene id | Name | Class | Unlock |
|----------|------|-------|--------|
| `solar-system` | Local Solar System | tutorial / solar | always |
| `scene-001` | The Lyman-alpha Furnace | deep field | `space_optical` tier (or `first_deep_field_ready` milestone) |
| `radio-cmb-survey` | Radio CMB Survey | radio survey | `radio` |
| `stellar-remnant-field` | Stellar Remnant Field | high energy | `xray_gamma` |
| `cosmic-web-map` | Cosmic Web Map | deep field / structure | `dark_matter_mapper` |
| `now-scope-anomaly-field` | Now-Scope Anomaly Field | speculative | `now_scope` |

Full scene reference: [campaign-scenes.md](campaign-scenes.md).

Each entry includes default generator seed, output path, recommended surveys, and signal modes.

## Game state

`ResearchState.campaign` holds:

- `active_scene_id` — campaign focus (default `solar-system`)
- per-scene `unlocked`, `visited`, unlock/visit turns
- `completed_scene_ids` (reserved for future use)

Older saves without `campaign` load with solar unlocked and deep field locked until tiers/milestones are evaluated.

## CLI workflow

```bash
uv run universe generate solar-system --seed local-sky --out data/generated/solar-system

uv run universe game init --name "Hydrogen Ghost Institute" \
  --out data/generated/game-state.json

uv run universe game observe \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/game-state.json

uv run universe game scenes --state data/generated/game-state.json

uv run universe game generate-scene --scene scene-001

uv run universe game set-scene \
  --state data/generated/game-state.json \
  --scene scene-001 \
  --out data/generated/game-state.json

uv run universe game observe \
  --scene data/generated/scene-001/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/game-state.json
```

Also: `universe game campaign` prints active scene, unlocks, and recommended next scene.

## Frontends

### Static HTML (`export-ui`)

Embeds the scene catalog and a **Campaign** tab with lock state and generate/set-scene commands. The HTML file still renders **one** `scene.json`; switching scenes requires regenerating/exporting with the desired scene file.

### Godot

`export-godot-data` writes `scene_catalog.json`. The **Campaign / Observing Program** tab lists all scenes with lock status, file presence, recommended surveys/signals, and actions to **Load Scene** / **Set Active**. Godot mirrors campaign unlock rules in `GameState.gd` but does not run Python — missing files show `uv run universe game generate-scene --scene <id>`. See [godot-frontend.md](godot-frontend.md).

### Unreal

Unreal remains a **cinematic renderer** for specific exported scenes (currently Scene 001). Campaign progression is decided in Python; export Scene 001 for Unreal when the campaign recommends it.

## Playtesting

| Scenario | Strategy | Use |
|----------|----------|-----|
| `solar_to_deep_field_campaign` | `campaign_greedy` | Solar → deep field transition only |
| `campaign_instrument_ladder` | `campaign_ordered` | Full six-scene ladder pacing |

Balance reports include campaign transition timing (§7e) and **Campaign Ladder Analysis** (§7f) when ladder runs are in the matrix input. See [balance-playtesting.md](balance-playtesting.md).

**Transient events** fire on fixed turn windows per scene (solar flares, magnetar bursts, speculative now-scope echoes). List with `game transients`; observe with `game observe-transient`. See [transient-events.md](transient-events.md).
