"""Tests for balance tuning: surveys, milestones, speculative anomaly."""

from universe.game.discovery import calculate_identification_confidence, observe_scene
from universe.game.milestones import evaluate_milestones, get_milestone_by_id
from universe.game.models import ResearchState
from universe.game.surveys import get_survey_by_id, start_survey
from universe.game.tech_tree import unlock_tier
from universe.procedural.region import generate_scene_001
from universe.procedural.solar_system import generate_solar_system
from universe.models import ObjectType


class TestFirstLightSurvey:
    def test_survey_renamed_and_goal_eight(self):
        s = get_survey_by_id("local_sky_survey")
        assert s is not None
        assert s.name == "First Light Survey"
        assert s.completion_goal == 8
        assert s.reward_research_points == 8

    def test_citizen_bonus_not_on_small_surveys(self):
        from universe.game.entity import make_research_entity
        from universe.game.surveys import update_survey_progress_for_discovery

        survey = get_survey_by_id("small_bodies_watch")
        assert survey is not None
        assert survey.completion_goal < 8
        state = ResearchState(
            research_entity=make_research_entity("CSN", entity_type="citizen_science_network"),
        )
        state = state.model_copy(update={"active_survey_id": survey.id})
        state, _ = update_survey_progress_for_discovery(
            state,
            object_id="ast-1",
            object_type="asteroid",
            detected_signals=["visible_light"],
            confidence=0.8,
            scene_id="solar-system",
        )
        prog = state.survey_progress[survey.id]
        assert prog.discoveries_completed == 1


class TestDeepFieldMilestone:
    def test_first_deep_field_ready_after_space_optical(self):
        scene = generate_solar_system(seed="milestone-df")
        state = ResearchState(research_points=500)
        state, _ = observe_scene(scene, state)
        state, _ = unlock_tier(state, "ground_optical")
        state, _ = unlock_tier(state, "improved_ground")
        state, _ = unlock_tier(state, "space_optical")
        prog = state.survey_progress.get("local_sky_survey")
        if prog is None or not prog.completed:
            state, _ = start_survey(state, "local_sky_survey")
            state, _ = observe_scene(scene, state)
        evaluate_milestones(state)
        rec = state.milestones.get("first_deep_field_ready")
        assert rec is not None and rec.achieved
        m = get_milestone_by_id("first_deep_field_ready")
        assert m is not None
        assert 10 <= m.reward_research_points <= 20


class TestSpeculativeAnomaly:
    def test_scene_001_includes_anomaly(self):
        scene = generate_scene_001(seed="spec-anom")
        anomaly = next(
            (o for o in scene.objects if o.type == ObjectType.SPECULATIVE_ANOMALY),
            None,
        )
        assert anomaly is not None
        assert anomaly.id == "spec-now-anomaly-001"

    def test_now_scope_detects_anomaly_not_naked_eye(self):
        scene = generate_scene_001(seed="spec-det")
        anomaly = next(o for o in scene.objects if o.id == "spec-now-anomaly-001")
        naked = ResearchState()
        conf_naked, _ = calculate_identification_confidence(anomaly, naked)
        assert conf_naked == 0.0

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
        conf_now, signals = calculate_identification_confidence(anomaly, state)
        assert conf_now > 0.0
        assert "speculative_now_signal" in signals
