# Import Planning: Unreal Engine & Godot

## Overview

The `scene.json` format is the bridge between the `universe` data core and rendering engines. Each engine needs an importer that reads the JSON and instantiates engine-native representations.

**Status:** Godot has a playable importer/renderer (`frontends/godot/`). Unreal has a C++ prototype importer (`frontends/unreal/`, see `docs/unreal-frontend.md`).

```
scene.json → Importer Plugin → Engine-native actors/nodes/materials/particles
```

## Object type mapping

| Scene type | Unreal Engine | Godot |
|---|---|---|
| `cosmic_web_node` | Static mesh (octahedron) or instanced sprite | MeshInstance3D or MultiMeshInstance3D |
| `cosmic_web_filament` | Spline mesh / procedural tube / volumetric tube | Path3D + CSGPolygon3D or custom shader tube |
| `galaxy` | Instanced static mesh / Niagara sprite particle | MultiMeshInstance3D or GPUParticles3D |
| `lyman_alpha_blob` | Volumetric fog volume + noise material | FogVolume + custom VolumetricFog shader |
| `quasar` | Point light + Niagara jet system + lens flare | OmniLight3D + GPUParticles3D + custom shader |
| `black_hole` | Static mesh + post-process lensing material | MeshInstance3D + custom shader (screen distortion) |
| `magnetar` | Small emissive mesh + Niagara burst on flare | MeshInstance3D + GPUParticles3D |
| `void` | Invisible/wireframe debug volume | Invisible or wireframe debug mesh |
| `cmb_background` | Sky sphere material (very faint thermal) | WorldEnvironment sky shader |

## Unreal Engine notes

### Cosmic web filaments

- Use `USplineComponent` with spline points from `control_points_mpc`.
- Attach `USplineMeshComponent` segments or a procedural mesh along the spline.
- Material: translucent, emissive, with density-mapped opacity.
- Consider `UProceduralMeshComponent` for tube geometry.

### Lyman-alpha blob

- Use `AVolumetricCloud` or a custom volumetric material with a `VolumetricFog` volume.
- Noise-driven opacity and emission. Animate noise offset for subtle motion.
- Material parameters: base color (teal-green), emission intensity, noise scale, opacity.
- Alternative: large translucent sphere with Fresnel falloff for simpler first pass.

### Quasar jets (Niagara)

- Two `UNiagaraComponent` systems for bipolar jets.
- Emitter: cone shape, aligned to jet axis.
- Particles: elongated sprites with velocity-stretch.
- Material: additive blend, orange-red gradient along length.
- Accretion disk: separate Niagara system or torus mesh with emissive material.

### Black hole lensing

- Post-process material with screen-space distortion.
- Shader samples screen texture with radial offset proportional to `1/r²` from BH screen position.
- `lensing_strength` from `visual.extras` controls distortion amplitude.
- Consider `SceneCapture2D` for reflection-based approach.

### Scale handling

- Scene coordinates are in cMpc. At the default scale, 1 cMpc = 1 Unreal unit is too small.
- Use a **floating origin** system: the camera stays near (0,0,0) and the world shifts around it.
- Define scale factor: e.g., 1 cMpc = 100 Unreal units (adjustable).
- Use **LOD buckets**: galaxies become sprites beyond a threshold distance.

### Coordinate mapping

```
scene.json (x, y, z) cMpc → Unreal (X, Y, Z) * scale_factor
```

Right-handed to left-handed conversion: negate Z or swap Y/Z depending on convention choice.

## Godot notes

### Cosmic web filaments

- Use `Path3D` with `Curve3D` built from control points.
- Attach `CSGPolygon3D` in path mode for tube geometry, or generate `ArrayMesh` procedurally.
- `ShaderMaterial` with density-mapped transparency.
- For many filaments, consider `MultiMeshInstance3D` with cylinder segments.

### Lyman-alpha blob

- `FogVolume` node with a custom `VolumetricFog` shader.
- Alternatively: `MeshInstance3D` with a custom spatial shader using `ALPHA` and view-dependent Fresnel.
- Noise texture for internal structure variation.
- Animate `TIME` in shader for subtle motion.

### Quasar particles

- `GPUParticles3D` with cone emission shape for jets.
- `ParticleProcessMaterial` with velocity-stretch and additive blending.
- Accretion disk: `MeshInstance3D` (torus) with emissive `ShaderMaterial`.

### Black hole

- `MeshInstance3D` (dark sphere) with a custom screen-space shader for lensing.
- Use `SCREEN_TEXTURE` and `SCREEN_UV` with radial distortion.
- Accretion ring as a separate torus mesh.

### Scale handling

- Similar floating origin approach as Unreal.
- Godot 4's `Node3D` supports large coordinates but precision degrades beyond ~10,000 units.
- Use a world-shifting system or scaled coordinates.

### Scene importer

The Godot importer should:

1. Read `scene.json` from a file path or `res://` resource.
2. Iterate over `nodes`, `filaments`, and `objects`.
3. Instantiate packed scenes or procedural geometry for each type.
4. Apply `visual` hints to materials.
5. Store `properties` and `relationships` in node metadata for UI/inspector use.

```gdscript
# Pseudocode for Godot importer
var scene_data = JSON.parse_string(file_content)
for obj in scene_data["objects"]:
    var node = _create_node_for_type(obj["type"])
    node.position = Vector3(obj["position_mpc"]["x"], obj["position_mpc"]["y"], obj["position_mpc"]["z"]) * SCALE
    node.set_meta("properties", obj["properties"])
    add_child(node)
```

## Common importer requirements

Both engines need:

1. **Type dispatcher**: Map `object.type` string to a factory function or packed scene.
2. **Relationship resolver**: After all objects are instantiated, wire up relationships (e.g., quasar holds reference to black hole node).
3. **Visual mode system**: Material parameter sets that can be swapped at runtime.
4. **Scale configuration**: User-adjustable scale factor with floating origin support.
5. **Metadata display**: UI panel that shows `properties` and `relationships` for a selected object.
