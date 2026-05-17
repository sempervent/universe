class_name TransientEngine
extends RefCounted
# TransientEngine — turn-window events (mirrors universe.game.transients).


static func load_definitions(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		return parsed
	return []


static func by_id(defs: Array) -> Dictionary:
	var out: Dictionary = {}
	for raw_d in defs:
		var d: Dictionary = raw_d as Dictionary
		if d.has("id"):
			out[str(d["id"])] = d
	return out


static func update_states(state: Dictionary, defs: Array) -> Dictionary:
	var out: Dictionary = state.duplicate(true)
	var events: Dictionary = out.get("transient_events", {})
	if not (events is Dictionary):
		events = {}
	var turn: int = int(out.get("turn", 0))
	for raw_d in defs:
		var d: Dictionary = raw_d as Dictionary
		var eid: String = str(d.get("id", ""))
		if eid == "":
			continue
		var start: int = int(d.get("start_turn", 1))
		var dur: int = int(d.get("duration_turns", 1))
		var end: int = start + dur
		var prev: Dictionary = events.get(eid, {"event_id": eid})
		events[eid] = {
			"event_id": eid,
			"active": turn >= start and turn < end,
			"discovered": bool(prev.get("discovered", false)),
			"observed_turns": prev.get("observed_turns", []),
			"first_observed_turn": prev.get("first_observed_turn"),
			"expired": turn >= end,
			"reward_claimed": bool(prev.get("reward_claimed", false)),
		}
	out["transient_events"] = events
	return out


static func is_observable(
	scene: Dictionary,
	state: Dictionary,
	defn: Dictionary,
	tech_tree: Array,
) -> Dictionary:
	var result := {"ok": false, "reason": ""}
	var eid: String = str(defn.get("id", ""))
	if str(scene.get("id", "")) != str(defn.get("scene_id", "")):
		result["reason"] = "Wrong scene."
		return result
	state = update_states(state, [defn])
	var ts: Dictionary = state["transient_events"].get(eid, {})
	if bool(ts.get("expired", false)):
		result["reason"] = "Expired."
		return result
	if not bool(ts.get("active", false)):
		result["reason"] = "Not active."
		return result
	if bool(ts.get("reward_claimed", false)) and not bool(defn.get("repeatable", false)):
		result["reason"] = "Already observed."
		return result
	var min_tier: String = str(defn.get("minimum_telescope_tier", "naked_eye"))
	if not _tier_ok(state, min_tier, tech_tree):
		result["reason"] = "Tier too low."
		return result
	var req: Array = defn.get("required_signal_types", [])
	if req.size() > 0:
		var known: Array = state.get("known_signal_types", [])
		var hit := false
		for s in req:
			if str(s) in known:
				hit = true
				break
		if not hit:
			result["reason"] = "Missing signal."
			return result
	result["ok"] = true
	return result


static func observe(
	scene: Dictionary,
	state: Dictionary,
	defn: Dictionary,
	tech_tree: Array,
) -> Dictionary:
	var check := is_observable(scene, state, defn, tech_tree)
	if not bool(check["ok"]):
		return {"state": state, "ok": false, "message": str(check["reason"])}
	var eid: String = str(defn.get("id", ""))
	state = update_states(state, [defn])
	var rp: int = int(defn.get("reward_research_points", 0))
	var events: Dictionary = state["transient_events"].duplicate(true)
	var ts: Dictionary = events[eid].duplicate(true)
	var turns: Array = ts.get("observed_turns", [])
	turns.append(int(state.get("turn", 0)))
	ts["observed_turns"] = turns
	ts["discovered"] = true
	ts["reward_claimed"] = true
	if ts.get("first_observed_turn") == null:
		ts["first_observed_turn"] = int(state.get("turn", 0))
	events[eid] = ts
	state = state.duplicate(true)
	state["transient_events"] = events
	state["research_points"] = int(state.get("research_points", 0)) + rp
	var spec := " [SPECULATIVE]" if bool(defn.get("speculative", false)) else ""
	return {
		"state": state,
		"ok": true,
		"message": "Transient: %s%s — +%d RP" % [str(defn.get("name", eid)), spec, rp],
	}


static func _tier_ok(state: Dictionary, min_tier: String, tech_tree: Array) -> bool:
	var unlocked: Array = state.get("unlocked_tiers", [])
	if min_tier in unlocked:
		return true
	var min_idx := _tier_index(min_tier, tech_tree)
	var active: String = str(state.get("active_telescope_tier", "naked_eye"))
	var act_idx := _tier_index(active, tech_tree)
	return act_idx >= min_idx and min_idx >= 0


static func _tier_index(tier_id: String, tech_tree: Array) -> int:
	for t in tech_tree:
		if t is Dictionary and str(t.get("id", "")) == tier_id:
			return int(t.get("tier_index", -1))
	return -1
