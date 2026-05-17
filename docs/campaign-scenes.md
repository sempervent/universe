# Campaign observation scenes

Each scene is a **deterministic** `scene.json` bundle teaching one observational regime. Scenes unlock with telescope tiers; the campaign tracks which are active, visited, and available.

| Scene id | Name | Unlock tier | Primary signals |
|----------|------|-------------|-----------------|
| `solar-system` | Local Solar System | (starter) | visible_light |
| `scene-001` | The Lyman-alpha Furnace | space_optical | optical, radio, X-ray, lensing, now-scope |
| `radio-cmb-survey` | Radio CMB Survey | radio | radio, microwave |
| `stellar-remnant-field` | Stellar Remnant Field | xray_gamma | xray, gamma_ray |
| `cosmic-web-map` | Cosmic Web Map | dark_matter_mapper | weak_lensing, dark_matter_inference |
| `now-scope-anomaly-field` | Now-Scope Anomaly Field | now_scope | speculative_now_signal |

## Generate

```bash
uv run universe generate radio-cmb-survey --seed radio-first-light --out data/generated/radio-cmb-survey
uv run universe generate stellar-remnant-field --seed high-energy-remnants --out data/generated/stellar-remnant-field
uv run universe generate cosmic-web-map --seed invisible-architecture --out data/generated/cosmic-web-map
uv run universe generate now-scope-anomaly-field --seed impossible-now --out data/generated/now-scope-anomaly-field

# Or via campaign catalog defaults:
uv run universe game generate-scene --scene radio-cmb-survey
```

## Visual support

- **Python / HTML / Godot**: all scenes use generic object-type rendering and signal modes.
- **Godot**: use the **Campaign** tab to load generated `scene.json` files and set the active observing program (see [godot-frontend.md](godot-frontend.md)).
- **Unreal**: currently targets Scene 001 only; other scenes are canonical in Python first.

## Object-type notes

Scenes reuse existing object types (`galaxy`, `magnetar`, `cmb_background`, etc.). Per-object `required_signal_types` in `properties` restrict which instruments can detect highlights (e.g. radio-loud galaxies need radio, not optical alone).

See also [campaign-progression.md](campaign-progression.md) for CLI workflow and frontend limitations.

## Balance alignment

Each catalog entry lists `recommended_survey_ids` and `recommended_signal_modes`. Before tuning unlock tiers or rewards, run:

```bash
uv run universe game playtest-matrix --out data/generated/playtests/matrix
uv run universe game balance-report \
  --input data/generated/playtests/matrix \
  --out data/generated/playtests/balance-report.md
```

Section **7g** flags missing surveys, targets absent from a scene, or objects not detectable at the scene’s unlock tier. Ladder runs (`campaign_instrument_ladder`) populate §7f per-scene discovery and RP tables.

`campaign_ordered` autoplay spends minimum turns per scene, starts recommended surveys before advancing, and respects per-observe RP caps so Scene 001 does not fund the entire tech tree in one pass.
