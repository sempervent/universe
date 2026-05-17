# Unreal Engine Frontend (Scene 001 Cinematic Prototype)

**Status:** C++ scaffold + runtime scene importer. First target: **Scene 001 — The Lyman-alpha Furnace**.

## Architecture

| Layer | Role |
|-------|------|
| **Python** (`src/universe/`) | Canonical scene generation, game logic, `scene.json` export |
| **Godot** (`frontends/godot/`) | Playable open-source telescope game frontend |
| **Unreal** (`frontends/unreal/`) | Cinematic high-fidelity renderer (this project) |

Unreal does **not** port surveys, tech tree, or save-game loops in this pass. It loads `scene.json`, spawns placeholder geometry, and exposes a telescope camera + HUD inspector.

## Requirements

- **Unreal Engine 5.4+** (5.3 may work; project file targets 5.4)
- C++ toolchain matching your engine install
- Generated Scene 001 data from the Python CLI

## Quickstart

From the repository root:

```bash
uv sync
uv run universe generate scene-001 \
  --seed lyman-alpha-furnace \
  --out data/generated/scene-001

# Optional convenience bundle (normalized coordinates + material hints)
uv run universe game export-unreal-data \
  --scene data/generated/scene-001/scene.json \
  --out frontends/unreal/Data
```

### Open the project

1. Open `frontends/unreal/Universe.uproject` in Unreal Editor.
2. Allow the editor to compile the **Universe** C++ module on first launch.
3. Open the default template map (Open World) or any empty level.
4. Place **`AUniverseSceneActor`** in the level (Place Actors → search “Universe Scene”).
5. Press **Play**.

By default `AUniverseSceneActor` loads:

`../../../data/generated/scene-001/scene.json`

(relative to `frontends/unreal/`).

Override at runtime:

```
universe.SceneJsonPath /absolute/path/to/scene.json
```

Or set **Scene Json Path** on the placed actor.

## Controls (PIE)

| Key | Action |
|-----|--------|
| Mouse drag | Orbit telescope |
| Mouse wheel | Zoom |
| **Click** (release) | Select object under cursor |
| **M** | Cycle signal visualization mode (10 primary modes) |
| **F** | Focus selected object, or recommended target (LAB by metadata) |
| **R** | Reset camera framing (clears selection) |
| **N** | Toggle labels for featured / recommended objects |
| **Tab** | Cycle featured objects (from scene metadata) |

## Materials (no committed .uasset required)

`UUniverseCosmicMaterials` applies **engine stock** materials via dynamic instances
(`BasicShapeMaterial`, `DefaultParticleMaterial`). Signal modes update color,
emissive strength, and opacity every frame. See `Content/Docs/Materials.md`.

HUD panels show scene kind, redshift, region size, signal help, and selection (when wired).

## Project layout

```
frontends/unreal/
  Universe.uproject
  Config/                 # DefaultEngine, Input, Game
  Content/README.md       # No binary assets committed — engine primitives only
  Data/                   # export-unreal-data output (optional)
  Docs/unreal-scene-import.md
  Scripts/README.md
  Source/Universe/        # C++ module
```

## Implemented vs scaffolded

| Feature | Status |
|---------|--------|
| `scene.json` import (`UUniverseSceneImporter`) | **Implemented** |
| Deep-field layout (centroid + scale) | **Implemented** |
| LAB nested shells + pulse | **Implemented** (primitive meshes) |
| Quasar core + cylinder jets | **Implemented** (Niagara **TODO**) |
| Black hole + torus accretion | **Implemented** (placeholder) |
| Magnetar pulse + field tori | **Implemented** |
| Filaments via control points | **Implemented** (cylinder segments) |
| Galaxy instancing | **Implemented** (`UInstancedStaticMeshComponent`) |
| Cosmic web nodes | **Implemented** (marker actors) |
| CMB shell | **Implemented** (large sphere, mode visibility) |
| Signal modes subsystem | **Implemented** |
| Telescope pawn + HUD overlay | **Implemented** |
| UMG widget assets | **Scaffolded** — HUD uses canvas draw for zero-asset startup |
| Click-to-select | **Implemented** (visibility line trace; filaments/galaxies deferred) |
| Code-side materials | **Implemented** (`UUniverseCosmicMaterials`) |
| Metadata initial signal/camera | **Implemented** |
| Gravitational lensing post-process | **TODO** (see docs) |
| Niagara jets / volumetric LAB | **TODO** |

## Limitations

- Materials use engine defaults; dynamic parameters (`BaseColor`, `EmissiveStrength`, `Opacity`) require a parent material with those parameters or will be no-ops visually until you assign project materials in Content.
- No game-state / discovery progression in Unreal.
- CI does not compile Unreal; Python tests check scaffold + export only.
- Do not commit `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/` (see repo `.gitignore`).

## See also

- [`docs/unreal-frontend.md`](../../docs/unreal-frontend.md) — design contract
- [`Docs/unreal-scene-import.md`](Docs/unreal-scene-import.md) — import mapping
- [`docs/import-planning.md`](../../docs/import-planning.md) — long-form engine mapping
