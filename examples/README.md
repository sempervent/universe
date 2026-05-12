# Examples

## `scene_001_config.json`

Configuration template showing the parameters accepted by the Scene 001 generator.

## `scene_001_example/`

A small committed example scene (4 nodes, 5 galaxies) for documentation and quick reference.
This is a real output from the generator, not hand-crafted.

### Regenerating

```bash
python examples/generate_example.py
```

Or generate a full-size scene:

```bash
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
```

Full-size generated scenes are written to `data/generated/` which is gitignored.
