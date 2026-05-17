extends Node3D
# Main — entry point for the Godot telescope frontend prototype.
#
# Wires TelescopeCamera (orbit/zoom/pick ray), SkyRenderer (pick areas +
# discovery visuals + signal modes), and TelescopeConsole.

const TechTreeS := preload("res://scripts/TechTree.gd")
const SceneLoaderS := preload("res://scripts/SceneLoader.gd")
const GameStateS := preload("res://scripts/GameState.gd")
const DiscoveryEngineS := preload("res://scripts/DiscoveryEngine.gd")
const SurveyEngineS := preload("res://scripts/SurveyEngine.gd")
const MilestoneEngineS := preload("res://scripts/MilestoneEngine.gd")
const SkyRendererS := preload("res://scripts/SkyRenderer.gd")
const TelescopeConsoleS := preload("res://scripts/TelescopeConsole.gd")
const TelescopeCameraS := preload("res://scripts/TelescopeCamera.gd")
const EntityModifiersS := preload("res://scripts/EntityModifiers.gd")
const TransientEngineS := preload("res://scripts/TransientEngine.gd")
const ObjectiveEngineS := preload("res://scripts/ObjectiveEngine.gd")

var scene_data: Dictionary = {}
var state: Dictionary = {}
var tech_tree: Array = []
var surveys: Array = []
var milestones: Array = []
var requirements_map: Dictionary = {}
var surveys_map: Dictionary = {}
var entity_modifiers: Array = []
var scene_catalog: Array = []
var transient_defs: Array = []
var objective_defs: Array = []

var _scene_path: String = ""
var _state_path: String = ""
var _last_save_path: String = ""

var sky: SkyRenderer = null
var console: CanvasLayer = null
var camera: TelescopeCamera = null
var world_env: WorldEnvironment = null


func _ready() -> void:
	_setup_3d()
	_setup_console()
	_load_static_data()
	_load_scene_and_state()
	_render_all()
	_apply_camera_framing()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_L:
			console.toggle_labels_from_hotkey()


func _setup_3d() -> void:
	camera = TelescopeCameraS.new()
	camera.name = "TelescopeCamera"
	camera.current = true
	camera.pick_attempt.connect(_on_pick_raycast)
	camera.focus_requested.connect(_on_focus_selected)
	add_child(camera)

	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-45, 30, 0)
	light.light_energy = 0.8
	add_child(light)

	world_env = WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.02, 0.05)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.25, 0.3, 0.4)
	env.ambient_light_energy = 0.4
	world_env.environment = env
	add_child(world_env)

	sky = SkyRendererS.new()
	sky.name = "SkyRenderer"
	add_child(sky)
	sky.object_picked.connect(_on_object_picked)


func _setup_console() -> void:
	console = TelescopeConsoleS.new()
	console.name = "TelescopeConsole"
	add_child(console)
	console.setup_signal_modes(_load_signal_modes_json())
	console.action_observe.connect(_on_observe)
	console.action_survey.connect(_on_survey)
	console.action_save.connect(_on_save)
	console.action_reload.connect(_on_reload)
	console.action_select_object.connect(_on_object_picked)
	console.action_start_survey.connect(_on_start_survey)
	console.action_unlock_tier.connect(_on_unlock_tier)
	console.action_set_active_tier.connect(_on_set_active_tier)
	console.action_toggle_labels.connect(_on_toggle_labels)
	console.action_signal_mode_changed.connect(_on_signal_mode_changed)
	console.action_reset_state.connect(_on_reset_state)
	console.action_export_state.connect(_on_export_state)
	console.action_campaign_load_scene.connect(_on_campaign_load_scene)
	console.action_campaign_set_active.connect(_on_campaign_set_active_scene)
	console.action_campaign_load_and_set.connect(_on_campaign_load_and_set_scene)
	console.action_campaign_refresh.connect(refresh_campaign_ui)
	console.action_observe_transient.connect(_on_observe_transient)


func _load_signal_modes_json() -> Array:
	if not FileAccess.file_exists(FilePaths.SIGNALS_PATH):
		return [
			"visible_light", "radio", "microwave", "xray", "gamma_ray",
			"gravitational_wave", "neutrino", "weak_lensing", "dark_matter_inference",
			"speculative_now_signal",
		]
	var f := FileAccess.open(FilePaths.SIGNALS_PATH, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		return parsed
	return ["visible_light"]


func _load_static_data() -> void:
	tech_tree = TechTreeS.load_tree(FilePaths.TECH_TREE_PATH)
	surveys = SurveyEngineS.load_programs(FilePaths.SURVEYS_PATH)
	milestones = MilestoneEngineS.load_milestones(FilePaths.MILESTONES_PATH)
	requirements_map = _load_requirements_map(FilePaths.DISCOVERY_REQS_PATH)
	entity_modifiers = EntityModifiersS.load_table(FilePaths.ENTITY_MODIFIERS_PATH)
	surveys_map = SurveyEngineS.by_id(surveys)
	scene_catalog = _load_scene_catalog()
	transient_defs = TransientEngineS.load_definitions(FilePaths.TRANSIENTS_PATH)
	objective_defs = ObjectiveEngineS.load_definitions(FilePaths.OBJECTIVES_PATH)
	if tech_tree.is_empty():
		_log("[!] frontends/godot/data/ is empty — run `universe game export-godot-data`.", "#ff8888")


func _load_scene_catalog() -> Array:
	if not FileAccess.file_exists(FilePaths.SCENE_CATALOG_PATH):
		return []
	var f := FileAccess.open(FilePaths.SCENE_CATALOG_PATH, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		return parsed
	return []


func _load_requirements_map(path: String) -> Dictionary:
	var out := {}
	if not FileAccess.file_exists(path):
		return out
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Array:
		for r in parsed:
			if r is Dictionary and r.has("object_type"):
				out[r["object_type"]] = r
	return out


func _load_scene_and_state() -> void:
	_scene_path = FilePaths.resolve_scene_path()
	_state_path = FilePaths.resolve_state_path()

	scene_data = SceneLoaderS.load_scene(_scene_path)
	if not SceneLoaderS.validate_scene_minimal(scene_data):
		_log("[!] No scene at %s — generate one with `universe generate solar-system`." % _scene_path, "#ff8888")
		scene_data = {"id": "missing", "name": "(no scene loaded)", "objects": []}

	state = GameStateS.load_state(_state_path)
	state = load_campaign_catalog()
	_last_save_path = _state_path
	if state.get("research_entity", {}).get("name", "") == GameStateS.DEFAULT_ENTITY_NAME:
		_log("Tip: set the entity name with `universe game init` before launch.")


func load_campaign_catalog() -> Dictionary:
	scene_catalog = _load_scene_catalog()
	state = GameStateS.ensure_campaign(state, scene_catalog)
	return GameStateS.update_scene_unlocks(state, scene_catalog)["state"]


func refresh_campaign_ui() -> void:
	if scene_catalog.is_empty():
		scene_catalog = _load_scene_catalog()
	state = GameStateS.ensure_campaign(state, scene_catalog)
	console.render_campaign_program(
		state, scene_catalog, scene_data, _scene_path, surveys_map,
	)


func refresh_campaign_unlocks() -> void:
	if scene_catalog.is_empty():
		return
	var result: Dictionary = GameStateS.update_scene_unlocks(state, scene_catalog)
	state = result["state"]
	for sid in result.get("newly_unlocked", []):
		var entry := _catalog_entry(sid)
		var nm: String = str(entry.get("name", sid)) if not entry.is_empty() else str(sid)
		_log("New observing scene unlocked: %s" % nm, "#ffcc66")
		if not entry.is_empty() and not FilePaths.scene_exists_for_catalog_entry(entry):
			_log("Generate: %s" % FilePaths.make_generate_command(sid), "#88ccff")
	refresh_campaign_ui()


func _catalog_entry(scene_id: String) -> Dictionary:
	for entry in scene_catalog:
		if entry is Dictionary and str(entry.get("id", "")) == scene_id:
			return entry
	return {}


func load_catalog_scene(scene_id: String) -> bool:
	var entry := _catalog_entry(scene_id)
	if entry.is_empty():
		_log("Unknown campaign scene: %s" % scene_id, "#ff8888")
		return false
	var st: Dictionary = state.get("campaign", {}).get("scenes", {}).get(scene_id, {})
	if not st.get("unlocked", scene_id == "solar-system"):
		_log(
			"Scene locked. Requires: %s" % entry.get("unlock_requirement", "?"),
			"#ff8888",
		)
		return false
	var path := FilePaths.scene_path_for_catalog_entry(entry)
	if not FileAccess.file_exists(path):
		_log("Scene file missing. Run:\n%s" % FilePaths.make_generate_command(scene_id), "#ff8888")
		return false
	_scene_path = path
	scene_data = SceneLoaderS.load_scene(_scene_path)
	if not SceneLoaderS.validate_scene_minimal(scene_data):
		_log("[!] Invalid scene at %s" % _scene_path, "#ff8888")
		return false
	_apply_scene_signal_mode_from_metadata()
	_log("Loaded scene: %s" % scene_data.get("name", scene_id), "#88ff99")
	_render_all()
	_apply_camera_framing()
	return true


func set_active_campaign_scene(scene_id: String) -> bool:
	var res: Dictionary = GameStateS.set_active_campaign_scene(state, scene_id, scene_catalog)
	if not res.get("ok", false):
		_log(str(res.get("message", "Failed.")), "#ff8888")
		return false
	state = res["state"]
	_log(str(res.get("message", "OK")), "#88ff99")
	refresh_campaign_ui()
	return true


func load_and_set_campaign_scene(scene_id: String) -> bool:
	if not load_catalog_scene(scene_id):
		return false
	return set_active_campaign_scene(scene_id)


func _apply_scene_signal_mode_from_metadata() -> void:
	var meta: Dictionary = scene_data.get("metadata", {})
	if meta is Dictionary:
		var mode: String = str(meta.get("recommended_initial_signal_mode", ""))
		if mode != "":
			console.select_signal_mode(mode)
			_on_signal_mode_changed(mode)


func _on_campaign_load_scene(scene_id: String) -> void:
	load_catalog_scene(scene_id)


func _on_campaign_set_active_scene(scene_id: String) -> void:
	set_active_campaign_scene(scene_id)


func _on_campaign_load_and_set_scene(scene_id: String) -> void:
	load_and_set_campaign_scene(scene_id)


func _apply_camera_framing() -> void:
	camera.apply_scene_framing(
		sky.is_deep_field_scene(),
		sky.get_default_camera_target(),
		sky.get_default_camera_fit_radius(),
	)


func _render_all() -> void:
	state = TransientEngineS.update_states(state, transient_defs)
	sky.render_scene(scene_data, state, requirements_map)
	sky.apply_visual_state(
		state,
		requirements_map,
		console.get_signal_mode(),
		console.selected_id(),
		console.is_labels_visible(),
	)
	console.set_scene_objects(
		SceneLoaderS.get_objects(scene_data),
		state,
		scene_data,
		surveys_map,
	)
	var mod: Dictionary = EntityModifiersS.modifier_for_state(state, entity_modifiers)
	console.render_header(state, scene_data, _last_save_path, _scene_path, mod)
	console.render_signal_mode_help(console.get_signal_mode(), SceneLoaderS.is_deep_field_scene(scene_data))
	console.render_survey_hint(scene_data, state, surveys_map)
	refresh_campaign_ui()
	console.render_detail(state, requirements_map)
	console.render_tech_tree(state, tech_tree, entity_modifiers)
	console.render_surveys(state, surveys, surveys_map, entity_modifiers)
	console.render_milestones(state, milestones, entity_modifiers)
	console.render_transients(state, transient_defs, scene_data, tech_tree)
	console.render_objectives(state, objective_defs)
	_apply_environment_for_signal(console.get_signal_mode())


func _apply_environment_for_signal(mode: String) -> void:
	if world_env == null:
		return
	var bg := Color(0.02, 0.02, 0.06)
	var amb := Color(0.22, 0.26, 0.38)
	match mode:
		"visible_light":
			bg = Color(0.02, 0.02, 0.07)
			amb = Color(0.25, 0.3, 0.42)
		"radio":
			bg = Color(0.04, 0.02, 0.08)
			amb = Color(0.35, 0.22, 0.45)
		"microwave":
			bg = Color(0.06, 0.02, 0.05)
			amb = Color(0.45, 0.25, 0.35)
		"xray", "gamma_ray":
			bg = Color(0.01, 0.02, 0.06)
			amb = Color(0.2, 0.35, 0.55)
		"gravitational_wave":
			bg = Color(0.02, 0.03, 0.08)
			amb = Color(0.25, 0.3, 0.5)
		"neutrino":
			bg = Color(0.02, 0.04, 0.07)
			amb = Color(0.22, 0.38, 0.42)
		"weak_lensing", "dark_matter_inference":
			bg = Color(0.03, 0.03, 0.06)
			amb = Color(0.28, 0.32, 0.48)
		"speculative_now_signal":
			bg = Color(0.06, 0.01, 0.08)
			amb = Color(0.5, 0.2, 0.45)
	world_env.environment.background_color = bg
	world_env.environment.ambient_light_color = amb


func _on_pick_raycast(screen_pos: Vector2) -> void:
	var space := get_world_3d().direct_space_state
	var origin := camera.project_ray_origin(screen_pos)
	var dir := camera.project_ray_normal(screen_pos)
	var to := origin + dir * 3000.0
	var q := PhysicsRayQueryParameters3D.create(origin, to)
	q.collide_with_areas = true
	q.collide_with_bodies = true
	var hit := space.intersect_ray(q)
	if hit.is_empty():
		return
	var col: Variant = hit.get("collider", null)
	if col is Area3D:
		var holder := col.get_parent()
		if holder is Node3D and holder.name != "":
			_on_object_picked(String(holder.name))


func _on_focus_selected() -> void:
	var oid := console.selected_id()
	if oid == "":
		_log("Nothing selected to focus (F).", "#ffaa88")
		return
	var pos := sky.get_object_world_position(oid)
	var rad := sky.get_object_radius(oid)
	camera.focus_on(pos, rad)
	_log("Camera focused on %s." % oid, "#7799cc")


func _on_toggle_labels(on: bool) -> void:
	sky.toggle_labels(on)
	_render_all()


func _on_signal_mode_changed(mode: String) -> void:
	sky.set_signal_mode(mode)
	_apply_environment_for_signal(mode)
	console.render_signal_mode_help(mode, SceneLoaderS.is_deep_field_scene(scene_data))
	_render_all()
	_log("Signal view: %s" % mode, "#aaccff")


func _on_reset_state() -> void:
	state = GameStateS.default_state()
	_last_save_path = _state_path
	_log("Game state reset to defaults (not saved yet — use Save State).", "#ffaa88")
	_render_all()


func _on_export_state() -> void:
	console.show_export_json(JSON.stringify(state, "  "))


# ── Selection / discovery ─────────────────────────────────────────────


func _on_object_picked(object_id: String) -> void:
	console.set_selected(object_id)
	sky.highlight(object_id)
	sky.apply_visual_state(
		state,
		requirements_map,
		console.get_signal_mode(),
		object_id,
		console.is_labels_visible(),
	)
	console.render_detail(state, requirements_map)


func _on_observe_transient(event_id: String) -> void:
	var defs_map := TransientEngineS.by_id(transient_defs)
	if not defs_map.has(event_id):
		_log("Unknown transient: %s" % event_id, "#ff8888")
		return
	var defn: Dictionary = defs_map[event_id]
	var res := TransientEngineS.observe(scene_data, state, defn, tech_tree)
	if not bool(res.get("ok", false)):
		_log(str(res.get("message", "Cannot observe.")), "#ff8888")
		return
	state = res["state"]
	_log(str(res.get("message", "Observed.")), "#aaffaa")
	_post_observe()


func _on_observe() -> void:
	var oid := console.selected_id()
	if oid == "":
		_log("Select an object first.")
		return
	state["turn"] = int(state.get("turn", 0)) + 1
	_observe_one(oid)
	_post_observe()


func _on_survey() -> void:
	state["turn"] = int(state.get("turn", 0)) + 1
	for o in SceneLoaderS.get_objects(scene_data):
		if o is Dictionary:
			_observe_one(o.get("id", ""))
	_post_observe()


func _observe_one(oid: String) -> void:
	var obj := _find_object(oid)
	if obj.is_empty():
		return
	var calc := DiscoveryEngineS.calculate_confidence(
		obj, state, tech_tree, requirements_map, entity_modifiers,
	)
	var conf: float = calc["confidence"]
	if conf < 0.01:
		return
	var prev: Dictionary = state["discoveries"].get(oid, {})
	var is_new := prev.is_empty()
	var is_upgrade := not is_new and conf > float(prev.get("confidence", 0)) + 0.05
	if not is_new and not is_upgrade:
		return
	var pts: int = DiscoveryEngineS.award_points(
		obj, conf, is_new, requirements_map, state, entity_modifiers,
	)
	if not is_new:
		pts = max(1, pts / 2)
	state["research_points"] = int(state.get("research_points", 0)) + pts
	state["discoveries"][oid] = {
		"object_id": oid,
		"object_type": obj.get("type", ""),
		"confidence": conf,
		"detected_signals": calc["detected"],
		"research_points_earned": int(prev.get("research_points_earned", 0)) + pts,
		"first_detected_tier": state.get("active_telescope_tier", "naked_eye"),
	}
	var label := DiscoveryEngineS.confidence_label(conf)
	var name: String = obj.get("name", oid)
	var tag := "[NEW]" if is_new else "[UPGRADED]"
	_log("%s %s (%s) — %s %d%%, +%d RP" % [tag, name, obj.get("type", ""), label, int(round(conf * 100)), pts], "#aaffaa")

	var sresult := SurveyEngineS.update_progress(
		state,
		scene_data,
		oid,
		obj.get("type", ""),
		calc["detected"],
		conf,
		surveys_map,
		entity_modifiers,
	)
	state = sresult["state"]
	var ev: Dictionary = sresult["event"]
	if not ev.is_empty():
		match ev.get("type", ""):
			"completed":
				_log("Survey '%s' complete — +%d RP" % [ev["survey"]["name"], ev["reward"]], "#88ff99")
			"progress":
				_log("  ↳ %s: %d/%d" % [ev["survey"]["name"], ev["done"], ev["goal"]], "#7799cc")


func _post_observe() -> void:
	var mres := MilestoneEngineS.evaluate(state, milestones, entity_modifiers)
	state = mres["state"]
	for m in mres["achieved"]:
		var spec := " [SPECULATIVE]" if m.get("speculative", false) else ""
		var rp: int = int(m.get("_awarded_rp", m.get("reward_research_points", 0)))
		_log("Milestone: %s%s — +%d RP" % [m["name"], spec, rp], "#ffcc66")
	_evaluate_objectives()
	refresh_campaign_unlocks()
	_render_all()


func _evaluate_objectives() -> void:
	var res := ObjectiveEngineS.evaluate(state, scene_data, objective_defs)
	state = res["state"]
	for o in res["completed"]:
		_log(
			"Objective: %s — +%d RP" % [str(o.get("title", "")), int(o.get("reward_research_points", 0))],
			"#88ccff",
		)


func _on_start_survey(sid: String) -> void:
	var r := SurveyEngineS.start_survey(state, sid, surveys_map)
	state = r["state"]
	_log(r["message"])
	_render_all()


func _on_unlock_tier(tid: String) -> void:
	var tm := TechTreeS.tier_map(tech_tree)
	if not tm.has(tid):
		return
	var tier: Dictionary = tm[tid]
	var cost: int = EntityModifiersS.effective_tier_cost(tier, state, entity_modifiers)
	if int(state.get("research_points", 0)) < cost:
		return
	state["research_points"] = int(state["research_points"]) - cost
	if not (tid in state["unlocked_tiers"]):
		state["unlocked_tiers"].append(tid)
	state["active_telescope_tier"] = tid
	var sigs := {}
	for s in state.get("known_signal_types", []):
		sigs[s] = true
	for s in tier.get("signal_types", []):
		sigs[s] = true
	state["known_signal_types"] = sigs.keys()
	_log("Unlocked tier: %s" % tier["name"], "#88ff99")
	refresh_campaign_unlocks()
	_post_observe()


func _on_set_active_tier(tid: String) -> void:
	if tid in state.get("unlocked_tiers", []):
		state["active_telescope_tier"] = tid
		_log("Active telescope: %s" % tid)
		_render_all()


func _on_save() -> void:
	var result := GameStateS.save_state(_state_path, state)
	if result["ok"]:
		_last_save_path = str(result["path"])
		_log("State saved successfully → %s" % _last_save_path, "#88ff99")
	else:
		var fallback := FilePaths.absolute_fallback_state()
		var r2 := GameStateS.save_state(fallback, state)
		if r2["ok"]:
			_state_path = fallback
			_last_save_path = str(r2["path"])
			_log("Primary path not writable; saved to fallback → %s" % _last_save_path, "#ffcc66")
		else:
			_log("Save failed: %s" % result.get("error", "?"), "#ff8888")
	_render_all()


func _on_reload() -> void:
	_load_scene_and_state()
	refresh_campaign_unlocks()
	_render_all()
	_apply_camera_framing()
	_log("Scene + state reloaded from disk.", "#7799cc")


func _find_object(oid: String) -> Dictionary:
	for o in SceneLoaderS.get_objects(scene_data):
		if o is Dictionary and o.get("id", "") == oid:
			return o
	return {}


func _log(text: String, color: String = "#bbcce0") -> void:
	if console != null:
		console.add_log(text, color)
	else:
		print(text)
