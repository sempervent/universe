# Imaging system

Metadata-first **camera capture** and **multi-signal composites** (Python canonical, Godot mirror).

## Cameras

Exported in `camera_catalog.json`. Unlocked when the required telescope tier is unlocked.

Default: `naked_eye_memory` (visible light only).

## CLI

```bash
uv run universe game cameras --state data/generated/game-state.json
uv run universe game capture-image --scene ... --state ... --object sun --camera naked_eye_memory --signal visible_light
uv run universe game images --state data/generated/game-state.json
uv run universe game combine-images --state ... --images img-a,img-b
```

## Rules (summary)

- Camera must be unlocked and support the active signal mode.
- Daylight blocks faint optical deep-sky captures; Sun allowed with reduced quality.
- Composites need **2+ images of the same object** in **different signal modes**.
- Images persist in `captured_images` on game state (save/reload).

No binary image files in v1 — titles, quality, signals, and metadata only.
