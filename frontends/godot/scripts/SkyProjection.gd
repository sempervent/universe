class_name SkyProjection
extends RefCounted
## Deterministic sky angles and dome placement for Observatory View.
## Observer is fixed at the origin; targets sit on an inner celestial sphere.

const ECLIPTIC_TILT := 0.409  # ~23.5° in radians for layout flavor
const DOME_RADIUS := 420.0

const _SOLAR_AZ := {
	"sun": 0.15,
	"moon": 0.42,
	"planet-mercury": 0.55,
	"planet-venus": 0.72,
	"planet-mars": 1.85,
	"planet-jupiter": 2.35,
	"planet-saturn": 2.95,
	"planet-uranus": 3.55,
	"planet-neptune": 4.1,
	"asteroid-belt": 2.1,
	"comet-halley-proxy": 4.8,
}


static func object_to_sky_angles(obj: Dictionary, scene: Dictionary) -> Vector2:
	# Returns (azimuth, elevation) in radians.
	if SceneLoader.is_solar_system_scene(scene):
		return _solar_angles(obj)
	return _deep_field_angles(obj, scene)


static func project_target_at_time(obj: Dictionary, scene: Dictionary, state: Dictionary) -> Vector3:
	var angles: Vector2 = object_to_sky_angles_timed(obj, scene, state)
	return dome_position(angles.x, angles.y)


static func object_to_sky_angles_timed(obj: Dictionary, scene: Dictionary, state: Dictionary) -> Vector2:
	var base: Vector2 = object_to_sky_angles(obj, scene)
	var frac: float = ObservatoryTime.get_fraction(state)
	var sidereal: float = frac * TAU
	var oid: String = str(obj.get("id", ""))

	if SceneLoader.is_solar_system_scene(scene):
		if oid == "sun":
			var el_s: float = clampf(sin((frac - 0.25) * TAU) * 0.82 + 0.12, -0.2, 1.2)
			var az_s: float = 0.2 + sidereal * 0.08
			return Vector2(az_s, el_s)
		var drift: float = _daily_drift_rate(obj)
		var az: float = base.x + sidereal * (1.0 + drift * 0.02)
		var el: float = base.y + sin(sidereal + _hash01(oid) * TAU) * 0.04
		if oid == "moon":
			el = 0.25 + sin(sidereal * 2.1) * 0.35
			az = 0.45 + sidereal * 1.8
		return Vector2(az, el)

	var az_df: float = base.x + sidereal * 0.04
	var el_df: float = base.y
	return Vector2(az_df, el_df)


static func is_above_horizon(angles: Vector2) -> bool:
	return angles.y > 0.06


static func _daily_drift_rate(obj: Dictionary) -> float:
	var oid: String = str(obj.get("id", ""))
	if oid.begins_with("moon-"):
		return 3.5
	if oid == "moon":
		return 2.8
	match str(obj.get("type", "")):
		"planet":
			if oid in ["planet-mercury", "planet-venus"]:
				return 1.6
			return 0.6
		"asteroid", "comet":
			return 1.2
		_:
			return 0.3


static func direction_from_angles(az: float, el: float) -> Vector3:
	var cel: float = cos(el)
	var y: float = sin(el)
	return Vector3(cel * cos(az), y, cel * sin(az)).normalized()


static func dome_position(az: float, el: float, radius: float = DOME_RADIUS) -> Vector3:
	return direction_from_angles(az, el) * radius


static func angular_size_on_dome(obj: Dictionary, scene: Dictionary) -> float:
	var props: Dictionary = obj.get("properties", {}) as Dictionary
	var arcsec: float = float(props.get("angular_size_arcsec", 0.0))
	if arcsec > 0.0:
		# Map arcsec to apparent dome size (clamped).
		return clampf(1.2 + log(1.0 + arcsec) * 0.35, 0.35, 14.0)
	var otype: String = str(obj.get("type", ""))
	if SceneLoader.is_solar_system_scene(scene):
		match otype:
			"star":
				return 9.0
			"moon":
				return 7.0
			"planet":
				return 2.2
			"satellite":
				return 1.0
			"asteroid", "comet":
				return 0.55
			_:
				return 0.8
	match otype:
		"galaxy":
			return 0.9
		"quasar":
			return 1.4
		"lyman_alpha_blob":
			return 5.5
		"black_hole":
			return 1.1
		"magnetar":
			return 1.0
		"cosmic_web_node":
			return 0.7
		_:
			return 0.65


static func apparent_brightness(obj: Dictionary) -> float:
	var props: Dictionary = obj.get("properties", {}) as Dictionary
	if props.has("apparent_magnitude"):
		var mag: float = float(props.get("apparent_magnitude", 10.0))
		return clampf(1.0 - (mag + 10.0) / 30.0, 0.05, 1.0)
	return 0.65


static func _solar_angles(obj: Dictionary) -> Vector2:
	var oid: String = str(obj.get("id", ""))
	if _SOLAR_AZ.has(oid):
		var az: float = float(_SOLAR_AZ[oid])
		var el: float = 0.12 + 0.08 * sin(az * 0.7)
		if oid == "sun":
			el = 0.55
		elif oid == "moon":
			el = 0.38
			az = 0.5
		return Vector2(az, el)
	var props: Dictionary = obj.get("properties", {}) as Dictionary
	var au: float = float(props.get("distance_au", 1.0))
	var phase: float = atan2(au, 1.0) * 0.35 + _hash01(oid) * TAU
	var el: float = clampf(ECLIPTIC_TILT * sin(phase) + 0.18, 0.08, 1.1)
	return Vector2(phase, el)


static func _deep_field_angles(obj: Dictionary, scene: Dictionary) -> Vector2:
	var pos: Dictionary = obj.get("position_mpc", {}) as Dictionary
	var v := Vector3(
		float(pos.get("x", 0.0)),
		float(pos.get("y", 0.0)),
		float(pos.get("z", 0.0)),
	)
	if v.length_squared() < 1e-12:
		var oid: String = str(obj.get("id", ""))
		var h: float = _hash01(oid)
		return Vector2(h * TAU, 0.25 + 0.5 * _hash01(oid + "_el"))
	var dir: Vector3 = v.normalized()
	# Map 3D direction to azimuth / elevation.
	var el: float = asin(clampf(dir.y, -1.0, 1.0))
	var az: float = atan2(dir.z, dir.x)
	return Vector2(az, el)


static func _hash01(s: String) -> float:
	var h: int = hash(s)
	return float(abs(h % 10007)) / 10007.0
