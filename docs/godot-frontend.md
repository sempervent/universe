# Godot Frontend

The Godot 4 frontend is the first real engine integration of the
`universe` telescope game.  It is **a thin client** — the Python project
remains the source of truth for scene data, game definitions, and the
game-state schema.

The Unreal frontend is intentionally deferred to a later phase.  Godot
was chosen first because it is open-source, repo-friendly, and well
suited to a console-style prototype.

## Goals

- Prove that the canonical `scene.json` + `game-state.json` documents
  drive a real engine view of the universe.
- Expose every core gameplay action (observe, survey, upgrade, claim) in
  a Godot-native UI.
- Keep visual responsibilities clearly separated from gameplay logic.

Non-goals for this prototype:

- Cinematic visuals, volumetric Lyman-alpha rendering, lensing post-FX.
- Orbital mechanics or scientifically accurate motion.
- A full asset pipeline (no binary art committed).

## Project location

```
frontends/godot/
```

Open `project.godot` with Godot 4.x.  Press F5 to run the main scene.

## Data flow

```
Python CLI ──┬─ generate solar-system ─→ data/generated/solar-system/scene.json
             ├─ game init / observe / start-survey ─→ data/generated/game-state.json
             └─ game export-godot-data ─→ frontends/godot/data/*.json
                                                    ↓
                                          Godot opens project.godot
                                                    ↓
                            FilePaths.gd resolves scene + state paths
                                                    ↓
                          SceneLoader / GameState load JSON dicts
                                                    ↓
              SkyRenderer (3D) + TelescopeCamera + TelescopeConsole (UI)
                                                    ↓
                  Player actions mutate state → Save State writes back
```

The "frontend bundle" — `tech_tree.json`, `surveys.json`,
`milestones.json`, `discovery_requirements.json`, `entity_modifiers.json`,
`scene_catalog.json`, plus signal/entity metadata — is committed alongside
the scripts so the project is runnable on first open.  Regenerate with:

```bash
uv run universe game export-godot-data --out frontends/godot/data
```

## Scripts

| File | Role |
|---|---|
| `Main.gd` | Orchestrator. Wires camera ray-pick, sky rebuild, console, environment tint per signal mode. |
| `FilePaths.gd` | Autoload. Resolves repo-relative paths and an optional `user://overrides.json`. |
| `SceneLoader.gd` | Parses scene.json with minimal validation helpers. |
| `GameState.gd` | Load/save game state. Provides `default_state()` and `ensure_backward_compatibility()`. |
| `TechTree.gd` | Aggregates capabilities from unlocked tiers. |
| `DiscoveryEngine.gd` | Confidence calculation + RP awards. Subset port of Python. |
| `SurveyEngine.gd` | Survey status, start, claim, per-discovery progress. |
| `MilestoneEngine.gd` | Predicate-based milestone evaluator with auto-claim. |
| `EntityModifiers.gd` | Loads `entity_modifiers.json`; effective tier costs, survey/milestone rewards, discovery RP/confidence nudges (mirrors Python). |
| `TelescopeCamera.gd` | Orbital camera: drag orbit, wheel zoom, middle / Shift+drag pan, F/R, tap-to-pick ray. |
| `SkyRenderer.gd` | Builds meshes + `Area3D` pick spheres, `Label3D` names, discovery materials, signal-mode emphasis. |
| `TelescopeConsole.gd` | CanvasLayer UI: signal mode dropdown + help, labels toggle, reset/export, tabs, log. |

## What is mirrored vs canonical

| Mechanism | Where it lives |
|---|---|
| Scene generation | Canonical Python only. Godot never generates. |
| Tier definitions | Canonical Python; exported as JSON. |
| Survey definitions | Canonical Python; exported as JSON. |
| Milestone definitions | Canonical Python; exported as JSON. |
| Discovery requirements | Canonical Python; exported as JSON. |
| **Confidence calculation** | Mirrored in GDScript (subset). |
| **Survey progression rules** | Mirrored in GDScript. |
| **Milestone predicates** | Mirrored in GDScript. |
| Game-state schema | Canonical Python. Godot reads the same JSON. |

When the Python and Godot rule implementations differ, **Python wins.**
The Godot `DiscoveryEngine` is intentionally simpler (no per-distance
penalty, simpler saturation curves); it gives indistinguishable results
for the included scenes.

## Save / load

`GameState.save_state(path, state)` writes to the requested path.  When
that fails (path read-only, sandbox restriction, etc.) `Main.gd` falls
back to `user://game-state.json` and reports the new path in the
discovery log.  This guarantees Save State never silently fails.

`GameState.ensure_backward_compatibility(state)` fills in
`research_entity`, `survey_progress`, `milestones`, and `turn` for
state files that pre-date those features — matching Python's
backward-compatibility contract.

## Configuring data paths

The default scene/state paths are relative to the Godot project, pointing
into the parent repo's `data/generated/` (solar-system + shared game state).
To override without editing scripts, drop a JSON file at
`user://overrides.json` (absolute paths recommended):

```json
{
  "scene_path": "/abs/path/to/scene.json",
  "state_path": "/abs/path/to/game-state.json"
}
```

**Solar system (default):** after `universe generate solar-system …`, paths
resolve to `data/generated/solar-system/scene.json` and
`data/generated/game-state.json` relative to the Godot project.

**Scene 001 deep field:** generate with
`universe game generate-scene --scene scene-001`, then use the **Campaign**
tab **Load Scene** (or set `scene_path` in overrides). Use **Reload Scene/State**
after changing overrides.

## Campaign scene picker

The **Campaign** tab (Observing Program) lists every entry in
`scene_catalog.json`:

- Lock/unlock from mirrored `GameState.ensure_campaign` / `update_scene_unlocks`
  (tier + milestone rules match Python).
- File status: whether `data/generated/<scene>/scene.json` exists (resolved via
  `FilePaths.scene_path_for_catalog_entry`).
- Actions: **Load Scene**, **Set Active**, **Load + Set Active**, **Refresh File Status**.

Godot does **not** invoke `uv run universe …`. Missing files show the exact
`game generate-scene` command in the detail panel.

**Active vs loaded:** `campaign.active_scene_id` is the observing program focus;
the loaded `scene.json` drives the 3D sky. The header and Campaign tab warn when
they differ.

## Deep-field rendering (Scene 001)

`SceneLoader.gd` classifies scenes as **solar system** vs **deep field** using `metadata.scene_class`, scene id heuristics (`scene-001`), and presence of high redshift + cosmic web data.

For deep-field scenes, `SkyRenderer.gd`:

- Normalizes comoving **Mpc** positions by `size_mpc` around a centroid derived from `metadata.featured_object_ids` (fallback: LAB / quasar / black hole average).
- Draws **filaments** as short **cylinder** segments through JSON `control_points_mpc` when present (not only node endpoints).
- Renders **cosmic web nodes** as extra markers (protocluster core enlarged).
- Uses a layered translucent **LAB** shell stack with a shared emission pulse (false-color placeholder, not radiative transfer).
- Gives **quasars** deterministic **bipolar jets** (axis from `hash(object_id)`), with **radio** / **X-ray** modes adjusting jet vs core emphasis in code + materials.
- Models **black holes** as a very dark core plus a translucent **accretion torus** placeholder (mostly indirect in visible light).
- Adds faint **torus** rings around **magnetars** as a magnetic-field sketch.

`TelescopeCamera.gd` **R** / initial load calls `apply_scene_framing(...)`: deep-field presets use a wider default distance from `SkyRenderer`’s fit radius around `metadata.recommended_camera_target_object_id` (fallback: LAB id).

`TelescopeConsole.gd` shows scene kind, **z**, **cMpc** span, deep-field-specific **signal help** copy, optional **survey suggestions** when no survey is active, and a simple **object list filter**.

Scene JSON may include optional `metadata` teaching fields (`teaching_summary`, `scale_description`, etc.); older files without them still load.

## Viewport controls

| Control | Action |
|--------|--------|
| Click object (short click, no orbit drag) | Select object (ray hits `Area3D`) |
| Mouse wheel | Zoom |
| Left or right drag | Orbit |
| Middle drag, or Shift + left drag | Pan |
| **F** | Focus on selected object |
| **R** | Reset camera |
| **L** | Toggle labels (same as console checkbox) |
| **+** / **-** | Zoom |

Picking uses `PhysicsRayQueryParameters3D` from the camera through the
mouse position (`Main.gd`); each sky object has a `SphereShape3D` on an
`Area3D` built in `SkyRenderer.gd`.

## Signal visualization modes

The console **Signal visualization** dropdown lists modes from
`res://data/signal_types.json` (exported with `game export-godot-data`).
Changing the mode updates:

- World `Environment` background / ambient tint (`Main.gd`).
- Per-object emphasis in `SkyRenderer` (objects whose discovery requirements
  mention compatible signals are brighter; others are dimmed — illustrative,
  not a physical radiative transfer model). **Deep-field scenes** add
  additional heuristics (e.g. filaments and nodes emphasized under weak
  lensing / dark-matter inference; CMB shell under microwave).

`speculative_now_signal` is labelled as fictional in the help panel.

## Limitations

- GDScript rules are a subset of Python; use the CLI when results must match
  canonical logic exactly.
- LAB remains a **stacked translucent shell** placeholder, not volumetric gas.
- Filaments are **segmented cylinders**, not hydrodynamic density tubes.
- No Godot headless tests in CI — Python tests assert project files and
  export bundle shape only.
- Optional: if the `godot` binary is on your PATH, open the editor once after
  large script changes to catch import errors.

## Future work

- Replace the LAB shells with a `FogVolume` and a custom 3D-noise shader.
- Thicker filament tubes with curvature smoothing / GPU line rendering.
- Skybox/environment presets per scene id.
- Time-domain events (when added Python-side).
- An Unreal Engine pass for the cinematic counterpart — see
  `docs/import-planning.md` for the long-form mapping.
