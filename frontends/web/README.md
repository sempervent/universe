# Web Frontend

**Status:** Partially implemented via the `preview.html` generator.

## Current implementation

The `universe` core generates a self-contained `preview.html` file using Three.js (loaded from CDN). This provides:

- 3D orbit controls (rotate, zoom, pan)
- Object type toggles
- Visual mode selector (7 modes)
- Click/hover metadata inspector
- Color-coded legend

## Future improvements

- Bloom post-processing for emissive objects
- Particle systems for quasar jets
- Volumetric approximation for LAB (raymarched shader)
- Camera path animation (flythrough presets)
- WebGPU renderer option for better performance
- Progressive loading for larger scenes
