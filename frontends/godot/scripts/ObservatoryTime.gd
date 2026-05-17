class_name ObservatoryTime
extends RefCounted
## Simplified local observatory clock (mirrors Python ObservatoryTimeState).

const DEFAULT_LAT := 35.96
const DEFAULT_LON := -83.92


static func default_dict() -> Dictionary:
	return {
		"local_day_fraction": 0.5,
		"time_scale": 1.0,
		"paused": false,
		"day_index": 0,
		"location_name": "Earth Observatory",
		"latitude_deg": DEFAULT_LAT,
		"longitude_deg": DEFAULT_LON,
		"timezone_offset_hours": -5.0,
		"current_datetime_iso": "",
	}


static func ensure(state: Dictionary) -> Dictionary:
	if not state.has("observatory_time") or not (state["observatory_time"] is Dictionary):
		state["observatory_time"] = default_dict()
		return state
	var ot: Dictionary = state["observatory_time"]
	if not ot.has("local_day_fraction"):
		ot["local_day_fraction"] = 0.5
	if not ot.has("paused"):
		ot["paused"] = false
	if not ot.has("time_scale"):
		ot["time_scale"] = 1.0
	if not ot.has("day_index"):
		ot["day_index"] = 0
	state["observatory_time"] = ot
	return state


static func get_fraction(state: Dictionary) -> float:
	return float(state.get("observatory_time", {}).get("local_day_fraction", 0.5))


static func is_paused(state: Dictionary) -> bool:
	return bool(state.get("observatory_time", {}).get("paused", false))


static func get_time_scale(state: Dictionary) -> float:
	return float(state.get("observatory_time", {}).get("time_scale", 1.0))


static func is_daytime(state: Dictionary) -> bool:
	var f: float = get_fraction(state)
	return f >= 0.22 and f <= 0.78


static func sun_altitude_factor(state: Dictionary) -> float:
	var f: float = get_fraction(state)
	return maxf(0.0, sin((f - 0.25) * TAU))


static func sky_brightness(state: Dictionary) -> float:
	return clampf(sun_altitude_factor(state) * 1.15, 0.0, 1.0)


static func advance_hours(state: Dictionary, hours: float) -> Dictionary:
	var ot: Dictionary = state.get("observatory_time", default_dict()).duplicate(true)
	var frac: float = float(ot.get("local_day_fraction", 0.5)) + hours / 24.0
	var day: int = int(ot.get("day_index", 0))
	while frac >= 1.0:
		frac -= 1.0
		day += 1
	while frac < 0.0:
		frac += 1.0
		day = maxi(0, day - 1)
	ot["local_day_fraction"] = frac
	ot["day_index"] = day
	var out: Dictionary = state.duplicate(true)
	out["observatory_time"] = ot
	return out


static func set_paused(state: Dictionary, paused: bool) -> Dictionary:
	var out: Dictionary = state.duplicate(true)
	var ot: Dictionary = state.get("observatory_time", default_dict()).duplicate(true)
	ot["paused"] = paused
	out["observatory_time"] = ot
	return out


static func set_time_scale(state: Dictionary, scale: float) -> Dictionary:
	var out: Dictionary = state.duplicate(true)
	var ot: Dictionary = state.get("observatory_time", default_dict()).duplicate(true)
	ot["time_scale"] = maxf(0.0, scale)
	out["observatory_time"] = ot
	return out


static func sidereal_hours(state: Dictionary) -> float:
	return get_fraction(state) * 24.0


static func time_label(state: Dictionary) -> String:
	var f: float = get_fraction(state)
	var h: int = int(floor(f * 24.0)) % 24
	var m: int = int(floor(fmod(f * 24.0, 1.0) * 60.0))
	var phase: String = "Night"
	if is_daytime(state):
		phase = "Day" if f < 0.45 or f > 0.55 else "Twilight"
	return "Day %d · %02d:%02d · %s" % [
		int(state.get("observatory_time", {}).get("day_index", 0)),
		h,
		m,
		phase,
	]
