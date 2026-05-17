# Scene 001: The Lyman-alpha Furnace

## Concept

A flythrough of a high-redshift protocluster at z ≈ 3.1, centered on a luminous Lyman-alpha blob (LAB). The scene captures the cosmic web environment where massive galaxies are assembling for the first time.

## Included phenomena

| Object | Count | Description |
|---|---|---|
| Cosmic web nodes | ~12 | Intersection points of the large-scale structure graph |
| Cosmic web filaments | ~20–40 | Tube-like connections between nodes, scaffolding for galaxy placement |
| Protocluster core | 1 | Highest-density node at the scene center |
| Lyman-alpha blob | 1 | "The Furnace" — a ~300 ckpc diffuse gas nebula glowing in Lyman-α |
| Quasar | 1 | "Lucerna" — a high-luminosity AGN with relativistic jets |
| Supermassive black hole | 1 | "Tenebris" — the engine behind Lucerna |
| Galaxies | ~80 | Young star-forming galaxies scattered along filaments |
| Magnetar | 1 | "Pulsar Ignis" — a compact remnant embedded in a galaxy |
| Voids | 2 | Low-density reference regions |
| CMB shell | 1 | Metadata-only background reference |

## Scientific motivation

Lyman-alpha blobs are among the most spectacular objects in the high-redshift universe. They are enormous (~100–400 kpc) diffuse gas structures that glow in the Lyman-alpha emission line of hydrogen. They are preferentially found in protocluster environments and are thought to be powered by a combination of:

- Cold gas accretion from the cosmic web
- Starburst-driven superwinds from embedded galaxies
- AGN/quasar photoionization

This scene combines these elements into a single navigable environment.

## Simplifications

- Positions are random with density biasing, not from N-body cosmology.
- The cosmic web is a proximity graph, not a Voronoi/Delaunay tessellation.
- Galaxy properties are order-of-magnitude estimates.
- The LAB is represented as a single object in JSON; **Godot** draws it as nested translucent shells (false-color metaphor), not a resolved gas distribution.
- Redshift perturbations are cosmetic, not from peculiar velocities or Hubble flow.
- The magnetar is placed for narrative interest, not from a stellar evolution model.

## Regeneration

```bash
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
```

The output is deterministic for a given seed.

## Optional scene metadata (for frontends)

Exported `scene.json` includes optional `metadata` fields such as `scene_class`
(`deep_field`), `recommended_camera_target_object_id`, `featured_object_ids`,
`teaching_summary`, and `scale_description`. These are hints only; Godot falls
back to heuristics if they are absent.

## Godot workflow

1. `uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001`
2. `uv run universe game export-godot-data --out frontends/godot/data`
3. Open `frontends/godot/project.godot`, set `user://overrides.json` with **absolute** paths to `scene-001/scene.json` and your `game-state.json`.
4. Run Main → **Reload Scene/State** if overrides changed.

See `docs/godot-frontend.md` and `frontends/godot/README.md` for deep-field signal behavior and a manual test checklist.

## Unreal workflow

```bash
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
uv run universe game export-unreal-data \
  --scene data/generated/scene-001/scene.json \
  --out frontends/unreal/Data
```

Open `frontends/unreal/Universe.uproject`, place `AUniverseSceneActor`, press Play. See `docs/unreal-frontend.md`.
