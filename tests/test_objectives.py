"""Tests for first-run tutorial objectives."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from universe.cli import main
from universe.game.entity import make_research_entity
from universe.game.models import ObjectiveStatus, ResearchState
from universe.game.objectives import (
    ensure_objective_progress,
    evaluate_objectives,
    get_default_objectives,
    get_objective,
)
from universe.game.scenes import ensure_campaign_state, update_scene_unlocks
from universe.game.transients import ensure_transient_states, observe_transient_event, update_transient_event_states
from universe.procedural.registry import generate_scene_by_id


class TestObjectiveCatalog:
    def test_ids_unique(self):
        ids = [o.id for o in get_default_objectives()]
        assert len(ids) == len(set(ids))

    def test_first_objective_active_on_fresh_state(self):
        state = ensure_objective_progress(ResearchState())
        assert state.active_objective_ids == ["name_research_entity"]
        assert state.objectives["name_research_entity"].status == ObjectiveStatus.ACTIVE

    def test_definitions_serialize(self):
        for o in get_default_objectives():
            data = o.model_dump(mode="json")
            assert data["id"] == o.id


class TestObjectiveEvaluation:
    def _fresh(self) -> ResearchState:
        return ensure_objective_progress(
            ensure_transient_states(ensure_campaign_state(ResearchState()))
        )

    def test_named_entity_completes(self):
        state = self._fresh()
        entity = make_research_entity(name="Hydrogen Ghost Institute")
        state = state.model_copy(update={"research_entity": entity})
        state, done = evaluate_objectives(state)
        assert any(c.definition.id == "name_research_entity" for c in done)

    def test_observe_local_sky_completes(self):
        state = self._fresh()
        entity = make_research_entity(name="Sky Lab")
        state = state.model_copy(update={"research_entity": entity})
        state, _ = evaluate_objectives(state)
        from universe.game.models import DiscoveryRecord

        state = state.model_copy(
            update={
                "discoveries": {
                    "sun": DiscoveryRecord(
                        object_id="sun",
                        object_type="star",
                        confidence=0.6,
                    )
                }
            }
        )
        state, done = evaluate_objectives(state)
        ids = {c.definition.id for c in done}
        assert "observe_local_sky" in ids or state.objectives["observe_local_sky"].status == ObjectiveStatus.COMPLETED

    def test_first_light_survey_completes(self):
        from universe.game.models import DiscoveryRecord, SurveyProgress

        state = self._fresh()
        entity = make_research_entity(name="Survey Lab")
        state = state.model_copy(update={"research_entity": entity})
        state, _ = evaluate_objectives(state)
        state = state.model_copy(
            update={
                "discoveries": {
                    "sun": DiscoveryRecord(object_id="sun", object_type="star", confidence=0.6)
                },
                "survey_progress": {
                    "local_sky_survey": SurveyProgress(
                        survey_id="local_sky_survey",
                        discoveries_completed=5,
                        completed=True,
                    )
                },
            }
        )
        state, _ = evaluate_objectives(state)
        state, done = evaluate_objectives(state)
        assert "complete_first_light_survey" in {c.definition.id for c in done} or state.objectives[
            "complete_first_light_survey"
        ].status == ObjectiveStatus.COMPLETED

    def test_ground_optical_completes(self):
        from universe.game.models import DiscoveryRecord, SurveyProgress

        state = self._fresh()
        entity = make_research_entity(name="Tier Lab")
        state = state.model_copy(
            update={
                "research_entity": entity,
                "discoveries": {
                    "sun": DiscoveryRecord(object_id="sun", object_type="star", confidence=0.6)
                },
                "survey_progress": {
                    "local_sky_survey": SurveyProgress(
                        survey_id="local_sky_survey",
                        discoveries_completed=5,
                        completed=True,
                    )
                },
                "unlocked_tiers": ["naked_eye", "ground_optical"],
            }
        )
        state, done = evaluate_objectives(state)
        prog = state.objectives.get("unlock_ground_optical")
        assert prog is not None and prog.status == ObjectiveStatus.COMPLETED

    def test_transient_objective_completes(self):
        from universe.game.models import DiscoveryRecord, ObjectiveProgress, SurveyProgress

        scene = generate_scene_by_id("solar-system", seed="local-sky")
        state = self._fresh()
        entity = make_research_entity(name="Transient Lab")
        objectives = dict(state.objectives)
        for oid in [
            "name_research_entity",
            "observe_local_sky",
            "complete_first_light_survey",
            "unlock_ground_optical",
        ]:
            objectives[oid] = ObjectiveProgress(
                objective_id=oid,
                status=ObjectiveStatus.COMPLETED,
                completed_turn=1,
                reward_claimed=True,
            )
        state = state.model_copy(
            update={
                "research_entity": entity,
                "objectives": objectives,
                "active_objective_ids": ["observe_first_transient"],
                "discoveries": {
                    "sun": DiscoveryRecord(object_id="sun", object_type="star", confidence=0.6)
                },
                "survey_progress": {
                    "local_sky_survey": SurveyProgress(
                        survey_id="local_sky_survey",
                        discoveries_completed=5,
                        completed=True,
                    )
                },
                "turn": 3,
                "unlocked_tiers": ["naked_eye", "ground_optical"],
                "active_telescope_tier": "ground_optical",
            }
        )
        state = update_transient_event_states(state)
        state, result, err = observe_transient_event(scene, state, "solar_flare_001")
        assert result is not None and not err
        state, done = evaluate_objectives(state, scene)
        assert "observe_first_transient" in {c.definition.id for c in done} or state.objectives[
            "observe_first_transient"
        ].status == ObjectiveStatus.COMPLETED

    def test_scene_001_unlock_completes(self):
        from universe.game.models import DiscoveryRecord, ObjectiveProgress, SurveyProgress

        state = self._fresh()
        entity = make_research_entity(name="Scene Lab")
        objectives = dict(state.objectives)
        for oid in [
            "name_research_entity",
            "observe_local_sky",
            "complete_first_light_survey",
            "unlock_ground_optical",
            "observe_first_transient",
            "unlock_space_optical",
        ]:
            objectives[oid] = ObjectiveProgress(
                objective_id=oid,
                status=ObjectiveStatus.COMPLETED,
                completed_turn=1,
                reward_claimed=True,
            )
        state = state.model_copy(
            update={
                "research_entity": entity,
                "objectives": objectives,
                "discoveries": {
                    "sun": DiscoveryRecord(object_id="sun", object_type="star", confidence=0.6)
                },
                "survey_progress": {
                    "local_sky_survey": SurveyProgress(
                        survey_id="local_sky_survey",
                        discoveries_completed=5,
                        completed=True,
                    )
                },
                "unlocked_tiers": ["naked_eye", "ground_optical", "improved_ground", "space_optical"],
            }
        )
        state, _ = update_scene_unlocks(state)
        state, _ = evaluate_objectives(state)
        cs = state.campaign.scenes.get("scene-001")
        assert cs is not None and cs.unlocked
        assert state.objectives["unlock_scene_001"].status == ObjectiveStatus.COMPLETED

    def test_deep_field_discovery_completes(self):
        from universe.game.models import DiscoveryRecord

        state = self._fresh()
        entity = make_research_entity(name="Deep Lab")
        state = state.model_copy(
            update={
                "research_entity": entity,
                "active_survey_id": "deep_field_survey",
                "survey_progress": {
                    "deep_field_survey": {
                        "survey_id": "deep_field_survey",
                        "discoveries_completed": 1,
                        "completed": False,
                    }
                },
                "discoveries": {
                    "g1": DiscoveryRecord(
                        object_id="g1",
                        object_type="galaxy",
                        confidence=0.8,
                    )
                },
            }
        )
        from universe.game.models import ObjectiveProgress

        objectives = dict(state.objectives)
        for oid in [
            "name_research_entity",
            "observe_local_sky",
            "complete_first_light_survey",
            "unlock_ground_optical",
            "observe_first_transient",
            "unlock_space_optical",
            "unlock_scene_001",
            "switch_to_scene_001",
            "start_deep_field_survey",
        ]:
            objectives[oid] = ObjectiveProgress(
                objective_id=oid,
                status=ObjectiveStatus.COMPLETED,
                completed_turn=1,
                reward_claimed=True,
            )
        state = state.model_copy(update={"objectives": objectives})
        state, done = evaluate_objectives(state)
        final = get_objective("first_deep_field_discovery")
        assert final is not None
        assert state.objectives[final.id].status == ObjectiveStatus.COMPLETED

    def test_rewards_claimed_once(self):
        state = self._fresh()
        entity = make_research_entity(name="Test Institute")
        state = state.model_copy(update={"research_entity": entity, "research_points": 0})
        state, done = evaluate_objectives(state)
        rp1 = state.research_points
        state, done2 = evaluate_objectives(state)
        assert done2 == []
        assert state.research_points == rp1

    def test_out_of_order_catch_up(self):
        from universe.game.models import DiscoveryRecord

        state = self._fresh()
        entity = make_research_entity(name="Fast Track Lab")
        from universe.game.models import SurveyProgress

        state = state.model_copy(
            update={
                "research_entity": entity,
                "unlocked_tiers": ["naked_eye", "ground_optical", "improved_ground", "space_optical"],
                "discoveries": {
                    "sun": DiscoveryRecord(object_id="sun", object_type="star", confidence=0.8),
                    "g1": DiscoveryRecord(object_id="g1", object_type="galaxy", confidence=0.9),
                },
                "survey_progress": {
                    "local_sky_survey": SurveyProgress(
                        survey_id="local_sky_survey",
                        discoveries_completed=5,
                        completed=True,
                    ),
                },
            },
        )
        state, _ = update_scene_unlocks(state)
        state, done = evaluate_objectives(state)
        assert len(done) >= 4


class TestObjectiveCLI:
    def test_game_objectives_command(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            out = Path("state.json")
            runner.invoke(
                main,
                [
                    "game",
                    "init",
                    "--name",
                    "CLI Lab",
                    "--entity-type",
                    "private_institute",
                    "--out",
                    str(out),
                ],
            )
            result = runner.invoke(main, ["game", "objectives", "--state", str(out)])
            assert result.exit_code == 0
            assert "Tutorial Objectives" in result.output
            assert "Observe the Local Sky" in result.output or "Name Your" in result.output

    def test_status_shows_active_objective(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            out = Path("state.json")
            runner.invoke(
                main,
                [
                    "game",
                    "init",
                    "--name",
                    "Status Lab",
                    "--entity-type",
                    "private_institute",
                    "--out",
                    str(out),
                ],
            )
            result = runner.invoke(main, ["game", "status", "--state", str(out)])
            assert result.exit_code == 0
            assert "Tutorial objective" in result.output


class TestObjectiveHTML:
    def test_html_embeds_objectives(self):
        from universe.game.telescope_ui import export_telescope_ui

        scene = generate_scene_by_id("solar-system", seed="ui-obj")
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=path)
            html = path.read_text(encoding="utf-8")
            assert "OBJECTIVES" in html or "__OBJECTIVES_DATA__" not in html
            assert "tab-objectives" in html
            assert "Tutorial Objectives" in html or "renderObjectives" in html


class TestObjectivePlaytest:
    def test_ladder_summary_includes_tutorial_fields(self):
        from universe.game.playtest import run_playtest

        from universe.game.playtest import get_scenario_by_id

        run = run_playtest(
            get_scenario_by_id("campaign_instrument_ladder"),
            entity_type="private_institute",
            seed="local-sky",
            max_turns=80,
        )
        assert "tutorial_objectives_completed_count" in run.summary
        assert run.summary["tutorial_objectives_completed_count"] >= 1
