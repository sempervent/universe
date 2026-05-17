# Telescope Progression

## Overview

The player advances through 12 telescope tiers, each unlocking new signal types, improved sensitivity, and access to previously invisible object classes.

## Tier definitions

### Tier 0: Naked Eye / Ancient Sky
- **Instruments:** naked_eye
- **Signals:** visible_light
- **Detects:** Sun, Moon, bright planets, constellations, Milky Way band
- **Resolution:** ~60 arcsec (1 arcmin)
- **Sensitivity:** Very low — only apparent magnitude ≲6
- **Atmosphere:** Full atmospheric penalty
- **Cost:** 0 (starting tier)

### Tier 1: Ground Optical Telescope
- **Instruments:** optical_telescope
- **Signals:** visible_light
- **Detects:** Lunar craters, planet disks, Jupiter's moons, bright nebulae, star clusters
- **Resolution:** ~2 arcsec
- **Sensitivity:** mag ≲12
- **Atmosphere:** Seeing-limited
- **Cost:** 10 RP

### Tier 2: Improved Ground Observatory
- **Instruments:** optical_telescope (improved)
- **Signals:** visible_light, infrared
- **Detects:** Asteroids, comets, outer planets, faint galaxies, variable stars
- **Resolution:** ~1 arcsec (adaptive optics)
- **Sensitivity:** mag ≲18
- **Atmosphere:** Partially corrected
- **Cost:** 25 RP

### Tier 3: Space Optical Telescope
- **Instruments:** space_telescope
- **Signals:** visible_light, infrared, ultraviolet
- **Detects:** Deep-field galaxies, quasars, galaxy morphology, exoplanet transits
- **Resolution:** ~0.05 arcsec
- **Sensitivity:** mag ≲30
- **Atmosphere:** None (space-based)
- **Cost:** 60 RP

### Tier 4: Radio Telescope
- **Instruments:** radio_telescope
- **Signals:** radio, microwave
- **Detects:** Pulsars, neutral hydrogen, radio galaxies, quasar jets, CMB anisotropy
- **Resolution:** ~1 arcsec (large arrays)
- **Sensitivity:** μJy level
- **Atmosphere:** Minimal (radio-transparent)
- **Cost:** 80 RP

### Tier 5: X-ray / Gamma Observatory
- **Instruments:** xray_observatory, gamma_observatory
- **Signals:** xray, gamma_ray
- **Detects:** Magnetars, accretion disks, black hole candidates, GRBs, hot galaxy clusters
- **Resolution:** ~0.5 arcsec (X-ray), ~1° (gamma)
- **Sensitivity:** High-energy photon counting
- **Atmosphere:** None (space-based required for X-ray/gamma)
- **Cost:** 120 RP

### Tier 6: Interferometer Array
- **Instruments:** interferometer
- **Signals:** visible_light, infrared, radio (combined baselines)
- **Detects:** Black hole shadows, stellar surfaces, precise astrometry
- **Resolution:** ~10 μas (microarcsecond)
- **Sensitivity:** Baseline-dependent
- **Atmosphere:** Mixed (ground + space baselines)
- **Cost:** 180 RP

### Tier 7: Gravitational-Wave Observatory
- **Instruments:** gravitational_wave_detector
- **Signals:** gravitational_wave
- **Detects:** Black hole mergers, neutron star mergers, compact binary inspiral
- **Resolution:** ~deg (poor sky localization alone)
- **Sensitivity:** Strain h ~ 10⁻²³
- **Atmosphere:** N/A (non-electromagnetic)
- **Cost:** 250 RP

### Tier 8: Neutrino / Cosmic-Ray Observatory
- **Instruments:** neutrino_detector, cosmic_ray_detector
- **Signals:** neutrino, cosmic_ray
- **Detects:** Core-collapse supernovae (neutrino burst), high-energy cosmic accelerators
- **Resolution:** ~deg
- **Sensitivity:** Event-counting
- **Atmosphere:** Requires deep underground/ice detectors
- **Cost:** 325 RP

### Tier 9: Multi-Messenger Observatory
- **Instruments:** Combines all previous
- **Signals:** All real signal types combined
- **Detects:** Confident identification of multi-signal events (e.g. NS merger: GW + gamma + optical + neutrino)
- **Resolution:** Combined localization
- **Sensitivity:** Cross-correlation improves confidence
- **Atmosphere:** Mixed
- **Cost:** 450 RP

### Tier 10: Dark Matter / Weak-Lensing Observatory
- **Instruments:** weak_lensing_mapper, dark_matter_observatory
- **Signals:** weak_lensing, dark_matter_inference
- **Detects:** Dark matter halos, cosmic web mass distribution, lensing anomalies, dark galaxy candidates
- **Resolution:** Statistical (field-level)
- **Sensitivity:** Requires large survey areas
- **Atmosphere:** Space-preferred
- **Cost:** 650 RP
- **Note:** Extrapolation — real science but the "observatory" as a single instrument is a game abstraction.

### Tier 11: Now-Scope (Speculative)
- **Instruments:** now_scope
- **Signals:** speculative_now_signal
- **Detects:** "Current state" of distant objects — bypasses light travel time
- **Resolution:** Hypothetically perfect
- **Sensitivity:** Hypothetically unlimited
- **Atmosphere:** N/A
- **Cost:** 1000 RP
- **⚠ SPECULATIVE:** This instrument violates causality and is fictional. It exists as an endgame fantasy mechanic. All objects detected exclusively through this instrument are marked `speculative: true`.

## Progression philosophy

- Early tiers are cheap and fast — get the player engaged quickly.
- Mid tiers require deliberate observation and multi-instrument thinking.
- Late tiers are expensive and reward accumulated skill.
- The final tier is a narrative reward, not a scientific claim.

## Campaign alignment

Each tier unlocks campaign scenes that expect its signal families (`radio` → `radio-cmb-survey`, `xray_gamma` → `stellar-remnant-field`, etc.). Use `campaign_instrument_ladder` playtests and balance report §7f to verify players reach each scene near the matching tier unlock, not several tiers early or late.
