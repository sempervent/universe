"""Tests for balance playtest instrumentation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from universe.cli import main
from universe.game.playtest import (
    KNOWN_SCENE_IDS,
    get_default_scenarios,
    get_scenario_by_id,
    load_scene,
    run_playtest,
)
from universe.game.telemetry import PlaytestEvent, PlaytestRun
from universe.game.models import ResearchState


class TestTelemetryModels:
    def test_playtest_event_serializes(self):
        before = ResearchState(research_points=10)
        after = ResearchState(research_points=15, turn=1)
        ev = PlaytestEvent.from_state_delta(
            turn=1,
            event_type="discover_object",
            entity_type="backyard_observatory",
            state_before=before,
            state_after=after,
            message="test",
            object_id="sun",
        )
        data = json.loads(ev.model_dump_json())
        assert data["delta_research_points"] == 5
        assert data["research_points_before"] == 10
        assert data["research_points_after"] == 15

    def test_playtest_run_serializes(self):
        state = ResearchState()
        run = PlaytestRun(
            id="abc",
            seed="local-sky",
            entity_name="Test",
            entity_type="custom",
            scenario_id="solar_tutorial_basic",
            events=[],
            final_state=state,
            summary={"turns_played": 0},
        )
        data = json.loads(run.model_dump_json())
        assert data["scenario_id"] == "solar_tutorial_basic"
        assert data["final_state"]["research_points"] == 0


class TestScenarios:
    def test_default_scenarios_unique_ids(self):
        ids = [s.id for s in get_default_scenarios()]
        assert len(ids) == len(set(ids))

    def test_scenarios_reference_valid_scenes(self):
        for s in get_default_scenarios():
            assert s.max_turns > 0
            for scene_id in s.scene_sequence:
                assert scene_id in KNOWN_SCENE_IDS

    def test_get_scenario_by_id(self):
        assert get_scenario_by_id("solar_tutorial_basic") is not None
        assert get_scenario_by_id("nonexistent") is None


class TestAutoplayer:
    def test_greedy_observes_solar_system(self):
        sc = get_scenario_by_id("solar_tutorial_basic")
        assert sc is not None
        run = run_playtest(sc, entity_type="backyard_observatory", seed="playtest-test")
        assert run.summary["turns_played"] > 0
        assert len(run.events) > 0
        discovery_events = [
            e for e in run.events
            if e.event_type in (
                "discover_object",
                "observe_object",
                "confirm_object",
                "characterize_object",
            )
        ]
        assert discovery_events, run.events[:5]

    def test_greedy_unlocks_ground_optical_when_balance_allows(self):
        sc = get_scenario_by_id("solar_tutorial_basic")
        assert sc is not None
        run = run_playtest(
            sc, entity_type="backyard_observatory", seed="playtest-test", max_turns=80
        )
        tiers = run.summary.get("tier_unlock_turn") or {}
        assert "ground_optical" in tiers or "improved_ground" in tiers

    def test_no_infinite_loop_respects_max_turns(self):
        sc = get_scenario_by_id("solar_tutorial_basic")
        assert sc is not None
        run = run_playtest(sc, entity_type="custom", seed="x", max_turns=12)
        assert run.summary["turns_played"] <= 12

    def test_deterministic_same_seed(self):
        sc = get_scenario_by_id("solar_tutorial_basic")
        assert sc is not None
        a = run_playtest(sc, entity_type="university_lab", seed="deterministic")
        b = run_playtest(sc, entity_type="university_lab", seed="deterministic")
        assert a.id == b.id
        assert a.summary["final_rp"] == b.summary["final_rp"]
        assert a.summary["tier_unlock_turn"] == b.summary["tier_unlock_turn"]

    def test_different_entity_types_can_differ(self):
        sc = get_scenario_by_id("solar_tutorial_basic")
        assert sc is not None
        backyard = run_playtest(sc, entity_type="backyard_observatory", seed="entity-compare")
        citizen = run_playtest(sc, entity_type="citizen_science_network", seed="entity-compare")
        assert backyard.entity_type != citizen.entity_type
        # At least one of RP curve or tier timing should differ with modifiers.
        assert (
            backyard.summary["final_rp"] != citizen.summary["final_rp"]
            or backyard.summary.get("tier_unlock_turn")
            != citizen.summary.get("tier_unlock_turn")
            or backyard.summary.get("survey_complete_turn")
            != citizen.summary.get("survey_complete_turn")
        )


class TestPlaytestCLI:
    def test_playtest_writes_run_json(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run.json"
            result = runner.invoke(
                main,
                [
                    "game",
                    "playtest",
                    "--scenario",
                    "solar_tutorial_basic",
                    "--entity-type",
                    "backyard_observatory",
                    "--seed",
                    "cli-playtest",
                    "--max-turns",
                    "15",
                    "--out",
                    str(out),
                    "--no-events",
                ],
            )
            assert result.exit_code == 0, result.output
            assert out.exists()
            data = json.loads(out.read_text())
            assert data["scenario_id"] == "solar_tutorial_basic"

    def test_playtest_matrix_writes_summary(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "matrix"
            result = runner.invoke(
                main,
                [
                    "game",
                    "playtest-matrix",
                    "--out",
                    str(out_dir),
                    "--scenario",
                    "solar_tutorial_basic",
                    "--entity-type",
                    "custom",
                    "--entity-type",
                    "backyard_observatory",
                    "--max-turns",
                    "10",
                    "--no-deep-field",
                ],
            )
            assert result.exit_code == 0, result.output
            summary = out_dir / "matrix-summary.json"
            assert summary.exists()
            data = json.loads(summary.read_text())
            assert data["run_count"] == 2

    def test_balance_report_writes_markdown(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            matrix_dir = Path(tmp) / "matrix"
            runner.invoke(
                main,
                [
                    "game",
                    "playtest-matrix",
                    "--out",
                    str(matrix_dir),
                    "--scenario",
                    "solar_tutorial_basic",
                    "--entity-type",
                    "custom",
                    "--max-turns",
                    "8",
                    "--no-deep-field",
                ],
            )
            report_path = Path(tmp) / "balance-report.md"
            result = runner.invoke(
                main,
                [
                    "game",
                    "balance-report",
                    "--input",
                    str(matrix_dir),
                    "--out",
                    str(report_path),
                ],
            )
            assert result.exit_code == 0, result.output
            text = report_path.read_text()
            assert "Telescope Tier Unlock Timing" in text
            assert "Warnings" in text

    def test_balance_report_campaign_ladder_when_present(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            matrix_dir = Path(tmp) / "matrix"
            runner.invoke(
                main,
                [
                    "game",
                    "playtest",
                    "--scenario",
                    "campaign_instrument_ladder",
                    "--entity-type",
                    "custom",
                    "--seed",
                    "ladder-report",
                    "--max-turns",
                    "25",
                    "--out",
                    str(matrix_dir / "ladder.json"),
                    "--no-events",
                ],
            )
            report_path = Path(tmp) / "balance-report.md"
            result = runner.invoke(
                main,
                [
                    "game",
                    "balance-report",
                    "--input",
                    str(matrix_dir),
                    "--out",
                    str(report_path),
                ],
            )
            assert result.exit_code == 0, result.output
            text = report_path.read_text()
            assert "Campaign Ladder Analysis" in text
            assert "now-scope-anomaly-field" in text


class TestLoadScene:
    def test_load_solar_system(self):
        scene = load_scene("solar-system", "test-seed")
        assert scene.id == "solar-system"
