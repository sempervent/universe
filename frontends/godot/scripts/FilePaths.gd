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
const TRANSIENTS_PATH := "res://data/transient_events.json"
const OBJECTIVES_PATH := "res://data/objectives.json"
const CAMERA_CATALOG_PATH := "res://data/camera_catalog.json"

# ── Generated runtime data (lives in the parent repo) ──────────────────
const DEFAULT_SCENE_RELATIVE := "../../data/generated/solar-system/scene.json"
const DEFAULT_STATE_RELATIVE := "../../data/generated/game-state.json"
const USER_STATE_FALLBACK := "user://game-state.json"
const USER_OVERRIDES_PATH := "user://overrides.json"
const DEFAULT_STATE_REPO_RELATIVE := "data/generated/game-state.json"


static func project_root() -> String:
	return ProjectSettings.globalize_path("res://")


static func get_repo_root() -> String:
	# Universe repo root (parent of frontends/godot).
	return project_root().path_join("../..").simplify_path()


static func absolute_default_scene() -> String:
	return project_root().path_join(DEFAULT_SCENE_RELATIVE).simplify_path()


static func absolute_default_state() -> String:
	return project_root().path_join(DEFAULT_STATE_RELATIVE).simplify_path()


static func absolute_fallback_state() -> String:
	return ProjectSettings.globalize_path(USER_STATE_FALLBACK)


static func default_state_path() -> String:
	return resolve_state_path()


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
		return str(ov["scene_path"])
	return absolute_default_scene()


static func resolve_state_path() -> String:
	var ov := read_overrides()
	if ov.has("state_path") and ov["state_path"] is String and ov["state_path"] != "":
		return str(ov["state_path"])
	return absolute_default_state()


static func _resolve_repo_relative(rel_path: String) -> String:
	var p := rel_path.strip_edges()
	if p == "":
		return ""
	if p.begins_with("/"):
		return p
	if p.begins_with("res://"):
		return ProjectSettings.globalize_path(p)
	if p.begins_with("user://"):
		return ProjectSettings.globalize_path(p)
	# Catalog paths like data/generated/foo — repo root relative.
	if p.begins_with("data/") or p.begins_with("../"):
		return get_repo_root().path_join(p).simplify_path()
	return project_root().path_join(p).simplify_path()


static func scene_path_for_catalog_entry(scene_entry: Dictionary) -> String:
	if scene_entry.is_empty():
		return ""
	var explicit: String = str(scene_entry.get("scene_json_path", ""))
	if explicit != "":
		return _resolve_repo_relative(explicit)
	var out_dir: String = str(scene_entry.get("default_output_path", ""))
	if out_dir == "":
		return ""
	return _resolve_repo_relative(out_dir.path_join("scene.json"))


static func scene_exists_for_catalog_entry(scene_entry: Dictionary) -> bool:
	var path := scene_path_for_catalog_entry(scene_entry)
	return path != "" and FileAccess.file_exists(path)


static func make_generate_command(scene_id: String) -> String:
	return "uv run universe game generate-scene --scene %s" % scene_id


static func make_set_scene_command(scene_id: String) -> String:
	var state_rel := DEFAULT_STATE_REPO_RELATIVE
	return (
		"uv run universe game set-scene --scene %s "
		+ "--state %s --out %s" % [scene_id, state_rel, state_rel]
	)
