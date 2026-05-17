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
