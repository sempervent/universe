# Godot Frontend Data Bundle

These JSON files are **generated** from the Python game definitions:

```
src/universe/game/tech_tree.py        → tech_tree.json
src/universe/game/surveys.py          → surveys.json
src/universe/game/milestones.py       → milestones.json
src/universe/game/discovery.py        → discovery_requirements.json
src/universe/game/models.py           → signal_types.json
src/universe/game/entity.py           → entity_types.json, random_entity_names.json
```

To regenerate after a Python-side change:

```bash
uv run universe game export-godot-data --out frontends/godot/data
```

`manifest.json` lists the bundled files and the schema version.  The
Godot project loads these at startup via `res://data/...`.

The files are committed so that opening the Godot project does not
require a Python toolchain.  Re-export whenever the canonical Python
definitions change.
