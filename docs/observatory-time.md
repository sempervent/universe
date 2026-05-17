# Observatory time

Simplified **local day/night clock** for the Godot Observatory View (mirrored in Python `ObservatoryTimeState`).

- **Not real ephemerides** — deterministic fractions and rotation only.
- Default start: **day** (`local_day_fraction = 0.5`, ~noon).
- **Space**: pause/resume · **`.` / `]`**: +1 hour · **`,` / `[`**: −1 hour
- UI: Pause, +1h, +6h, Next Night, time-scale buttons (1× / 10× / 100×)

## Behavior

| Phase | Sky |
|-------|-----|
| Day | Bright dome, Sun on ecliptic arc, stars hidden |
| Night | Dark dome, starfield visible, faint targets easier in optical modes |
| Twilight | Transitional colors |

Objects move with `local_day_fraction` (daily rotation + per-body drift). Targets below the horizon are hidden in optical modes.

See also [godot-frontend.md](godot-frontend.md).
