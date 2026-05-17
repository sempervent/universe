"""Tests for progression guidance hints."""

from universe.game.discovery import observe_scene
from universe.game.guidance import get_guidance_hints, solar_system_mostly_exhausted
from universe.game.models import ResearchState
from universe.game.surveys import start_survey
from universe.game.tech_tree import unlock_tier
from universe.procedural.solar_system import generate_solar_system


def _exhausted_solar_state(scene) -> ResearchState:
    state = ResearchState(research_points=500)
    state, _ = start_survey(state, "local_sky_survey")
    state, _ = observe_scene(scene, state)
    for tid in ("ground_optical", "improved_ground", "space_optical"):
        state, _ = unlock_tier(state, tid)
    state, _ = observe_scene(scene, state)
    assert "space_optical" in state.unlocked_tiers
    return state


class TestGuidanceHints:
    def test_solar_exhausted_deep_field_ready(self):
        scene = generate_solar_system(seed="guidance-df")
        state = _exhausted_solar_state(scene)
        assert solar_system_mostly_exhausted(scene, state)
        ids = {h.id for h in get_guidance_hints(scene, state)}
        assert "solar_exhausted_deep_field_ready" in ids

    def test_solar_exhausted_need_upgrade_without_space(self):
        scene = generate_solar_system(seed="guidance-up")
        state = ResearchState()
        state, _ = observe_scene(scene, state)
        for _ in range(5):
            state, _ = observe_scene(scene, state)
        ids = {h.id for h in get_guidance_hints(scene, state)}
        assert "solar_exhausted_need_upgrade" in ids
        assert "solar_exhausted_deep_field_ready" not in ids

    def test_now_scope_hint_without_speculative_discovery(self):
        from universe.procedural.region import generate_scene_001

        scene = generate_scene_001(seed="guidance-now")
        state = ResearchState(research_points=5000)
        for tid in (
            "naked_eye",
            "ground_optical",
            "improved_ground",
            "space_optical",
            "radio",
            "xray_gamma",
            "interferometer",
            "gravitational_wave",
            "neutrino_cosmic_ray",
            "multi_messenger",
            "dark_matter_mapper",
            "now_scope",
        ):
            state, _ = unlock_tier(state, tid)
        assert "now_scope" in state.unlocked_tiers
        ids = {h.id for h in get_guidance_hints(scene, state)}
        assert "now_scope_needs_speculative_targets" in ids
