class_name TelescopeOverlay
extends Control
## Centered viewfinder / reticle for Observatory View (code-drawn, no assets).

var _reticle: Control
var _fov_ring: Control
var _hud_top: Label
var _hud_bottom: Label
var _lock_frame: Control
var _visible_in_observatory: bool = true


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build()


func _build() -> void:
	_fov_ring = Control.new()
	_fov_ring.set_anchors_preset(Control.PRESET_CENTER)
	_fov_ring.custom_minimum_size = Vector2(320, 320)
	_fov_ring.size = Vector2(320, 320)
	_fov_ring.position = Vector2(-160, -160)
	_fov_ring.draw.connect(_draw_fov_ring)
	add_child(_fov_ring)

	_reticle = Control.new()
	_reticle.set_anchors_preset(Control.PRESET_CENTER)
	_reticle.custom_minimum_size = Vector2(48, 48)
	_reticle.size = Vector2(48, 48)
	_reticle.position = Vector2(-24, -24)
	_reticle.draw.connect(_draw_reticle)
	add_child(_reticle)

	_lock_frame = Control.new()
	_lock_frame.set_anchors_preset(Control.PRESET_CENTER)
	_lock_frame.custom_minimum_size = Vector2(72, 72)
	_lock_frame.size = Vector2(72, 72)
	_lock_frame.position = Vector2(-36, -36)
	_lock_frame.visible = false
	_lock_frame.draw.connect(_draw_lock)
	add_child(_lock_frame)

	_hud_top = Label.new()
	_hud_top.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_hud_top.offset_top = 118
	_hud_top.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hud_top.add_theme_font_size_override("font_size", 11)
	_hud_top.add_theme_color_override("font_color", Color(0.7, 0.82, 0.95, 0.9))
	add_child(_hud_top)

	_hud_bottom = Label.new()
	_hud_bottom.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_hud_bottom.offset_bottom = -118
	_hud_bottom.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hud_bottom.add_theme_font_size_override("font_size", 10)
	_hud_bottom.add_theme_color_override("font_color", Color(0.55, 0.68, 0.82, 0.85))
	add_child(_hud_bottom)


func set_observatory_active(active: bool) -> void:
	_visible_in_observatory = active
	visible = active
	if _fov_ring:
		_fov_ring.visible = active
	if _reticle:
		_reticle.visible = active
	if _hud_top:
		_hud_top.visible = active
	if _hud_bottom:
		_hud_bottom.visible = active


func update_hud(
	tier_name: String,
	signal_mode: String,
	fov_degrees: float,
	selected_name: String,
	has_selection: bool,
) -> void:
	var fov_lbl: String = "Wide" if fov_degrees > 45.0 else ("Medium" if fov_degrees > 20.0 else "Narrow")
	_hud_top.text = "Instrument: %s  ·  Signal: %s  ·  FOV: %.0f° (%s)" % [
		tier_name,
		signal_mode.replace("_", " "),
		fov_degrees,
		fov_lbl,
	]
	if has_selection and selected_name != "":
		_hud_bottom.text = (
			"Target lock: %s  ·  F center  ·  Observe  ·  Capture in Imaging tab" % selected_name
		)
		_lock_frame.visible = true
	else:
		_hud_bottom.text = "Click sky target to select  ·  F center  ·  V Scene Map"
		_lock_frame.visible = false
	_reticle.queue_redraw()
	_fov_ring.queue_redraw()
	_lock_frame.queue_redraw()


func flash_observe() -> void:
	modulate = Color(1.2, 1.15, 0.9, 1.0)
	var tw := create_tween()
	tw.tween_property(self, "modulate", Color.WHITE, 0.35)


func _draw_reticle() -> void:
	var c := Vector2(24, 24)
	var col := Color(0.75, 0.88, 1.0, 0.85)
	_reticle.draw_line(c + Vector2(-14, 0), c + Vector2(-4, 0), col, 1.5)
	_reticle.draw_line(c + Vector2(4, 0), c + Vector2(14, 0), col, 1.5)
	_reticle.draw_line(c + Vector2(0, -14), c + Vector2(0, -4), col, 1.5)
	_reticle.draw_line(c + Vector2(0, 4), c + Vector2(0, 14), col, 1.5)
	_reticle.draw_arc(c, 3.0, 0, TAU, 24, Color(0.9, 0.95, 1, 0.5), 1.0)


func _draw_fov_ring() -> void:
	var c := Vector2(160, 160)
	var r := 140.0
	_fov_ring.draw_arc(c, r, 0, TAU, 64, Color(0.45, 0.55, 0.7, 0.22), 1.0)


func _draw_lock() -> void:
	var c := Vector2(36, 36)
	var col := Color(1.0, 0.92, 0.55, 0.75)
	var s := 28.0
	_lock_frame.draw_line(c + Vector2(-s, -s), c + Vector2(-s + 8, -s), col, 1.5)
	_lock_frame.draw_line(c + Vector2(-s, -s), c + Vector2(-s, -s + 8), col, 1.5)
	_lock_frame.draw_line(c + Vector2(s, -s), c + Vector2(s - 8, -s), col, 1.5)
	_lock_frame.draw_line(c + Vector2(s, -s), c + Vector2(s, -s + 8), col, 1.5)
	_lock_frame.draw_line(c + Vector2(-s, s), c + Vector2(-s + 8, s), col, 1.5)
	_lock_frame.draw_line(c + Vector2(-s, s), c + Vector2(-s, s - 8), col, 1.5)
	_lock_frame.draw_line(c + Vector2(s, s), c + Vector2(s - 8, s), col, 1.5)
	_lock_frame.draw_line(c + Vector2(s, s), c + Vector2(s, s - 8), col, 1.5)
