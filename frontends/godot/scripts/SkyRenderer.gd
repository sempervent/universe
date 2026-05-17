class_name SkyRenderer
extends Node3D
# SkyRenderer — 3D scene representation with pickable Area3D colliders,
# discovery-based materials, signal visualization modes, and Label3D text.
#
# Picking: each object holder has an Area3D + SphereShape3D; Main raycasts
# and reads holder.name as object_id.

signal object_picked(object_id: String)
signal object_hovered(object_id: String)

const TYPE_COLORS := {
	"star": Color(1, 1, 0.6),
	"planet": Color(0.55, 0.7, 1),
	"moon": Color(0.85, 0.85, 0.85),
	"asteroid": Color(0.6, 0.6, 0.55),
	"comet": Color(0.6, 0.85, 1),
	"observatory": Color(0.3, 0.55, 1),
	"galaxy": Color(0.45, 0.55, 1),
	"lyman_alpha_blob": Color(0.2, 1, 0.7, 0.45),
	"quasar": Color(1, 0.95, 0.85),
	"black_hole": Color(0.05, 0.05, 0.07),
	"magnetar": Color(1, 0.3, 1),
	"cosmic_web_node": Color(1, 0.65, 0.25),
	"cosmic_web_filament": Color(0.6, 0.4, 0.7, 0.5),
	"void": Color(0.1, 0.1, 0.18, 0.35),
	"cmb_background": Color(0.25, 0.08, 0.08, 0.4),
}

const TYPE_SIZES := {
	"star": 1.4,
	"planet": 0.6,
	"moon": 0.25,
	"asteroid": 0.18,
	"comet": 0.22,
	"observatory": 0.4,
	"galaxy": 0.3,
	"lyman_alpha_blob": 2.5,
	"quasar": 0.7,
	"black_hole": 0.6,
	"magnetar": 0.35,
	"cosmic_web_node": 0.5,
	"void": 4.0,
	"cmb_background": 0.0,
}

## Current visualization signal (not necessarily unlocked — "what if" view).
var signal_mode: String = "visible_light"

var _id_to_entry: Dictionary = {}  # id -> {holder, mesh, mat, label, area, base_color, otype, size, obj, jet_mats, ...}
var _labels_visible := true
var _selected_id: String = ""
var _hover_id: String = ""
var _pulse_materials: Array[StandardMaterial3D] = []
var _scene_ref: Dictionary = {}
var _requirements_map: Dictionary = {}
var _cmb_shell: MeshInstance3D = null

var _is_deep_field := false
var _df_centroid := Vector3.ZERO
var _df_scale := 1.0
var _camera_aim := Vector3.ZERO
var _camera_fit_radius := 14.0

var _filament_segments: Array[Dictionary] = []
var _node_entries: Array[Dictionary] = []


func _process(_delta: float) -> void:
	var t := Time.get_ticks_msec() * 0.003
	for m in _pulse_materials:
		if m != null:
			m.emission_energy_multiplier = 0.45 + 0.55 * sin(t)


func is_deep_field_scene() -> bool:
	return _is_deep_field


func get_default_camera_target() -> Vector3:
	return _camera_aim


func get_default_camera_fit_radius() -> float:
	return _camera_fit_radius


func render_scene(scene: Dictionary, state: Dictionary, requirements: Dictionary) -> void:
	for child in get_children():
		child.queue_free()
	_id_to_entry.clear()
	_pulse_materials.clear()
	_filament_segments.clear()
	_node_entries.clear()
	_cmb_shell = null
	_scene_ref = scene
	_requirements_map = requirements

	_is_deep_field = SceneLoader.is_deep_field_scene(scene)
	_df_centroid = _compute_df_centroid(scene)
	var size_mpc := float(scene.get("size_mpc", 50.0))
	_df_scale = 32.0 / maxf(size_mpc, 1e-6)

	var solar := SceneLoader.is_solar_system_scene(scene)
	var positions := _compute_positions(scene, solar)

	_update_camera_hints(scene, positions)

	for obj in SceneLoader.get_objects(scene):
		if obj is Dictionary:
			var otype: String = obj.get("type", "")
			if otype == "cmb_background":
				continue
			_render_object(obj, positions, solar)

	if not solar:
		_render_filaments(scene, positions)
		_render_deep_field_nodes(scene, positions)
		_render_cmb_shell()

	apply_visual_state(state, requirements, signal_mode, _selected_id, _labels_visible)


func _compute_df_centroid(scene: Dictionary) -> Vector3:
	var meta: Dictionary = scene.get("metadata", {})
	var feat: Variant = meta.get("featured_object_ids", [])
	if feat is Array and feat.size() > 0:
		var acc := Vector3.ZERO
		var n := 0
		for oid in feat:
			for obj in SceneLoader.get_objects(scene):
				if obj is Dictionary and str(obj.get("id", "")) == str(oid):
					acc += _vec_mpc(obj.get("position_mpc", {}))
					n += 1
		if n > 0:
			return acc / float(n)
	var acc2 := Vector3.ZERO
	var n2 := 0
	for obj in SceneLoader.get_objects(scene):
		if not (obj is Dictionary):
			continue
		var t := str(obj.get("type", ""))
		if t in ["lyman_alpha_blob", "quasar", "black_hole"]:
			acc2 += _vec_mpc(obj.get("position_mpc", {}))
			n2 += 1
	if n2 > 0:
		return acc2 / float(n2)
	return Vector3.ZERO


func _vec_mpc(d: Variant) -> Vector3:
	if not (d is Dictionary):
		return Vector3.ZERO
	var dd: Dictionary = d
	return Vector3(float(dd.get("x", 0.0)), float(dd.get("y", 0.0)), float(dd.get("z", 0.0)))


func _to_render_space(mpc: Vector3, solar: bool) -> Vector3:
	if solar:
		return mpc
	return (mpc - _df_centroid) * _df_scale


func _update_camera_hints(scene: Dictionary, positions: Dictionary) -> void:
	var meta: Dictionary = scene.get("metadata", {})
	var aim_id := str(meta.get("recommended_camera_target_object_id", ""))
	if aim_id == "" or not positions.has(aim_id):
		# Prefer LAB, then quasar, then first object with position.
		for pref in ["lyman_alpha_blob", "quasar", "galaxy"]:
			for obj in SceneLoader.get_objects(scene):
				if obj is Dictionary and str(obj.get("type", "")) == pref:
					var pid: String = str(obj.get("id", ""))
					if positions.has(pid):
						aim_id = pid
						break
			if aim_id != "" and positions.has(aim_id):
				break
	if aim_id == "":
		for k in positions.keys():
			aim_id = str(k)
			break
	_camera_aim = positions.get(aim_id, Vector3.ZERO)
	var max_r := 1.0
	for v in positions.values():
		if v is Vector3:
			max_r = maxf(max_r, (v as Vector3).distance_to(_camera_aim))
	_camera_fit_radius = maxf(max_r * 1.15, 4.0)


func _compute_positions(scene: Dictionary, solar: bool) -> Dictionary:
	var out: Dictionary = {}
	for obj in SceneLoader.get_objects(scene):
		if not (obj is Dictionary):
			continue
		var pos: Dictionary = obj.get("position_mpc", {})
		var px := float(pos.get("x", 0.0))
		var py := float(pos.get("y", 0.0))
		var pz := float(pos.get("z", 0.0))
		var v := Vector3(px, py, pz)
		if solar:
			var au_to_mpc := 4.848e-12
			var au_x := px / au_to_mpc
			var au_z := pz / au_to_mpc
			out[obj["id"]] = _log_compress(Vector3(au_x, py, au_z))
		else:
			out[obj["id"]] = _to_render_space(v, solar)
	return out


func _log_compress(v: Vector3) -> Vector3:
	var r := Vector3(v.x, 0, v.z).length()
	if r < 1e-6:
		return Vector3(0, 0, 0)
	var compressed := log(1.0 + r) * 1.5
	var scale := compressed / r
	return Vector3(v.x * scale, 0, v.z * scale)


func _base_size_for(otype: String, solar: bool) -> float:
	var s := float(TYPE_SIZES.get(otype, 0.3))
	if _is_deep_field and otype == "galaxy":
		s *= 0.52
	if _is_deep_field and otype == "void":
		s *= 1.15
	return s


func _render_object(obj: Dictionary, positions: Dictionary, solar: bool) -> void:
	var oid: String = obj.get("id", "")
	var otype: String = obj.get("type", "galaxy")
	var pos: Vector3 = positions.get(oid, Vector3.ZERO)
	var base: Color = TYPE_COLORS.get(otype, Color(0.6, 0.6, 0.6))
	var size: float = _base_size_for(otype, solar)

	var holder := Node3D.new()
	holder.name = oid
	holder.position = pos
	add_child(holder)

	var mesh: MeshInstance3D = null
	var mat: StandardMaterial3D = null
	var jet_mats: Array[StandardMaterial3D] = []

	if otype == "lyman_alpha_blob":
		_render_lab_visual(holder, size, base)
		mesh = holder.get_node_or_null("LABShell0") as MeshInstance3D
		mat = mesh.material_override as StandardMaterial3D if mesh else null
	elif otype == "black_hole":
		_render_black_hole_visual(holder, size, base)
		mesh = holder.get_node_or_null("Mesh") as MeshInstance3D
		mat = mesh.material_override as StandardMaterial3D if mesh else null
	elif otype == "magnetar":
		mesh = _render_magnetar_visual(holder, size, base)
		mat = mesh.material_override as StandardMaterial3D
	else:
		mesh = MeshInstance3D.new()
		mesh.name = "Mesh"
		var sphere := SphereMesh.new()
		sphere.radius = size
		sphere.height = size * 2.0
		sphere.radial_segments = 16
		sphere.rings = 8
		mesh.mesh = sphere

		mat = StandardMaterial3D.new()
		mat.albedo_color = base
		if otype in ["star", "quasar", "magnetar", "lyman_alpha_blob"]:
			mat.emission_enabled = true
			mat.emission = base
			mat.emission_energy_multiplier = 1.2
		if otype == "void":
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		if otype == "black_hole":
			mat.metallic = 0.9
			mat.roughness = 0.05
		mesh.material_override = mat
		holder.add_child(mesh)

	if otype == "quasar":
		jet_mats = _add_quasar_jets(holder, base, oid)

	var label := Label3D.new()
	label.name = "Label"
	label.text = obj.get("name", oid)
	label.position = Vector3(0, size + 0.45, 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.font_size = 18
	label.modulate = Color(0.85, 0.92, 1, 0.9)
	label.visible = _labels_visible
	holder.add_child(label)

	var area := Area3D.new()
	area.name = "PickArea"
	area.collision_layer = 1
	area.collision_mask = 0
	var shape := CollisionShape3D.new()
	var ss := SphereShape3D.new()
	ss.radius = size * (1.55 if otype == "lyman_alpha_blob" else 1.35)
	shape.shape = ss
	area.add_child(shape)
	holder.add_child(area)
	area.input_event.connect(_on_area_input.bind(oid))
	area.mouse_entered.connect(func(): _hover_id = oid; object_hovered.emit(oid))
	area.mouse_exited.connect(func(): if _hover_id == oid: _hover_id = ""; object_hovered.emit(""))

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
		"jet_mats": jet_mats,
	}


func _render_lab_visual(holder: Node3D, size: float, base: Color) -> void:
	var radii := [size * 1.05, size * 0.82, size * 0.62]
	var alphas := [0.14, 0.1, 0.07]
	var i := 0
	for r in radii:
		var shell := MeshInstance3D.new()
		shell.name = "LABShell%d" % i
		var sp := SphereMesh.new()
		sp.radius = r
		sp.height = r * 2.0
		sp.radial_segments = 20
		sp.rings = 10
		shell.mesh = sp
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(base.r, base.g, base.b, alphas[i])
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.emission_enabled = true
		m.emission = Color(base.r, base.g, base.b, 1.0)
		m.emission_energy_multiplier = 0.55 + float(i) * 0.12
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		shell.material_override = m
		holder.add_child(shell)
		_pulse_materials.append(m)
		i += 1


func _render_black_hole_visual(holder: Node3D, size: float, base: Color) -> void:
	var core := MeshInstance3D.new()
	core.name = "Mesh"
	var sp := SphereMesh.new()
	var cr := size * 0.38
	sp.radius = cr
	sp.height = cr * 2.0
	sp.radial_segments = 18
	sp.rings = 9
	core.mesh = sp
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.02, 0.02, 0.03, 1.0)
	mat.metallic = 1.0
	mat.roughness = 0.12
	mat.emission_enabled = false
	core.material_override = mat
	holder.add_child(core)

	var ring := MeshInstance3D.new()
	ring.name = "AccretionRing"
	var tor := TorusMesh.new()
	tor.inner_radius = cr * 1.35
	tor.outer_radius = cr * 1.75
	tor.rings = 12
	tor.radial_segments = 24
	ring.mesh = tor
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(1.0, 0.55, 0.2, 0.85)
	rmat.emission_enabled = true
	rmat.emission = Color(1.0, 0.45, 0.15)
	rmat.emission_energy_multiplier = 0.9
	rmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring.material_override = rmat
	ring.rotation_degrees = Vector3(72, 12, 0)
	holder.add_child(ring)


func _render_magnetar_visual(holder: Node3D, size: float, base: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	mesh.name = "Mesh"
	var sphere := SphereMesh.new()
	sphere.radius = size * 0.9
	sphere.height = sphere.radius * 2.0
	sphere.radial_segments = 14
	sphere.rings = 7
	mesh.mesh = sphere
	var mat := StandardMaterial3D.new()
	mat.albedo_color = base
	mat.emission_enabled = true
	mat.emission = base
	mat.emission_energy_multiplier = 1.35
	mesh.material_override = mat
	holder.add_child(mesh)
	_pulse_materials.append(mat)

	for ang in [0.0, 120.0]:
		var tor := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = size * 1.05
		tm.outer_radius = size * 1.18
		tm.rings = 6
		tm.radial_segments = 16
		tor.mesh = tm
		var tmat := StandardMaterial3D.new()
		tmat.albedo_color = Color(base.r, base.g, base.b, 0.22)
		tmat.emission_enabled = true
		tmat.emission = base
		tmat.emission_energy_multiplier = 0.35
		tmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		tmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		tor.material_override = tmat
		tor.rotation_degrees = Vector3(55 + ang, 20, 10)
		holder.add_child(tor)
	return mesh


func _jet_direction_for(oid: String) -> Vector3:
	var h: int = hash(oid)
	var v := Vector3(
		float(h % 97) / 48.5 - 1.0,
		float((h / 97) % 97) / 48.5 - 1.0,
		float((h / (97 * 97)) % 97) / 48.5 - 1.0,
	)
	if v.length() < 1e-3:
		v = Vector3(0.15, 1.0, 0.08)
	return v.normalized()


func _basis_y_along(d: Vector3) -> Basis:
	var y := d.normalized()
	var x := Vector3.UP.cross(y)
	if x.length() < 0.02:
		x = Vector3.RIGHT.cross(y)
	x = x.normalized()
	var z := x.cross(y).normalized()
	return Basis(x, y, z)


func _add_quasar_jets(parent: Node3D, color: Color, oid: String) -> Array[StandardMaterial3D]:
	var dir := _jet_direction_for(oid)
	var out: Array[StandardMaterial3D] = []
	for sign in [1.0, -1.0]:
		var jet := MeshInstance3D.new()
		jet.name = "QuasarJet"
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.024
		cyl.bottom_radius = 0.06
		cyl.height = 1.75
		jet.mesh = cyl
		var d := dir * sign
		jet.transform = Transform3D(_basis_y_along(d), d * 0.92)
		var jm := StandardMaterial3D.new()
		jm.albedo_color = color
		jm.emission_enabled = true
		jm.emission = color
		jm.emission_energy_multiplier = 2.0
		jet.material_override = jm
		parent.add_child(jet)
		out.append(jm)
	return out


func _on_area_input(oid: String, _camera: Node, event: InputEvent, _event_position: Vector3, _normal: Vector3, _shape_idx: int) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed and not mb.shift_pressed:
			object_picked.emit(oid)


func _filament_path_mpc(fil: Dictionary, node_mpc: Dictionary) -> Array[Vector3]:
	var pts: Array[Vector3] = []
	var sid: String = str(fil.get("start_node_id", ""))
	var eid: String = str(fil.get("end_node_id", ""))
	if not node_mpc.has(sid) or not node_mpc.has(eid):
		return pts
	pts.append(node_mpc[sid])
	var cpts: Variant = fil.get("control_points_mpc", [])
	if cpts is Array:
		for c in cpts:
			if c is Dictionary:
				pts.append(_vec_mpc(c))
	pts.append(node_mpc[eid])
	return pts


func _render_filaments(scene: Dictionary, positions: Dictionary) -> void:
	var solar := SceneLoader.is_solar_system_scene(scene)
	var node_mpc: Dictionary = {}
	for n in SceneLoader.get_nodes(scene):
		if n is Dictionary and n.has("position_mpc"):
			var nid: String = str(n.get("id", ""))
			node_mpc[nid] = _vec_mpc(n.get("position_mpc", {}))

	var root := Node3D.new()
	root.name = "FilamentsRoot"
	add_child(root)

	for fil in SceneLoader.get_filaments(scene):
		if not (fil is Dictionary):
			continue
		var path_mpc: Array = _filament_path_mpc(fil, node_mpc)
		if path_mpc.size() < 2:
			continue
		var path_render: Array[Vector3] = []
		for p in path_mpc:
			path_render.append(_to_render_space(p as Vector3, solar))
		_add_filament_polyline(root, path_render)


func _add_filament_polyline(parent: Node3D, points: Array[Vector3]) -> void:
	var base_col: Color = TYPE_COLORS["cosmic_web_filament"]
	for i in range(points.size() - 1):
		var a: Vector3 = points[i]
		var b: Vector3 = points[i + 1]
		var seg := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		var h: float = a.distance_to(b)
		if h < 1e-5:
			continue
		cyl.height = h
		var rad := 0.045
		cyl.top_radius = rad
		cyl.bottom_radius = rad
		seg.mesh = cyl
		var d := (b - a) / h
		seg.transform = Transform3D(_basis_y_along(d), (a + b) * 0.5)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(base_col.r, base_col.g, base_col.b, 0.55)
		mat.emission_enabled = true
		mat.emission = Color(base_col.r, base_col.g, base_col.b)
		mat.emission_energy_multiplier = 0.35
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		seg.material_override = mat
		parent.add_child(seg)
		_filament_segments.append({"mat": mat})


func _render_deep_field_nodes(scene: Dictionary, positions: Dictionary) -> void:
	if not _is_deep_field:
		return
	var root := Node3D.new()
	root.name = "CosmicWebNodes"
	add_child(root)

	var node_mpc: Dictionary = {}
	for n in SceneLoader.get_nodes(scene):
		if n is Dictionary and n.has("id"):
			node_mpc[str(n["id"])] = _vec_mpc(n.get("position_mpc", {}))

	for n in SceneLoader.get_nodes(scene):
		if not (n is Dictionary):
			continue
		var nid: String = str(n.get("id", ""))
		if not node_mpc.has(nid):
			continue
		var pos := _to_render_space(node_mpc[nid], false)
		var nclass := str(n.get("node_class", "filament_intersection"))
		var dens := float(n.get("density", 1.0))
		var holder := Node3D.new()
		holder.name = "nodeviz_%s" % nid
		holder.position = pos
		root.add_child(holder)

		var sz := 0.42 + dens * 0.22
		if nclass == "protocluster_core":
			sz *= 1.55
		elif nclass == "void_boundary":
			sz *= 0.75

		var mesh := MeshInstance3D.new()
		var sp := SphereMesh.new()
		sp.radius = sz
		sp.height = sz * 2.0
		sp.radial_segments = 14
		sp.rings = 7
		mesh.mesh = sp
		var col := Color(1, 0.55, 0.2) if nclass == "protocluster_core" else TYPE_COLORS["cosmic_web_node"]
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(col.r, col.g, col.b, 0.55)
		mat.emission_enabled = true
		mat.emission = col
		mat.emission_energy_multiplier = 0.55
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mesh.material_override = mat
		holder.add_child(mesh)
		_node_entries.append({"mat": mat, "node_class": nclass})


func _render_cmb_shell() -> void:
	var mesh := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 48.0
	sphere.height = 96.0
	mesh.mesh = sphere
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.12, 0.04, 0.06, 0.15)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.cull_mode = BaseMaterial3D.CULL_FRONT
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mesh.material_override = mat
	mesh.name = "cmb_shell"
	add_child(mesh)
	_cmb_shell = mesh


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
		var holder: Node3D = e["holder"]
		holder.scale = Vector3.ONE * (1.22 if oid == selected_id else 1.0)


func get_object_world_position(object_id: String) -> Vector3:
	var e: Dictionary = _id_to_entry.get(object_id, {})
	var h: Node3D = e.get("holder", null)
	if h:
		return h.global_position
	return Vector3.ZERO


func get_object_radius(object_id: String) -> float:
	var e: Dictionary = _id_to_entry.get(object_id, {})
	var otype: String = str(e.get("otype", ""))
	var s := float(e.get("size", 0.5))
	if otype == "lyman_alpha_blob":
		return s * 1.2
	return s


func apply_visual_state(
	state: Dictionary,
	requirements: Dictionary,
	mode: String,
	selected_id: String,
	labels_on: bool,
) -> void:
	_requirements_map = requirements
	signal_mode = mode
	_selected_id = selected_id
	_labels_visible = labels_on
	_pulse_materials.clear()

	for oid in _id_to_entry.keys():
		var e: Dictionary = _id_to_entry[oid]
		var mat: StandardMaterial3D = e.get("mat", null)
		var label: Label3D = e["label"]
		var obj: Dictionary = e["obj"]
		var otype: String = e["otype"]
		var base: Color = e["base_color"]
		var disc: Dictionary = state.get("discoveries", {}).get(oid, {})
		var conf := float(disc.get("confidence", 0.0))

		var emphasis := _mode_emphasis(otype, mode, requirements.get(otype, {}))
		var band := _discovery_band(conf)
		if otype == "lyman_alpha_blob":
			var holder: Node3D = e["holder"]
			for c in holder.get_children():
				if c is MeshInstance3D and str(c.name).begins_with("LABShell"):
					var sm: StandardMaterial3D = c.material_override as StandardMaterial3D
					if sm:
						_apply_discovery_material(sm, base, otype, band, emphasis)
			_refresh_lab_shell_pulse(holder)
		elif mat != null:
			_apply_discovery_material(mat, base, otype, band, emphasis)

		if band == "anomaly" and mat != null and mat.emission_enabled and otype not in ["lyman_alpha_blob", "magnetar"]:
			_pulse_materials.append(mat)
		if band == "anomaly" and otype == "magnetar" and mat != null:
			_pulse_materials.append(mat)

		var show_lbl := labels_on and _should_show_label(oid, otype, conf, selected_id)
		label.visible = show_lbl
		label.text = _label_text(obj, conf)
		if oid == selected_id:
			label.outline_size = 10
			label.modulate = Color(1, 1, 0.88, 1.0)
		else:
			label.outline_size = 4
			label.modulate = Color(0.82, 0.9, 1, 0.72 if conf < 0.5 else 0.9)

		if otype == "quasar":
			_apply_quasar_jet_materials(e.get("jet_mats", []), mode)

		_refresh_black_hole_ring(e["holder"], otype, mode, emphasis)

	if _cmb_shell and _cmb_shell.material_override is StandardMaterial3D:
		var cmat: StandardMaterial3D = _cmb_shell.material_override
		var cvis := 0.1
		if mode == "microwave":
			cvis = 0.42
		elif mode == "radio":
			cvis = 0.22
		elif mode == "weak_lensing" or mode == "dark_matter_inference":
			cvis = 0.18
		cmat.albedo_color.a = cvis

	_refresh_filament_materials(mode)
	_refresh_node_materials(mode)


func _refresh_lab_shell_pulse(holder: Node3D) -> void:
	for c in holder.get_children():
		if c is MeshInstance3D and str(c.name).begins_with("LABShell"):
			var m: StandardMaterial3D = c.material_override as StandardMaterial3D
			if m:
				_pulse_materials.append(m)


func _apply_quasar_jet_materials(jet_mats: Array, mode: String) -> void:
	var jet_em := 0.55
	if mode == "radio":
		jet_em = 2.8
	elif mode in ["xray", "gamma_ray"]:
		jet_em = 1.1
	elif mode == "visible_light":
		jet_em = 0.9
	elif mode in ["weak_lensing", "dark_matter_inference", "gravitational_wave", "neutrino"]:
		jet_em = 0.25
	for jm in jet_mats:
		if jm is StandardMaterial3D:
			(jm as StandardMaterial3D).emission_energy_multiplier = jet_em


func _refresh_black_hole_ring(holder: Node3D, otype: String, mode: String, emphasis: float) -> void:
	if otype != "black_hole":
		return
	var ring: MeshInstance3D = holder.get_node_or_null("AccretionRing") as MeshInstance3D
	if ring == null or not (ring.material_override is StandardMaterial3D):
		return
	var rmat: StandardMaterial3D = ring.material_override
	var bright := 0.25
	if mode in ["xray", "gamma_ray"]:
		bright = 2.2
	elif mode == "radio":
		bright = 0.85
	elif mode == "visible_light":
		bright = 0.18 * emphasis
	else:
		bright = 0.35 * emphasis
	rmat.emission_energy_multiplier = bright
	rmat.albedo_color.a = clampf(0.35 + bright * 0.12, 0.2, 0.95)


func _refresh_filament_materials(mode: String) -> void:
	var fe := _filament_mode_emphasis(mode)
	for seg in _filament_segments:
		var mat: StandardMaterial3D = seg.get("mat", null)
		if mat == null:
			continue
		var base: Color = TYPE_COLORS["cosmic_web_filament"]
		mat.albedo_color = Color(base.r, base.g, base.b, clampf(0.18 + fe * 0.5, 0.08, 0.75))
		mat.emission_energy_multiplier = 0.12 + fe * 1.85


func _filament_mode_emphasis(mode: String) -> float:
	if mode in ["weak_lensing", "dark_matter_inference"]:
		return 1.0
	if mode == "visible_light":
		return 0.22
	if mode == "microwave":
		return 0.12
	if mode == "radio":
		return 0.28
	if mode in ["xray", "gamma_ray"]:
		return 0.2
	if mode in ["gravitational_wave", "neutrino"]:
		return 0.15
	if mode == "speculative_now_signal":
		return 0.55
	return 0.25


func _refresh_node_materials(mode: String) -> void:
	for ne in _node_entries:
		var mat: StandardMaterial3D = ne.get("mat", null)
		var nclass: String = str(ne.get("node_class", ""))
		if mat == null:
			continue
		var em := 0.45
		if mode in ["weak_lensing", "dark_matter_inference"]:
			em = 1.15 if nclass == "protocluster_core" else 0.95
		elif mode == "visible_light":
			em = 0.35
		elif mode == "microwave":
			em = 0.18
		else:
			em = 0.5
		mat.emission_energy_multiplier = em


func _discovery_band(conf: float) -> String:
	if conf < 0.01:
		return "undiscovered"
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
	mode_emphasis: float,
) -> void:
	var c := base
	var emit_mult := 1.0
	match band:
		"undiscovered":
			c = Color(0.25, 0.26, 0.3, base.a)
			emit_mult = 0.15
		"anomaly":
			c = base.lerp(Color(0.5, 0.45, 0.55), 0.5)
			emit_mult = 0.35
		"candidate":
			c = base.lerp(Color(0.7, 0.75, 0.85), 0.35)
			emit_mult = 0.65
		"confirmed":
			c = base
			emit_mult = 1.0
		"characterized":
			c = base.lightened(0.12)
			emit_mult = 1.35

	c = c.lerp(Color.BLACK, 1.0 - clampf(mode_emphasis, 0.06, 1.0))
	mat.albedo_color = Color(c.r, c.g, c.b, base.a)

	if otype in ["star", "quasar", "magnetar", "lyman_alpha_blob"]:
		mat.emission_enabled = true
		mat.emission = base
		mat.emission_energy_multiplier = emit_mult * (1.2 + (0.5 if band == "characterized" else 0.0))
	elif otype == "black_hole":
		mat.emission_enabled = band in ["confirmed", "characterized"] and mode_emphasis > 0.2
		mat.emission = Color(0.15, 0.08, 0.2)
		mat.emission_energy_multiplier = emit_mult * mode_emphasis * 0.6
	else:
		mat.emission_enabled = band == "characterized" or band == "confirmed"
		mat.emission = base
		mat.emission_energy_multiplier = emit_mult * 0.8


func _mode_emphasis(otype: String, mode: String, req: Dictionary) -> float:
	if _is_deep_field:
		return _mode_emphasis_deep_field(otype, mode, req)
	return _mode_emphasis_default(otype, mode, req)


func _mode_emphasis_default(otype: String, mode: String, req: Dictionary) -> float:
	if mode == "speculative_now_signal":
		if otype in ["quasar", "black_hole", "galaxy", "lyman_alpha_blob", "magnetar"]:
			return 0.9
		return 0.12

	if mode == "gravitational_wave":
		if otype in ["black_hole", "magnetar", "quasar"]:
			return 1.0
		return 0.12

	if mode == "neutrino":
		if otype in ["magnetar", "black_hole", "quasar"]:
			return 0.85
		return 0.15

	if mode == "weak_lensing" or mode == "dark_matter_inference":
		if otype in ["cosmic_web_filament", "cosmic_web_node", "void", "galaxy"]:
			return 1.0
		return 0.18

	if mode == "microwave":
		if otype == "cmb_background":
			return 1.0
		return 0.35

	if mode == "radio":
		if otype in ["cmb_background", "quasar", "galaxy", "magnetar"]:
			return 0.95
		return 0.22

	if mode in ["xray", "gamma_ray"]:
		if otype in ["black_hole", "magnetar", "quasar", "lyman_alpha_blob"]:
			return 1.0
		return 0.15

	if mode == "visible_light":
		if otype in ["star", "planet", "moon", "galaxy", "quasar", "observatory", "asteroid", "comet", "lyman_alpha_blob"]:
			return 1.0
		return 0.25

	var req_list: Array = req.get("required_signal_types", [])
	var opt_list: Array = req.get("optional_signal_types", [])
	if mode in req_list or mode in opt_list:
		return 1.0
	return 0.28


func _quasar_bh_dominated() -> bool:
	# Heuristic: if quasar is selected or always-on for LAB xray dimming — use scene relationships.
	for oid in _id_to_entry.keys():
		var e: Dictionary = _id_to_entry[oid]
		if str(e.get("otype", "")) != "quasar":
			continue
		var obj: Dictionary = e.get("obj", {})
		var rels: Array = obj.get("relationships", [])
		if not (rels is Array):
			continue
		for r in rels:
			if r is Dictionary and str(r.get("relation", "")) == "hosts":
				return true
	return false


func _mode_emphasis_deep_field(otype: String, mode: String, _req: Dictionary) -> float:
	match mode:
		"visible_light":
			match otype:
				"galaxy", "quasar":
					return 1.0
				"lyman_alpha_blob":
					return 0.48
				"black_hole":
					return 0.1
				"magnetar":
					return 0.55
				"void":
					return 0.38
				"cmb_background":
					return 0.22
				"star", "planet", "moon", "observatory", "comet", "asteroid":
					return 0.9
			return 0.2
		"radio":
			match otype:
				"quasar", "magnetar":
					return 1.0
				"cmb_background":
					return 0.35
				"galaxy":
					return 0.32
				"lyman_alpha_blob":
					return 0.28
				"black_hole":
					return 0.35
			return 0.18
		"microwave":
			if otype == "cmb_background":
				return 1.0
			return 0.18
		"xray":
			match otype:
				"magnetar", "black_hole", "quasar":
					return 1.0
				"lyman_alpha_blob":
					return 0.35 if _quasar_bh_dominated() else 0.55
			return 0.14
		"gamma_ray":
			match otype:
				"magnetar", "black_hole", "quasar":
					return 1.0
				"lyman_alpha_blob":
					return 0.22
			return 0.12
		"gravitational_wave":
			if otype in ["black_hole", "magnetar", "quasar"]:
				return 0.88
			return 0.1
		"neutrino":
			if otype in ["black_hole", "magnetar", "quasar"]:
				return 0.82
			return 0.11
		"weak_lensing":
			match otype:
				"void", "galaxy":
					return 0.92
				"lyman_alpha_blob", "quasar":
					return 0.42
				"black_hole", "magnetar":
					return 0.35
				"cmb_background":
					return 0.25
			return 0.35
		"dark_matter_inference":
			match otype:
				"void", "galaxy":
					return 0.55
				"lyman_alpha_blob", "quasar", "star", "planet", "moon":
					return 0.12
				"black_hole", "magnetar":
					return 0.22
				"cmb_background":
					return 0.2
			return 0.35
		"speculative_now_signal":
			if otype in ["quasar", "black_hole", "lyman_alpha_blob", "magnetar", "void", "galaxy"]:
				return 0.92
			return 0.14
		"ultraviolet":
			match otype:
				"lyman_alpha_blob":
					return 1.0
				"galaxy", "quasar":
					return 0.85
				"black_hole":
					return 0.35
				"magnetar":
					return 0.65
			return 0.22
		"infrared":
			if otype in ["galaxy", "quasar", "lyman_alpha_blob"]:
				return 0.75
			return 0.28
	return _mode_emphasis_default(otype, mode, _req)


func _should_show_label(oid: String, otype: String, conf: float, selected: String) -> bool:
	if oid == selected:
		return true
	if _is_deep_field:
		if otype == "galaxy":
			return conf >= 0.55
		if otype in ["lyman_alpha_blob", "quasar", "black_hole", "magnetar", "void"]:
			return conf >= 0.35
		return conf >= 0.75
	if conf >= 0.75:
		return true
	if otype in ["star", "planet", "observatory"] and conf >= 0.25:
		return true
	return false


func _label_text(obj: Dictionary, conf: float) -> String:
	if conf < 0.25:
		return "Unknown source"
	if conf < 0.50:
		return "Signal anomaly"
	if conf < 0.75:
		return "Candidate: %s" % obj.get("type", "?")
	return str(obj.get("name", obj.get("id", "?")))


func object_node(object_id: String) -> Node3D:
	var e: Dictionary = _id_to_entry.get(object_id, {})
	return e.get("holder", null)
