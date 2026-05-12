# Discovery Loop

## Overview

The core gameplay loop is: **observe → detect → identify → earn → upgrade → repeat**.

## Detection levels

| Confidence | Label | Meaning |
|---|---|---|
| 0.00–0.24 | Not detected | Instrument cannot perceive this object |
| 0.25–0.49 | Signal anomaly | Something is there but unclassifiable |
| 0.50–0.74 | Candidate | Likely classification but not confirmed |
| 0.75–0.94 | Confirmed | Confident identification |
| 0.95–1.00 | Characterized | Fully understood — all accessible properties measured |

## How confidence is calculated

Confidence depends on:

1. **Signal coverage:** What fraction of the object's required signal types can the player detect?
   - Required signals must all be available for >0.75 confidence.
   - Optional signals add bonus confidence.
2. **Telescope sensitivity:** Can the instrument reach the object's distance/brightness?
3. **Resolution:** Can the instrument resolve the object at its apparent size/separation?
4. **Multi-messenger bonus:** Combining independent signal types from different instruments adds confidence.

```
base_confidence = signal_coverage_fraction * sensitivity_factor * resolution_factor
multi_messenger_bonus = 0.1 * number_of_independent_signal_types_beyond_required
final_confidence = min(1.0, base_confidence + multi_messenger_bonus)
```

## Research points

Points are awarded based on:

| Object difficulty | Base points |
|---|---|
| Solar system (naked eye) | 1–3 |
| Solar system (telescope) | 3–5 |
| Nearby star / nebula | 5–10 |
| Galaxy | 10–15 |
| Quasar | 15–25 |
| Black hole (indirect) | 20–30 |
| Magnetar / exotic compact | 20–30 |
| Lyman-alpha blob | 25–35 |
| Cosmic web filament | 30–40 |
| Dark matter structure | 40–60 |
| Speculative objects | 50–100 |

Bonuses:
- First detection of a type: +50%
- Confirmation upgrade (candidate → confirmed): +25%
- Full characterization: +25%

## Observation workflow

1. Player selects a scene (solar system, deep-field, etc.).
2. Player's active telescope determines available signals and sensitivity.
3. Game evaluates each object in the scene against current capabilities.
4. New detections are reported with confidence levels.
5. Research points are awarded for new/upgraded detections.
6. Player spends points to unlock new telescope tiers.
7. With new instruments, previously invisible objects become detectable.

## Multi-messenger astronomy

The key mid-to-late-game mechanic. Examples:

- **Neutron star merger:** GW signal (Tier 7) + gamma-ray burst (Tier 5) + optical afterglow (Tier 3) = confirmed NS merger with high confidence.
- **Black hole:** X-ray accretion (Tier 5) + gravitational lensing (Tier 10) + GW from merger (Tier 7) = fully characterized BH.
- **Cosmic web filament:** Galaxy survey (Tier 3) + weak lensing (Tier 10) + radio neutral hydrogen (Tier 4) = confirmed filament.

Single-instrument detections yield candidates; multi-messenger confirms.

## Telescope UI

The telescope UI implements this loop client-side. The JavaScript discovery engine faithfully ports the Python `calculate_identification_confidence` function, including signal coverage, sensitivity/resolution factors, distance penalties, and multi-messenger bonuses.

See `docs/telescope-ui.md` for the interactive UI documentation.
