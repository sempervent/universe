class_name SurveyEngine
extends RefCounted
# SurveyEngine — port of universe.game.surveys (subset).

const _EntityModifiers := preload("res://scripts/EntityModifiers.gd")
#
# Implements survey status, start/claim, and per-discovery progress.
# Definitions live in res://data/surveys.json (generated from Python).


const STATUS_LOCKED := "locked"
const STATUS_AVAILABLE := "available"
const STATUS_ACTIVE := "active"
const STATUS_COMPLETED := "completed"


static func load_programs(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		return parsed
	return []


static func by_id(programs: Array) -> Dictionary:
	var m := {}
	for p in programs:
		if p is Dictionary and p.has("id"):
			m[p["id"]] = p
	return m


static func _scope_matches(survey: Dictionary, scene: Dictionary) -> bool:
	var scope: String = survey.get("scene_scope", "any")
	if scope == "any":
		return true
	var scene_id: String = scene.get("id", "")
	if scope == "solar_system":
		return scene_id == "solar-system"
	if scope == "deep_field":
		return scene_id != "solar-system"
	return false


static func status(survey: Dictionary, state: Dictionary) -> String:
	var sp: Dictionary = state.get("survey_progress", {})
	var prog: Dictionary = sp.get(survey["id"], {})
	if prog.get("completed", false):
		return STATUS_COMPLETED
	if state.get("active_survey_id", null) == survey["id"]:
		return STATUS_ACTIVE
	var unlocked := {}
	for t in state.get("unlocked_tiers", []):
		unlocked[t] = true
	var sigs := {}
	for s in state.get("known_signal_types", []):
		sigs[s] = true
	for tid in survey.get("required_tier_ids", []):
		if not unlocked.has(tid):
			return STATUS_LOCKED
	for sig in survey.get("required_signal_types", []):
		if not sigs.has(sig):
			return STATUS_LOCKED
	return STATUS_AVAILABLE


static func start_survey(state: Dictionary, survey_id: String, programs_map: Dictionary) -> Dictionary:
	# Returns {state: Dictionary, message: String}
	if not programs_map.has(survey_id):
		return {"state": state, "message": "Unknown survey: %s" % survey_id}
	var survey: Dictionary = programs_map[survey_id]
	var st := status(survey, state)
	if st == STATUS_COMPLETED:
		return {"state": state, "message": "%s already completed." % survey["name"]}
	if st == STATUS_LOCKED:
		return {"state": state, "message": "%s is locked." % survey["name"]}
	state["active_survey_id"] = survey_id
	if not state["survey_progress"].has(survey_id):
		state["survey_progress"][survey_id] = _empty_progress(survey_id)
	return {"state": state, "message": "Started survey: %s" % survey["name"]}


static func claim_reward(
	state: Dictionary,
	survey_id: String,
	programs_map: Dictionary,
	modifiers_table: Array = [],
) -> Dictionary:
	if not programs_map.has(survey_id):
		return {"state": state, "message": "Unknown survey: %s" % survey_id}
	var survey: Dictionary = programs_map[survey_id]
	var prog: Dictionary = state.get("survey_progress", {}).get(survey_id, {})
	if not prog.get("completed", false):
		return {"state": state, "message": "%s not yet complete." % survey["name"]}
	if prog.get("claimed_reward", false):
		return {"state": state, "message": "Reward already claimed."}
	var reward: int = _EntityModifiers.effective_survey_reward(survey, state, modifiers_table)
	prog["claimed_reward"] = true
	state["survey_progress"][survey_id] = prog
	state["research_points"] = int(state.get("research_points", 0)) + reward
	return {"state": state, "message": "Claimed +%d RP for %s" % [reward, survey["name"]]}


static func _empty_progress(sid: String) -> Dictionary:
	return {
		"survey_id": sid,
		"observations_completed": 0,
		"discoveries_completed": 0,
		"completed": false,
		"claimed_reward": false,
		"discovered_object_ids": [],
	}


static func _matches(survey: Dictionary, obj_type: String, detected: Array, confidence: float, scene: Dictionary) -> bool:
	var targets: Array = survey.get("target_object_types", [])
	if targets.size() > 0 and not (obj_type in targets):
		# Speculative survey with empty target list accepts any object.
		if not (survey.get("speculative", false) and targets.is_empty()):
			return false
	var min_conf: float = float(survey.get("min_confidence", 0.5))
	if confidence < min_conf:
		return false
	if not _scope_matches(survey, scene):
		return false
	for sig in survey.get("required_signal_types", []):
		if not (sig in detected):
			return false
	return true


static func update_progress(
	state: Dictionary,
	scene: Dictionary,
	obj_id: String,
	obj_type: String,
	detected: Array,
	confidence: float,
	programs_map: Dictionary,
	modifiers_table: Array = [],
) -> Dictionary:
	# Returns {state: Dictionary, event: Dictionary} where event may be empty.
	var sid: Variant = state.get("active_survey_id", null)
	if sid == null or sid == "":
		return {"state": state, "event": {}}
	if not programs_map.has(sid):
		return {"state": state, "event": {}}
	var survey: Dictionary = programs_map[sid]
	if not _matches(survey, obj_type, detected, confidence, scene):
		return {"state": state, "event": {}}
	var prog: Dictionary = state["survey_progress"].get(sid, _empty_progress(sid))
	if prog.get("completed", false):
		return {"state": state, "event": {}}
	if obj_id in prog["discovered_object_ids"]:
		return {"state": state, "event": {}}

	prog["discovered_object_ids"].append(obj_id)
	var delta: int = 1
	if not modifiers_table.is_empty():
		delta = _EntityModifiers.survey_progress_delta(state, modifiers_table)
	var next_count: int = mini(
		int(survey.get("completion_goal", 1)),
		int(prog.get("discoveries_completed", 0)) + delta
	)
	prog["discoveries_completed"] = next_count
	state["survey_progress"][sid] = prog

	var goal: int = int(survey.get("completion_goal", 1))
	if prog["discoveries_completed"] >= goal and not prog["completed"]:
		prog["completed"] = true
		if not prog.get("claimed_reward", false):
			prog["claimed_reward"] = true
			var reward: int = _EntityModifiers.effective_survey_reward(survey, state, modifiers_table)
			state["research_points"] = int(state.get("research_points", 0)) + reward
			return {
				"state": state,
				"event": {"type": "completed", "survey": survey, "reward": reward},
			}
	return {
		"state": state,
		"event": {
			"type": "progress",
			"survey": survey,
			"done": prog["discoveries_completed"],
			"goal": goal,
		},
	}
