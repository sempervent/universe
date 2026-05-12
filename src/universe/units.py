"""Coordinate and unit conventions for the universe project.

Coordinate system
-----------------
- **Large-scale positions**: comoving megaparsecs (cMpc).
  1 cMpc ≈ 3.086 × 10²² m ≈ 3.26 million light-years.
- **Object sizes**: comoving kiloparsecs (ckpc) unless otherwise noted.
- **Masses**: solar masses (M☉).
- **Luminosities**: erg s⁻¹ or solar luminosities (L☉), specified per field.
- **Redshift**: dimensionless z.  Physical (proper) distances at redshift z are
  ``d_proper = d_comoving / (1 + z)``.

Orientation
-----------
Right-handed Cartesian.  +X = "right", +Y = "up", +Z = "toward observer"
when projected for preview purposes.  No preferred astronomical orientation
is imposed in the data layer — engine importers choose their own mapping.

Scientific caveats
------------------
- Comoving coordinates ignore local peculiar velocities.
- No curvature corrections are applied at the ≲100 cMpc scale of Scene 001.
- Object sizes are order-of-magnitude representative, not survey-derived.
"""

# Conversion helpers (kept minimal — no heavy astropy dependency yet)

MPC_TO_KPC: float = 1_000.0
KPC_TO_MPC: float = 1.0 / MPC_TO_KPC

# Representative scale references for Scene 001 (z ≈ 3.1)
SCENE_001_REDSHIFT: float = 3.1
SCENE_001_REGION_SIZE_MPC: float = 80.0

UNIT_CONVENTIONS = {
    "position": "comoving Mpc (cMpc)",
    "size": "comoving kpc (ckpc) unless noted",
    "mass": "solar masses (M☉)",
    "luminosity": "erg/s or solar luminosities (L☉)",
    "redshift": "dimensionless z",
    "coordinate_system": "right-handed Cartesian",
}
