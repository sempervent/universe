# Game Design: universe

## Core concept

`universe` is a telescope-based cosmic discovery game. The player represents a named Research Entity — an observatory, institute, or research group — that begins on Earth with naked-eye observation and progressively unlocks instruments that reveal deeper layers of reality.

There is no spaceship. The viewpoint is always a telescope or observatory interface. The player expands perception, not physical location.

## Research Entity

At game start, the player names their Research Entity. This identity appears throughout the game — in status displays, discovery logs, reports, and the telescope UI header.

Entity types (flavor only, no mechanical effect):
- Backyard Observatory, University Lab, National Observatory, Private Institute, Orbital Consortium, AI Research Bureau, Citizen Science Network, Occult Sky Society, Corporate Research Division, Custom.

See `docs/research-entity.md` for full documentation.

## Core loop

```
Observe → Detect signal → Identify object → Earn research points
  → Upgrade instruments → Unlock deeper phenomena → Combine observations
    → Discover increasingly exotic cosmic structures
```

## Telescope-first viewpoint

The player never physically flies to objects. Instead:

1. Point the telescope at a region of sky or a known target.
2. The instrument detects signals within its capability (wavelength, sensitivity, resolution).
3. The game evaluates what the instrument can resolve and reports detection confidence.
4. Partial detections create "candidates" — the player must combine instruments or upgrade to confirm.
5. Research points are earned from confirmed identifications.

## Progression

The player begins with naked-eye stargazing (Sun, Moon, bright planets, constellations). Over 12 telescope tiers, they advance from ground-based optical through radio, X-ray, gravitational-wave, neutrino, and eventually speculative instruments.

See `telescope-progression.md` for full tier definitions.

## Research points

Points are earned by:
- First detection of an object type (+base points)
- Confirming a candidate to higher confidence (+bonus)
- Characterizing an object fully (+completion bonus)
- Discovering objects requiring multi-messenger observations (+difficulty bonus)

Points are spent to unlock telescope tiers.

## Scientific vs speculative content

| Tier range | Status |
|---|---|
| 0–9 | Scientifically grounded |
| 10 | Extrapolation (dark matter detection is real science but individual dark matter "observatories" are speculative as game objects) |
| 11 | Explicitly speculative/fictional — the "now-scope" violates causality and is labeled as such |

Objects detected only by speculative instruments are marked `speculative: true` in data.

## How the existing universe data feeds the game

The game layer reads `scene.json` files produced by the existing deterministic generator. It does not modify or depend on the generation internals:

```
Generator → scene.json → Game layer reads scene → Evaluates vs player state → Returns discoveries
```

The game layer imports `SceneRegion` from the data model but does not call procedural generators at runtime. It operates purely on exported scene data.

## Starter experience

The player begins with a solar-system scene containing the Sun, Moon, and planets. These are observable with naked-eye and early optical telescopes. This teaches the observe→identify→earn loop before introducing deep-sky objects.

Scene 001 ("The Lyman-alpha Furnace") is available as the first deep-sky target once the player has sufficient telescope capability (roughly Tier 3+).

## Telescope UI

The first interactive UI is a self-contained static HTML file — the Observatory Console. It implements the full observe→discover→upgrade loop client-side using embedded JSON data and browser localStorage for persistence.

To generate:

```bash
uv run universe game export-ui \
  --scene data/generated/solar-system/scene.json \
  --out data/generated/telescope-ui.html
```

See `docs/telescope-ui.md` for full documentation.

## Future directions

- Enhanced telescope UI (signal mode switching, import state, animations)
- Unreal/Godot rendering frontends
- Time-domain events (supernovae, GRBs, magnetar flares)
- Catalog comparison (player discoveries vs real survey data)
- Multiplayer observing campaigns
