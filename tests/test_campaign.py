"""Tests for multi-scene campaign progression."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from universe.cli import main
from universe.game.guidance import get_guidance_hints
from universe.game.models import ResearchState
from universe.game.playtest import get_scenario_by_id, run_playtest
from universe.game.scenes import (
    ensure_campaign_state,
    get_default_scene_catalog,
    get_scene_definition,
    recommended_next_scene,
    set_active_scene,
    update_scene_unlocks,
)
from universe.game.surveys import get_default_survey_programs
from universe.game.telescope_ui import export_telescope_ui
from universe.procedural.solar_system import generate_solar_system


class TestSceneCatalog:
    def test_default_scenes_unique_ids(self):
        ids = [s.id for s in get_default_scene_catalog()]
        assert len(ids) == len(set(ids))
        assert len(ids) == 6

    def test_solar_system_unlocked_by_default(self):
        state = ensure_campaign_state(ResearchState())
        assert state.campaign.scenes["solar-system"].unlocked
        assert state.campaign.active_scene_id == "solar-system"

    def test_scene_001_requires_space_optical(self):
        defn = get_scene_definition("scene-001")
        assert defn is not None
        assert defn.unlock_tier_id == "space_optical"

    def test_scene_definitions_reference_valid_surveys_and_signals(self):
        survey_ids = {s.id for s in get_default_survey_programs()}
        from universe.game.models import SignalType

        valid_signals = {s.value for s in SignalType}
        for defn in get_default_scene_catalog():
            for sid in defn.recommended_survey_ids:
                assert sid in survey_ids, f"{defn.id} references unknown survey {sid}"
            for sig in defn.recommended_signal_modes:
                assert sig.value in valid_signals


class TestCampaignState:
    def test_backward_compatible_research_state(self):
        raw = ResearchState().model_dump()
        raw.pop("campaign", None)
        state = ResearchState.model_validate(raw)
        state = ensure_campaign_state(state)
        assert state.campaign.scenes["solar-system"].unlocked

    def test_scene_001_unlocks_after_space_optical(self):
        state = ResearchState(unlocked_tiers=["naked_eye", "ground_optical", "space_optical"])
        state, newly = update_scene_unlocks(state)
        assert state.campaign.scenes["scene-001"].unlocked
        assert "scene-001" in newly or state.campaign.scenes["scene-001"].unlocked

    def test_set_active_scene_rejects_locked(self):
        state = ensure_campaign_state(ResearchState())
        new_state, msg = set_active_scene(state, "scene-001")
        assert new_state.campaign.active_scene_id == "solar-system"
        assert "locked" in msg.lower()

    def test_set_active_scene_marks_visited(self):
        state = ResearchState(unlocked_tiers=["space_optical"])
        state, _ = update_scene_unlocks(state)
        new_state, msg = set_active_scene(state, "scene-001")
        assert "Active campaign" in msg or "already" in msg.lower()
        assert new_state.campaign.scenes["scene-001"].visited

    def test_recommended_next_scene_after_solar(self):
        state = ResearchState(unlocked_tiers=["space_optical"])
        state, _ = update_scene_unlocks(state)
        rec = recommended_next_scene(state)
        assert rec is not None
        assert rec.id == "scene-001"


class TestCampaignCLI:
    def test_game_scenes_lists_both(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "game-state.json"
            state_path.write_text(ResearchState().model_dump_json(indent=2))
            result = runner.invoke(
                main,
                ["game", "scenes", "--state", str(state_path)],
            )
            assert result.exit_code == 0, result.output
            assert "solar-system" in result.output
            assert "scene-001" in result.output
            assert "Local Solar System" in result.output

    def test_game_set_scene_unlocked(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "game-state.json"
            state = ResearchState(unlocked_tiers=["space_optical"])
            state = ensure_campaign_state(state)
            state, _ = update_scene_unlocks(state)
            state_path.write_text(state.model_dump_json(indent=2))
            result = runner.invoke(
                main,
                [
                    "game",
                    "set-scene",
                    "--state",
                    str(state_path),
                    "--scene",
                    "scene-001",
                    "--out",
                    str(state_path),
                ],
            )
            assert result.exit_code == 0, result.output
            loaded = ResearchState.model_validate_json(state_path.read_text())
            assert loaded.campaign.active_scene_id == "scene-001"

    def test_game_generate_scene_writes_files(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "scene-001"
            result = runner.invoke(
                main,
                ["game", "generate-scene", "--scene", "scene-001", "--out", str(out)],
            )
            assert result.exit_code == 0, result.output
            assert (out / "scene.json").exists()

    def test_game_status_includes_active_scene(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "game-state.json"
            state_path.write_text(ResearchState().model_dump_json(indent=2))
            result = runner.invoke(
                main,
                ["game", "status", "--state", str(state_path)],
            )
            assert result.exit_code == 0, result.output
            assert "solar-system" in result.output.lower() or "Campaign" in result.output


class TestCampaignGuidance:
    def test_guidance_uses_catalog_commands(self):
        state = ResearchState(
            unlocked_tiers=["naked_eye", "ground_optical", "space_optical"],
            research_points=50,
        )
        state = ensure_campaign_state(state)
        state, _ = update_scene_unlocks(state)
        scene = generate_solar_system("local-sky")
        hints = get_guidance_hints(scene, state)
        campaign_hints = [h for h in hints if h.related_scene_id == "scene-001"]
        assert campaign_hints, "expected campaign guidance toward scene-001"
        text = " ".join(h.message + " " + h.suggested_action for h in campaign_hints)
        assert "scene-001" in text or "generate-scene" in text or "set-scene" in text


class TestCampaignHTML:
    def test_export_embeds_campaign_panel(self):
        scene = generate_solar_system("local-sky")
        state = ensure_campaign_state(ResearchState(unlocked_tiers=["space_optical"]))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, state, out)
            html = out.read_text(encoding="utf-8")
            assert "Campaign" in html
            assert "SCENE_CATALOG" in html or "scene-001" in html


class TestCampaignPlaytest:
    def test_campaign_scenario_transitions(self):
        scenario = get_scenario_by_id("solar_to_deep_field_campaign")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="campaign-test",
        )
        assert run.summary.get("campaign_transition_turn") is not None
        assert run.summary.get("active_scene_id") == "scene-001"
