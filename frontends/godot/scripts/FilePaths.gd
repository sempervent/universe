extends Node
# FilePaths — autoload constant module for resolving project-relative data paths.
#
# Godot resource paths use res:// during development.  When running the
# exported game, fall back to user:// so writes always succeed.
#
# Generated data lives outside the Godot project, in the parent repo's
# data/generated/ directory.  We resolve those paths through the engine's
# OS layer because res:// is read-only at export time.

# ── Bundled frontend constants (small, version-controlled) ──────────────
const TECH_TREE_PATH := "res://data/tech_tree.json"
const SURVEYS_PATH := "res://data/surveys.json"
const MILESTONES_PATH := "res://data/milestones.json"
const DISCOVERY_REQS_PATH := "res://data/discovery_requirements.json"
const ENTITY_MODIFIERS_PATH := "res://data/entity_modifiers.json"
const SIGNALS_PATH := "res://data/signal_types.json"
const ENTITY_TYPES_PATH := "res://data/entity_types.json"
const RANDOM_NAMES_PATH := "res://data/random_entity_names.json"
const SCENE_CATALOG_PATH := "res://data/scene_catalog.json"

# ── Generated runtime data (lives in the parent repo) ──────────────────
# Defaults assume the Godot project lives at frontends/godot/ inside the
# universe repo.  Override by writing user://overrides.json with keys
# "scene_path" and "state_path".
const DEFAULT_SCENE_RELATIVE := "../../data/generated/solar-system/scene.json"
const DEFAULT_STATE_RELATIVE := "../../data/generated/game-state.json"
const USER_STATE_FALLBACK := "user://game-state.json"
const USER_OVERRIDES_PATH := "user://overrides.json"


static func project_root() -> String:
	# OS-native absolute path of the Godot project root.
	return ProjectSettings.globalize_path("res://")


static func absolute_default_scene() -> String:
	return project_root().path_join(DEFAULT_SCENE_RELATIVE).simplify_path()


static func absolute_default_state() -> String:
	return project_root().path_join(DEFAULT_STATE_RELATIVE).simplify_path()


static func absolute_fallback_state() -> String:
	return ProjectSettings.globalize_path(USER_STATE_FALLBACK)


static func read_overrides() -> Dictionary:
	if not FileAccess.file_exists(USER_OVERRIDES_PATH):
		return {}
	var f := FileAccess.open(USER_OVERRIDES_PATH, FileAccess.READ)
	if f == null:
		return {}
	var data: Variant = JSON.parse_string(f.get_as_text())
	if data is Dictionary:
		return data
	return {}


static func resolve_scene_path() -> String:
	var ov := read_overrides()
	if ov.has("scene_path") and ov["scene_path"] is String and ov["scene_path"] != "":
		return ov["scene_path"]
	return absolute_default_scene()


static func resolve_state_path() -> String:
	var ov := read_overrides()
	if ov.has("state_path") and ov["state_path"] is String and ov["state_path"] != "":
		return ov["state_path"]
	return absolute_default_state()
