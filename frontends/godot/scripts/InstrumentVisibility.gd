class_name InstrumentVisibility
extends RefCounted
## Legible tier + signal-mode visibility for Observatory View (Godot-only).

const FULL := "full"
const DIM := "dim"
const HIDDEN := "hidden"

const _BRIGHT_PLANETS := [
	"planet-mercury", "planet-venus", "planet-mars",
	"planet-jupiter", "planet-saturn",
]


static func signal_mode_blurb(mode: String) -> String:
	match mode:
		"visible_light":
			return "Optical view: reflected/starlight sources."
		"radio":
			return "Radio view: jets, cold gas, compact sources."
		"microwave":
			return "Microwave view: background radiation / CMB."
		"xray":
			return "X-ray view: accretion and compact-object violence."
		"gamma_ray":
			return "Gamma view: extreme transients and magnetars."
		"gravitational_wave":
			return "Inference view: compact-object mergers, not ordinary images."
		"neutrino":
			return "Neutrino view: high-energy event messengers."
		"weak_lensing":
			return "Lensing view: inferred mass distortions."
		"dark_matter_inference":
			return "Mass map: inferred invisible structure."
		"speculative_now_signal":
			return "Speculative fictional final instrument."
		"infrared":
			return "Infrared view: dust and cool extended emission."
		"ultraviolet":
			return "Ultraviolet view: hot gas and Lyman-line tracers."
		_:
			return "Instrument channel: %s." % mode.replace("_", " ")


static func evaluate(
	obj: Dictionary,
	scene: Dictionary,
	state: Dictionary,
	tree: Array,
	requirements_map: Dictionary,
	signal_mode: String,
) -> Dictionary:
	var oid: String = str(obj.get("id", ""))
	var otype: String = str(obj.get("type", ""))
	var conf: float = 0.0
	var disc: Dictionary = state.get("discoveries", {}).get(oid, {}) as Dictionary
	if not disc.is_empty():
		conf = float(disc.get("confidence", 0.0))

	var tier: int = TechTree.max_tier_index(tree, state)
	var vis: String = _tier_visibility(obj, scene, tier)
	vis = _signal_visibility(vis, obj, otype, signal_mode, tree, state, requirements_map)

	if conf >= 0.25 and vis == HIDDEN:
		vis = DIM
	if conf >= 0.75:
		vis = FULL

	var reason: String = visibility_reason(vis, obj, scene, tier, signal_mode, tree, state, requirements_map)
	var pickable: bool = vis != HIDDEN
	return {"visibility": vis, "pickable": pickable, "reason": reason}


static func visibility_reason(
	vis: String,
	obj: Dictionary,
	scene: Dictionary,
	tier: int,
	signal_mode: String,
	tree: Array,
	state: Dictionary,
	requirements_map: Dictionary,
) -> String:
	if vis == FULL:
		return "Visible to current instrument."
	var otype: String = str(obj.get("type", ""))
	var req: Dictionary = requirements_map.get(otype, {}) as Dictionary
	var min_tier: int = int(req.get("minimum_telescope_tier", 0))
	if vis == HIDDEN and tier < min_tier:
		return "Hidden: unlock a higher telescope tier (need tier %d+)." % min_tier
	if vis == HIDDEN and SceneLoader.is_deep_field_scene(scene) and tier < 3:
		return "Hidden: deep-field sources need Space Optical tier or better."
	if vis == HIDDEN and otype in ["asteroid", "comet"] and tier < 2:
		return "Hidden: faint solar-system body — needs Improved Ground Observatory+."
	if vis == HIDDEN and str(obj.get("id", "")).begins_with("moon-"):
		return "Hidden: Galilean moons need a ground optical telescope+."
	if vis == HIDDEN and signal_mode == "microwave":
		return "Hidden in microwave view except CMB / radio-bright sources."
	if vis == HIDDEN and signal_mode in ["weak_lensing", "dark_matter_inference"]:
		return "Hidden: not a mass-map tracer in this mode."
	if vis == DIM:
		return "Dim: at edge of current tier or signal mode — upgrade or switch instrument."
	return "Not visible to current instrument."


static func _tier_visibility(obj: Dictionary, scene: Dictionary, tier: int) -> String:
	var oid: String = str(obj.get("id", ""))
	var otype: String = str(obj.get("type", ""))
	var props: Dictionary = obj.get("properties", {}) as Dictionary
	var mag: float = float(props.get("apparent_magnitude", 10.0))

	if SceneLoader.is_solar_system_scene(scene):
		if oid in ["sun", "moon"]:
			return FULL
		if otype == "planet":
			if oid in ["planet-uranus", "planet-neptune"]:
				if tier >= 2:
					return FULL
				if tier >= 1:
					return DIM
				return HIDDEN
			if oid in _BRIGHT_PLANETS or mag < 2.5:
				return FULL
			return DIM if tier >= 1 else HIDDEN
		if oid.begins_with("moon-"):
			if tier >= 2:
				return FULL
			if tier >= 1:
				return DIM
			return HIDDEN
		if otype in ["asteroid", "comet"]:
			if tier >= 2:
				return FULL
			if tier >= 1:
				return DIM
			return HIDDEN
		if otype == "star":
			return FULL
		return DIM if tier >= 1 else HIDDEN

	# Deep field
	if tier < 3:
		if otype in ["galaxy", "quasar", "lyman_alpha_blob", "black_hole", "magnetar", "cosmic_web_node"]:
			return HIDDEN
		return DIM
	if otype == "galaxy":
		return FULL if tier >= 3 else DIM
	if otype == "quasar":
		return FULL if tier >= 3 else DIM
	if otype == "lyman_alpha_blob":
		return FULL if tier >= 4 else DIM
	if otype in ["black_hole", "magnetar"]:
		return DIM if tier >= 4 else HIDDEN
	if otype == "cosmic_web_node":
		return DIM
	return FULL


static func _signal_visibility(
	base: String,
	obj: Dictionary,
	otype: String,
	signal_mode: String,
	tree: Array,
	state: Dictionary,
	requirements_map: Dictionary,
) -> String:
	if base == HIDDEN:
		return HIDDEN

	var known: Dictionary = {}
	for s in TechTree.all_known_signal_types(tree, state):
		known[s] = true

	var req: Dictionary = requirements_map.get(otype, {}) as Dictionary
	var required: Array = req.get("required_signal_types", [])
	var optional: Array = req.get("optional_signal_types", [])

	var mode_ok: bool = signal_mode in required or signal_mode in optional
	if signal_mode == "visible_light" and (required.is_empty() or "visible_light" in required):
		mode_ok = true

	match signal_mode:
		"microwave":
			if otype == "cmb_background":
				return FULL
			if otype in ["quasar", "galaxy"]:
				return DIM if base == FULL else base
			if otype in ["planet", "moon", "star", "asteroid", "comet"]:
				return HIDDEN
		"radio":
			if otype in ["quasar", "magnetar", "galaxy"]:
				return FULL if base != HIDDEN else base
			if otype in ["planet", "moon"]:
				return DIM if base == FULL else base
		"xray", "gamma_ray":
			if otype in ["magnetar", "black_hole", "quasar"]:
				return FULL if base != HIDDEN else base
			if otype in ["planet", "moon", "asteroid", "comet", "galaxy"]:
				return DIM if base == FULL else HIDDEN
		"weak_lensing", "dark_matter_inference":
			if otype in ["cosmic_web_node", "galaxy", "lyman_alpha_blob"]:
				return FULL if base != HIDDEN else DIM
			if otype in ["planet", "moon", "star"]:
				return HIDDEN
		"gravitational_wave", "neutrino":
			if otype in ["black_hole", "magnetar", "quasar"]:
				return DIM if base != HIDDEN else HIDDEN
		"speculative_now_signal":
			if bool(req.get("speculative", false)) or otype in ["quasar", "magnetar", "black_hole"]:
				return FULL
			return DIM if base == FULL else HIDDEN
		"visible_light", "infrared", "ultraviolet":
			if not mode_ok and not optional.is_empty():
				return DIM if base == FULL else base
			return base

	if not mode_ok and required.size() > 0:
		return DIM if base == FULL else base
	return base
