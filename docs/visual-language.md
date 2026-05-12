# Visual Language

## Design philosophy

Visual modes are honest abstractions, not fake "human eye" realism. Each mode maps physical quantities to a coherent color palette and rendering style.

## Visual modes

### beauty

The default cinematic mode. Objects use aesthetically chosen colors to convey their nature at a glance.

- Galaxies: blue-white points
- Lyman-alpha blob: teal-green translucent volume
- Quasar: bright white with orange-red jet hints
- Black hole: dark core with glowing accretion ring
- Filaments: dark blue semi-transparent tubes
- Nodes: warm orange markers
- Voids: near-invisible dark wireframes

### science

Reduced aesthetics, emphasis on classification. Objects use flat, distinct colors for unambiguous identification.

- LAB rendered in wireframe to show extent without obscuring interior
- Colors chosen for colorblind-friendliness where practical

### lyman_alpha

Simulates a narrowband Lyman-alpha filter observation. The LAB dominates; most other objects fade to dark green-black.

### xray

Simulates an X-ray telescope view. AGN and compact objects brighten; diffuse structures appear as soft blue-purple halos.

### radio

Simulates a radio telescope view. Jets and lobes dominate in warm orange-red; galaxies are dim.

### density

Maps local matter density to a green intensity scale. High-density regions (nodes, core) are bright; voids are nearly black.

### cmb

Everything except the CMB background fades to near-black. The CMB shell renders as a warm orange glow. Useful for scale context.

## Object visual metaphors

| Object | Geometry | Key visual cue |
|---|---|---|
| Galaxy | Small sphere | Blue glow, size varies with visual.scale |
| Lyman-alpha blob | Large icosahedron | Translucent green, pulsing glow |
| Quasar | Medium sphere | Bright white, intense emissive |
| Black hole | Small sphere + torus | Dark core, orange accretion ring |
| Magnetar | Tiny octahedron | Magenta, high emissive |
| Cosmic web node | Small octahedron | Warm orange, density-scaled |
| Filament | CatmullRom tube | Semi-transparent, follows control points |
| Void | Wireframe icosahedron | Very faint, dark |
| CMB | Large inside-out icosahedron | Faint background shell |

## Future rendering goals

- Volumetric fog for Lyman-alpha blob (Unreal volumetric materials, Godot fog volumes)
- Niagara particle systems for quasar jets and accretion disk
- Post-process gravitational lensing around black hole
- Instanced sprite rendering for distant galaxies
- Adaptive LOD based on camera distance
- Physically-based spectral mapping for wavelength modes
