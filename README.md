# universe

Engine-agnostic cosmic visualization sandbox and telescope-based discovery game.

## What this is

`universe` generates scientifically grounded, navigable cosmic scenes and wraps them in a telescope progression game. The player begins on Earth with naked-eye observation and progressively unlocks instruments — from ground optical through radio, X-ray, gravitational-wave, and eventually speculative observatories — discovering increasingly exotic phenomena along the way.

The project produces an engine-agnostic JSON scene format, a browser-previewable Three.js visualization, and a CLI-driven game prototype. The data core is designed for future import into Unreal Engine, Godot, or any 3D frontend.

## Current vertical slice

**Scene generation:**
- Deterministic procedural generation of Scene 001: "The Lyman-alpha Furnace" (z ≈ 3.1 protocluster).
- Starter solar system scene with Sun, Moon, planets, moons, asteroid, and comet.
- Typed Pydantic data models for all cosmic objects.
- Object relationships: quasar↔black hole, LAB↔embedded galaxies, magnetar↔host galaxy.
- Interactive Three.js preview with bloom, star field, orbit controls, visual modes, and metadata inspector.

**Game prototype:**
- Player-named Research Entity (observatory, institute, sky cult, etc.).
- 12-tier telescope tech tree (naked eye → now-scope).
- Signal-based discovery engine with confidence levels.
- Research point progression and instrument upgrades.
- Multi-messenger astronomy bonus for combining signal types.
- CLI commands for the full observe→discover→upgrade loop.
- Browser-playable telescope UI with naming flow, sky map, tech tree, and discovery log.

## Quickstart — Scene generation

```bash
uv sync

# Generate the deep-sky scene
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
open data/generated/scene-001/preview.html

# Generate the starter solar system
uv run universe generate solar-system --seed local-sky --out data/generated/solar-system

# Inspect a scene
uv run universe inspect data/generated/scene-001/scene.json

# Run tests
uv run pytest
```

## Quickstart — Game prototype

```bash
# Generate the starter scene
uv run universe generate solar-system --seed local-sky --out data/generated/solar-system

# Initialize game state with a named Research Entity
uv run universe game init \
  --name "Hydrogen Ghost Institute" \
  --entity-type private_institute \
  --motto "Listening for the old light." \
  --out data/generated/game-state.json

# Observe the solar system (earn research points)
uv run universe game observe \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/game-state.json

# Check status
uv run universe game status --state data/generated/game-state.json

# Upgrade telescope
uv run universe game upgrade \
  --state data/generated/game-state.json \
  --tier ground_optical

# Observe again to find new objects
uv run universe game observe \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/game-state.json

# View the tech tree
uv run universe game tech-tree

# Generate a discovery report
uv run universe game report \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/game-report.md
```

## Quickstart — Telescope UI (browser game)

```bash
# Generate scene and export the playable UI
uv run universe generate solar-system --seed local-sky --out data/generated/solar-system
uv run universe game export-ui \
  --scene data/generated/solar-system/scene.json \
  --out data/generated/telescope-ui.html
open data/generated/telescope-ui.html
```

The telescope UI is a self-contained HTML file with the observatory console — observe objects, earn research points, unlock telescope tiers, and discover increasingly exotic phenomena. Game state persists in browser localStorage.

See [Telescope UI docs](docs/telescope-ui.md) for details.

## What is intentionally not implemented yet

- Unreal/Godot rendering frontends (scaffolded only — see `frontends/`).
- Real N-body cosmological simulation.
- Volumetric rendering, gravitational lensing, relativistic jet particles.
- Time-domain events (supernovae, GRBs, magnetar flares).
- Real astronomical catalog ingestion.

## Project structure

```
src/universe/
  models.py             # Pydantic data models (Vector3, CosmicObject, SceneRegion, etc.)
  units.py              # Coordinate/unit conventions
  schema.py             # JSON Schema utilities
  cli.py                # Click CLI (generate, inspect, summarize, game)
  procedural/
    cosmic_web.py        # Cosmic web graph (nodes + filaments)
    objects.py           # Object factories (galaxies, LAB, quasar, BH, magnetar)
    region.py            # Scene 001 assembler
    solar_system.py      # Starter solar system scene
  export/
    scene_json.py        # Export to scene.json + summary.md + preview.html
  preview/
    static_html.py       # Three.js interactive preview generator
  game/
    models.py            # Game models (SignalType, TelescopeTier, ResearchState, etc.)
    entity.py            # Research Entity model, types, random names
    tech_tree.py         # 12-tier telescope progression
    discovery.py         # Detection rules, confidence, research points
    telescope_ui.py      # Static HTML telescope UI generator
tests/                   # pytest test suite
docs/                    # Architecture, science model, game design, roadmap
frontends/               # Placeholder frontend docs (Unreal, Godot, Web)
data/generated/          # Generated artifacts (gitignored)
```

## Documentation

**Architecture & science:**
- [Architecture](docs/architecture.md)
- [Scene 001: The Lyman-alpha Furnace](docs/scene-001-lyman-alpha-furnace.md)
- [Science Model](docs/science-model.md)
- [Visual Language](docs/visual-language.md)
- [Schema Documentation](docs/schema.md)
- [Import Planning: Unreal & Godot](docs/import-planning.md)

**Game design:**
- [Game Design](docs/game-design.md)
- [Telescope Progression](docs/telescope-progression.md)
- [Discovery Loop](docs/discovery-loop.md)
- [Instrument Model](docs/instrument-model.md)
- [Research Entity](docs/research-entity.md)
- [Telescope UI](docs/telescope-ui.md)
- [Roadmap](docs/roadmap.md)

## License

See repository root for license terms.
