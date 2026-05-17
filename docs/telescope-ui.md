# Telescope UI

## Overview

The telescope UI is a self-contained static HTML file that implements the observatory console — a browser-playable interface for the telescope discovery game. No backend server is required.

## Generating the UI

```bash
# Generate the solar system scene first
uv run universe generate solar-system --seed local-sky --out data/generated/solar-system

# Optionally initialize game state (the UI creates default state if omitted)
uv run universe game init --out data/generated/game-state.json

# Export the telescope UI
uv run universe game export-ui \
  --scene data/generated/solar-system/scene.json \
  --out data/generated/telescope-ui.html

# Or with existing game state:
uv run universe game export-ui \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/telescope-ui.html

# Open in browser
open data/generated/telescope-ui.html
```

## First-run: naming your Research Entity

On first launch (or after a reset), the UI shows a naming modal. Enter a name for your research entity (e.g. "Hydrogen Ghost Institute"), choose an entity type, and optionally add a motto. Click "Random Name" for inspiration.

The entity name appears in the header and in discovery log messages for major events.

See [Research Entity](research-entity.md) for details.

## How to play

1. **Name.** On first launch, name your Research Entity. This is your observatory/institute identity.

2. **Observe.** Click an object in the left panel, then click "Observe Selected" to detect it. Or click "Survey All" to scan every object at once.

2. **Earn.** New detections and confidence upgrades award research points (RP). First-of-type detections earn a 50% bonus.

3. **Upgrade.** Open the Tech Tree tab on the right panel. Click "Unlock" on a tier you can afford. New tiers add signal types, improve sensitivity and resolution, and extend effective distance.

4. **Repeat.** After upgrading, re-observe or survey again. Previously invisible objects may now be detectable. Candidate classifications may upgrade to confirmed.

5. **Explore.** Switch active telescope in the Tech Tree panel to use specific instruments. Combine observations from different tiers for multi-messenger confidence bonuses.

## UI layout

| Panel | Purpose |
|---|---|
| **Header** | Research Entity name, active telescope, RP, signal count, discovery count |
| **Left: Controls** | Observe/Survey buttons, scrollable object list |
| **Center: Sky Map** | 2D radial projection — Earth/observatory at center, objects by distance |
| **Right: Tabs** | Object detail · Tech tree · **Surveys** · **Milestones** |
| **Bottom: Log** | Timestamped discovery log |

### Surveys tab

Lists every survey program with current status (Locked / Available /
Active / Completed), progress (e.g. `3/5`), prerequisites, and reward.
Available surveys expose a **Start Survey** button; completed surveys with
unclaimed rewards expose a **Claim** button (defensive — surveys are
auto-claimed on completion).

### Milestones tab

Splits achievements into "Achieved" and "Remaining". Each card shows the
description, reward, and a SPECULATIVE badge where applicable. Achieved
milestones display the auto-claimed reward; remaining ones display the
target reward.

## Sky map

The sky map uses a 2D top-down radial layout:

- **Solar system scenes:** Logarithmic distance compression — Earth at center, planets placed by approximate AU distance.
- **Deep-field scenes:** Linear projection from observer origin.

Objects are color-coded by type and alpha-faded by confidence. Undiscovered objects appear dimmed. Click an object on the map to select it.

## State persistence

Game state is stored in browser `localStorage` keyed by scene ID. Each scene has independent progress.

- **Reset:** Click the "Reset" button in the header to clear all progress for the current scene.
- **Export:** Click "Export" to download the current state as JSON.
- **Import:** Not yet implemented in the UI. State can be loaded via the CLI `--state` flag when generating the HTML.

## Confidence levels

| Range | Label | Display |
|---|---|---|
| 0.00–0.24 | Not detected | Object hidden or barely visible |
| 0.25–0.49 | Signal anomaly | Shown as "Signal Anomaly" — type uncertain |
| 0.50–0.74 | Candidate | Name shown with "(candidate)" suffix |
| 0.75–0.94 | Confirmed | Full name, properties, relationships |
| 0.95–1.00 | Characterized | Full detail including all properties |

## Embedded data

The HTML file embeds nine JSON datasets at build time:

1. **Scene data** — full `SceneRegion` (objects, nodes, filaments, metadata).
2. **Game state** — `ResearchState` (RP, unlocked tiers, discoveries, research entity, surveys, milestones, turn).
3. **Tech tree** — all 12 `TelescopeTier` definitions.
4. **Discovery requirements** — per-object-type signal/sensitivity/resolution rules.
5. **Random entity names** — curated list for the "Random Name" button.
6. **Entity type labels** — display names for the entity type dropdown.
7. **Entity modifiers** — per-entity-type mechanical effects (mirrors Python `EntityModifier`).
8. **Survey programs** — all `SurveyProgram` definitions (id, targets, requirements, reward).
9. **Milestones** — all `Milestone` definitions (id, description, reward, speculative flag).

The client-side JavaScript implements the same confidence calculation,
point-award logic (including entity **discovery_rp_multiplier**), tier **effective costs**, survey-progress rules (including **survey_progress_bonus**), survey/milestone **reward multipliers**, and milestone predicates as the
Python modules. Survey/milestone state is persisted in `localStorage`
alongside discoveries and entity data.

## Current limitations

- No import-state UI (use CLI `--state` flag instead).
- No visual/signal mode switching (planned for Phase 4).
- Sky map is 2D — no 3D orbit controls (use `preview.html` for 3D view).
- No animation or time-domain events.
- No sound or visual effects for discovery moments.
- Discovery log is session-only (not persisted).
- Only one active survey at a time; no survey queue.
- Milestone notifications appear in the discovery log only — no toasts.

## Future: Unreal/Godot mapping

The telescope UI is a prototype for the observatory console concept. In engine frontends:

- **Unreal Engine:** UMG widget implementing the same panels. Telescope viewfinder renders the actual 3D scene with instrument-specific post-processing. Tech tree becomes a UMG tree widget.
- **Godot:** Control nodes for panels. Telescope viewfinder uses Godot's 3D viewport with custom shaders per instrument.

The embedded JSON data format is identical to what the engine importers will consume.
