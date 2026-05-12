# Instrument Model

## Signal types

| Signal | Wavelength/carrier | Detected by | Real-world examples |
|---|---|---|---|
| `visible_light` | ~400–700 nm | Naked eye, optical, space telescopes | HST, VLT, Keck |
| `infrared` | ~700 nm – 1 mm | Ground IR, space telescopes | JWST, Spitzer |
| `ultraviolet` | ~10–400 nm | Space telescopes | GALEX, HST/UV |
| `radio` | ~1 mm – 10 m | Radio telescopes, interferometers | VLA, ALMA, SKA |
| `microwave` | ~1 mm – 30 cm | Radio/microwave receivers | Planck, WMAP |
| `xray` | ~0.01–10 nm | X-ray space observatories | Chandra, XMM-Newton |
| `gamma_ray` | < 0.01 nm | Gamma-ray space observatories | Fermi, Swift |
| `gravitational_wave` | N/A (spacetime strain) | GW detectors | LIGO, Virgo, LISA |
| `neutrino` | N/A (particle) | Neutrino detectors | IceCube, Super-K |
| `cosmic_ray` | N/A (particle) | CR detectors | Auger, HAWC |
| `weak_lensing` | Derived from imaging | Survey telescopes + statistical analysis | Euclid, Rubin/LSST |
| `dark_matter_inference` | Derived from dynamics/lensing | Combination instruments | Game abstraction |
| `speculative_now_signal` | Fictional | Now-scope | Fictional |

## Key instrument parameters

### Resolution (arcseconds)

How small an angular separation the instrument can distinguish.

- Naked eye: ~60"
- Ground optical: ~1–2" (seeing-limited)
- Space optical: ~0.05"
- Radio (single dish): ~arcminutes
- Radio (interferometer): ~milliarcseconds
- X-ray: ~0.5"
- Gamma: ~degrees
- GW: ~degrees (poor localization)

### Sensitivity

How faint/weak a signal the instrument can detect. Represented as a dimensionless factor (0–1 scale normalized to each signal type) for gameplay simplicity.

In reality this varies enormously by instrument and wavelength. The game uses a single sensitivity number per tier as a gameplay abstraction.

### Effective distance (Mpc)

Maximum distance at which the instrument can usefully detect objects. This is a severe simplification — real sensitivity depends on source luminosity, not just distance — but it provides a useful gameplay gate.

- Naked eye: ~0.001 Mpc (a few kpc — nearby stars)
- Ground optical: ~10 Mpc
- Space optical: ~5000 Mpc (deep field)
- Radio: ~3000 Mpc
- X-ray: ~2000 Mpc
- GW: ~1000 Mpc (current), ~10000 Mpc (future)
- Now-scope: unlimited

### Atmosphere penalty

Ground-based instruments suffer from atmospheric absorption, turbulence (seeing), and light pollution. Represented as a multiplier (0–1) on effective sensitivity.

- Ground optical: 0.4–0.7
- Ground radio: 0.9 (mostly transparent)
- Ground IR: 0.3 (water vapor absorption)
- Space-based: 1.0 (no penalty)
- GW detectors: 1.0 (not affected by atmosphere)
- Underground detectors: 1.0 (shielded)

### Lookback time

All electromagnetic observations see the past. An object at distance d is seen as it was d/c years ago.

- Moon: 1.3 seconds
- Sun: 8.3 minutes
- Jupiter: ~35–52 minutes
- Nearest star: ~4.2 years
- Andromeda: ~2.5 million years
- Scene 001 (z=3.1): ~11.5 billion years

The game tracks lookback time for flavor text but does not simulate time evolution in the first prototype.

### Signal-to-noise

The game abstracts S/N into the confidence calculation rather than modeling it physically. Higher sensitivity and longer integration time (future mechanic) improve confidence.

## Object visibility requirements

Each object type has:
- **Required signals:** Must have at least these signal types to detect at all.
- **Optional signals:** Improve confidence and characterization.
- **Minimum tier:** Lowest telescope tier that could possibly detect this object type.
- **Minimum sensitivity:** Threshold below which the object is invisible regardless of signal coverage.

See `discovery-loop.md` for the confidence calculation.
