# Tutorial objectives

First-run **tutorial objectives** guide new players through the core loop without a quest engine or story rails. They differ from **milestones** (celebration of firsts) and **guidance hints** (soft nudges).

## Chain (10 steps)

1. Name your Research Entity  
2. Observe the local sky (solar-system discovery)  
3. Complete First Light Survey (`local_sky_survey`)  
4. Unlock `ground_optical`  
5. Observe a transient event  
6. Unlock `space_optical`  
7. Unlock Scene 001 in the campaign  
8. Switch active scene to `scene-001`  
9. Start `deep_field_survey`  
10. First deep-field discovery (galaxy / quasar / LAB)

Rewards are intentionally small (5–25 RP each). Evaluation catches up if the player completes steps out of order.

## CLI

```bash
uv run universe game objectives --state data/generated/game-state.json
```

`game status` shows the active objective. `game observe`, `upgrade`, `start-survey`, `set-scene`, and `observe-transient` evaluate objectives and print completions.

## UI

- **Static HTML:** Objectives tab + header hint; embedded `OBJECTIVES` catalog.  
- **Godot:** Objectives tab; `ObjectiveEngine.gd` mirrors Python lightly.

## Data

Exported in `objectives.json` via `universe game export-godot-data` (manifest schema **0.5.0**).

## Related docs

- [discovery-loop.md](discovery-loop.md)  
- [transient-events.md](transient-events.md)  
- [campaign-progression.md](campaign-progression.md)
