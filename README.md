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
- 10 survey programs as named, prerequisite-gated research campaigns.
- 14 milestones recognizing meaningful firsts in the entity's history.
- CLI commands for the full observe→discover→upgrade loop, plus survey/milestone management.
- Deterministic balance playtests (`game playtest`, `playtest-matrix`, `balance-report`) — see [balance playtesting](docs/balance-playtesting.md).
- Browser-playable telescope UI with naming flow, sky map, tech tree, surveys, milestones, and discovery log.

**Engine frontends:**
- **Godot 4 prototype** (`frontends/godot/`) — playable telescope game on `scene.json` / `game-state.json` (see `docs/godot-frontend.md`).
- **Unreal Engine 5 prototype** (`frontends/unreal/`) — cinematic Scene 001 renderer: JSON import, signal modes, telescope camera, HUD inspector (see `docs/unreal-frontend.md`). No full game port.

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

# List available survey programs
uv run universe game surveys --state data/generated/game-state.json

# Activate the Local Sky Survey
uv run universe game start-survey \
  --state data/generated/game-state.json \
  --survey local_sky_survey \
  --out data/generated/game-state.json

# Observe the solar system (earn research points + survey progress + milestones)
uv run universe game observe \
  --scene data/generated/solar-system/scene.json \
  --state data/generated/game-state.json \
  --out data/generated/game-state.json

# Campaign scenes (unlock with instrument tiers — see docs/campaign-scenes.md)
uv run universe game scenes --state data/generated/game-state.json
uv run universe game generate-scene --scene radio-cmb-survey
# See docs/campaign-progression.md for full workflow

# List milestones
uv run universe game milestones --state data/generated/game-state.json

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

## Quickstart — Balance playtesting

```bash
uv run universe game playtest \
  --scenario solar_tutorial_basic \
  --entity-type backyard_observatory \
  --seed local-sky \
  --out data/generated/playtests/solar_tutorial_basic_backyard.json

uv run universe game playtest-matrix --out data/generated/playtests/matrix

uv run universe game balance-report \
  --input data/generated/playtests/matrix \
  --out data/generated/playtests/balance-report.md

# Full six-scene campaign ladder (ordered autoplay)
uv run universe game playtest \
  --scenario campaign_instrument_ladder \
  --entity-type private_institute \
  --seed local-sky \
  --out data/generated/playtests/campaign_instrument_ladder_private.json
```

See [docs/balance-playtesting.md](docs/balance-playtesting.md). Campaign ladder findings appear in **§7f Campaign Ladder Analysis** when matrix runs include `campaign_instrument_ladder`.

Transient turn-window events: [docs/transient-events.md](docs/transient-events.md).

First-run tutorial objectives: [docs/tutorial-objectives.md](docs/tutorial-objectives.md).

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

## Quickstart — Godot 4 frontend (prototype)

```bash
# 1. Generate scene + state (as above)
uv run universe generate solar-system --seed local-sky --out data/generated/solar-system
uv run universe game init \
  --name "Hydrogen Ghost Institute" \
  --entity-type private_institute \
  --motto "Listening for the old light." \
  --out data/generated/game-state.json

# 2. Export the Godot data bundle (tech tree, surveys, milestones, requirements)
uv run universe game export-godot-data --out frontends/godot/data

# 3. Open the project in Godot 4.x and press F5
#    frontends/godot/project.godot
```

The Godot project consumes the same canonical JSON. See
[Godot frontend docs](docs/godot-frontend.md).

### Unreal Engine (cinematic prototype)

```bash
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
uv run universe game export-unreal-data \
  --scene data/generated/scene-001/scene.json \
  --out frontends/unreal/Data
# Open frontends/unreal/Universe.uproject in UE 5.4+, compile, place AUniverseSceneActor, Play
```

See [Unreal frontend docs](docs/unreal-frontend.md).

## What is intentionally not implemented yet
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
    surveys.py           # Survey programs (named research campaigns)
    milestones.py        # Milestones / achievements
    telescope_ui.py      # Static HTML telescope UI generator
tests/                   # pytest test suite
docs/                    # Architecture, science model, game design, roadmap
frontends/
  godot/                 # Playable Godot 4 telescope frontend
  unreal/                # Cinematic Unreal 5 Scene 001 prototype
  web/                   # Web frontend notes
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
- [Entity backgrounds (modifiers)](docs/entity-backgrounds.md)
- [Survey Programs](docs/survey-programs.md)
- [Milestones](docs/milestones.md)
- [Telescope UI](docs/telescope-ui.md)
- [Godot Frontend](docs/godot-frontend.md)
- [Unreal Frontend](docs/unreal-frontend.md)
- [Roadmap](docs/roadmap.md)

## License

See repository root for license terms.
