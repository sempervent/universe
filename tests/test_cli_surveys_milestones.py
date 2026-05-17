"""Smoke tests for the new game CLI subcommands."""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from universe.cli import main
from universe.export.scene_json import export_scene
from universe.procedural.solar_system import generate_solar_system


def _setup(tmpdir: Path) -> tuple[Path, Path]:
    """Generate a solar-system scene + game state, return (scene_path, state_path)."""
    scene = generate_solar_system(seed="cli-surveys")
    artifacts = export_scene(scene, tmpdir / "scene")
    state_path = tmpdir / "state.json"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "game", "init",
            "--name", "Hydrogen Ghost Institute",
            "--entity-type", "private_institute",
            "--motto", "Listening for the old light.",
            "--out", str(state_path),
        ],
    )
    assert result.exit_code == 0, result.output
    return artifacts["scene.json"], state_path


class TestGameSurveysCommand:
    def test_surveys_lists_local_sky(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            _, state_path = _setup(Path(tmp))
            result = runner.invoke(main, ["game", "surveys", "--state", str(state_path)])
            assert result.exit_code == 0, result.output
            assert "First Light Survey" in result.output
            assert "local_sky_survey" in result.output


class TestStartSurveyCommand:
    def test_start_local_sky_survey(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            _, state_path = _setup(Path(tmp))
            result = runner.invoke(
                main,
                ["game", "start-survey", "--state", str(state_path), "--survey", "local_sky_survey"],
            )
            assert result.exit_code == 0, result.output
            data = json.loads(state_path.read_text())
            assert data["active_survey_id"] == "local_sky_survey"


class TestObservationProgressesSurvey:
    def test_observe_completes_survey_and_milestones(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            scene_path, state_path = _setup(Path(tmp))
            runner.invoke(main, [
                "game", "start-survey",
                "--state", str(state_path),
                "--survey", "local_sky_survey",
            ])
            result = runner.invoke(main, [
                "game", "observe",
                "--scene", str(scene_path),
                "--state", str(state_path),
                "--out", str(state_path),
            ])
            assert result.exit_code == 0, result.output
            data = json.loads(state_path.read_text())
            prog = data["survey_progress"]["local_sky_survey"]
            assert prog["completed"] is True
            assert prog["claimed_reward"] is True
            # First-light + first_planet + first_moon + named_entity at minimum
            achieved = [r for r in data["milestones"].values() if r["achieved"]]
            assert len(achieved) >= 3


class TestMilestonesCommand:
    def test_milestones_lists_all(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            _, state_path = _setup(Path(tmp))
            result = runner.invoke(main, ["game", "milestones", "--state", str(state_path)])
            assert result.exit_code == 0, result.output
            assert "First Light" in result.output
            assert "Founding Charter" in result.output
            assert "Now-Scope First Light" in result.output


class TestClaimMilestonesCommand:
    def test_claim_after_naming_triggers_named_entity(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            _, state_path = _setup(Path(tmp))
            result = runner.invoke(main, [
                "game", "claim-milestones",
                "--state", str(state_path),
                "--out", str(state_path),
            ])
            assert result.exit_code == 0, result.output
            data = json.loads(state_path.read_text())
            assert data["milestones"]["named_entity"]["achieved"] is True
            assert data["research_points"] >= 5

    def test_idempotent_second_claim(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            _, state_path = _setup(Path(tmp))
            runner.invoke(main, [
                "game", "claim-milestones",
                "--state", str(state_path),
                "--out", str(state_path),
            ])
            rp_first = json.loads(state_path.read_text())["research_points"]
            result = runner.invoke(main, [
                "game", "claim-milestones",
                "--state", str(state_path),
                "--out", str(state_path),
            ])
            assert result.exit_code == 0, result.output
            assert "No newly achieved" in result.output
            rp_second = json.loads(state_path.read_text())["research_points"]
            assert rp_second == rp_first


class TestStatusShowsSurveysAndMilestones:
    def test_status_includes_survey_milestone_counts(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            scene_path, state_path = _setup(Path(tmp))
            runner.invoke(main, [
                "game", "start-survey", "--state", str(state_path),
                "--survey", "local_sky_survey",
            ])
            runner.invoke(main, [
                "game", "observe",
                "--scene", str(scene_path),
                "--state", str(state_path),
                "--out", str(state_path),
            ])
            result = runner.invoke(main, ["game", "status", "--state", str(state_path)])
            assert result.exit_code == 0, result.output
            assert "Surveys completed" in result.output
            assert "Milestones achieved" in result.output


class TestReportIncludesSurveysAndMilestones:
    def test_report_has_survey_and_milestone_sections(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            scene_path, state_path = _setup(Path(tmp))
            runner.invoke(main, [
                "game", "start-survey", "--state", str(state_path),
                "--survey", "local_sky_survey",
            ])
            runner.invoke(main, [
                "game", "observe",
                "--scene", str(scene_path),
                "--state", str(state_path),
                "--out", str(state_path),
            ])
            report_path = Path(tmp) / "report.md"
            result = runner.invoke(main, [
                "game", "report",
                "--scene", str(scene_path),
                "--state", str(state_path),
                "--out", str(report_path),
            ])
            assert result.exit_code == 0, result.output
            content = report_path.read_text()
            assert "Survey Programs" in content
            assert "Achieved Milestones" in content
            assert "First Light Survey" in content
