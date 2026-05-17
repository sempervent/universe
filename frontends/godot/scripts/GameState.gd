class_name GameState
extends RefCounted
# GameState — load, save, and backward-compat normalize the player state.
#
# The state schema mirrors universe.game.models.ResearchState and is kept
# in lock-step with that file.  Fields added in newer Python versions land
# here too; older state files load with safe defaults.

const DEFAULT_ENTITY_NAME := "Unnamed Research Entity"
const DEFAULT_ACTIVE_SCENE_ID := "solar-system"


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
		"campaign": default_campaign(),
		"transient_events": {},
		"objectives": {},
		"active_objective_ids": [],
	}


static func default_campaign_scene_state(scene_id: String, unlocked: bool = false) -> Dictionary:
	return {
		"scene_id": scene_id,
		"unlocked": unlocked,
		"visited": false,
		"first_unlocked_turn": null,
		"first_visited_turn": null,
		"completed": false,
		"metadata": {},
	}


static func default_campaign() -> Dictionary:
	return {
		"active_scene_id": DEFAULT_ACTIVE_SCENE_ID,
		"scenes": {
			DEFAULT_ACTIVE_SCENE_ID: default_campaign_scene_state(DEFAULT_ACTIVE_SCENE_ID, true),
		},
		"completed_scene_ids": [],
	}


static func ensure_backward_compatibility(state: Dictionary) -> Dictionary:
	var defaults := default_state()
	var out: Dictionary = state.duplicate(true)
	for key in defaults.keys():
		if not out.has(key):
			out[key] = defaults[key]

	if not (out["unlocked_tiers"] is Array) or out["unlocked_tiers"].is_empty():
		out["unlocked_tiers"] = ["naked_eye"]

	if not (out["research_entity"] is Dictionary):
		out["research_entity"] = defaults["research_entity"].duplicate(true)
	else:
		var e_def: Dictionary = defaults["research_entity"]
		for k in e_def.keys():
			if not out["research_entity"].has(k):
				out["research_entity"][k] = e_def[k]

	for dict_key in ["discoveries", "survey_progress", "milestones", "transient_events", "objectives"]:
		if not (out[dict_key] is Dictionary):
			out[dict_key] = {}

	if not (out["turn"] is int):
		out["turn"] = 0
	if not (out["research_points"] is int):
		out["research_points"] = int(out["research_points"])

	if not (out["campaign"] is Dictionary):
		out["campaign"] = default_campaign()
	else:
		out["campaign"] = _normalize_campaign_dict(out["campaign"])

	return out


static func _normalize_campaign_dict(campaign: Dictionary) -> Dictionary:
	var out: Dictionary = campaign.duplicate(true)
	if not (out.get("scenes") is Dictionary):
		out["scenes"] = {}
	if not (out.get("completed_scene_ids") is Array):
		out["completed_scene_ids"] = []
	if not out.has("active_scene_id") or str(out["active_scene_id"]) == "":
		out["active_scene_id"] = DEFAULT_ACTIVE_SCENE_ID
	var scenes: Dictionary = out["scenes"]
	if not scenes.has(DEFAULT_ACTIVE_SCENE_ID):
		scenes[DEFAULT_ACTIVE_SCENE_ID] = default_campaign_scene_state(DEFAULT_ACTIVE_SCENE_ID, true)
	return out


static func _scene_unlocked_for_entry(
	entry: Dictionary,
	state: Dictionary,
) -> bool:
	if entry.is_empty():
		return false
	var sid: String = str(entry.get("id", ""))
	if sid == DEFAULT_ACTIVE_SCENE_ID:
		return true
	var tier_req: String = str(entry.get("unlock_tier_id", ""))
	if tier_req != "" and tier_req in state.get("unlocked_tiers", []):
		return true
	var ms_req: String = str(entry.get("unlock_milestone_id", ""))
	if ms_req != "":
		var rec: Variant = state.get("milestones", {}).get(ms_req, null)
		if rec is Dictionary and rec.get("achieved", false):
			return true
	return false


static func ensure_campaign(
	state: Dictionary,
	catalog: Array,
) -> Dictionary:
	var out: Dictionary = ensure_backward_compatibility(state)
	if catalog.is_empty():
		return out
	var campaign: Dictionary = out["campaign"]
	var scenes: Dictionary = campaign.get("scenes", {}).duplicate(true)
	for entry in catalog:
		if not entry is Dictionary:
			continue
		var sid: String = str(entry.get("id", ""))
		if sid == "":
			continue
		var prev: Dictionary = scenes.get(sid, default_campaign_scene_state(sid, false))
		var should: bool = _scene_unlocked_for_entry(entry, out)
		var unlocked: bool = prev.get("unlocked", false) or should
		scenes[sid] = {
			"scene_id": sid,
			"unlocked": unlocked,
			"visited": prev.get("visited", false),
			"first_unlocked_turn": prev.get("first_unlocked_turn", null),
			"first_visited_turn": prev.get("first_visited_turn", null),
			"completed": prev.get("completed", false),
			"metadata": prev.get("metadata", {}) if prev.get("metadata") is Dictionary else {},
		}
	campaign["scenes"] = scenes
	var active: String = str(campaign.get("active_scene_id", DEFAULT_ACTIVE_SCENE_ID))
	var active_st: Dictionary = scenes.get(active, {})
	if active_st.is_empty() or not active_st.get("unlocked", false):
		campaign["active_scene_id"] = DEFAULT_ACTIVE_SCENE_ID
	out["campaign"] = campaign
	return out


static func update_scene_unlocks(
	state: Dictionary,
	catalog: Array,
) -> Dictionary:
	var out: Dictionary = ensure_campaign(state, catalog)
	if catalog.is_empty():
		return {"state": out, "newly_unlocked": []}
	var newly: Array = []
	var campaign: Dictionary = out["campaign"]
	var scenes: Dictionary = campaign.get("scenes", {}).duplicate(true)
	var turn: int = int(out.get("turn", 0))
	for entry in catalog:
		if not entry is Dictionary:
			continue
		var sid: String = str(entry.get("id", ""))
		if sid == "":
			continue
		var prev: Dictionary = scenes.get(sid, default_campaign_scene_state(sid, false))
		var was_unlocked: bool = prev.get("unlocked", false)
		var should: bool = _scene_unlocked_for_entry(entry, out)
		var unlocked: bool = was_unlocked or should
		var first_unlock: Variant = prev.get("first_unlocked_turn", null)
		if unlocked and not was_unlocked:
			newly.append(sid)
			if first_unlock == null:
				first_unlock = turn
		scenes[sid] = {
			"scene_id": sid,
			"unlocked": unlocked,
			"visited": prev.get("visited", false),
			"first_unlocked_turn": first_unlock,
			"first_visited_turn": prev.get("first_visited_turn", null),
			"completed": prev.get("completed", false),
			"metadata": prev.get("metadata", {}) if prev.get("metadata") is Dictionary else {},
		}
	campaign["scenes"] = scenes
	var active: String = str(campaign.get("active_scene_id", DEFAULT_ACTIVE_SCENE_ID))
	var active_st: Dictionary = scenes.get(active, {})
	if active_st.is_empty() or not active_st.get("unlocked", false):
		campaign["active_scene_id"] = DEFAULT_ACTIVE_SCENE_ID
	out["campaign"] = campaign
	return {"state": out, "newly_unlocked": newly}


static func set_active_campaign_scene(
	state: Dictionary,
	scene_id: String,
	catalog: Array,
) -> Dictionary:
	var refreshed := update_scene_unlocks(state, catalog)
	var out: Dictionary = refreshed["state"]
	var campaign: Dictionary = out["campaign"]
	var scenes: Dictionary = campaign.get("scenes", {})
	var st: Dictionary = scenes.get(scene_id, {})
	if st.is_empty() or not st.get("unlocked", false):
		var req := "unknown"
		for entry in catalog:
			if entry is Dictionary and str(entry.get("id", "")) == scene_id:
				req = str(entry.get("unlock_requirement", entry.get("unlock_tier_id", "tier")))
				break
		return {
			"ok": false,
			"state": out,
			"message": "Scene '%s' is locked (requires %s)." % [scene_id, req],
		}
	var turn: int = int(out.get("turn", 0))
	campaign["active_scene_id"] = scene_id
	st = st.duplicate(true)
	if not st.get("visited", false):
		st["visited"] = true
		if st.get("first_visited_turn", null) == null:
			st["first_visited_turn"] = turn
	scenes[scene_id] = st
	campaign["scenes"] = scenes
	out["campaign"] = campaign
	var name := scene_id
	for entry in catalog:
		if entry is Dictionary and str(entry.get("id", "")) == scene_id:
			name = str(entry.get("name", scene_id))
			break
	return {
		"ok": true,
		"state": out,
		"message": "Active observing program: %s (%s)" % [name, scene_id],
	}


static func load_state(path: String) -> Dictionary:
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
