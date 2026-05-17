class_name DiscoveryEngine
extends RefCounted
# DiscoveryEngine — port of universe.game.discovery (subset).

const _EntityModifiers := preload("res://scripts/EntityModifiers.gd")
#
# Computes detection confidence and research-point awards client-side.
# This mirror is intentionally simpler than the Python version:
#   - Uses linear blending instead of full saturation curves.
#   - Distance/penalty terms are omitted for solar-system objects (everything
#     is well within range for any unlocked tier).
# When in doubt, treat the Python implementation as canonical.


static func _label(c: float) -> String:
	if c < 0.25:
		return "not detected"
	if c < 0.50:
		return "signal anomaly"
	if c < 0.75:
		return "candidate"
	if c < 0.95:
		return "confirmed"
	return "characterized"


static func calculate_confidence(
	obj: Dictionary,
	state: Dictionary,
	tree: Array,
	requirements_map: Dictionary,
	modifiers_table: Array = [],
) -> Dictionary:
	# Returns {"confidence": float, "detected": Array[String]}
	var obj_type: String = obj.get("type", "")
	var req: Dictionary = requirements_map.get(obj_type, {})
	if req.is_empty():
		return {"confidence": 0.0, "detected": []}

	var known := TechTree.all_known_signal_types(tree, state)
	var known_set := {}
	for s in known:
		known_set[s] = true

	var required: Array = req.get("required_signal_types", [])
	var optional: Array = req.get("optional_signal_types", [])

	var have_required := 0
	var detected: Array = []
	for s in required:
		if known_set.has(s):
			have_required += 1
			detected.append(s)
	for s in optional:
		if known_set.has(s):
			detected.append(s)

	var sensitivity := TechTree.best_sensitivity(tree, state)
	var resolution := TechTree.best_resolution(tree, state)
	var min_sens: float = float(req.get("minimum_sensitivity", 0.0))
	var min_res: float = float(req.get("minimum_resolution_arcsec", 3600.0))
	var min_tier: int = int(req.get("minimum_telescope_tier", 0))
	var have_tier := TechTree.max_tier_index(tree, state)

	if have_tier < min_tier:
		return {"confidence": 0.0, "detected": detected}
	if required.size() > 0 and have_required == 0:
		return {"confidence": 0.0, "detected": detected}

	var coverage := 0.0
	if required.size() > 0:
		coverage = float(have_required) / float(required.size())
	else:
		coverage = 1.0

	var sens_factor := clampf(sensitivity / max(min_sens, 0.0001), 0.0, 1.5)
	var res_factor := clampf(min_res / max(resolution, 0.0001), 0.0, 1.5)

	var base := coverage * min(sens_factor, 1.0) * min(res_factor, 1.0)

	var optional_detected := 0
	for s in optional:
		if known_set.has(s):
			optional_detected += 1
	var bonus := 0.1 * float(optional_detected)
	var confidence := clampf(base + bonus, 0.0, 1.0)

	# Multi-messenger boost: 3+ signal channels confirms.
	if detected.size() >= 3:
		confidence = max(confidence, 0.85)
	if detected.size() >= 4:
		confidence = max(confidence, 0.95)

	confidence = _EntityModifiers.apply_confidence_bonus(confidence, state, modifiers_table)
	return {"confidence": confidence, "detected": detected}


static func award_points(
	obj: Dictionary,
	confidence: float,
	is_new: bool,
	requirements_map: Dictionary,
	state: Dictionary,
	modifiers_table: Array = [],
) -> int:
	if confidence < 0.25:
		return 0
	var obj_type: String = obj.get("type", "")
	var req: Dictionary = requirements_map.get(obj_type, {})
	var base: int = int(req.get("base_research_points", 5))
	var pts: float = float(base) * confidence
	if is_new:
		pts *= 1.5
	pts = max(1.0, float(round(pts)))
	pts *= _EntityModifiers.discovery_rp_multiplier(state, modifiers_table)
	return max(1, int(round(pts)))


static func confidence_label(c: float) -> String:
	return _label(c)
