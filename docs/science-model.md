# Science Model

## Coordinate system

- **Position unit**: comoving megaparsecs (cMpc). 1 cMpc ≈ 3.26 million light-years.
- **Size unit**: comoving kiloparsecs (ckpc). 1 Mpc = 1000 kpc.
- **Mass unit**: solar masses (M☉).
- **Luminosity unit**: erg s⁻¹ (or solar luminosities where noted).
- **Redshift**: dimensionless z.
- **Coordinate frame**: right-handed Cartesian. No preferred astronomical orientation.

Physical (proper) distance at redshift z:

```
d_proper = d_comoving / (1 + z)
```

At z = 3.1, a 1 cMpc comoving distance corresponds to ~0.244 proper Mpc.

## Redshift conventions

Scene 001 is set at z ≈ 3.1. Individual objects have small redshift perturbations (σ ≈ 0.01) for visual variety. These are **not** physical peculiar velocity offsets — they are cosmetic.

The CMB background is referenced at z = 1100 for context.

## Procedural cosmic web model

The cosmic web generator uses a simplified approach:

1. **Node placement**: Uniform random within a cubic region, with density biased toward center (Gaussian falloff). One node is forced near the origin as the protocluster core.
2. **Node classification**: Core node → `protocluster_core`. Edge nodes (>85% of half-width) → `void_boundary`. Others → `filament_intersection`.
3. **Filament connection**: Nodes within a distance threshold are connected. Filaments get 1–3 Gaussian-jittered control points for curvature.
4. **Density assignment**: Average of connected node densities.

This is **not** equivalent to:
- N-body simulation with gravitational collapse
- Zel'dovich approximation
- Delaunay tessellation field estimation (DTFE)
- Halo occupation distribution (HOD) models

It produces a visually plausible cosmic web graph suitable for scene scaffolding.

## Object placement rules

| Object | Placement rule |
|---|---|
| Galaxies | Distributed along filaments (proportional to galaxy_count_hint) and clustered around protocluster core |
| Lyman-alpha blob | Near protocluster core (σ = 2 cMpc jitter) |
| Quasar | Near protocluster core (σ = 1.5 cMpc jitter) |
| Black hole | Co-located with quasar |
| Magnetar | Inside nearest galaxy to protocluster core (σ = 0.01 cMpc jitter) |
| Voids | In outer regions of the scene volume |

## Known inaccuracies

1. Galaxy stellar masses and SFRs are drawn from uniform log distributions, not from a mass function or luminosity function.
2. The LAB has a single representative luminosity, not a spatially resolved emission profile.
3. Quasar luminosity is not self-consistently linked to black hole mass and accretion rate.
4. Filament radii and densities are not from hydrodynamic simulation.
5. The cosmic web topology has no guaranteed connectedness or planarity constraints.
6. Magnetar placement is narrative-driven, not from a stellar IMF or SN rate model.

## Future improvements

- Use a Zel'dovich-like displacement field for more realistic web topology.
- Draw galaxy properties from observed luminosity/mass functions.
- Add proper cosmological distance calculations (comoving vs angular diameter vs luminosity distance).
- Import real protocluster catalogs (e.g., from COSMOS or ODIN surveys).
