"""Tests for milestones."""

from universe.game.discovery import observe_scene
from universe.game.entity import make_research_entity
from universe.game.milestones import (
    claim_milestone_rewards,
    evaluate_milestones,
    get_default_milestones,
    get_milestone_by_id,
)
from universe.game.models import ResearchState
from universe.game.tech_tree import unlock_tier
from universe.procedural.solar_system import generate_solar_system


class TestMilestoneCatalogue:
    def test_unique_ids(self):
        ids = [m.id for m in get_default_milestones()]
        assert len(ids) == len(set(ids))

    def test_now_scope_is_speculative(self):
        m = get_milestone_by_id("now_scope_first_light")
        assert m is not None
        assert m.speculative is True

    def test_other_milestones_not_speculative(self):
        speculative_ids = {"now_scope_first_light", "first_speculative_transient"}
        for m in get_default_milestones():
            if m.id not in speculative_ids:
                assert m.speculative is False, f"{m.id} unexpectedly speculative"

    def test_unknown_milestone_returns_none(self):
        assert get_milestone_by_id("nope") is None


class TestNamedEntityMilestone:
    def test_default_name_does_not_trigger(self):
        state = ResearchState()
        new_state, achieved = evaluate_milestones(state)
        assert all(a.milestone.id != "named_entity" for a in achieved)

    def test_custom_name_triggers(self):
        entity = make_research_entity("Hydrogen Ghost Institute")
        state = ResearchState(research_entity=entity)
        new_state, achieved = evaluate_milestones(state)
        ids = [a.milestone.id for a in achieved]
        assert "named_entity" in ids


class TestObservationMilestones:
    def test_first_light_after_observe(self):
        scene = generate_solar_system(seed="m1")
        state = ResearchState()
        new_state, _ = observe_scene(scene, state)
        assert new_state.milestones.get("first_light").achieved is True

    def test_first_planet_milestone_solar_system(self):
        scene = generate_solar_system(seed="m2")
        state = ResearchState()
        new_state, _ = observe_scene(scene, state)
        assert new_state.milestones.get("first_planet").achieved is True
        assert new_state.milestones.get("first_moon").achieved is True

    def test_first_upgrade_milestone(self):
        state = ResearchState(research_points=20)
        state, _ = unlock_tier(state, "ground_optical")
        new_state, achieved = evaluate_milestones(state)
        ids = [a.milestone.id for a in achieved]
        assert "first_upgrade" in ids


class TestRewardClaimingIdempotent:
    def test_reward_credited_once(self):
        scene = generate_solar_system(seed="m3")
        state = ResearchState()
        new_state, _ = observe_scene(scene, state)
        rp_after = new_state.research_points
        # Claim again — no new rewards expected
        new_state2, achieved = claim_milestone_rewards(new_state)
        assert achieved == []
        assert new_state2.research_points == rp_after

    def test_milestone_record_persists_with_reward_claimed(self):
        scene = generate_solar_system(seed="m4")
        state = ResearchState()
        new_state, _ = observe_scene(scene, state)
        for record in new_state.milestones.values():
            if record.achieved:
                assert record.reward_claimed is True


class TestDeepSkyMilestones:
    def test_first_deep_sky_object_via_scene_001(self):
        from universe.procedural.region import generate_scene_001

        scene = generate_scene_001(seed="ms-deep", num_galaxies=10, num_nodes=5)
        state = ResearchState(research_points=10000)
        for tid in ["ground_optical", "improved_ground", "space_optical"]:
            state, _ = unlock_tier(state, tid)
        new_state, _ = observe_scene(scene, state)
        # Should achieve first_deep_sky_object since galaxies/quasars present
        assert new_state.milestones.get("first_deep_sky_object") is not None
        assert new_state.milestones["first_deep_sky_object"].achieved is True


class TestBackwardCompatNoMilestones:
    def test_old_state_loads_with_empty_milestones(self):
        import json

        old_json = json.dumps({
            "research_points": 0,
            "unlocked_tiers": ["naked_eye"],
            "active_telescope_tier": "naked_eye",
            "known_signal_types": ["visible_light"],
            "discoveries": {},
        })
        state = ResearchState.model_validate_json(old_json)
        assert state.milestones == {}
        assert state.turn == 0
