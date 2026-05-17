# Scripts

Optional automation for Unreal (not required for the prototype).

Examples you may add later:

- `generate_project_files.sh` — run UnrealBuildTool / GenerateProjectFiles
- `cook_scene_001.sh` — headless cook for CI machines with UE installed

Python scene generation remains the only required pre-step:

```bash
uv run universe generate scene-001 --seed lyman-alpha-furnace --out data/generated/scene-001
```
