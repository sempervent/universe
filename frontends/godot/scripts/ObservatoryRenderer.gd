class_name ObservatoryRenderer
extends Node3D
## Observatory / telescope view — objects as sky targets on a celestial dome.
## The observer is fixed at the origin; this is not a free-flying spatial map.

signal object_picked(object_id: String)

const TYPE_COLORS := SkyRenderer.TYPE_COLORS

var signal_mode: String = "visible_light"

var _id_to_entry: Dictionary = {}
var _labels_visible: bool = true
var _selected_id: String = ""
var _scene_ref: Dictionary = {}
var _requirements_map: Dictionary = {}
var _tech_tree: Array = []
var _state_ref: Dictionary = {}
var _is_deep_field: bool = false
var _camera_aim_dir: Vector3 = Vector3(0, 0.4, 1).normalized()
var _camera_fit_angle: float = 0.35
var _pulse_materials: Array[StandardMaterial3D] = []
var _cmb_dome: MeshInstance3D = null
var _filament_segments: Array[Dictionary] = []
var _sky_dome: MeshInstance3D = null
var _starfield_root: Node3D = null
var _star_meshes: Array[MeshInstance3D] = []


func _process(_delta: float) -> void:
	var t: float = Time.get_ticks_msec() * 0.003
	for m in _pulse_materials:
		if m != null:
			m.emission_energy_multiplier = 0.45 + 0.55 * sin(t)


func is_deep_field_scene() -> bool:
	return _is_deep_field


func get_default_camera_target() -> Vector3:
	return _camera_aim_dir * SkyProjection.DOME_RADIUS * 0.5


func get_default_camera_fit_radius() -> float:
	return _camera_fit_angle * SkyProjection.DOME_RADIUS


func set_signal_mode(mode: String) -> void:
	signal_mode = mode


func toggle_labels(on: bool) -> void:
	_labels_visible = on
	for e in _id_to_entry.values():
		var lbl: Label3D = e.get("label", null)
		if lbl:
			lbl.visible = on


func highlight(selected_id: String) -> void:
	_selected_id = selected_id
	for oid in _id_to_entry.keys():
		var e: Dictionary = _id_to_entry[oid]
		var holder: Node3D = e.get("holder", null)
		if holder:
			holder.scale = Vector3.ONE * (1.35 if oid == selected_id else 1.0)


func get_object_world_position(object_id: String) -> Vector3:
	var e: Dictionary = _id_to_entry.get(object_id, {})
	var h: Node3D = e.get("holder", null)
	if h:
		return h.global_position
	return _camera_aim_dir * SkyProjection.DOME_RADIUS


func get_object_radius(object_id: String) -> float:
	var e: Dictionary = _id_to_entry.get(object_id, {})
	return float(e.get("size", 1.0))


func get_visibility_reason(object_id: String) -> String:
	var e: Dictionary = _id_to_entry.get(object_id, {})
	return str(e.get("visibility_reason", ""))


func render_scene(
	scene: Dictionary,
	state: Dictionary,
	requirements: Dictionary,
	tree: Array = [],
) -> void:
	for child in get_children():
		child.queue_free()
	_id_to_entry.clear()
	_pulse_materials.clear()
	_filament_segments.clear()
	_cmb_dome = null
	_scene_ref = scene
	_state_ref = state
	_requirements_map = requirements
	_tech_tree = tree
	_is_deep_field = SceneLoader.is_deep_field_scene(scene)

	_build_sky_backdrop()
	_build_horizon()
	_build_starfield()

	for obj in SceneLoader.get_objects(scene):
		if not (obj is Dictionary):
			continue
		var otype: String = str(obj.get("type", ""))
		if otype == "cmb_background":
			continue
		if otype == "observatory":
			continue
		_place_sky_target(obj as Dictionary)

	if _is_deep_field:
		_build_deep_field_overlays(scene)
		_build_cmb_dome()

	_update_camera_hints(scene)
	_apply_sky_time_of_day(state)
	apply_visual_state(state, requirements, signal_mode, _selected_id, _labels_visible, tree)


func _build_sky_backdrop() -> void:
	var dome := MeshInstance3D.new()
	dome.name = "SkyDome"
	var sp := SphereMesh.new()
	sp.radius = SkyProjection.DOME_RADIUS * 1.02
	sp.height = sp.radius * 2.0
	dome.mesh = sp
	var mat := StandardMaterial3D.new()
	mat.cull_mode = BaseMaterial3D.CULL_FRONT
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if _is_deep_field:
		mat.albedo_color = Color(0.01, 0.015, 0.04)
	else:
		mat.albedo_color = Color(0.01, 0.02, 0.06)
	dome.material_override = mat
	add_child(dome)
	_sky_dome = dome


func _build_starfield() -> void:
	_starfield_root = Node3D.new()
	_starfield_root.name = "Starfield"
	add_child(_starfield_root)
	_star_meshes.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(_scene_ref.get("id", "sky"))
	for i in range(220):
		var az: float = rng.randf() * TAU
		var el: float = 0.12 + rng.randf() * 0.75
		var pos: Vector3 = SkyProjection.dome_position(az, el)
		var star := MeshInstance3D.new()
		var sp := SphereMesh.new()
		var sz: float = 0.12 + rng.randf() * 0.22
		sp.radius = sz
		sp.height = sz * 2.0
		star.mesh = sp
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(0.85, 0.9, 1.0, 0.7)
		mat.emission_enabled = true
		mat.emission = Color(0.9, 0.95, 1.0)
		mat.emission_energy_multiplier = 0.4 + rng.randf() * 0.6
		star.material_override = mat
		star.position = pos
		_starfield_root.add_child(star)
		_star_meshes.append(star)


func _apply_sky_time_of_day(state: Dictionary) -> void:
	var bright: float = ObservatoryTime.sky_brightness(state)
	if _sky_dome and _sky_dome.material_override is StandardMaterial3D:
		var mat: StandardMaterial3D = _sky_dome.material_override
		if _is_deep_field:
			mat.albedo_color = Color(0.01, 0.015, 0.04).lerp(Color(0.08, 0.1, 0.18), bright * 0.35)
		else:
			mat.albedo_color = Color(0.01, 0.02, 0.06).lerp(Color(0.45, 0.55, 0.75), bright)
	if _starfield_root:
		_starfield_root.rotation.y = ObservatoryTime.get_fraction(state) * TAU
	var night: float = 1.0 - bright
	for star in _star_meshes:
		star.visible = night > 0.45
		if star.material_override is StandardMaterial3D:
			var sm: StandardMaterial3D = star.material_override
			sm.albedo_color.a = clampf(night * 0.85, 0.0, 0.9)


func _build_horizon() -> void:
	var ring := MeshInstance3D.new()
	ring.name = "Horizon"
	var tor := TorusMesh.new()
	tor.inner_radius = SkyProjection.DOME_RADIUS * 0.92
	tor.outer_radius = SkyProjection.DOME_RADIUS * 0.94
	tor.rings = 48
	ring.mesh = tor
	ring.rotation_degrees = Vector3(90, 0, 0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.04, 0.05, 0.08, 0.35)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ring.material_override = mat
	add_child(ring)


func _place_sky_target(obj: Dictionary) -> void:
	var oid: String = str(obj.get("id", ""))
	var otype: String = str(obj.get("type", ""))
	var angles: Vector2 = SkyProjection.object_to_sky_angles_timed(obj, _scene_ref, _state_ref)
	var pos: Vector3 = SkyProjection.dome_position(angles.x, angles.y)
	var dir: Vector3 = pos.normalized()

	var holder := Node3D.new()
	holder.name = oid
	holder.position = pos
	holder.look_at(pos + dir, Vector3.UP)
	add_child(holder)

	var size: float = SkyProjection.angular_size_on_dome(obj, _scene_ref)
	if oid == "sun":
		size = minf(size, 9.0)
	elif oid.begins_with("moon-") and oid != "moon":
		size = minf(size, 1.2)
	elif otype in ["asteroid", "comet"]:
		size = minf(size, 0.75)
	var base: Color = TYPE_COLORS.get(otype, Color(0.7, 0.75, 0.85)) as Color
	var bright: float = SkyProjection.apparent_brightness(obj)

	var mesh := MeshInstance3D.new()
	mesh.name = "Target"
	var sphere := SphereMesh.new()
	sphere.radius = size
	sphere.height = size * 2.0
	mesh.mesh = sphere
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(base.r, base.g, base.b, clampf(0.35 + bright * 0.55, 0.2, 1.0))
	mat.emission_enabled = otype in ["star", "quasar", "magnetar"] or bright > 0.7
	mat.emission = base
	mat.emission_energy_multiplier = 0.4 + bright * 1.2
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if otype == "lyman_alpha_blob":
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.albedo_color.a = 0.35
	elif otype == "black_hole":
		mat.albedo_color = Color(0.35, 0.15, 0.55, 0.5)
		mat.emission_enabled = true
		mat.emission = Color(0.5, 0.2, 0.8)
	elif otype == "quasar":
		mat.emission_energy_multiplier = 1.4
	mesh.material_override = mat
	holder.add_child(mesh)

	var area := Area3D.new()
	area.name = "PickArea"
	var shape := CollisionShape3D.new()
	var ss := SphereShape3D.new()
	ss.radius = maxf(size * 1.4, 0.8)
	shape.shape = ss
	area.add_child(shape)
	holder.add_child(area)

	var label := Label3D.new()
	label.name = "Label"
	label.text = str(obj.get("name", oid))
	label.font_size = 22
	label.modulate = Color(0.85, 0.92, 1, 0.85)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.position = dir * (size + 1.2)
	label.visible = false
	holder.add_child(label)

	_id_to_entry[oid] = {
		"holder": holder,
		"mesh": mesh,
		"mat": mat,
		"label": label,
		"area": area,
		"base_color": base,
		"otype": otype,
		"size": size,
		"obj": obj,
		"dir": dir,
		"angles": angles,
	}


func _build_deep_field_overlays(scene: Dictionary) -> void:
	var root := Node3D.new()
	root.name = "DeepFieldOverlays"
	add_child(root)
	for fil in scene.get("filaments", []):
		if not (fil is Dictionary):
			continue
		var pts: Array = fil.get("control_points_mpc", [])
		if pts.size() < 2:
			continue
		var a0: Vector3 = _mpc_to_dir(pts[0] as Dictionary)
		var a1: Vector3 = _mpc_to_dir(pts[pts.size() - 1] as Dictionary)
		_add_filament_arc(root, a0, a1)


func _mpc_to_dir(d: Dictionary) -> Vector3:
	var fake := {"position_mpc": d}
	return SkyProjection.direction_from_angles(
		SkyProjection.object_to_sky_angles(fake, _scene_ref).x,
		SkyProjection.object_to_sky_angles(fake, _scene_ref).y,
	)


func _add_filament_arc(parent: Node3D, dir_a: Vector3, dir_b: Vector3) -> void:
	var seg := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.08
	cyl.bottom_radius = 0.08
	var mid: Vector3 = (dir_a + dir_b).normalized() * SkyProjection.DOME_RADIUS
	var h: float = (dir_a * SkyProjection.DOME_RADIUS - dir_b * SkyProjection.DOME_RADIUS).length()
	cyl.height = maxf(h, 2.0)
	seg.mesh = cyl
	seg.position = mid
	seg.look_at(mid + mid.normalized(), Vector3.UP)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.45, 0.35, 0.75, 0.25)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	seg.material_override = mat
	parent.add_child(seg)
	_filament_segments.append({"mat": mat, "mesh": seg})


func _build_cmb_dome() -> void:
	var mesh := MeshInstance3D.new()
	var sp := SphereMesh.new()
	sp.radius = SkyProjection.DOME_RADIUS * 0.98
	sp.height = sp.radius * 2.0
	mesh.mesh = sp
	var mat := StandardMaterial3D.new()
	mat.cull_mode = BaseMaterial3D.CULL_FRONT
	mat.albedo_color = Color(0.15, 0.05, 0.05, 0.08)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mesh.material_override = mat
	add_child(mesh)
	_cmb_dome = mesh


func _update_camera_hints(scene: Dictionary) -> void:
	var meta: Dictionary = scene.get("metadata", {}) as Dictionary
	var aim_id: String = str(meta.get("recommended_camera_target_object_id", ""))
	if aim_id != "" and _id_to_entry.has(aim_id):
		var e: Dictionary = _id_to_entry[aim_id]
		_camera_aim_dir = e.get("dir", Vector3.UP) as Vector3
	else:
		for pref in ["sun", "moon", "lyman_alpha_blob", "quasar"]:
			for oid in _id_to_entry.keys():
				var e: Dictionary = _id_to_entry[oid]
				if str(e.get("otype", "")) == pref or oid == pref:
					_camera_aim_dir = e.get("dir", Vector3.UP) as Vector3
					break
			if _camera_aim_dir != Vector3.UP:
				break
	_camera_fit_angle = 0.28


func apply_visual_state(
	state: Dictionary,
	requirements: Dictionary,
	mode: String,
	selected_id: String,
	labels_on: bool,
	tree: Array = [],
) -> void:
	_requirements_map = requirements
	_state_ref = state
	if not tree.is_empty():
		_tech_tree = tree
	signal_mode = mode
	_selected_id = selected_id
	_labels_visible = labels_on
	_pulse_materials.clear()

	for oid in _id_to_entry.keys():
		var e: Dictionary = _id_to_entry[oid]
		var mat: StandardMaterial3D = e.get("mat", null)
		var label: Label3D = e.get("label", null)
		var holder: Node3D = e.get("holder", null)
		var area: Area3D = e.get("area", null)
		var obj: Dictionary = e.get("obj", {}) as Dictionary
		var otype: String = str(e.get("otype", ""))
		var base: Color = e.get("base_color", Color.WHITE) as Color
		var disc: Dictionary = state.get("discoveries", {}).get(oid, {}) as Dictionary
		var conf: float = float(disc.get("confidence", 0.0))
		if holder:
			var pos: Vector3 = SkyProjection.project_target_at_time(obj, _scene_ref, state)
			holder.position = pos
			var dir: Vector3 = pos.normalized()
			holder.look_at(pos + dir, Vector3.UP)
		var angles: Vector2 = SkyProjection.object_to_sky_angles_timed(obj, _scene_ref, state)
		e["angles"] = angles
		if not SkyProjection.is_above_horizon(angles) and otype not in [
			"quasar", "magnetar", "black_hole", "lyman_alpha_blob", "cosmic_web_node"
		]:
			if mode in ["visible_light", "infrared", "ultraviolet"]:
				holder.visible = false
				if area:
					area.input_ray_pickable = false
				continue
		var vis_info: Dictionary = InstrumentVisibility.evaluate(
			obj, _scene_ref, state, _tech_tree, requirements, mode,
		)
		var vis: String = str(vis_info.get("visibility", InstrumentVisibility.FULL))
		var bright: float = ObservatoryTime.sky_brightness(state)
		if bright > 0.4 and mode == "visible_light" and otype in ["galaxy", "quasar"]:
			vis = InstrumentVisibility.DIM if vis == InstrumentVisibility.FULL else vis
		var emphasis: float = _mode_emphasis(otype, mode, requirements.get(otype, {}) as Dictionary)
		if vis == InstrumentVisibility.HIDDEN:
			emphasis *= 0.05
		elif vis == InstrumentVisibility.DIM:
			emphasis *= 0.35
		var band: String = _discovery_band(conf)
		if holder:
			holder.visible = vis != InstrumentVisibility.HIDDEN or oid == selected_id
		if area:
			area.monitorable = vis != InstrumentVisibility.HIDDEN
			area.input_ray_pickable = bool(vis_info.get("pickable", true))
		if mat:
			_apply_discovery_material(mat, base, otype, band, emphasis)
			if mode == "speculative_now_signal" and otype in ["quasar", "magnetar", "black_hole"]:
				mat.emission = Color(0.9, 0.4, 1.0)
				mat.emission_enabled = true
		if band == "anomaly" and mat and mat.emission_enabled:
			_pulse_materials.append(mat)
		if otype == "magnetar" and mode in ["xray", "gamma_ray", "radio"]:
			if mat:
				_pulse_materials.append(mat)
		var show_lbl: bool = labels_on and _should_show_label(oid, otype, conf, selected_id)
		if label:
			label.visible = show_lbl and vis != InstrumentVisibility.HIDDEN
			label.text = _label_text(obj, conf)
			if oid == selected_id:
				label.modulate = Color(1, 1, 0.88, 1.0)
			else:
				label.modulate = Color(0.82, 0.9, 1, 0.75)
		e["visibility"] = vis
		e["visibility_reason"] = str(vis_info.get("reason", ""))

	if _cmb_dome and _cmb_dome.material_override is StandardMaterial3D:
		var cmat: StandardMaterial3D = _cmb_dome.material_override
		cmat.albedo_color.a = 0.48 if mode == "microwave" else 0.06
		_cmb_dome.visible = mode == "microwave" or TechTree.max_tier_index(_tech_tree, state) >= 4

	for seg in _filament_segments:
		var fmat: StandardMaterial3D = seg.get("mat", null)
		var fmesh: MeshInstance3D = seg.get("mesh", null)
		var show_fil: bool = mode in ["weak_lensing", "dark_matter_inference"]
		if fmat:
			fmat.albedo_color.a = 0.58 if show_fil else 0.08
		if fmesh:
			fmesh.visible = show_fil or TechTree.max_tier_index(_tech_tree, state) >= 5

	_apply_sky_time_of_day(state)
	highlight(selected_id)


func _mode_emphasis(otype: String, mode: String, req: Dictionary) -> float:
	if req.is_empty():
		return 0.35
	var required: Array = req.get("required_signal_types", [])
	var optional: Array = req.get("optional_signal_types", [])
	if mode in required:
		return 1.0
	if mode in optional:
		return 0.65
	if mode == "visible_light":
		return 0.45
	return 0.12


func _discovery_band(conf: float) -> String:
	if conf < 0.25:
		return "undiscovered"
	if conf < 0.50:
		return "anomaly"
	if conf < 0.75:
		return "candidate"
	if conf < 0.95:
		return "confirmed"
	return "characterized"


func _apply_discovery_material(
	mat: StandardMaterial3D,
	base: Color,
	otype: String,
	band: String,
	emphasis: float,
) -> void:
	var dim := 0.15 + emphasis * 0.85
	match band:
		"undiscovered":
			mat.albedo_color = Color(base.r * 0.2, base.g * 0.2, base.b * 0.25, 0.25 * dim)
			mat.emission_enabled = false
		"anomaly":
			mat.albedo_color = Color(base.r * 0.5, base.g * 0.5, base.b * 0.6, 0.45 * dim)
			mat.emission_enabled = true
			mat.emission = base
			mat.emission_energy_multiplier = 0.8
		_:
			mat.albedo_color = Color(base.r * dim, base.g * dim, base.b * dim, clampf(0.5 + emphasis * 0.4, 0.25, 1.0))
			mat.emission_enabled = band in ["confirmed", "characterized"]
			mat.emission = base
			mat.emission_energy_multiplier = 0.35 + emphasis * 0.5


func _should_show_label(oid: String, otype: String, conf: float, selected_id: String) -> bool:
	if oid == selected_id:
		return true
	if conf >= 0.5:
		return true
	if otype in ["star", "moon", "planet", "quasar", "lyman_alpha_blob"]:
		return conf >= 0.25
	return false


func _label_text(obj: Dictionary, conf: float) -> String:
	var name: String = str(obj.get("name", ""))
	if conf < 0.25:
		return "%s (?)" % name
	if conf < 0.50:
		return "%s · anomaly" % name
	if conf < 0.75:
		return "%s · candidate" % name
	return name
