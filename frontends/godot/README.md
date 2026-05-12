# Godot Frontend

**Status:** Not yet implemented. This directory is a placeholder for future Godot integration.

## Intended architecture

A Godot 4.x scene importer that reads `scene.json` and creates engine-native nodes:

- Cosmic web filaments → Path3D + CSGPolygon3D or procedural ArrayMesh
- Lyman-alpha blob → FogVolume with custom VolumetricFog shader
- Quasar → OmniLight3D + GPUParticles3D for jets
- Black hole → MeshInstance3D with screen-space lensing shader
- Galaxies → MultiMeshInstance3D
- Magnetar → MeshInstance3D + GPUParticles3D burst

See `docs/import-planning.md` for detailed mapping and implementation notes.

## Prerequisites

- Godot 4.x
- GDScript or C# importer
- JSON parsing (built-in via `JSON` class)
