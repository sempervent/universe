# Unreal scene import

## Canonical input

`scene.json` from:

```bash
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
```

## C++ entry points

| Class | Role |
|-------|------|
| `UUniverseSceneImporter` | Parse JSON → `FUniverseSceneRegion` |
| `AUniverseSceneActor` | Spawn actors / instances |
| `AUniverseObjectActor` | Per-object visuals (LAB, quasar, BH, magnetar, void) |
| `AUniverseFilamentActor` | Spline path + cylinder segments |
| `UUniverseSignalModeSubsystem` | Instrument emphasis |

## Coordinate mapping

Deep-field scenes (Scene 001):

1. Compute centroid from `metadata.featured_object_ids` (fallback: LAB/quasar/BH).
2. `render_scale = 32 / size_mpc` (matches Godot).
3. World position = `(position_mpc - centroid) * render_scale`.

Solar-system scenes use log-radial AU compression (same formula as Godot).

## Filaments

For each `CosmicWebFilament`:

1. Start at `start_node_id` position.
2. Append each `control_points_mpc` entry.
3. End at `end_node_id` position.
4. Spawn `AUniverseFilamentActor` with cylinder segments along the polyline.

## Optional bundle

`universe game export-unreal-data` writes `scene_unreal.json` with precomputed `position_render` arrays. The importer can load this file when `bPreferUnrealBundle` is enabled.

## Console variable

```
universe.SceneJsonPath=/abs/path/to/scene.json
```
