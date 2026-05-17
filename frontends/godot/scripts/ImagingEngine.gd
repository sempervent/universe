class_name ImagingEngine
extends RefCounted
## Imaging capture/composite — mirrors universe.game.imaging (subset).


static func load_catalog(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var p: Variant = JSON.parse_string(f.get_as_text())
	return p if p is Array else []


static func catalog_by_id(catalog: Array) -> Dictionary:
	var m := {}
	for c in catalog:
		if c is Dictionary and c.has("id"):
			m[c["id"]] = c
	return m


static func unlocked_camera_ids(state: Dictionary, catalog: Array) -> Array:
	var out: Array = []
	for cid in state.get("unlocked_camera_ids", []):
		if cid not in out:
			out.append(cid)
	var tiers: Array = state.get("unlocked_tiers", [])
	for c in catalog:
		if c is Dictionary and str(c.get("required_tier_id", "")) in tiers:
			var id: String = str(c.get("id", ""))
			if id != "" and id not in out:
				out.append(id)
	return out


static func capture(
	scene_id: String,
	state: Dictionary,
	object_id: String,
	object_name: String,
	object_type: String,
	signal_mode: String,
	camera_id: String,
	confidence: float,
	catalog: Array,
) -> Dictionary:
	var cats: Dictionary = catalog_by_id(catalog)
	if not cats.has(camera_id):
		return {"ok": false, "message": "Unknown camera."}
	var cam: Dictionary = cats[camera_id]
	var unlocked: Array = unlocked_camera_ids(state, catalog)
	if camera_id not in unlocked:
		return {
			"ok": false,
			"message": "Camera locked — requires tier %s." % cam.get("required_tier_id", "?"),
		}
	var sigs: Array = cam.get("signal_types", [])
	if signal_mode not in sigs:
		return {"ok": false, "message": "Camera does not support this signal mode."}
	var known: Array = state.get("known_signal_types", [])
	if signal_mode not in known:
		return {"ok": false, "message": "Signal mode not unlocked."}

	var penalty: float = 1.0
	var block: String = ""
	if signal_mode in ["visible_light", "infrared", "ultraviolet"]:
		var bright: float = ObservatoryTime.sky_brightness(state)
		if bright > 0.35 and object_type in ["galaxy", "quasar", "lyman_alpha_blob", "cosmic_web_node"]:
			return {"ok": false, "message": "Daylight blocks faint optical/deep-sky capture."}
		if bright > 0.5:
			penalty = 0.35

	var quality: float = clampf(
		0.35 * float(cam.get("resolution_rating", 0.5))
			+ 0.35 * float(cam.get("sensitivity_rating", 0.5))
			+ 0.2 * confidence
			+ 0.1 * penalty,
		0.05,
		1.0,
	)
	var img_id: String = "img-%s" % str(Time.get_ticks_usec())
	var ot: Dictionary = state.get("observatory_time", {})
	var img := {
		"id": img_id,
		"object_id": object_id,
		"scene_id": scene_id,
		"object_name": object_name,
		"captured_turn": int(state.get("turn", 0)),
		"local_day_fraction": float(ot.get("local_day_fraction", 0.5)),
		"signal_modes": [signal_mode],
		"camera_ids": [camera_id],
		"image_type": "single_signal",
		"quality_score": quality,
		"confidence_at_capture": confidence,
		"title": "%s · %s" % [object_name, signal_mode],
		"description": "Captured with %s." % cam.get("name", camera_id),
		"metadata": {},
	}
	var images: Dictionary = state.get("captured_images", {}).duplicate(true)
	images[img_id] = img
	var new_state: Dictionary = state.duplicate(true)
	new_state["captured_images"] = images
	return {"ok": true, "state": new_state, "image": img, "message": "Captured (quality %d%%)." % int(round(quality * 100))}


static func combine(state: Dictionary, image_ids: Array) -> Dictionary:
	if image_ids.size() < 2:
		return {"ok": false, "message": "Need two or more images."}
	var images: Dictionary = state.get("captured_images", {})
	var refs: Array = []
	for iid in image_ids:
		if not images.has(iid):
			return {"ok": false, "message": "Missing image %s." % iid}
		refs.append(images[iid])
	var obj_id: String = str((refs[0] as Dictionary).get("object_id", ""))
	for r in refs:
		if str((r as Dictionary).get("object_id", "")) != obj_id:
			return {"ok": false, "message": "Composite requires same object."}
	var sigs := {}
	for r in refs:
		for s in (r as Dictionary).get("signal_modes", []):
			sigs[s] = true
	if sigs.size() < 2:
		return {"ok": false, "message": "Need different signal modes."}
	var quality: float = 0.0
	for r in refs:
		quality += float((r as Dictionary).get("quality_score", 0.0))
	quality = clampf(quality / float(refs.size()) + 0.15 * float(sigs.size()), 0.1, 1.0)
	var img_id: String = "img-%s" % str(Time.get_ticks_usec())
	var img := {
		"id": img_id,
		"object_id": obj_id,
		"scene_id": (refs[0] as Dictionary).get("scene_id", ""),
		"object_name": (refs[0] as Dictionary).get("object_name", ""),
		"captured_turn": int(state.get("turn", 0)),
		"local_day_fraction": (refs[0] as Dictionary).get("local_day_fraction", 0.5),
		"signal_modes": sigs.keys(),
		"camera_ids": [],
		"image_type": "composite",
		"quality_score": quality,
		"confidence_at_capture": 0.0,
		"title": "%s · composite" % (refs[0] as Dictionary).get("object_name", ""),
		"description": "Multi-instrument composite.",
		"metadata": {"source_image_ids": image_ids},
	}
	var all_imgs: Dictionary = images.duplicate(true)
	all_imgs[img_id] = img
	var new_state: Dictionary = state.duplicate(true)
	new_state["captured_images"] = all_imgs
	return {"ok": true, "state": new_state, "image": img, "message": "Composite created."}
