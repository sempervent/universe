class_name MilestoneEngine
extends RefCounted
# MilestoneEngine — port of universe.game.milestones.

const _EntityModifiers := preload("res://scripts/EntityModifiers.gd")
#
# Predicates are expressed as plain GDScript checks against the state
# dictionary.  Same conditions, same auto-claim semantics as Python.

const CANDIDATE := 0.5
const CONFIRMED := 0.75
const DEFAULT_NAME := "Unnamed Research Entity"


static func load_milestones(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		return parsed
	return []


static func _has_discovery(state: Dictionary, types: Array, min_conf: float) -> bool:
	for raw_d in state.get("discoveries", {}).values():
		var d: Dictionary = raw_d as Dictionary
		if (d.get("object_type", "") in types) and float(d.get("confidence", 0.0)) >= min_conf:
			return true
	return false


static func _has_signal(state: Dictionary, signal_name: String) -> bool:
	for raw_d in state.get("discoveries", {}).values():
		var d: Dictionary = raw_d as Dictionary
		if signal_name in d.get("detected_signals", []):
			return true
	return false


static func _condition(milestone_id: String, state: Dictionary) -> bool:
	match milestone_id:
		"first_light":
			return int(state.get("turn", 0)) >= 1 or state.get("discoveries", {}).size() > 0
		"named_entity":
			var entity: Dictionary = state.get("research_entity", {}) as Dictionary
			var n: String = str(entity.get("name", ""))
			return n != "" and n != DEFAULT_NAME
		"first_planet":
			return _has_discovery(state, ["planet"], CONFIRMED)
		"first_moon":
			return _has_discovery(state, ["moon"], CONFIRMED)
		"first_comet":
			return _has_discovery(state, ["comet"], CANDIDATE)
		"first_upgrade":
			var count: int = 0
			for t in state.get("unlocked_tiers", []):
				if t != "naked_eye":
					count += 1
			return count >= 1
		"radio_first_light":
			if "radio" in state.get("known_signal_types", []):
				return true
			return _has_signal(state, "radio")
		"first_deep_sky_object":
			return _has_discovery(state, ["galaxy", "quasar", "lyman_alpha_blob"], CANDIDATE)
		"first_black_hole_candidate":
			return _has_discovery(state, ["black_hole"], CANDIDATE)
		"first_magnetar":
			return _has_discovery(state, ["magnetar"], CONFIRMED)
		"multi_messenger_confirmation":
			for raw_d in state.get("discoveries", {}).values():
				var d: Dictionary = raw_d as Dictionary
				var sigs: Array = d.get("detected_signals", [])
				if sigs.size() >= 3 and float(d.get("confidence", 0.0)) >= CONFIRMED:
					return true
			return false
		"cosmic_web_mapped":
			return _has_discovery(state, ["cosmic_web_filament", "cosmic_web_node"], CONFIRMED)
		"dark_matter_inferred":
			return _has_signal(state, "dark_matter_inference")
		"now_scope_first_light":
			if _has_signal(state, "speculative_now_signal"):
				return true
			for raw_d in state.get("discoveries", {}).values():
				var d: Dictionary = raw_d as Dictionary
				if d.get("first_detected_tier", "") == "now_scope":
					return true
			return false
	return false


static func evaluate(state: Dictionary, milestones: Array, modifiers_table: Array = []) -> Dictionary:
	# Returns {state: Dictionary, achieved: Array[Dictionary]} — each dict is milestone + _awarded_rp.
	var achieved: Array = []
	var extra_rp: int = 0
	for raw_m in milestones:
		var m: Dictionary = raw_m as Dictionary
		var mid: String = str(m.get("id", ""))
		var existing: Dictionary = state["milestones"].get(mid, {})
		if existing.get("achieved", false):
			continue
		if not _condition(mid, state):
			continue
		var rp: int = int(m.get("reward_research_points", 0))
		if not modifiers_table.is_empty():
			rp = _EntityModifiers.effective_milestone_reward(m, state, modifiers_table)
		state["milestones"][mid] = {
			"milestone_id": mid,
			"achieved": true,
			"achieved_at_turn": int(state.get("turn", 0)),
			"reward_claimed": true,
		}
		extra_rp += rp
		var row: Dictionary = m.duplicate()
		row["_awarded_rp"] = rp
		achieved.append(row)
	if achieved.size() > 0:
		state["research_points"] = int(state.get("research_points", 0)) + extra_rp
	return {"state": state, "achieved": achieved}
