"""Tests for follow-up observation diminishing returns."""

from universe.game.discovery import observe_scene
from universe.game.models import ResearchState
from universe.game.tech_tree import unlock_tier
from universe.procedural.solar_system import generate_solar_system


class TestFollowupResearch:
    def test_first_followup_awards_small_rp(self):
        scene = generate_solar_system(seed="followup-1")
        state = ResearchState()
        state, results1 = observe_scene(scene, state)
        assert results1
        rp_after_first = state.research_points
        state, _ = unlock_tier(state, "ground_optical")
        state2, results2 = observe_scene(scene, state)
        followups = [r for r in results2 if r.message.startswith("Follow-up:")]
        assert followups
        assert state2.research_points > rp_after_first
        assert state2.research_points - rp_after_first <= len(scene.objects) * 5

    def test_followup_caps_per_object(self):
        scene = generate_solar_system(seed="followup-cap")
        state = ResearchState()
        state, _ = observe_scene(scene, state)
        sun_id = "sun"
        for _ in range(5):
            state, results = observe_scene(scene, state)
            followups = [r for r in results if r.object_id == sun_id and "Follow-up" in r.message]
            if not followups:
                break
        assert state.followup_observation_counts.get(sun_id, 0) <= 2

    def test_no_infinite_rp_loop(self):
        scene = generate_solar_system(seed="followup-loop")
        state = ResearchState()
        state, _ = observe_scene(scene, state)
        rp0 = state.research_points
        for _ in range(20):
            state, _ = observe_scene(scene, state)
        assert state.research_points < rp0 + 200

    def test_backward_compatible_state_loads(self):
        import json

        old = json.dumps(
            {
                "research_points": 0,
                "unlocked_tiers": ["naked_eye"],
                "active_telescope_tier": "naked_eye",
                "known_signal_types": ["visible_light"],
                "discoveries": {},
            }
        )
        state = ResearchState.model_validate_json(old)
        assert state.followup_observation_counts == {}
        assert state.consecutive_no_rp_turns == 0
