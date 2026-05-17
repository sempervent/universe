class_name TelescopeConsole
extends CanvasLayer
# TelescopeConsole — observatory UI overlay (controls, signal view, tabs, log).

const _EntityModifiers := preload("res://scripts/EntityModifiers.gd")
const _SceneLoader := preload("res://scripts/SceneLoader.gd")
const _SurveyEngine := preload("res://scripts/SurveyEngine.gd")
const _TransientEngine := preload("res://scripts/TransientEngine.gd")

signal action_observe()
signal action_survey()
signal action_save()
signal action_reload()
signal action_select_object(object_id: String)
signal action_start_survey(survey_id: String)
signal action_unlock_tier(tier_id: String)
signal action_set_active_tier(tier_id: String)
signal action_toggle_labels(enabled: bool)
signal action_signal_mode_changed(mode: String)
signal action_reset_state()
signal action_export_state()
signal action_campaign_load_scene(scene_id: String)
signal action_campaign_set_active(scene_id: String)
signal action_campaign_load_and_set(scene_id: String)
signal action_campaign_refresh()
signal action_observe_transient(event_id: String)

const PANEL_BG := Color(0.04, 0.05, 0.08, 0.92)
const TEXT_DIM := Color(0.65, 0.7, 0.85)
const TEXT_BRIGHT := Color(0.85, 0.95, 1)

var _root: Control
var _header_label: Label
var _meta_label: Label
var _save_path_label: Label
var _objects_list: ItemList
var _detail_text: RichTextLabel
var _log_text: RichTextLabel
var _tab_container: TabContainer
var _tech_text: RichTextLabel
var _surveys_text: RichTextLabel
var _milestones_text: RichTextLabel
var _transients_text: RichTextLabel
var _objectives_text: RichTextLabel
var _btn_observe_transient: Button
var _selected_transient_id: String = ""
var _campaign_summary: Label
var _campaign_scene_list: ItemList
var _campaign_detail: RichTextLabel
var _campaign_cmd: RichTextLabel
var _btn_campaign_load: Button
var _btn_campaign_set: Button
var _btn_campaign_both: Button
var _btn_campaign_refresh: Button
var _selected_campaign_id: String = ""
var _labels_toggle: CheckBox
var _signal_option: OptionButton
var _signal_help: RichTextLabel
var _survey_hint: RichTextLabel
var _object_filter: OptionButton

var _all_objects: Array = []
var _state_for_filter: Dictionary = {}
var _scene_for_filter: Dictionary = {}
var _surveys_map_for_filter: Dictionary = {}
var _selected_id: String = ""
var _signal_mode: String = "visible_light"
var _reset_dialog: ConfirmationDialog = null
var _export_window: Window = null


func _ready() -> void:
	_build_ui()


func setup_signal_modes(modes: Array) -> void:
	_signal_option.clear()
	for m in modes:
		if m is String:
			_signal_option.add_item(m)
	# Select visible_light if present
	for i in range(_signal_option.item_count):
		if _signal_option.get_item_text(i) == "visible_light":
			_signal_option.select(i)
			_signal_mode = "visible_light"
			return
	if _signal_option.item_count > 0:
		_signal_option.select(0)
		_signal_mode = _signal_option.get_item_text(0)


func get_signal_mode() -> String:
	return _signal_mode


func select_signal_mode(mode: String) -> void:
	for i in range(_signal_option.item_count):
		if _signal_option.get_item_text(i) == mode:
			_signal_option.select(i)
			_signal_mode = mode
			return


func is_labels_visible() -> bool:
	return _labels_toggle.button_pressed


func toggle_labels_from_hotkey() -> void:
	_labels_toggle.button_pressed = not _labels_toggle.button_pressed
	action_toggle_labels.emit(_labels_toggle.button_pressed)


func render_signal_mode_help(mode: String, deep_field: bool = false) -> void:
	var body := ""
	if deep_field:
		match mode:
			"visible_light":
				body = "Deep field optical metaphor: galaxies and quasar cores bright; filaments faint; LAB shown as translucent false-color volume (not a radiative-transfer model); black holes mostly indirect."
			"radio":
				body = "Radio view: quasar jets and magnetized compact sources emphasized; ordinary galaxy disks dimmer; CMB shell subtle."
			"microwave":
				body = "Microwave / surface-brightness: CMB shell emphasized; most discrete galaxies and filaments intentionally muted."
			"xray", "gamma_ray":
				body = "High-energy deep field: magnetar hotspots, accretion-ring placeholders, and quasar cores emphasized; LAB de-emphasized unless a bright quasar/BH dominates the line of sight."
			"gravitational_wave":
				body = "GW-style inference overlay: compact-object channels emphasized as abstract tracers; extended structure dimmed (illustrative, not a waveform map)."
			"neutrino":
				body = "Neutrino-channel metaphor: compact high-energy candidates emphasized abstractly; most extended luminous sources dimmed."
			"weak_lensing":
				body = "Weak lensing map: filaments, nodes, voids, and galaxy distributions emphasized as mass tracers; cosmic background inference context in HUD."
			"dark_matter_inference":
				body = "Dark-matter inference visualization: filaments, nodes, and voids strongly emphasized; ordinary optical appearance intentionally suppressed."
			"ultraviolet":
				body = "UV / Lyman-line metaphor: Lyman-alpha blob strongly emphasized alongside young galaxies."
			"infrared":
				body = "IR rest-frame metaphor: dusty galaxies and quasar hosts slightly favored (illustrative colors)."
			"speculative_now_signal":
				body = "[color=#ffaa77][b]FICTIONAL / SPECULATIVE[/b][/color] — causality-violating \"now\" view for flavor only; not physically meaningful."
			_:
				body = "Deep-field emphasis rules for this instrument channel (prototype visualization)."
	else:
		match mode:
			"visible_light":
				body = "Optical / human-band metaphor: stars, planets, resolved galaxies emphasized."
			"radio":
				body = "Long-wavelength view: radio-bright quasars, galaxies, magnetars; planets dimmed."
			"microwave":
				body = "CMB / surface-brightness emphasis. Cosmic microwave background shell highlighted."
			"xray", "gamma_ray":
				body = "High-energy view: accreting black holes, magnetars, hot quasar cores stand out."
			"gravitational_wave":
				body = "Compact mergers / GW tracers emphasized; extended solar-system objects muted."
			"neutrino":
				body = "Neutrino-bright compact sources slightly favored (illustrative)."
			"weak_lensing", "dark_matter_inference":
				body = "Large-scale mass mapping: filaments, voids, galaxy distributions emphasized."
			"speculative_now_signal":
				body = "[color=#ffaa77][b]FICTIONAL / SPECULATIVE[/b][/color] — causality-violating \"now\" view for late-game flavor only."
			_:
				body = "Visualization emphasis derived from discovery requirement signal lists where possible."
	_signal_help.text = "[i]%s[/i]" % body


func render_header(
	state: Dictionary,
	scene: Dictionary,
	last_save_path: String,
	scene_path: String,
	entity_modifier: Dictionary = {},
) -> void:
	var entity: Dictionary = state.get("research_entity", {})
	var name: String = entity.get("name", "Unnamed Research Entity")
	var motto: String = entity.get("motto", "")
	_header_label.text = name
	var pieces := PackedStringArray()
	if _SceneLoader.is_deep_field_scene(scene):
		if scene.get("id", "") == "scene-001":
			pieces.append("Scene kind: Deep Field · High-z protocluster")
		else:
			pieces.append("Scene kind: Deep Field")
	else:
		pieces.append("Scene kind: Solar System (tutorial sky)")
	var z := float(scene.get("redshift", 0.0))
	if z > 1e-4:
		pieces.append("z ≈ %.3f" % z)
	var sm := float(scene.get("size_mpc", 0.0))
	if sm > 1e-6:
		pieces.append("region ~%.1f cMpc" % sm)
	if motto != "":
		pieces.append("\"%s\"" % motto)
	if not entity_modifier.is_empty():
		pieces.append(
			"Background: %s — %s"
			% [str(entity_modifier.get("name", "?")), str(entity_modifier.get("description", ""))]
		)
	pieces.append("Telescope: %s" % state.get("active_telescope_tier", "naked_eye"))
	pieces.append("RP: %d" % int(state.get("research_points", 0)))
	pieces.append("Turn: %d" % int(state.get("turn", 0)))
	pieces.append("Scene: %s" % scene.get("name", "?"))
	_meta_label.text = " · ".join(pieces)
	var camp: Dictionary = state.get("campaign", {})
	var active_id: String = str(camp.get("active_scene_id", "solar-system"))
	if active_id != "":
		pieces.append("Campaign: %s" % active_id)
	_save_path_label.text = "Scene: %s\nLast save: %s" % [scene_path, last_save_path if last_save_path != "" else "(none)"]


func render_campaign_hint(
	state: Dictionary,
	catalog: Array,
	scene: Dictionary,
	scene_path: String,
) -> void:
	var lines := PackedStringArray()
	var camp: Dictionary = state.get("campaign", {})
	var active_id: String = str(camp.get("active_scene_id", "solar-system"))
	var scene_id: String = str(scene.get("id", ""))
	if active_id != "" and scene_id != "" and active_id != scene_id:
		lines.append(
			"[color=#ffaa66]Campaign active scene is '%s' but loaded scene is '%s'. "
			% [active_id, scene_id]
			+ "Regenerate the scene JSON or update user://overrides.json.[/color]"
		)
	for entry in catalog:
		if not entry is Dictionary:
			continue
		if str(entry.get("id", "")) != active_id:
			continue
		var expected: String = str(entry.get("scene_json_path", ""))
		if expected != "" and not scene_path.ends_with(expected.get_file()):
			lines.append(
				"[color=#aaaaaa]Expected scene file: %s[/color]" % expected
			)
		var gen_cmd: String = str(entry.get("generate_command", ""))
		if gen_cmd != "" and not FileAccess.file_exists(scene_path):
			lines.append("[color=#88ccff]%s[/color]" % gen_cmd)
	if catalog.is_empty():
		return
	var scenes_state: Dictionary = camp.get("scenes", {})
	for entry in catalog:
		if not entry is Dictionary:
			continue
		var sid: String = str(entry.get("id", ""))
		if sid == active_id:
			continue
		var st: Dictionary = scenes_state.get(sid, {})
		if st.get("unlocked", false) and not st.get("visited", false):
			var nm: String = str(entry.get("name", sid))
			var cmd: String = str(entry.get("generate_command", ""))
			lines.append(
				"[color=#aaddff]Unvisited: %s — generate then "
				% nm
				+ "`universe game set-scene --scene %s`.[/color]" % sid
			)
			if cmd != "":
				lines.append("[color=#888888]%s[/color]" % cmd)
			break
	if lines.is_empty():
		return
	var existing := _survey_hint.text
	if existing != "":
		_survey_hint.text = existing + "\n\n" + "\n".join(lines)
	else:
		_survey_hint.text = "\n".join(lines)


func show_export_json(json_text: String) -> void:
	if _export_window == null:
		_build_export_window()
	var te: TextEdit = _export_window.find_child("ExportText", true, false)
	te.text = json_text
	_export_window.popup_centered_ratio(0.6)


func _build_export_window() -> void:
	_export_window = Window.new()
	_export_window.title = "Export game state (JSON)"
	_export_window.size = Vector2i(720, 480)
	_export_window.unresizable = false
	var vb := VBoxContainer.new()
	vb.set_anchors_preset(Control.PRESET_FULL_RECT)
	vb.offset_left = 8
	vb.offset_top = 8
	vb.offset_right = -8
	vb.offset_bottom = -8
	_export_window.add_child(vb)
	var te := TextEdit.new()
	te.name = "ExportText"
	te.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vb.add_child(te)
	var hb := HBoxContainer.new()
	var close_btn := Button.new()
	close_btn.text = "Close"
	close_btn.pressed.connect(func(): _export_window.hide())
	hb.add_child(close_btn)
	vb.add_child(hb)
	add_child(_export_window)


func _build_ui() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(_root)

	_reset_dialog = ConfirmationDialog.new()
	_reset_dialog.dialog_text = "Reset all in-memory progress to a fresh game state?\n\nThis does not delete files until you choose Save State."
	_reset_dialog.ok_button_text = "Reset"
	_reset_dialog.canceled.connect(func(): pass)
	_reset_dialog.confirmed.connect(func(): action_reset_state.emit())
	add_child(_reset_dialog)

	_build_header()
	_build_left_panel()
	_build_right_panel()
	_build_log_panel()


func _build_header() -> void:
	var bar := PanelContainer.new()
	bar.set_anchors_preset(Control.PRESET_TOP_WIDE)
	bar.offset_top = 0
	bar.offset_bottom = 108
	bar.add_theme_stylebox_override("panel", _bg_style())
	_root.add_child(bar)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 2)
	bar.add_child(vb)
	_header_label = _label("", 17, TEXT_BRIGHT)
	_meta_label = _label("", 11, TEXT_DIM)
	_save_path_label = _label("", 9, Color(0.5, 0.58, 0.72))
	_save_path_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(_header_label)
	vb.add_child(_meta_label)
	vb.add_child(_save_path_label)
	_survey_hint = RichTextLabel.new()
	_survey_hint.bbcode_enabled = true
	_survey_hint.scroll_active = false
	_survey_hint.custom_minimum_size = Vector2(0, 36)
	_survey_hint.add_theme_font_size_override("normal_font_size", 10)
	_survey_hint.add_theme_color_override("default_color", Color(0.55, 0.62, 0.78))
	vb.add_child(_survey_hint)


func _build_left_panel() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	panel.offset_top = 94
	panel.offset_bottom = -210
	panel.offset_left = 0
	panel.size_flags_horizontal = Control.SIZE_FILL
	panel.custom_minimum_size = Vector2(300, 0)
	panel.add_theme_stylebox_override("panel", _bg_style())
	_root.add_child(panel)

	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 6)
	panel.add_child(vb)

	vb.add_child(_label("Controls", 11, TEXT_DIM))
	var btn_obs := Button.new()
	btn_obs.text = "Observe Selected"
	btn_obs.pressed.connect(func(): action_observe.emit())
	vb.add_child(btn_obs)
	var btn_sur := Button.new()
	btn_sur.text = "Survey All"
	btn_sur.pressed.connect(func(): action_survey.emit())
	vb.add_child(btn_sur)
	var btn_save := Button.new()
	btn_save.text = "Save State"
	btn_save.pressed.connect(func(): action_save.emit())
	vb.add_child(btn_save)
	var btn_reload := Button.new()
	btn_reload.text = "Reload Scene/State"
	btn_reload.pressed.connect(func(): action_reload.emit())
	vb.add_child(btn_reload)

	var btn_reset := Button.new()
	btn_reset.text = "Reset State…"
	btn_reset.pressed.connect(func(): _reset_dialog.popup_centered())
	vb.add_child(btn_reset)

	var btn_export := Button.new()
	btn_export.text = "Export State…"
	btn_export.pressed.connect(func(): action_export_state.emit())
	vb.add_child(btn_export)

	_labels_toggle = CheckBox.new()
	_labels_toggle.text = "Show labels (L)"
	_labels_toggle.button_pressed = true
	_labels_toggle.toggled.connect(func(on): action_toggle_labels.emit(on))
	vb.add_child(_labels_toggle)

	vb.add_child(_label("Signal visualization", 11, TEXT_DIM))
	_signal_option = OptionButton.new()
	_signal_option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_signal_option.item_selected.connect(_on_signal_selected)
	vb.add_child(_signal_option)

	_signal_help = RichTextLabel.new()
	_signal_help.bbcode_enabled = true
	_signal_help.scroll_active = false
	_signal_help.custom_minimum_size = Vector2(0, 56)
	vb.add_child(_signal_help)

	vb.add_child(_label("Object list filter", 11, TEXT_DIM))
	_object_filter = OptionButton.new()
	_object_filter.add_item("All")
	_object_filter.add_item("Unknown")
	_object_filter.add_item("Candidate")
	_object_filter.add_item("Confirmed")
	_object_filter.add_item("Exotic")
	_object_filter.add_item("Survey targets")
	_object_filter.item_selected.connect(_on_object_filter_selected)
	vb.add_child(_object_filter)

	vb.add_child(_label("Sky objects", 11, TEXT_DIM))
	_objects_list = ItemList.new()
	_objects_list.custom_minimum_size = Vector2(0, 300)
	_objects_list.item_selected.connect(_on_object_selected)
	vb.add_child(_objects_list)


func _on_signal_selected(idx: int) -> void:
	_signal_mode = _signal_option.get_item_text(idx)
	action_signal_mode_changed.emit(_signal_mode)


func _build_right_panel() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	panel.offset_top = 94
	panel.offset_bottom = -210
	panel.offset_right = 0
	panel.offset_left = -400
	panel.add_theme_stylebox_override("panel", _bg_style())
	_root.add_child(panel)

	_tab_container = TabContainer.new()
	panel.add_child(_tab_container)

	_detail_text = RichTextLabel.new()
	_detail_text.bbcode_enabled = true
	_detail_text.scroll_active = true
	_detail_text.name = "Detail"
	_tab_container.add_child(_detail_text)

	_tech_text = RichTextLabel.new()
	_tech_text.bbcode_enabled = true
	_tech_text.scroll_active = true
	_tech_text.meta_clicked.connect(_on_meta_clicked)
	_tech_text.name = "Tech"
	_tab_container.add_child(_tech_text)

	_surveys_text = RichTextLabel.new()
	_surveys_text.bbcode_enabled = true
	_surveys_text.scroll_active = true
	_surveys_text.meta_clicked.connect(_on_meta_clicked)
	_surveys_text.name = "Surveys"
	_tab_container.add_child(_surveys_text)

	_milestones_text = RichTextLabel.new()
	_milestones_text.bbcode_enabled = true
	_milestones_text.scroll_active = true
	_milestones_text.name = "Milestones"
	_tab_container.add_child(_milestones_text)

	var tr_scroll := ScrollContainer.new()
	tr_scroll.name = "Transients"
	tr_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tr_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_tab_container.add_child(tr_scroll)
	var tr_outer := VBoxContainer.new()
	tr_outer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tr_outer.add_theme_constant_override("separation", 6)
	tr_scroll.add_child(tr_outer)
	_transients_text = RichTextLabel.new()
	_transients_text.bbcode_enabled = true
	_transients_text.scroll_active = true
	_transients_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_transients_text.custom_minimum_size = Vector2(0, 280)
	tr_outer.add_child(_transients_text)
	_btn_observe_transient = Button.new()
	_btn_observe_transient.text = "Observe Event"
	_btn_observe_transient.disabled = true
	_btn_observe_transient.pressed.connect(_on_observe_transient_pressed)
	tr_outer.add_child(_btn_observe_transient)

	_objectives_text = RichTextLabel.new()
	_objectives_text.bbcode_enabled = true
	_objectives_text.scroll_active = true
	_objectives_text.name = "Objectives"
	_tab_container.add_child(_objectives_text)

	_build_campaign_tab()


func _build_campaign_tab() -> void:
	var scroll := ScrollContainer.new()
	scroll.name = "Campaign"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_tab_container.add_child(scroll)

	var outer := VBoxContainer.new()
	outer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	outer.add_theme_constant_override("separation", 6)
	scroll.add_child(outer)

	_campaign_summary = _label("Observing Program", 11, TEXT_DIM)
	_campaign_summary.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	outer.add_child(_campaign_summary)

	_campaign_scene_list = ItemList.new()
	_campaign_scene_list.custom_minimum_size = Vector2(0, 140)
	_campaign_scene_list.item_selected.connect(_on_campaign_scene_selected)
	outer.add_child(_campaign_scene_list)

	_campaign_detail = RichTextLabel.new()
	_campaign_detail.bbcode_enabled = true
	_campaign_detail.scroll_active = true
	_campaign_detail.custom_minimum_size = Vector2(0, 160)
	outer.add_child(_campaign_detail)

	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 4)
	_btn_campaign_load = Button.new()
	_btn_campaign_load.text = "Load Scene"
	_btn_campaign_load.pressed.connect(_on_campaign_load_pressed)
	hb.add_child(_btn_campaign_load)
	_btn_campaign_set = Button.new()
	_btn_campaign_set.text = "Set Active"
	_btn_campaign_set.pressed.connect(_on_campaign_set_pressed)
	hb.add_child(_btn_campaign_set)
	_btn_campaign_both = Button.new()
	_btn_campaign_both.text = "Load + Set Active"
	_btn_campaign_both.pressed.connect(_on_campaign_both_pressed)
	hb.add_child(_btn_campaign_both)
	outer.add_child(hb)

	_btn_campaign_refresh = Button.new()
	_btn_campaign_refresh.text = "Refresh File Status"
	_btn_campaign_refresh.pressed.connect(func(): action_campaign_refresh.emit())
	outer.add_child(_btn_campaign_refresh)

	_campaign_cmd = RichTextLabel.new()
	_campaign_cmd.bbcode_enabled = true
	_campaign_cmd.scroll_active = true
	_campaign_cmd.custom_minimum_size = Vector2(0, 72)
	outer.add_child(_campaign_cmd)


func _sorted_catalog(catalog: Array) -> Array:
	var sorted: Array = []
	for entry in catalog:
		if entry is Dictionary:
			sorted.append(entry)
	sorted.sort_custom(func(a, b): return int(a.get("order_index", 0)) < int(b.get("order_index", 0)))
	return sorted


func _survey_names(survey_ids: Array, surveys_map: Dictionary) -> String:
	var names: PackedStringArray = []
	for sid in survey_ids:
		var s: String = str(sid)
		if surveys_map.has(s):
			names.append(str(surveys_map[s].get("name", s)))
		else:
			names.append(s)
	return ", ".join(names) if names.size() > 0 else "—"


func render_campaign_program(
	state: Dictionary,
	catalog: Array,
	scene: Dictionary,
	scene_path: String,
	surveys_map: Dictionary = {},
) -> void:
	if _campaign_scene_list == null:
		return
	var camp: Dictionary = state.get("campaign", {})
	var scenes_st: Dictionary = camp.get("scenes", {})
	var active_id: String = str(camp.get("active_scene_id", "solar-system"))
	var loaded_id: String = str(scene.get("id", ""))
	var entity: Dictionary = state.get("research_entity", {})
	var ent_name: String = str(entity.get("name", "Research Entity"))

	var total := 0
	var unlocked_n := 0
	var visited_n := 0
	for entry in catalog:
		if not entry is Dictionary:
			continue
		total += 1
		var sid: String = str(entry.get("id", ""))
		var st: Dictionary = scenes_st.get(sid, {})
		if st.get("unlocked", sid == "solar-system"):
			unlocked_n += 1
		if st.get("visited", false):
			visited_n += 1

	var scene_class: String = str(scene.get("metadata", {}).get("scene_class", scene.get("scene_class", "?")))
	_campaign_summary.text = (
		"%s · Active: %s · Loaded: %s (%s)\n"
		% [ent_name, active_id, loaded_id if loaded_id != "" else "?", scene_class]
		+ "Progress: %d/%d unlocked, %d visited · Path: %s"
		% [unlocked_n, total, visited_n, scene_path]
	)

	_campaign_scene_list.clear()
	var sorted := _sorted_catalog(catalog)
	var select_idx := -1
	var preserve: String = _selected_campaign_id
	for i in range(sorted.size()):
		var entry: Dictionary = sorted[i]
		var sid: String = str(entry.get("id", ""))
		var st: Dictionary = scenes_st.get(sid, {})
		var is_unlocked: bool = st.get("unlocked", sid == "solar-system")
		var is_active := sid == active_id
		var visited: bool = st.get("visited", false)
		var exists := FilePaths.scene_exists_for_catalog_entry(entry)
		var markers := ""
		if is_active:
			markers += "★ "
		if visited:
			markers += "✓ "
		if entry.get("speculative", false):
			markers += "[SPEC] "
		var lock := "🔓" if is_unlocked else "🔒"
		var file_mark := "📄" if exists else "⚠ missing"
		var line := "%d. %s%s%s — %s" % [
			int(entry.get("order_index", i)),
			markers,
			lock,
			str(entry.get("name", sid)),
			file_mark,
		]
		_campaign_scene_list.add_item(line)
		_campaign_scene_list.set_item_metadata(i, sid)
		if preserve != "" and sid == preserve:
			select_idx = i
		elif preserve == "" and select_idx < 0 and is_active:
			select_idx = i
	if select_idx >= 0:
		_campaign_scene_list.select(select_idx)
		_selected_campaign_id = str(_campaign_scene_list.get_item_metadata(select_idx))
	elif sorted.size() > 0:
		_selected_campaign_id = str(sorted[0].get("id", ""))

	_render_campaign_detail(state, catalog, surveys_map)
	_update_campaign_buttons(state, catalog)


func _catalog_entry(catalog: Array, scene_id: String) -> Dictionary:
	for entry in catalog:
		if entry is Dictionary and str(entry.get("id", "")) == scene_id:
			return entry
	return {}


func _render_campaign_detail(
	state: Dictionary,
	catalog: Array,
	surveys_map: Dictionary,
) -> void:
	if _campaign_detail == null:
		return
	var sid := _selected_campaign_id
	var entry := _catalog_entry(catalog, sid)
	if entry.is_empty():
		_campaign_detail.text = "[i]Select a scene in the list.[/i]"
		_campaign_cmd.text = ""
		return
	var camp: Dictionary = state.get("campaign", {})
	var st: Dictionary = camp.get("scenes", {}).get(sid, {})
	var is_unlocked: bool = st.get("unlocked", sid == "solar-system")
	var exists := FilePaths.scene_exists_for_catalog_entry(entry)
	var path := FilePaths.scene_path_for_catalog_entry(entry)

	var h := ""
	h += "[b]%s[/b] [color=#888888](%s)[/color]\n" % [entry.get("name", sid), sid]
	h += "[i]%s[/i]\n\n" % entry.get("description", "")
	h += entry.get("teaching_summary", "") + "\n\n"
	h += "Scale: %s\n" % entry.get("scale_description", "—")
	h += "Class: %s\n" % entry.get("scene_class", "—")
	h += "Unlock: %s\n" % entry.get("unlock_requirement", "starter")
	h += "Surveys: %s\n" % _survey_names(entry.get("recommended_survey_ids", []), surveys_map)
	var sigs: Array = entry.get("recommended_signal_modes", [])
	h += "Signals: %s\n" % (", ".join(sigs) if sigs.size() > 0 else "—")
	h += "File: %s\n" % ("[color=#88ff99]present[/color]" if exists else "[color=#ff8888]missing[/color]")
	h += "Path: [color=#aaaaaa]%s[/color]\n" % path
	_campaign_detail.text = h

	var gen := str(entry.get("generate_command", FilePaths.make_generate_command(sid)))
	var set_cmd := FilePaths.make_set_scene_command(sid)
	_campaign_cmd.text = (
		"[b]Generate[/b] (run in terminal):\n[color=#88ccff]%s[/color]\n\n"
		% gen
		+ "[b]Set active in Python state[/b]:\n[color=#88ccff]%s[/color]"
		% set_cmd
	)


func _update_campaign_buttons(state: Dictionary, catalog: Array) -> void:
	var entry := _catalog_entry(catalog, _selected_campaign_id)
	if entry.is_empty():
		_btn_campaign_load.disabled = true
		_btn_campaign_set.disabled = true
		_btn_campaign_both.disabled = true
		return
	var st: Dictionary = state.get("campaign", {}).get("scenes", {}).get(_selected_campaign_id, {})
	var is_unlocked: bool = st.get("unlocked", _selected_campaign_id == "solar-system")
	var exists := FilePaths.scene_exists_for_catalog_entry(entry)
	_btn_campaign_load.disabled = not is_unlocked or not exists
	_btn_campaign_set.disabled = not is_unlocked
	_btn_campaign_both.disabled = not is_unlocked or not exists


func _on_campaign_scene_selected(idx: int) -> void:
	if idx < 0:
		return
	_selected_campaign_id = str(_campaign_scene_list.get_item_metadata(idx))
	action_campaign_refresh.emit()


func _on_campaign_load_pressed() -> void:
	if _selected_campaign_id != "":
		action_campaign_load_scene.emit(_selected_campaign_id)


func _on_campaign_set_pressed() -> void:
	if _selected_campaign_id != "":
		action_campaign_set_active.emit(_selected_campaign_id)


func _on_campaign_both_pressed() -> void:
	if _selected_campaign_id != "":
		action_campaign_load_and_set.emit(_selected_campaign_id)


func _build_log_panel() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	panel.offset_top = -200
	panel.offset_bottom = 0
	panel.add_theme_stylebox_override("panel", _bg_style())
	_root.add_child(panel)

	var vb := VBoxContainer.new()
	panel.add_child(vb)
	vb.add_child(_label("Discovery Log", 11, TEXT_DIM))
	_log_text = RichTextLabel.new()
	_log_text.bbcode_enabled = true
	_log_text.scroll_following = true
	_log_text.custom_minimum_size = Vector2(0, 170)
	vb.add_child(_log_text)


func render_survey_hint(scene: Dictionary, state: Dictionary, surveys_map: Dictionary) -> void:
	if _survey_hint == null:
		return
	if not _SceneLoader.is_deep_field_scene(scene):
		_survey_hint.text = ""
		return
	var active: Variant = state.get("active_survey_id", null)
	if active != null and str(active) != "":
		_survey_hint.text = ""
		return
	var suggestions := PackedStringArray()
	for sid in ["deep_field_survey", "radio_sky_survey", "compact_object_search"]:
		var s: Dictionary = surveys_map.get(sid, {})
		if s.is_empty():
			continue
		if _SurveyEngine.status(s, state) == "available":
			suggestions.append(s.get("name", sid))
	if suggestions.is_empty():
		_survey_hint.text = (
			"[i]No deep-field survey active — unlock [b]space_optical[/b], [b]radio[/b], "
			"or [b]xray_gamma[/b] tiers (see Tech) to start Deep Field / Radio / Compact programs.[/i]"
		)
	else:
		_survey_hint.text = (
			"[color=#aaccee][b]Suggested surveys:[/b] %s — open the Surveys tab to start.[/color]"
			% ", ".join(suggestions)
		)


func set_scene_objects(
	objects: Array,
	state: Dictionary = {},
	scene: Dictionary = {},
	surveys_map: Dictionary = {},
) -> void:
	_all_objects = objects.duplicate()
	_state_for_filter = state
	_scene_for_filter = scene
	_surveys_map_for_filter = surveys_map
	_rebuild_object_list()


func _rebuild_object_list() -> void:
	_objects_list.clear()
	for o in _all_objects:
		if not (o is Dictionary):
			continue
		if not _passes_object_filter(o):
			continue
		var oid: String = str(o.get("id", ""))
		_objects_list.add_item("%s — %s" % [o.get("type", "?"), o.get("name", oid)])
		_objects_list.set_item_metadata(_objects_list.item_count - 1, oid)


func _object_confidence(oid: String) -> float:
	var disc: Dictionary = _state_for_filter.get("discoveries", {}).get(oid, {})
	return float(disc.get("confidence", 0.0))


func _passes_object_filter(o: Dictionary) -> bool:
	var oid: String = str(o.get("id", ""))
	var t: String = str(o.get("type", ""))
	var conf := _object_confidence(oid)
	var fi := _object_filter.selected if _object_filter else 0
	match fi:
		0:
			return true
		1:
			return conf < 0.25
		2:
			return conf >= 0.25 and conf < 0.75
		3:
			return conf >= 0.75
		4:
			return t in ["quasar", "black_hole", "magnetar", "lyman_alpha_blob"]
		5:
			var types: Array = _active_survey_target_types()
			if types.is_empty():
				return true
			return t in types
	return true


func _active_survey_target_types() -> Array:
	var sid: Variant = _state_for_filter.get("active_survey_id", null)
	if sid == null or str(sid) == "":
		return []
	var s: Dictionary = _surveys_map_for_filter.get(str(sid), {})
	var ta: Variant = s.get("target_object_types", [])
	return ta if ta is Array else []


func _on_object_filter_selected(_idx: int) -> void:
	_rebuild_object_list()




func render_detail(state: Dictionary, requirements_map: Dictionary) -> void:
	if _selected_id == "":
		_detail_text.text = "[i]Select an object in the list or click in the 3D view. Keys: F focus, R reset camera, L labels.[/i]"
		return
	var obj: Dictionary = _find_object(_selected_id)
	if obj.is_empty():
		_detail_text.text = ""
		return
	var disc: Dictionary = state.get("discoveries", {}).get(_selected_id, {})
	var conf: float = float(disc.get("confidence", 0.0))
	var label := DiscoveryEngine.confidence_label(conf)
	var lines := PackedStringArray()
	if conf >= 0.5:
		lines.append("[b]%s[/b]" % obj.get("name", _selected_id))
	else:
		lines.append("[b]Unclassified Source[/b]")
	lines.append("[color=#7799cc]Type:[/color] %s" % obj.get("type", "?"))
	lines.append("[color=#7799cc]Status:[/color] %s (%d%%)" % [label, int(round(conf * 100))])
	if disc.has("detected_signals") and disc["detected_signals"].size() > 0:
		lines.append("[color=#7799cc]Detected:[/color] %s" % ", ".join(disc["detected_signals"]))
	var req: Dictionary = requirements_map.get(obj.get("type", ""), {})
	if not req.is_empty():
		lines.append("[color=#7799cc]Required signals:[/color] %s" % ", ".join(req.get("required_signal_types", [])))
		if req.has("notes"):
			lines.append("[i]%s[/i]" % req["notes"])
	if obj.has("description") and obj["description"] != "":
		lines.append("")
		lines.append(obj["description"])
	if str(obj.get("type", "")) == "lyman_alpha_blob":
		lines.append("")
		lines.append(
			"[color=#99aacc][i]Visualization:[/i] LAB is rendered as layered translucent shells "
			"(false-color science metaphor), not a true Lyman-alpha radiative-transfer volume.[/color]"
		)
	var meta: Dictionary = _scene_for_filter.get("metadata", {})
	var teach: String = str(meta.get("teaching_summary", ""))
	if teach != "":
		lines.append("")
		lines.append("[i]%s[/i]" % teach)
	if obj.has("relationships") and (obj["relationships"] is Array) and obj["relationships"].size() > 0:
		lines.append("")
		lines.append("[color=#7799cc]Relationships:[/color]")
		for r in obj["relationships"]:
			if r is Dictionary:
				lines.append("  • %s → %s" % [r.get("relation", "?"), r.get("target_id", "?")])
	_detail_text.text = "\n".join(lines)


func render_tech_tree(state: Dictionary, tree: Array, modifiers_table: Array = []) -> void:
	var unlocked := {}
	for tid in state.get("unlocked_tiers", []):
		unlocked[tid] = true
	var active: String = state.get("active_telescope_tier", "")
	var lines := PackedStringArray()
	for t in tree:
		var spec := " [color=#cc8855][SPECULATIVE][/color]" if t.get("speculative", false) else ""
		var base_c: int = int(t.get("research_cost", 0))
		var eff_c: int = base_c
		if not modifiers_table.is_empty():
			eff_c = _EntityModifiers.effective_tier_cost(t, state, modifiers_table)
		if unlocked.has(t["id"]):
			var marker := "[color=#88ff99]●[/color]"
			if t["id"] == active:
				marker = "[color=#aaffaa]▶[/color]"
			lines.append("%s [b]%s[/b]%s" % [marker, t["name"], spec])
			var cost_note := "%d RP" % eff_c
			if eff_c != base_c:
				cost_note = "%d RP (base %d)" % [eff_c, base_c]
			lines.append("    sigs: %s · cost: %s · res: %.2f\"" % [
				", ".join(t.get("signal_types", [])),
				cost_note,
				float(t.get("resolution_arcsec", 0)),
			])
			if t["id"] != active:
				lines.append("    [url=set:%s]set active[/url]" % t["id"])
		else:
			var prereq_ok := true
			for p in t.get("prerequisites", []):
				if not unlocked.has(p):
					prereq_ok = false
					break
			var afford := int(state.get("research_points", 0)) >= eff_c
			lines.append("[color=#7788aa]○ [b]%s[/b]%s[/color]" % [t["name"], spec])
			var cost_line := "%d RP" % eff_c
			if eff_c != base_c:
				cost_line = "%d RP (base %d)" % [eff_c, base_c]
			lines.append("    cost: %s · prereq: %s" % [
				cost_line,
				", ".join(t.get("prerequisites", [])) if t.get("prerequisites", []).size() > 0 else "(none)",
			])
			if prereq_ok and afford:
				lines.append("    [url=unlock:%s]unlock[/url]" % t["id"])
		lines.append("")
	_tech_text.text = "\n".join(lines)


func render_surveys(state: Dictionary, programs: Array, programs_map: Dictionary, modifiers_table: Array = []) -> void:
	var lines := PackedStringArray()
	for s in programs:
		var status := SurveyEngine.status(s, state)
		var prog: Dictionary = state.get("survey_progress", {}).get(s["id"], {})
		var done := int(prog.get("discoveries_completed", 0))
		var goal := int(s.get("completion_goal", 1))
		var base_r: int = int(s.get("reward_research_points", 0))
		var eff_r: int = base_r
		if not modifiers_table.is_empty():
			eff_r = _EntityModifiers.effective_survey_reward(s, state, modifiers_table)
		var spec := " [color=#cc8855][SPECULATIVE][/color]" if s.get("speculative", false) else ""
		var marker := "○"
		var color := "#7788aa"
		match status:
			"available": marker = " · "; color = "#bbcce0"
			"active": marker = "▶"; color = "#aaffaa"
			"completed": marker = "✓"; color = "#88ff99"
			"locked": marker = "🔒"; color = "#5566aa"
		lines.append("[color=%s]%s [b]%s[/b]%s[/color]" % [color, marker, s["name"], spec])
		var rew_s := "+%d RP" % eff_r
		if eff_r != base_r:
			rew_s = "+%d RP (base %d)" % [eff_r, base_r]
		lines.append("    %d/%d · reward %s · status %s" % [done, goal, rew_s, status])
		if status == "available":
			lines.append("    [url=startsurvey:%s]start survey[/url]" % s["id"])
		if s.get("required_tier_ids", []).size() > 0:
			lines.append("    [color=#7788aa]requires tiers: %s[/color]" % ", ".join(s["required_tier_ids"]))
		lines.append("")
	_surveys_text.text = "\n".join(lines)


func render_milestones(state: Dictionary, milestones: Array, modifiers_table: Array = []) -> void:
	var lines := PackedStringArray()
	var achieved := []
	var remaining := []
	for m in milestones:
		var rec: Dictionary = state.get("milestones", {}).get(m["id"], {})
		if rec.get("achieved", false):
			achieved.append(m)
		else:
			remaining.append(m)
	lines.append("[b]Achieved (%d/%d)[/b]" % [achieved.size(), milestones.size()])
	for m in achieved:
		var spec := " [color=#cc8855][SPECULATIVE][/color]" if m.get("speculative", false) else ""
		var br := int(m.get("reward_research_points", 0))
		lines.append("[color=#88ff99]✓ %s[/color]%s — +%d RP" % [m["name"], spec, br])
		lines.append("   [color=#7788aa]%s[/color]" % m.get("description", ""))
	lines.append("")
	lines.append("[b]Remaining[/b]")
	for m in remaining:
		var spec2 := " [color=#cc8855][SPECULATIVE][/color]" if m.get("speculative", false) else ""
		var base_m: int = int(m.get("reward_research_points", 0))
		var eff_m: int = base_m
		if not modifiers_table.is_empty():
			eff_m = _EntityModifiers.effective_milestone_reward(m, state, modifiers_table)
		var ms := "+%d RP" % eff_m
		if eff_m != base_m:
			ms = "+%d RP (base %d)" % [eff_m, base_m]
		lines.append("[color=#7788aa]○ %s[/color]%s — %s" % [m["name"], spec2, ms])
		lines.append("   [color=#5566aa]%s[/color]" % m.get("description", ""))
	_milestones_text.text = "\n".join(lines)


func render_transients(
	state: Dictionary,
	defs: Array,
	scene: Dictionary,
	tech_tree: Array,
) -> void:
	var lines := PackedStringArray()
	var sid: String = str(scene.get("id", ""))
	var turn: int = int(state.get("turn", 0))
	state = _TransientEngine.update_states(state, defs)
	var events: Dictionary = state.get("transient_events", {})
	lines.append("[b]Scene %s — turn %d[/b]" % [sid, turn])
	var active := []
	var upcoming := []
	var expired := []
	var observed := []
	for d in defs:
		if not (d is Dictionary):
			continue
		if str(d.get("scene_id", "")) != sid:
			continue
		var eid: String = str(d.get("id", ""))
		var ts: Dictionary = events.get(eid, {})
		if bool(ts.get("reward_claimed", false)):
			observed.append(d)
		elif bool(ts.get("expired", false)):
			expired.append(d)
		elif bool(ts.get("active", false)):
			active.append(d)
		else:
			upcoming.append(d)
	for label_text in ["Active", "Upcoming", "Expired", "Observed"]:
		var bucket: Array = []
		match label_text:
			"Active":
				bucket = active
			"Upcoming":
				bucket = upcoming
			"Expired":
				bucket = expired
			"Observed":
				bucket = observed
		if bucket.is_empty():
			continue
		lines.append("")
		lines.append("[b]%s[/b]" % label_text)
		for d in bucket:
			var spec := " [color=#cc8855][SPECULATIVE][/color]" if d.get("speculative", false) else ""
			var chk := _TransientEngine.is_observable(scene, state, d, tech_tree)
			var ok := bool(chk.get("ok", false))
			var mark := "[color=#88ff99]●[/color]" if ok else "[color=#7788aa]○[/color]"
			lines.append(
				"%s %s%s — +%d RP (t%d–%d)" % [
					mark,
					d.get("name", d.get("id", "")),
					spec,
					int(d.get("reward_research_points", 0)),
					int(d.get("start_turn", 0)),
					int(d.get("start_turn", 0)) + int(d.get("duration_turns", 0)) - 1,
				]
			)
			lines.append(
				"   [color=#5566aa]tier %s · signals %s[/color]" % [
					d.get("minimum_telescope_tier", "?"),
					str(d.get("required_signal_types", [])),
				]
			)
			if not ok and label_text == "Active":
				lines.append("   [color=#aa7766]%s[/color]" % chk.get("reason", ""))
	_transients_text.text = "\n".join(lines)
	_selected_transient_id = ""
	_btn_observe_transient.disabled = true
	for d in active:
		var eid: String = str(d.get("id", ""))
		var chk2 := _TransientEngine.is_observable(scene, state, d, tech_tree)
		if bool(chk2.get("ok", false)):
			_selected_transient_id = eid
			_btn_observe_transient.disabled = false
			break


func _on_observe_transient_pressed() -> void:
	if _selected_transient_id != "":
		action_observe_transient.emit(_selected_transient_id)


func render_objectives(state: Dictionary, defs: Array) -> void:
	var lines := PackedStringArray()
	lines.append("[b]Tutorial objectives[/b]")
	var active_ids: Array = state.get("active_objective_ids", [])
	var objectives: Dictionary = state.get("objectives", {})
	for d in defs:
		if not (d is Dictionary):
			continue
		var oid: String = str(d.get("id", ""))
		if oid not in active_ids:
			continue
		lines.append("[color=#ffcc66]→ %s[/color]" % d.get("title", oid))
		lines.append("   [color=#7788aa]%s[/color]" % d.get("hint", d.get("description", "")))
		break
	var done := 0
	for d in defs:
		if not (d is Dictionary):
			continue
		var prog: Dictionary = objectives.get(str(d.get("id", "")), {})
		if str(prog.get("status", "")) == "completed":
			done += 1
	lines.append("")
	lines.append("[color=#7788aa]%d / %d completed[/color]" % [done, defs.size()])
	_objectives_text.text = "\n".join(lines)


func add_log(text: String, color: String = "#bbcce0") -> void:
	var ts := Time.get_time_string_from_system()
	_log_text.append_text("[color=#5566aa]%s[/color]  [color=%s]%s[/color]\n" % [ts, color, text])


func selected_id() -> String:
	return _selected_id


func set_selected(object_id: String) -> void:
	_selected_id = object_id
	for i in range(_objects_list.item_count):
		if str(_objects_list.get_item_metadata(i)) == object_id:
			_objects_list.select(i)
			return


func _on_object_selected(idx: int) -> void:
	var oid := str(_objects_list.get_item_metadata(idx))
	_selected_id = oid
	action_select_object.emit(oid)


func _on_meta_clicked(meta: Variant) -> void:
	var s := str(meta)
	if s.begins_with("startsurvey:"):
		action_start_survey.emit(s.substr("startsurvey:".length()))
	elif s.begins_with("unlock:"):
		action_unlock_tier.emit(s.substr("unlock:".length()))
	elif s.begins_with("set:"):
		action_set_active_tier.emit(s.substr("set:".length()))


func _find_object(oid: String) -> Dictionary:
	for o in _all_objects:
		if o is Dictionary and o.get("id", "") == oid:
			return o
	return {}


func _label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l


func _bg_style() -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = PANEL_BG
	s.border_color = Color(0.18, 0.22, 0.32)
	s.border_width_left = 1
	s.border_width_right = 1
	s.border_width_top = 1
	s.border_width_bottom = 1
	s.content_margin_left = 12
	s.content_margin_right = 12
	s.content_margin_top = 8
	s.content_margin_bottom = 8
	return s
