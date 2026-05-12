"""Tests for discovery rules and observation."""

from universe.game.discovery import (
    calculate_identification_confidence,
    get_discovery_requirements,
    observe_scene,
)
from universe.game.models import ResearchState
from universe.game.tech_tree import unlock_tier
from universe.models import ObjectType
from universe.procedural.solar_system import generate_solar_system


def _solar_scene():
    return generate_solar_system(seed="test")


def _state_with_tiers(*tier_ids: str, rp: int = 10000) -> ResearchState:
    """Build a state with the given tiers unlocked (in order)."""
    state = ResearchState(research_points=rp)
    for tid in tier_ids:
        state, _ = unlock_tier(state, tid)
    return state


class TestDiscoveryRequirements:
    def test_requirements_exist(self):
        reqs = get_discovery_requirements()
        assert len(reqs) > 0

    def test_all_main_types_covered(self):
        reqs = get_discovery_requirements()
        types = {r.object_type for r in reqs}
        for expected in ["star", "planet", "moon", "galaxy", "quasar", "black_hole", "magnetar"]:
            assert expected in types, f"Missing requirement for {expected}"


class TestNakedEyeDiscovery:
    def test_can_detect_sun(self):
        scene = _solar_scene()
        state = ResearchState()
        sun = next(o for o in scene.objects if o.id == "sun")
        conf, signals = calculate_identification_confidence(sun, state)
        assert conf > 0.0
        assert "visible_light" in signals

    def test_can_detect_moon(self):
        scene = _solar_scene()
        state = ResearchState()
        moon_obj = next(o for o in scene.objects if o.id == "moon")
        conf, _ = calculate_identification_confidence(moon_obj, state)
        assert conf > 0.0

    def test_can_detect_bright_planets(self):
        scene = _solar_scene()
        state = ResearchState()
        venus = next(o for o in scene.objects if o.id == "planet-venus")
        conf, _ = calculate_identification_confidence(venus, state)
        assert conf > 0.0


class TestGroundOpticalDiscovery:
    def test_improves_planet_confidence(self):
        scene = _solar_scene()
        naked = ResearchState()
        optical = _state_with_tiers("ground_optical")

        mars = next(o for o in scene.objects if o.id == "planet-mars")
        conf_naked, _ = calculate_identification_confidence(mars, naked)
        conf_optical, _ = calculate_identification_confidence(mars, optical)
        assert conf_optical >= conf_naked


class TestDeepSkyDiscovery:
    def test_black_hole_not_trivially_optical(self):
        """Early optical telescopes alone should not confidently detect black holes."""
        from universe.procedural.region import generate_scene_001

        scene = generate_scene_001(seed="test-bh", num_galaxies=5, num_nodes=4)
        state = _state_with_tiers("ground_optical")
        bh = next(o for o in scene.objects if o.type == ObjectType.BLACK_HOLE)
        conf, _ = calculate_identification_confidence(bh, state)
        assert conf < 0.50, "BH should not be confidently detected with early optical"

    def test_xray_detects_magnetar(self):
        from universe.procedural.region import generate_scene_001

        scene = generate_scene_001(seed="test-mag", num_galaxies=5, num_nodes=4)
        state = _state_with_tiers(
            "ground_optical", "improved_ground", "space_optical", "radio", "xray_gamma"
        )
        mag = next(o for o in scene.objects if o.type == ObjectType.MAGNETAR)
        conf, signals = calculate_identification_confidence(mag, state)
        assert conf > 0.0, "X-ray should detect magnetar"
        assert "xray" in signals


class TestMultiMessengerBonus:
    def test_more_signals_increases_confidence(self):
        from universe.procedural.region import generate_scene_001

        scene = generate_scene_001(seed="test-mm", num_galaxies=5, num_nodes=4)
        quasar = next(o for o in scene.objects if o.type == ObjectType.QUASAR)

        state_basic = _state_with_tiers("ground_optical", "improved_ground", "space_optical")
        state_multi = _state_with_tiers(
            "ground_optical", "improved_ground", "space_optical", "radio", "xray_gamma"
        )

        conf_basic, _ = calculate_identification_confidence(quasar, state_basic)
        conf_multi, _ = calculate_identification_confidence(quasar, state_multi)
        assert conf_multi >= conf_basic


class TestObserveScene:
    def test_observe_returns_results(self):
        scene = _solar_scene()
        state = ResearchState()
        new_state, results = observe_scene(scene, state)
        assert len(results) > 0
        assert new_state.research_points > 0

    def test_observe_updates_discoveries(self):
        scene = _solar_scene()
        state = ResearchState()
        new_state, _ = observe_scene(scene, state)
        assert len(new_state.discoveries) > 0

    def test_second_observe_no_duplicates(self):
        scene = _solar_scene()
        state = ResearchState()
        state2, results1 = observe_scene(scene, state)
        state3, results2 = observe_scene(scene, state2)
        # Second pass should yield no new discoveries (same tier, same scene)
        assert len(results2) == 0 or all(not r.newly_discovered for r in results2)
