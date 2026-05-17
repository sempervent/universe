"""Simplified observatory local time — not real ephemerides."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ObservatoryTimeState(BaseModel):
    """Local observing clock for day/night and sky motion."""

    local_day_fraction: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="0=midnight, 0.25=sunrise-ish, 0.5=noon, 0.75=sunset",
    )
    time_scale: float = Field(default=1.0, ge=0.0)
    paused: bool = False
    day_index: int = 0
    location_name: str = "Earth Observatory"
    latitude_deg: float = 35.96
    longitude_deg: float = -83.92
    timezone_offset_hours: float = -5.0
    current_datetime_iso: str | None = None


def default_observatory_time() -> ObservatoryTimeState:
    return ObservatoryTimeState(local_day_fraction=0.5, paused=False)


def ensure_observatory_time(state_dict: dict) -> dict:
    """Normalize observatory_time on a raw state dict (load path)."""
    raw = state_dict.get("observatory_time")
    if raw is None:
        state_dict["observatory_time"] = default_observatory_time().model_dump()
        return state_dict
    if isinstance(raw, dict):
        state_dict["observatory_time"] = ObservatoryTimeState.model_validate(raw).model_dump()
    return state_dict


def get_observatory_time(state) -> ObservatoryTimeState:
    from universe.game.models import ResearchState

    if isinstance(state, ResearchState):
        ot = getattr(state, "observatory_time", None)
        if ot is None:
            return default_observatory_time()
        if isinstance(ot, ObservatoryTimeState):
            return ot
        return ObservatoryTimeState.model_validate(ot)
    raw = state.get("observatory_time", {}) if isinstance(state, dict) else {}
    if not raw:
        return default_observatory_time()
    return ObservatoryTimeState.model_validate(raw)


def _fraction_from_state(state) -> float:
    return get_observatory_time(state).local_day_fraction


def is_daytime(state) -> bool:
    f = _fraction_from_state(state)
    return 0.22 <= f <= 0.78


def sun_altitude_factor(state) -> float:
    """0 at night, ~1 at local noon."""
    f = _fraction_from_state(state)
    return max(0.0, sin((f - 0.25) * TAU))


def sky_brightness_factor(state) -> float:
    """0 = dark night, 1 = full daylight."""
    return clamp01(sun_altitude_factor(state) * 1.15)


def advance_observatory_time(state, hours: float = 1.0):
    from universe.game.models import ResearchState

    ot = get_observatory_time(state)
    frac_delta = hours / 24.0
    new_frac = ot.local_day_fraction + frac_delta
    day_index = ot.day_index
    while new_frac >= 1.0:
        new_frac -= 1.0
        day_index += 1
    while new_frac < 0.0:
        new_frac += 1.0
        day_index = max(0, day_index - 1)
    updated = ot.model_copy(
        update={"local_day_fraction": new_frac, "day_index": day_index}
    )
    if isinstance(state, ResearchState):
        return state.model_copy(update={"observatory_time": updated})
    out = dict(state)
    out["observatory_time"] = updated.model_dump()
    return out


def set_observatory_paused(state, paused: bool):
    from universe.game.models import ResearchState

    ot = get_observatory_time(state).model_copy(update={"paused": paused})
    if isinstance(state, ResearchState):
        return state.model_copy(update={"observatory_time": ot})
    out = dict(state)
    out["observatory_time"] = ot.model_dump()
    return out


def set_time_scale(state, scale: float):
    from universe.game.models import ResearchState

    ot = get_observatory_time(state).model_copy(update={"time_scale": max(0.0, scale)})
    if isinstance(state, ResearchState):
        return state.model_copy(update={"observatory_time": ot})
    out = dict(state)
    out["observatory_time"] = ot.model_dump()
    return out


def sidereal_rotation_hours(state) -> float:
    """Hours since local midnight for sky rotation."""
    return get_observatory_time(state).local_day_fraction * 24.0


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def sin(x: float) -> float:
    import math

    return math.sin(x)


TAU = 6.283185307179586
