"""Registry of procedural scene generators by campaign / CLI id."""

from __future__ import annotations

from collections.abc import Callable

from universe.models import SceneRegion
from universe.procedural.cosmic_web_map import generate_cosmic_web_map
from universe.procedural.now_scope_field import generate_now_scope_anomaly_field
from universe.procedural.radio_cmb import generate_radio_cmb_survey
from universe.procedural.region import generate_scene_001
from universe.procedural.solar_system import generate_solar_system
from universe.procedural.stellar_remnants import generate_stellar_remnant_field

SceneGenerator = Callable[..., SceneRegion]

_GENERATORS: dict[str, SceneGenerator] = {
    "solar-system": generate_solar_system,
    "starter": generate_solar_system,
    "scene-001": generate_scene_001,
    "radio-cmb-survey": generate_radio_cmb_survey,
    "stellar-remnant-field": generate_stellar_remnant_field,
    "cosmic-web-map": generate_cosmic_web_map,
    "now-scope-anomaly-field": generate_now_scope_anomaly_field,
}

CAMPAIGN_SCENE_IDS: frozenset[str] = frozenset(_GENERATORS.keys()) - frozenset({"starter"})


def generate_scene_by_id(scene_id: str, *, seed: str, **kwargs) -> SceneRegion:
    """Dispatch to the procedural generator for *scene_id*."""
    fn = _GENERATORS.get(scene_id)
    if fn is None:
        raise ValueError(
            f"Unknown scene id: {scene_id}. Known: {sorted(CAMPAIGN_SCENE_IDS)}"
        )
    if scene_id == "scene-001":
        return fn(seed=seed, **kwargs)
    return fn(seed=seed)
