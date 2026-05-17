"""Tests for survey programs."""

from universe.game.discovery import observe_scene
from universe.game.models import ResearchState
from universe.game.surveys import (
    SurveyProgramStatus,
    available_surveys,
    claim_survey_reward,
    get_default_survey_programs,
    get_survey_by_id,
    start_survey,
    survey_status,
)
from universe.game.tech_tree import unlock_tier
from universe.procedural.solar_system import generate_solar_system


def _state_with_tiers(*tier_ids: str, rp: int = 10000) -> ResearchState:
    state = ResearchState(research_points=rp)
    for tid in tier_ids:
        state, _ = unlock_tier(state, tid)
    return state


class TestSurveyCatalogue:
    def test_unique_ids(self):
        ids = [s.id for s in get_default_survey_programs()]
        assert len(ids) == len(set(ids))

    def test_prerequisites_reference_valid_tiers(self):
        from universe.game.tech_tree import get_default_tech_tree

        valid_tiers = {t.id for t in get_default_tech_tree()}
        for s in get_default_survey_programs():
            for tid in s.required_tier_ids:
                assert tid in valid_tiers, f"Survey {s.id} references unknown tier {tid}"

    def test_local_sky_survey_starts_available(self):
        state = ResearchState()
        s = get_survey_by_id("local_sky_survey")
        assert s is not None
        assert survey_status(state, s) == SurveyProgramStatus.AVAILABLE

    def test_now_scope_survey_is_speculative(self):
        s = get_survey_by_id("now_scope_first_light")
        assert s is not None
        assert s.speculative is True

    def test_get_unknown_survey_returns_none(self):
        assert get_survey_by_id("nonexistent_survey_xyz") is None


class TestStartSurvey:
    def test_start_available_survey(self):
        state = ResearchState()
        new_state, msg = start_survey(state, "local_sky_survey")
        assert new_state.active_survey_id == "local_sky_survey"
        assert "Started" in msg

    def test_cannot_start_locked_survey(self):
        state = ResearchState()
        new_state, msg = start_survey(state, "deep_field_survey")
        assert new_state.active_survey_id is None
        assert "locked" in msg.lower() or "missing" in msg.lower()

    def test_cannot_start_unknown_survey(self):
        state = ResearchState()
        _, msg = start_survey(state, "totally_made_up")
        assert "Unknown" in msg

    def test_state_immutable_on_start(self):
        state = ResearchState()
        start_survey(state, "local_sky_survey")
        assert state.active_survey_id is None


class TestSurveyProgress:
    def test_local_sky_progresses_on_observation(self):
        scene = generate_solar_system(seed="t1")
        state = ResearchState()
        state, _ = start_survey(state, "local_sky_survey")
        new_state, results = observe_scene(scene, state)
        prog = new_state.survey_progress.get("local_sky_survey")
        assert prog is not None
        assert prog.discoveries_completed >= 5  # solar system has many qualifying objects
        assert prog.completed is True
        assert prog.claimed_reward is True

    def test_completed_survey_awards_rp_once(self):
        scene = generate_solar_system(seed="t2")
        state = ResearchState()
        state, _ = start_survey(state, "local_sky_survey")
        new_state, _ = observe_scene(scene, state)
        rp_after_complete = new_state.research_points
        # Re-claim should be a no-op
        new_state2, msg = claim_survey_reward(new_state, "local_sky_survey")
        assert new_state2.research_points == rp_after_complete
        assert "already claimed" in msg

    def test_non_matching_discoveries_do_not_progress(self):
        # Local sky targets star/planet/moon — observatory is a discovery
        # but should not contribute to progress (not in target set)
        scene = generate_solar_system(seed="t3")
        state = ResearchState()
        state, _ = start_survey(state, "local_sky_survey")
        new_state, _ = observe_scene(scene, state)
        prog = new_state.survey_progress["local_sky_survey"]
        # observatory exists in scene but is not a target
        for oid in prog.discovered_object_ids:
            disc = new_state.discoveries.get(oid)
            assert disc is not None
            assert disc.object_type in {"star", "planet", "moon"}

    def test_no_active_survey_means_no_progress(self):
        scene = generate_solar_system(seed="t4")
        state = ResearchState()
        new_state, _ = observe_scene(scene, state)
        assert new_state.survey_progress == {}

    def test_survey_progress_does_not_double_count_same_object(self):
        scene = generate_solar_system(seed="t5")
        state = ResearchState()
        state, _ = start_survey(state, "local_sky_survey")
        new_state, _ = observe_scene(scene, state)
        prog = new_state.survey_progress["local_sky_survey"]
        # Re-observe with same state (no upgrades) should not add new entries
        # because everything is already at max confidence and recorded.
        new_state2, _ = observe_scene(scene, new_state)
        prog2 = new_state2.survey_progress["local_sky_survey"]
        assert prog2.discoveries_completed == prog.discoveries_completed


class TestAvailableSurveys:
    def test_only_naked_eye_initially(self):
        state = ResearchState()
        avail = available_surveys(state)
        ids = [s.id for s in avail]
        assert "local_sky_survey" in ids
        assert "deep_field_survey" not in ids

    def test_more_unlocked_after_optical(self):
        state = _state_with_tiers("ground_optical")
        avail = available_surveys(state)
        ids = [s.id for s in avail]
        assert "local_sky_survey" in ids
        # planetary_census requires ground_optical
        assert "planetary_census" in ids

    def test_active_survey_excluded(self):
        state = ResearchState()
        state, _ = start_survey(state, "local_sky_survey")
        avail = available_surveys(state)
        ids = [s.id for s in avail]
        assert "local_sky_survey" not in ids


class TestBackwardCompatNoSurveys:
    def test_old_state_loads_with_no_survey_fields(self):
        import json

        old_json = json.dumps({
            "research_points": 5,
            "unlocked_tiers": ["naked_eye"],
            "active_telescope_tier": "naked_eye",
            "known_signal_types": ["visible_light"],
            "discoveries": {},
        })
        state = ResearchState.model_validate_json(old_json)
        assert state.active_survey_id is None
        assert state.survey_progress == {}
        assert state.turn == 0
