class_name TelescopeCamera
extends Camera3D
## Telescope camera: Observatory mode (fixed observer, pan/zoom sky) or
## Scene Map mode (orbital debug camera around spatial layout).
##
## Left-click release without drag emits `pick_attempt` for 3D ray selection.

signal pick_attempt(screen_position: Vector2)
signal focus_requested()

@export var target: Vector3 = Vector3.ZERO
@export var distance: float = 22.0
@export var min_distance: float = 1.5
@export var max_distance: float = 500.0
@export var yaw: float = 0.7
@export var pitch: float = 0.45

@export var orbit_sensitivity: float = 0.005
@export var pan_sensitivity: float = 0.02
@export var pick_drag_threshold_px: float = 6.0

var observatory_mode: bool = true
var observatory_zoom: float = 1.0

var _orbit_button: int = MOUSE_BUTTON_NONE
var _orbiting := false
var _panning := false
var _press_pos := Vector2.ZERO
var _drag_beyond_threshold := false

var _preset_deep_field := false
var _preset_target := Vector3.ZERO
var _preset_fit_radius := 12.0
var _preset_aim_dir := Vector3(0, 0.35, 1).normalized()


func _ready() -> void:
	_refresh_transform()


func set_observatory_mode(enabled: bool) -> void:
	observatory_mode = enabled
	reset_view()


## Apply camera pose for the current scene (call after the active renderer has built the sky).
func apply_scene_framing(is_deep_field: bool, aim: Vector3, fit_radius: float) -> void:
	_preset_deep_field = is_deep_field
	_preset_target = aim
	_preset_fit_radius = maxf(fit_radius, 1.5)
	if aim.length_squared() > 1e-6:
		_preset_aim_dir = aim.normalized()
	reset_view()


func reset_view() -> void:
	observatory_zoom = 1.0
	if observatory_mode:
		target = _preset_aim_dir * SkyProjection.DOME_RADIUS * 0.55
		yaw = atan2(_preset_aim_dir.z, _preset_aim_dir.x)
		pitch = asin(clampf(_preset_aim_dir.y, -1.0, 1.0))
		distance = 1.0
	else:
		if _preset_deep_field:
			target = _preset_target
			var fit := maxf(_preset_fit_radius, 2.0)
			distance = clampf(fit * 3.35, 9.0, 220.0)
			yaw = 0.52
			pitch = 0.36
		else:
			target = Vector3.ZERO
			distance = 22.0
			yaw = 0.7
			pitch = 0.45
	_refresh_transform()


func focus_on(world_pos: Vector3, radius: float = 1.0) -> void:
	if observatory_mode:
		var dir: Vector3 = world_pos.normalized()
		if dir.length_squared() < 1e-8:
			return
		yaw = atan2(dir.z, dir.x)
		pitch = asin(clampf(dir.y, -1.0, 1.0))
		observatory_zoom = clampf(2.8 / maxf(radius, 0.5), 0.35, 4.5)
		target = dir * SkyProjection.DOME_RADIUS * 0.55
	else:
		target = world_pos
		distance = clampf(radius * 10.0, min_distance, max_distance * 0.45)
	_refresh_transform()


func _refresh_transform() -> void:
	pitch = clampf(pitch, -1.35, 1.35)
	if observatory_mode:
		global_position = Vector3.ZERO
		var cp := cos(pitch)
		var look_dir := Vector3(cp * sin(yaw), sin(pitch), cp * cos(yaw)).normalized()
		look_at(look_dir * 500.0, Vector3.UP)
		fov = clampf(62.0 / observatory_zoom, 6.0, 85.0)
	else:
		distance = clampf(distance, min_distance, max_distance)
		var cp := cos(pitch)
		var offset := Vector3(cp * sin(yaw), sin(pitch), cp * cos(yaw)) * distance
		global_position = target + offset
		look_at(target, Vector3.UP)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_F:
				focus_requested.emit()
			KEY_R:
				reset_view()
			KEY_EQUAL, KEY_KP_ADD:
				if observatory_mode:
					observatory_zoom *= 1.12
				else:
					distance *= 0.88
				_refresh_transform()
			KEY_MINUS, KEY_KP_SUBTRACT:
				if observatory_mode:
					observatory_zoom *= 0.88
				else:
					distance *= 1.12
				_refresh_transform()

	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			if observatory_mode:
				observatory_zoom *= 1.1
			else:
				distance *= 0.9
			_refresh_transform()
			get_viewport().set_input_as_handled()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			if observatory_mode:
				observatory_zoom *= 0.9
			else:
				distance *= 1.1
			_refresh_transform()
			get_viewport().set_input_as_handled()
		elif mb.button_index == MOUSE_BUTTON_MIDDLE:
			_panning = mb.pressed
			if mb.pressed:
				get_viewport().set_input_as_handled()
		elif mb.button_index == MOUSE_BUTTON_LEFT or mb.button_index == MOUSE_BUTTON_RIGHT:
			if mb.pressed:
				if mb.button_index == MOUSE_BUTTON_LEFT and Input.is_key_pressed(KEY_SHIFT):
					_panning = true
					_orbiting = false
					_orbit_button = MOUSE_BUTTON_NONE
				else:
					_orbiting = true
					_orbit_button = mb.button_index
					_press_pos = mb.position
					_drag_beyond_threshold = false
			else:
				if mb.button_index == MOUSE_BUTTON_LEFT:
					if _orbiting and _orbit_button == MOUSE_BUTTON_LEFT and not _drag_beyond_threshold:
						pick_attempt.emit(mb.position)
				_orbiting = false
				_orbit_button = MOUSE_BUTTON_NONE
				_panning = false
				_drag_beyond_threshold = false
				get_viewport().set_input_as_handled()

	if event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if _panning and (Input.is_mouse_button_pressed(MOUSE_BUTTON_MIDDLE) or (
			Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) and Input.is_key_pressed(KEY_SHIFT)
		)):
			if observatory_mode:
				_pan_sky(mm.relative)
			else:
				_pan_camera(mm.relative)
			get_viewport().set_input_as_handled()
		elif _orbiting and (
			(_orbit_button == MOUSE_BUTTON_LEFT and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT))
			or (_orbit_button == MOUSE_BUTTON_RIGHT and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT))
		):
			if not _drag_beyond_threshold and _press_pos.distance_to(mm.position) > pick_drag_threshold_px:
				_drag_beyond_threshold = true
			if _drag_beyond_threshold:
				yaw -= mm.relative.x * orbit_sensitivity
				pitch -= mm.relative.y * orbit_sensitivity
				_refresh_transform()
				get_viewport().set_input_as_handled()


func _pan_camera(rel: Vector2) -> void:
	var right := global_transform.basis.x
	var up := global_transform.basis.y
	target -= right * rel.x * pan_sensitivity
	target += up * rel.y * pan_sensitivity
	_refresh_transform()


func _pan_sky(rel: Vector2) -> void:
	yaw -= rel.x * orbit_sensitivity
	pitch -= rel.y * orbit_sensitivity
	_refresh_transform()
