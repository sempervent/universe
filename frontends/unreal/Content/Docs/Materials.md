# Materials strategy (Universe Unreal prototype)

## Current approach: code fallback

`UUniverseCosmicMaterials` (GameInstance subsystem) creates **MaterialInstanceDynamic**
objects from engine stock parents:

| Profile | Engine parent (typical) |
|---------|------------------------|
| Emissive | `/Engine/BasicShapes/BasicShapeMaterial` |
| Translucent | `/Engine/EngineMaterials/DefaultParticleMaterial` |
| Filament | BasicShapeMaterial |
| BlackHole / CMB | BasicShapeMaterial |

Parameters set on every apply (aliases for compatibility):

- `Color`, `BaseColor`, `Tint`
- `EmissiveColor`, `EmissiveStrength`
- `Opacity`, `OpacityMask`

Brightness is also driven by multiplying color by `(1 + EmissiveStrength * 4)`.

## Future: editor-authored masters

When you add Content assets (not committed in this repo), create:

- `M_CosmicEmissive`
- `M_CosmicTranslucent`
- `M_CosmicFilament`
- `M_CosmicBlackHole`
- `M_CosmicCMB`

Point `UUniverseCosmicMaterials` parent loaders at those paths, or assign them on
spawned meshes in Blueprint subclasses of `AUniverseObjectActor`.

## Selection highlight

Selected objects use **custom depth stencil** on pickable meshes plus scale bump.
A post-process outline material can be added later in the editor.
