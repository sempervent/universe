class_name SceneLoader
extends RefCounted
# SceneLoader — load and minimally validate scene.json.
#
# Mirrors the Python SceneRegion contract.  The engine never mutates the
# scene; the discovery loop reads it and updates a separate game-state
# document.  Use FilePaths.resolve_scene_path() to find the canonical path.


static func load_scene(path: String) -> Dictionary:
	# Returns a parsed scene dict, or {} on error.
	if path == "":
		push_warning("SceneLoader.load_scene called with empty path")
		return {}

	var file: FileAccess = null
	if path.begins_with("res://") or path.begins_with("user://"):
		file = FileAccess.open(path, FileAccess.READ)
	else:
		# Absolute filesystem path (produced by FilePaths helpers).
		file = FileAccess.open(path, FileAccess.READ)

	if file == null:
		push_warning("SceneLoader: could not open %s" % path)
		return {}

	var raw := file.get_as_text()
	var parsed: Variant = JSON.parse_string(raw)
	if not (parsed is Dictionary):
		push_warning("SceneLoader: %s is not a JSON object" % path)
		return {}
	return parsed


static func validate_scene_minimal(scene: Dictionary) -> bool:
	# Return true if the scene has the fields we actually consume.
	if not scene.has("id"):
		return false
	if not scene.has("name"):
		return false
	if not scene.has("objects"):
		return false
	if not (scene["objects"] is Array):
		return false
	return true


static func get_objects(scene: Dictionary) -> Array:
	if scene.has("objects") and scene["objects"] is Array:
		return scene["objects"]
	return []


static func get_nodes(scene: Dictionary) -> Array:
	if scene.has("nodes") and scene["nodes"] is Array:
		return scene["nodes"]
	return []


static func get_filaments(scene: Dictionary) -> Array:
	if scene.has("filaments") and scene["filaments"] is Array:
		return scene["filaments"]
	return []


static func is_solar_system_scene(scene: Dictionary) -> bool:
	if scene.get("id", "") == "solar-system":
		return true
	var meta: Dictionary = scene.get("metadata", {})
	return str(meta.get("scene_class", "")) == "solar_system"


static func is_deep_field_scene(scene: Dictionary) -> bool:
	if is_solar_system_scene(scene):
		return false
	var meta: Dictionary = scene.get("metadata", {})
	if str(meta.get("scene_class", "")) == "deep_field":
		return true
	if scene.get("id", "") == "scene-001":
		return true
	var z := float(scene.get("redshift", 0.0))
	var fils: Array = get_filaments(scene)
	var nds: Array = get_nodes(scene)
	if z > 0.08 and (fils.size() > 0 or nds.size() > 0):
		return true
	return false


## Back-compat alias (older scripts).
static func is_solar_system(scene: Dictionary) -> bool:
	return is_solar_system_scene(scene)
