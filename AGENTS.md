# AGENTS.md — universe

## Project purpose

Engine-agnostic cosmic visualization sandbox. The core produces deterministic procedural scene data (JSON). Rendering frontends are separate.

## Architecture

- `src/universe/models.py` — Pydantic data models. The single source of truth for the scene schema. Do not add engine-specific fields here.
- `src/universe/procedural/` — Deterministic generators. All use seeded RNG for reproducibility.
- `src/universe/export/` — Serialization to JSON/Markdown/HTML. Must not import engine-specific code.
- `src/universe/preview/` — Browser preview generator. Uses Three.js via CDN. Self-contained HTML output.
- `tests/` — pytest. Run with `uv run pytest`.

## Conventions

- Coordinates are comoving megaparsecs (cMpc).
- Object sizes are comoving kiloparsecs (ckpc).
- All generation is deterministic for a given seed string.
- JSON is the interchange format — frontends must not import Python models directly.
- Scientific approximations must be documented in code and in `docs/science-model.md`.

## Testing

```bash
uv run pytest
```

## Generation

```bash
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
```

## Key design rules

1. Never add engine-specific code (Unreal, Godot, Unity) to `src/universe/`.
2. Keep generation deterministic — same seed must produce identical output.
3. Document scientific simplifications honestly.
4. Generated artifacts go in `data/generated/` (gitignored).
5. The preview HTML must be self-contained and openable locally without a server.
