# Roadmap

## Phase 1: Deterministic scene generation ✅

- Typed Pydantic data models for all cosmic objects.
- Procedural cosmic web generator (nodes + filaments).
- Object placement with density-biased positioning.
- Object relationships (quasar↔BH, LAB↔galaxies, magnetar↔galaxy, filament↔nodes).
- JSON scene export with metadata and unit conventions.
- Interactive Three.js preview (bloom, star field, orbit controls, visual modes, metadata inspector).
- CLI: generate, inspect, summarize.
- Test suite for determinism, integrity, and export.

## Phase 2: Telescope progression game prototype ✅

- 12-tier telescope tech tree (naked eye → now-scope).
- Signal-based discovery engine with confidence levels (not detected → signal anomaly → candidate → confirmed → characterized).
- Research point progression and instrument upgrades.
- Starter solar system scene (Sun, Moon, planets, moons, asteroid, comet).
- Multi-messenger astronomy bonus for combining signal types.
- CLI game commands: init, observe, upgrade, status, tech-tree, report.
- Game design documentation (game-design.md, telescope-progression.md, discovery-loop.md, instrument-model.md).
- Test suite for tech tree integrity, research state, discovery rules, and solar system scene.

## Phase 3: Interactive telescope UI ✅

- Self-contained static HTML telescope UI (`export-ui` command).
- Observatory console layout: header, object list, sky map, tech tree, discovery log, object detail.
- Client-side game loop: observe, detect, earn RP, unlock tiers, re-observe.
- 2D radial sky map with logarithmic solar-system projection.
- localStorage persistence, export-state, and reset.
- Signal/confidence display matching Python discovery engine.
- Speculative tiers clearly marked.

## Phase 3.5: Research Entity identity ✅

- Player-named Research Entity (observatory, institute, sky cult, etc.).
- Entity types (backyard observatory, university lab, etc.) — flavor only.
- Optional motto.
- CLI `game init` supports `--name`, `--entity-type`, `--motto`.
- Entity name appears in CLI status, observe output, and reports.
- Telescope UI naming modal on first launch.
- Random name generator with curated list.
- Safe HTML escaping for user-provided names.
- Backward-compatible: old game state JSON loads with default entity.

## Phase 3b: Enhanced telescope UI (next)

- Visual/signal mode switching per observation.
- Import-state UI (file upload).
- Sound/visual effects for discovery moments.
- Observation animation.
- Entity-type gameplay bonuses (currently flavor only).

## Phase 4: Unreal/Godot visualization frontend

- Scene.json importer for Unreal Engine.
- Scene.json importer for Godot.
- Engine-native material and particle representations.
- Telescope viewfinder UI in-engine.
- See `docs/import-planning.md` for detailed mapping.

## Phase 5: Volumetric rendering

- Lyman-alpha blob as volumetric fog/noise material.
- Quasar jets as particle systems with magnetic field lines.
- Black hole gravitational lensing (post-process shader).
- Filaments as volumetric tubes with density-mapped opacity.

## Phase 6: Real astronomical catalog ingestion

- Import protocluster catalogs (COSMOS, ODIN, SSA22).
- Map real galaxy positions and properties to scene objects.
- Cross-match with spectroscopic redshift surveys.
- Provide real vs. procedural comparison mode.

## Phase 7: Multi-messenger observation UI

- Visual representation of combining instrument data.
- Cross-correlation confidence display.
- Alert system for transient events requiring multi-messenger response.
- "Discovery journal" tracking the player's observation history.

## Phase 8: Time-domain events

- Magnetar flares as time-domain events.
- Quasar variability and jet precession.
- Galaxy mergers as animated transitions.
- Gravitational wave events from BH mergers.
- Supernova neutrino bursts.

## Phase 9: Speculative endgame

- Now-scope mechanics and UI.
- Hypothetical objects only observable with speculative instruments.
- "Current state" universe view vs light-cone-limited view.
- Clear labeling of fictional/speculative content throughout.
