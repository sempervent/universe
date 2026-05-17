# Unreal Frontend

The Unreal Engine 5 project under `frontends/unreal/` is the **cinematic renderer** for the universe sandbox. It is intentionally separate from the playable Godot frontend and the Python game core.

## Division of responsibility

| System | Responsibility |
|--------|----------------|
| **Python** | Canonical procedural generation, discovery rules, `scene.json` / `game-state.json`, CLI |
| **Static HTML** | Browser telescope UI prototype |
| **Godot 4** | Full observe → discover → survey → milestone loop with save/load |
| **Unreal 5** | High-fidelity Scene 001 visualization, signal modes, telescope camera, HUD inspector |

Unreal does **not** replace Godot for gameplay in the current phase.

## Data flow

```
uv run universe generate scene-001 … → data/generated/scene-001/scene.json
                                              ↓
                         UUniverseSceneImporter (C++) loads JSON
                                              ↓
                         AUniverseSceneActor spawns meshes / instances
                                              ↓
                         AUniverseTelescopePawn + AUniverseTelescopeHUD
```

Optional convenience path:

```
uv run universe game export-unreal-data --scene …/scene.json --out frontends/unreal/Data
```

## Scene 001 visual targets

The prototype maps object types to engine primitives (see `docs/import-planning.md` for the long-term Niagara/volumetric plan):

- **Lyman-alpha blob** — nested translucent spheres, emission pulse
- **Quasar** — bright point light + cylinder jets (deterministic axis from object id)
- **Black hole** — dark core + torus accretion placeholder
- **Magnetar** — pulsing core + torus “field line” hints
- **Filaments** — polyline through `control_points_mpc`, cylinder segments
- **Galaxies** — `UInstancedStaticMeshComponent`
- **Nodes** — scaled marker actors; protocluster core enlarged via density
- **CMB** — large inverted shell; emphasized in microwave mode
- **Voids** — translucent sphere placeholders

## Signal modes

`UUniverseSignalModeSubsystem` implements the same conceptual modes as Godot:

`visible_light`, `radio`, `microwave`, `xray`, `gamma_ray`, `gravitational_wave`, `neutrino`, `weak_lensing`, `dark_matter_inference`, `speculative_now_signal`, plus `ultraviolet` / `infrared`.

Press **M** in PIE to cycle modes. `speculative_now_signal` is labelled fictional in the HUD help text.

Each mode applies **tint, emphasis, and opacity** per object type via `FUniverseSignalVisual`
and `UUniverseCosmicMaterials` (engine stock parents — see `frontends/unreal/Content/Docs/Materials.md`).

## Interaction (Scene 001 polish)

- **Click** (release) — line trace selects `AUniverseObjectActor` (LAB, quasar, nodes, etc.).
- **F** — focus selected object, else `recommended_camera_target_object_id` from metadata.
- **Tab** — cycle `featured_object_ids`.
- **N** — toggle labels for featured/recommended objects (not all 80 galaxies).
- **R** — reset camera and clear selection.
- Initial signal mode from `recommended_initial_signal_mode` when present.

No game-state, discovery, surveys, or milestones in Unreal.

## Opening the project

1. Install Unreal Engine **5.4+**.
2. Open `frontends/unreal/Universe.uproject`.
3. Compile the **Universe** module when prompted.
4. Place `AUniverseSceneActor` in the level.
5. Generate Scene 001 if needed (see `frontends/unreal/README.md`).
6. Play.

## Runtime validation

This repository does **not** run Unreal in CI. After pulling changes, open the project locally and confirm:

- Scene loads without JSON errors in the Output Log (`LogUniverse`).
- LAB / quasar / filaments are visible after framing with **F** / **R**.
- Signal mode cycle (**M**) changes emphasis.

## Limitations

- No binary Content assets committed; assign master materials in-editor for best results.
- No research progression, surveys, or milestones in Unreal.
- Click-to-select is scaffolded in docs; wire a line trace on the player controller for full parity.
- Lensing, true volumetric LAB, and Niagara jets remain future work.

## See also

- [`frontends/unreal/README.md`](../frontends/unreal/README.md) — quickstart + checklist
- [`frontends/unreal/Docs/unreal-scene-import.md`](../frontends/unreal/Docs/unreal-scene-import.md)
- [`docs/import-planning.md`](import-planning.md)
