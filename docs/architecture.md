# Architecture

## Overview

```
┌─────────────────────────────────────────────────────┐
│                   universe core                     │
│                                                     │
│  models.py ─── schema.py ─── units.py               │
│      │                                              │
│  procedural/                                        │
│    cosmic_web.py   objects.py   region.py            │
│      │                                              │
│  export/                                            │
│    scene_json.py ──► scene.json                     │
│                  ──► summary.md                     │
│  preview/                                           │
│    static_html.py ─► preview.html                   │
│                                                     │
│  cli.py ─── Click CLI                               │
└──────────────────────┬──────────────────────────────┘
                       │
                  scene.json
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    Unreal Engine    Godot        Web/WebGL
    (future)       (future)     (Three.js preview)
```

## Engine-agnostic core

The core library (`src/universe/`) has no dependency on any rendering engine. It produces a JSON scene format that any frontend can consume. The data contract is defined by the Pydantic models in `models.py`.

## Scene generation pipeline

1. **Seed** → deterministic RNG via SHA-256 hash.
2. **Cosmic web** → nodes placed with density-biased random scatter; filaments connect nearby nodes.
3. **Objects** → placed along filaments and near high-density nodes.
4. **Relationships** → quasar↔black hole, LAB↔galaxies, magnetar↔host galaxy, filament↔nodes.
5. **Export** → `scene.json` (full data), `summary.md` (human-readable), `preview.html` (interactive 3D).

## Export format

`scene.json` is the primary interchange format. It contains:

- `schema_version` — for forward compatibility.
- `metadata` — generator info, scientific caveats.
- `_units` — coordinate and measurement conventions.
- `nodes` — cosmic web nodes with positions and classifications.
- `filaments` — connections between nodes with control points.
- `objects` — all cosmic objects with typed properties, visual hints, and relationships.
- `visual_modes` — supported rendering modes.

## Future rendering frontends

Each frontend reads `scene.json` and maps objects to engine-native representations. See `docs/import-planning.md` for detailed mapping.

The core never imports from frontends. Frontends never import from the Python core at runtime — they consume the JSON export.
