class_name TechTree
extends RefCounted
# TechTree — derive aggregate telescope capabilities from the player's
# unlocked tiers.  Mirrors universe.game.tech_tree helpers.


static func load_tree(path: String) -> Array:
	if not FileAccess.file_exists(path):
		push_warning("TechTree: %s not found — run `universe game export-godot-data`" % path)
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		return parsed
	return []


static func tier_map(tree: Array) -> Dictionary:
	var m := {}
	for t in tree:
		if t is Dictionary and t.has("id"):
			m[t["id"]] = t
	return m


static func unlocked_tier_dicts(tree: Array, state: Dictionary) -> Array:
	var ids: Array = state.get("unlocked_tiers", [])
	var tm := tier_map(tree)
	var out: Array = []
	for id in ids:
		if tm.has(id):
			out.append(tm[id])
	return out


static func best_sensitivity(tree: Array, state: Dictionary) -> float:
	var best := 0.0
	for t in unlocked_tier_dicts(tree, state):
		var v: float = float(t.get("sensitivity", 0.0))
		if v > best:
			best = v
	return best


static func best_resolution(tree: Array, state: Dictionary) -> float:
	# Smaller arcsec = finer.  Returns the smallest (best) value.
	var best := INF
	for t in unlocked_tier_dicts(tree, state):
		var v: float = float(t.get("resolution_arcsec", 1e9))
		if v < best:
			best = v
	if best == INF:
		return 3600.0
	return best


static func max_distance_mpc(tree: Array, state: Dictionary) -> float:
	var best := 0.0
	for t in unlocked_tier_dicts(tree, state):
		var v: float = float(t.get("max_effective_distance_mpc", 0.0))
		if v > best:
			best = v
	return best


static func max_tier_index(tree: Array, state: Dictionary) -> int:
	var best := -1
	for t in unlocked_tier_dicts(tree, state):
		var v: int = int(t.get("tier_index", -1))
		if v > best:
			best = v
	return best


static func all_known_signal_types(tree: Array, state: Dictionary) -> Array:
	var sigs := {}
	for s in state.get("known_signal_types", []):
		sigs[s] = true
	for t in unlocked_tier_dicts(tree, state):
		for s in t.get("signal_types", []):
			sigs[s] = true
	return sigs.keys()


static func sync_known_signals(tree: Array, state: Dictionary) -> Dictionary:
	var sigs := {}
	for t in unlocked_tier_dicts(tree, state):
		for s in t.get("signal_types", []):
			sigs[s] = true
	if sigs.is_empty():
		sigs["visible_light"] = true
	var out: Dictionary = state.duplicate(true)
	out["known_signal_types"] = sigs.keys()
	return out


static func can_unlock(tree: Array, state: Dictionary, tier_id: String, modifiers: Array) -> Dictionary:
	var tm := tier_map(tree)
	if not tm.has(tier_id):
		return {"ok": false, "message": "Unknown tier."}
	if tier_id in state.get("unlocked_tiers", []):
		return {"ok": false, "message": "Already unlocked."}
	var tier: Dictionary = tm[tier_id]
	for p in tier.get("prerequisites", []):
		if p not in state.get("unlocked_tiers", []):
			return {"ok": false, "message": "Missing prerequisite: %s." % p}
	var cost: int = EntityModifiers.effective_tier_cost(tier, state, modifiers)
	if int(state.get("research_points", 0)) < cost:
		return {
			"ok": false,
			"message": "Not enough RP: need %d, have %d." % [cost, int(state.get("research_points", 0))],
		}
	return {"ok": true, "cost": cost, "tier": tier}


static func unlock_tier(tree: Array, state: Dictionary, tier_id: String, modifiers: Array) -> Dictionary:
	var check: Dictionary = can_unlock(tree, state, tier_id, modifiers)
	if not bool(check.get("ok", false)):
		return {"ok": false, "message": str(check.get("message", "Cannot unlock."))}
	var tier: Dictionary = check["tier"] as Dictionary
	var cost: int = int(check.get("cost", 0))
	var out: Dictionary = state.duplicate(true)
	out["research_points"] = int(out.get("research_points", 0)) - cost
	var tiers: Array = out.get("unlocked_tiers", []).duplicate()
	if tier_id not in tiers:
		tiers.append(tier_id)
	out["unlocked_tiers"] = tiers
	out["active_telescope_tier"] = tier_id
	out = sync_known_signals(tree, out)
	return {"ok": true, "state": out, "message": "Unlocked %s." % tier.get("name", tier_id)}
