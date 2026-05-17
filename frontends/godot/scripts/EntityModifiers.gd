class_name EntityModifiers
extends RefCounted
# Entity background modifiers — mirrors universe.game.entity.EntityModifier.
# Loaded from res://data/entity_modifiers.json (export-godot-data).


static func load_table(path: String) -> Array:
	if not FileAccess.file_exists(path):
		push_warning("EntityModifiers: %s missing — run export-godot-data" % path)
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var p: Variant = JSON.parse_string(f.get_as_text())
	return p if p is Array else []


static func modifier_for_state(state: Dictionary, table: Array) -> Dictionary:
	if table.is_empty():
		return _neutral()
	var et := str(state.get("research_entity", {}).get("entity_type", "custom"))
	for e in table:
		if e is Dictionary and str(e.get("entity_type", "")) == et:
			return e
	for e in table:
		if e is Dictionary and str(e.get("entity_type", "")) == "custom":
			return e
	return _neutral()


static func _neutral() -> Dictionary:
	return {
		"entity_type": "custom",
		"name": "Custom Charter",
		"description": "No institutional background modifier.",
		"discovery_rp_multiplier": 1.0,
		"milestone_rp_multiplier": 1.0,
		"survey_rp_multiplier": 1.0,
		"upgrade_cost_multiplier": 1.0,
		"early_optical_upgrade_cost_multiplier": 1.0,
		"space_upgrade_cost_multiplier": 1.0,
		"confidence_bonus": 0.0,
		"survey_progress_bonus": 0,
		"speculative_bonus": false,
	}


static func effective_tier_cost(tier: Dictionary, state: Dictionary, table: Array) -> int:
	var m := modifier_for_state(state, table)
	var cost := float(tier.get("research_cost", 0))
	cost *= float(m.get("upgrade_cost_multiplier", 1.0))
	var tid: String = str(tier.get("id", ""))
	if tid == "ground_optical" or tid == "improved_ground":
		cost *= float(m.get("early_optical_upgrade_cost_multiplier", 1.0))
	var tidx: int = int(tier.get("tier_index", 0))
	if tidx >= 3:
		cost *= float(m.get("space_upgrade_cost_multiplier", 1.0))
	return maxi(0, int(round(cost)))


static func apply_confidence_bonus(confidence: float, state: Dictionary, table: Array) -> float:
	if confidence <= 0.0:
		return confidence
	var m := modifier_for_state(state, table)
	var b: float = float(m.get("confidence_bonus", 0.0))
	return clampf(snapped(confidence + b, 0.0001), 0.0, 1.0)


static func discovery_rp_multiplier(state: Dictionary, table: Array) -> float:
	return float(modifier_for_state(state, table).get("discovery_rp_multiplier", 1.0))


static func effective_survey_reward(survey: Dictionary, state: Dictionary, table: Array) -> int:
	var m := modifier_for_state(state, table)
	var mult := float(m.get("survey_rp_multiplier", 1.0))
	if bool(m.get("speculative_bonus", false)) and bool(survey.get("speculative", false)):
		mult *= 1.1
	return maxi(0, int(round(float(survey.get("reward_research_points", 0)) * mult)))


static func effective_milestone_reward(milestone: Dictionary, state: Dictionary, table: Array) -> int:
	var m := modifier_for_state(state, table)
	var mult := float(m.get("milestone_rp_multiplier", 1.0))
	if bool(m.get("speculative_bonus", false)) and bool(milestone.get("speculative", false)):
		mult *= 1.1
	return maxi(0, int(round(float(milestone.get("reward_research_points", 0)) * mult)))


static func survey_progress_delta(state: Dictionary, table: Array) -> int:
	var m := modifier_for_state(state, table)
	return 1 + maxi(0, int(m.get("survey_progress_bonus", 0)))
