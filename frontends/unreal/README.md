# Unreal Engine Frontend

**Status:** Not yet implemented. This directory is a placeholder for future Unreal integration.

## Intended architecture

An Unreal Engine plugin that reads `scene.json` and instantiates engine-native actors:

- Cosmic web filaments → Spline meshes / procedural tubes
- Lyman-alpha blob → Volumetric fog volume with noise material
- Quasar → Point light + Niagara jet particle systems
- Black hole → Mesh + post-process gravitational lensing material
- Galaxies → Instanced static meshes or Niagara sprite particles
- Magnetar → Small emissive mesh with burst particle system

See `docs/import-planning.md` for detailed mapping and implementation notes.

## Prerequisites

- Unreal Engine 5.x
- C++ plugin or Blueprint-based importer
- JSON parsing (built-in or via JsonUtilities module)
