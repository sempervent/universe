# Content

No binary `.uasset` files are committed in this prototype.

Runtime geometry uses **Engine BasicShapes** (sphere, cylinder, torus) assigned from C++.

## Recommended next steps in-editor

1. Create a master material `M_CosmicMaster` with scalar parameters `EmissiveStrength`, `Opacity` and vector `BaseColor`.
2. Assign it as the default material on spawned meshes (or via `ConstructorHelpers` once assets exist).
3. Add a default map `Maps/UniverseMain` with a placed `AUniverseSceneActor` and save as the game default map in `Config/DefaultEngine.ini`.
