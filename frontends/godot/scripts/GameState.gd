class_name GameState
extends RefCounted
# GameState — load, save, and backward-compat normalize the player state.
#
# The state schema mirrors universe.game.models.ResearchState and is kept
# in lock-step with that file.  Fields added in newer Python versions land
# here too; older state files load with safe defaults.

const DEFAULT_ENTITY_NAME := "Unnamed Research Entity"


static func default_state() -> Dictionary:
	return {
		"research_points": 0,
		"unlocked_tiers": ["naked_eye"],
		"active_telescope_tier": "naked_eye",
		"known_signal_types": ["visible_light"],
		"discoveries": {},
		"research_entity": {
			"id": "",
			"name": DEFAULT_ENTITY_NAME,
			"entity_type": "custom",
			"motto": "",
			"founded_turn": 0,
			"description": "",
			"style": "",
			"created_at": "",
			"metadata": {},
		},
		"active_survey_id": null,
		"survey_progress": {},
		"milestones": {},
		"turn": 0,
	}


static func ensure_backward_compatibility(state: Dictionary) -> Dictionary:
	# Fill in any missing fields without overwriting existing values.
	var defaults := default_state()
	var out: Dictionary = state.duplicate(true)
	for key in defaults.keys():
		if not out.has(key):
			out[key] = defaults[key]

	if not (out["unlocked_tiers"] is Array) or out["unlocked_tiers"].is_empty():
		out["unlocked_tiers"] = ["naked_eye"]

	# research_entity should always be a fully shaped dict.
	if not (out["research_entity"] is Dictionary):
		out["research_entity"] = defaults["research_entity"].duplicate(true)
	else:
		var e_def: Dictionary = defaults["research_entity"]
		for k in e_def.keys():
			if not out["research_entity"].has(k):
				out["research_entity"][k] = e_def[k]

	# Coerce dict-typed fields if missing.
	for dict_key in ["discoveries", "survey_progress", "milestones"]:
		if not (out[dict_key] is Dictionary):
			out[dict_key] = {}

	if not (out["turn"] is int):
		out["turn"] = 0
	if not (out["research_points"] is int):
		out["research_points"] = int(out["research_points"])

	return out


static func load_state(path: String) -> Dictionary:
	# Returns the loaded + normalised state.  Falls back to the default
	# state if the file is missing or invalid.
	if path == "" or not FileAccess.file_exists(path):
		return default_state()

	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return default_state()
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if not (parsed is Dictionary):
		return default_state()
	return ensure_backward_compatibility(parsed)


static func save_state(path: String, state: Dictionary) -> Dictionary:
	# Writes JSON.  Returns {ok: bool, path: String, error: String}.
	if path == "":
		return {"ok": false, "path": path, "error": "empty path"}
	var dir := path.get_base_dir()
	if dir != "" and not DirAccess.dir_exists_absolute(dir):
		var err := DirAccess.make_dir_recursive_absolute(dir)
		if err != OK:
			return {"ok": false, "path": path, "error": "mkdir failed: %s" % err}
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return {"ok": false, "path": path, "error": "open failed"}
	f.store_string(JSON.stringify(state, "  "))
	return {"ok": true, "path": path, "error": ""}
