class_name ObjectiveEngine
extends RefCounted
# ObjectiveEngine — first-run tutorial objectives (mirrors universe.game.objectives).


static func load_definitions(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		return parsed
	return []


static func ensure_fields(state: Dictionary) -> Dictionary:
	var out: Dictionary = state.duplicate(true)
	if not (out.get("objectives") is Dictionary):
		out["objectives"] = {}
	if not (out.get("active_objective_ids") is Array):
		out["active_objective_ids"] = []
	return out


static func evaluate(state: Dictionary, scene: Dictionary, defs: Array) -> Dictionary:
	var result := {"state": state, "completed": []}
	state = ensure_fields(state)
	var changed := true
	while changed:
		changed = false
		var sorted := defs.duplicate()
		sorted.sort_custom(func(a, b): return int(a.get("tutorial_step", 0)) < int(b.get("tutorial_step", 0)))
		for defn in sorted:
			if not (defn is Dictionary):
				continue
			var oid: String = str(defn.get("id", ""))
			var objectives: Dictionary = state["objectives"]
			var prog: Dictionary = objectives.get(oid, {"objective_id": oid, "status": "locked"})
			if str(prog.get("status", "")) == "completed":
				continue
			if not _preds_ok(defn, state, defs):
				continue
			if not _condition(defn, state, scene):
				continue
			prog = prog.duplicate(true)
			prog["status"] = "completed"
			prog["completed_turn"] = int(state.get("turn", 0))
			prog["reward_claimed"] = true
			objectives[oid] = prog
			var active: Array = state.get("active_objective_ids", [])
			active = active.duplicate()
			active.erase(oid)
			for nxt in defn.get("next_objective_ids", []):
				var nid: String = str(nxt)
				if not objectives.has(nid):
					objectives[nid] = {"objective_id": nid, "status": "locked"}
				if str(objectives[nid].get("status", "")) == "locked":
					objectives[nid]["status"] = "active"
				if nid not in active:
					active.append(nid)
			if not bool(prog.get("reward_claimed", false)):
				state["research_points"] = int(state.get("research_points", 0)) + int(
					defn.get("reward_research_points", 0)
				)
			state["objectives"] = objectives
			state["active_objective_ids"] = active
			result["completed"].append(defn)
			changed = true
	state = ensure_fields(state)
	result["state"] = state
	return result


static func _preds_ok(defn: Dictionary, state: Dictionary, defs: Array) -> bool:
	var step: int = int(defn.get("tutorial_step", 0))
	for other in defs:
		if int(other.get("tutorial_step", 0)) >= step:
			continue
		var oid: String = str(other.get("id", ""))
		var prog: Dictionary = state["objectives"].get(oid, {})
		if str(prog.get("status", "")) != "completed":
			return false
	return true


static func _condition(defn: Dictionary, state: Dictionary, scene: Dictionary) -> bool:
	var tt: String = str(defn.get("trigger_type", ""))
	match tt:
		"entity_named":
			var name: String = str(state.get("research_entity", {}).get("name", ""))
			return name != "" and name != "Unnamed Research Entity"
		"solar_discovery":
			for d in state.get("discoveries", {}).values():
				if d is Dictionary and str(d.get("object_type", "")) in [
					"star", "planet", "moon", "asteroid", "comet", "observatory"
				]:
					return true
			return false
		"survey_complete":
			var sid: String = str(defn.get("required_survey_id", ""))
			var p: Dictionary = state.get("survey_progress", {}).get(sid, {})
			return bool(p.get("completed", false))
		"tier_unlocked":
			return str(defn.get("required_tier_id", "")) in state.get("unlocked_tiers", [])
		"transient_observed":
			for ts in state.get("transient_events", {}).values():
				if ts is Dictionary and bool(ts.get("reward_claimed", false)):
					return true
			return false
		"campaign_scene_unlocked":
			var cs: Dictionary = state.get("campaign", {}).get("scenes", {}).get(
				str(defn.get("required_scene_id", "")), {}
			)
			return bool(cs.get("unlocked", false))
		"campaign_scene_active":
			var sid: String = str(defn.get("required_scene_id", ""))
			return (
				str(state.get("campaign", {}).get("active_scene_id", "")) == sid
				or str(scene.get("id", "")) == sid
			)
		"survey_active_or_complete":
			var sv: String = str(defn.get("required_survey_id", ""))
			if state.get("active_survey_id") == sv:
				return true
			var sp: Dictionary = state.get("survey_progress", {}).get(sv, {})
			return bool(sp.get("completed", false))
		"deep_field_discovery":
			for d in state.get("discoveries", {}).values():
				if d is Dictionary and str(d.get("object_type", "")) in [
					"galaxy", "quasar", "lyman_alpha_blob"
				]:
					if float(d.get("confidence", 0)) >= 0.5:
						return true
			return false
	return false
