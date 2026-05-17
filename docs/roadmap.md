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

## Phase 3.6: Survey programs and milestones ✅

- 10 deterministic survey programs gated by telescope tiers and signal types.
- Per-survey progress, scope (solar-system / deep-field / any), and one-time RP rewards.
- Auto-completion and auto-claim on goal reached, with idempotent `claim-survey` command.
- 14 milestones recognising meaningful firsts, including a clearly-labelled speculative now-scope first light.
- Auto-evaluation in the discovery loop and at UI load; idempotent `claim-milestones` command.
- CLI: `surveys`, `start-survey`, `claim-survey`, `milestones`, `claim-milestones`; surveys/milestones surfaced in `status` and `report`.
- Telescope UI gains Surveys and Milestones tabs with persistent localStorage state.
- Backward-compatible: pre-survey state files load with empty progress and turn 0.

## Phase 3.7: Balance playtest instrumentation ✅

- `PlaytestEvent` / `PlaytestRun` telemetry models (`src/universe/game/telemetry.py`).
- Deterministic scenarios and `greedy_research` autoplay (`src/universe/game/playtest.py`).
- CLI: `game playtest`, `game playtest-matrix`, `game balance-report`.
- Markdown balance reports with tier/survey/milestone timing and heuristic warnings.
- Docs: [balance-playtesting.md](balance-playtesting.md).

## Phase 3b: Enhanced telescope UI (next)

- Visual/signal mode switching per observation.
- Import-state UI (file upload).
- Sound/visual effects for discovery moments.
- Observation animation.
- Entity-type gameplay bonuses (currently flavor only).
- Survey queues and re-runnable observation campaigns.
- In-UI milestone toasts.

## Phase 4a: Godot 4 telescope frontend ✅

- Real Godot 4 project under `frontends/godot/`.
- Loads canonical `scene.json` + `game-state.json` (with optional `user://overrides.json`).
- 3D scene rendering: stars, planets, moons, asteroids, comets, galaxies, quasars, magnetars, black holes, LAB, cosmic web nodes/filaments, voids.
- Observatory console UI: header, object list, detail, tech tree, surveys, milestones, log.
- GDScript ports of the discovery, survey, and milestone engines (Python remains canonical).
- Save State writes back to the same JSON, with `user://` fallback.
- New CLI command `game export-godot-data` produces the engine data bundle.

## Phase 4c: Godot campaign scene picker ✅

- **Campaign / Observing Program** tab: full `scene_catalog.json` list, lock/file status, load / set active, CLI generate hints.
- Mirrored campaign unlock rules in `GameState.gd`; Python remains canonical.

## Phase 3.10: Transient observation events ✅

- Deterministic turn-window catalog (`transients.py`) with eight events across campaign scenes.
- CLI: `game transients`, `game observe-transient`; playtest + balance report §7i.
- HTML Transients tab; Godot `transient_events.json` + `TransientEngine.gd`.
- Docs: [transient-events.md](transient-events.md).

## Phase 3.10: First-run UX & manual playtest polish ✅

- Canonical `get_next_actions()` (`src/universe/game/next_actions.py`) merges objectives, guidance, upgrades, transients, campaign, surveys.
- CLI `game status` / `report` show **Next actions** / recommended next step; polished `scenes`, `objectives`, `transients`.
- Static HTML + Godot mirrors: header next action, empty states, survey/transient grouping, campaign hot-swap note.
- [manual-playtest.md](manual-playtest.md) — 30–45 minute checklist.

## Phase 3.9: Campaign ladder balance tuning ✅

- Per-scene observation RP caps (`observation_rewards.py`) fix Scene 001 funding spikes.
- `campaign_ordered` min/max scene turns, survey-first behavior, refined `scene_ready_to_advance`.
- Late-game: now-scope cost 780, cosmic-web survey rewards, `dark_matter_instrument_online` milestone.
- Balance report §7h (RP caps), improved `recommended_signals_useful` heuristic.

## Phase 3.8: Campaign ladder balance pass ✅

- Six-scene catalog playtest scenario `campaign_instrument_ladder` with `campaign_ordered` autoplay.
- Per-scene ladder metrics in playtest summaries (`src/universe/game/campaign_balance.py`).
- Balance report §7f–7g: Campaign Ladder Analysis + scene/survey alignment checks.
- Tests: `tests/test_campaign_balance.py`.

## Phase 4b: Godot playability & telescope feel ✅ (prototype scope)

- ✅ 3D object picking (`Area3D` + camera raycast); selection synced with list + detail + log.
- ✅ **Scene 001 deep-field polish:** scene classification, Mpc normalization, filament polylines with control points, LAB / quasar / black-hole / magnetar differentiation, node markers, signal-mode tables, console survey hints + object filters, `user://overrides.json` smoke path (see `docs/godot-frontend.md`, `frontends/godot/README.md`).
- ✅ Orbit / zoom / pan camera (`TelescopeCamera.gd`); F focus, R reset, L labels.
- ✅ `Label3D` names with discovery-aware text; signal visualization modes + UI help.
- ✅ Visual bands for discovery confidence; selected-object highlight.
- ✅ Save/load messaging + fallback path + reset / export JSON from console.

## Phase 4c: Research entity background modifiers ✅

- Small **EntityModifier** effects on discovery RP, confidence (when already detectable), tier costs, survey progress/rewards, and milestone rewards — see `docs/entity-backgrounds.md`.
- `universe game export-godot-data` emits `entity_modifiers.json`; static HTML and Godot mirror the Python rules.

Still deferred in Godot / shared:

- FogVolume-based Lyman-alpha blob shader (Godot).
- Per-scene skybox.

## Phase 4d: Unreal Engine visualization frontend ✅ (prototype scope)

- ✅ C++ project `frontends/unreal/` with `UUniverseSceneImporter` (canonical `scene.json`).
- ✅ `AUniverseSceneActor` spawner: LAB shells, quasar jets (mesh), BH torus, magnetar, filaments, galaxy instances, nodes, CMB shell.
- ✅ `UUniverseSignalModeSubsystem` + telescope pawn / canvas HUD inspector.
- ✅ CLI `universe game export-unreal-data` → optional `frontends/unreal/Data/` bundle.
- See `docs/unreal-frontend.md` and `frontends/unreal/README.md`.

Still deferred in Unreal:

- Niagara jets and magnetar bursts.
- Volumetric LAB / `VolumetricCloud`.
- Gravitational lensing post-process.
- Full UMG assets and click-to-select line trace.
- See `docs/import-planning.md` for the cinematic target mapping.

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
