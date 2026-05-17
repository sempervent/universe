"""Tests for next-action suggestions and UX polish."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from universe.cli import main
from universe.game.entity import make_research_entity
from universe.game.models import ResearchState
from universe.game.next_actions import get_next_actions
from universe.game.objectives import ensure_objective_progress
from universe.game.scenes import ensure_campaign_state
from universe.game.transients import ensure_transient_states
from universe.procedural.registry import generate_scene_by_id


def _fresh_state(**kwargs) -> ResearchState:
    base = ensure_objective_progress(
        ensure_transient_states(ensure_campaign_state(ResearchState(**kwargs)))
    )
    return base


class TestNextActions:
    def test_active_objective_first(self):
        state = _fresh_state(
            research_entity=make_research_entity(name="Test Lab"),
        )
        scene = generate_scene_by_id("solar-system", seed="t")
        actions = get_next_actions(state, scene)
        assert actions
        assert actions[0].id.startswith("objective:")

    def test_missing_scene_generate_command(self, monkeypatch, tmp_path):
        state = _fresh_state()
        from universe.game.scenes import update_scene_unlocks
        from universe.game.tech_tree import unlock_tier

        for tid in ["ground_optical", "improved_ground", "space_optical"]:
            state, _ = unlock_tier(state, tid)
        state, _ = update_scene_unlocks(state)

        def _fake_path(defn):
            return str(tmp_path / defn.id / "scene.json")

        monkeypatch.setattr("universe.game.next_actions.scene_json_path", _fake_path)
        actions = get_next_actions(state, None)
        ids = {a.id for a in actions}
        assert any(a.startswith("missing_scene:") for a in ids)

    def test_affordable_upgrade_action(self):
        state = _fresh_state(research_points=500)
        actions = get_next_actions(state, None)
        assert any(a.id.startswith("upgrade:") for a in actions)

    def test_transient_when_active_and_observable(self):
        scene = generate_scene_by_id("solar-system", seed="t")
        state = _fresh_state(
            turn=3,
            unlocked_tiers=["naked_eye", "ground_optical"],
            active_telescope_tier="ground_optical",
        )
        actions = get_next_actions(state, scene)
        assert any(a.id.startswith("transient_observe:") for a in actions)

    def test_scene_mismatch_warning(self):
        from universe.game.models import CampaignSceneState

        scene = generate_scene_by_id("solar-system", seed="t")
        state = _fresh_state()
        scenes = dict(state.campaign.scenes)
        scenes["scene-001"] = CampaignSceneState(scene_id="scene-001", unlocked=True)
        state = state.model_copy(
            update={
                "campaign": state.campaign.model_copy(
                    update={"active_scene_id": "scene-001", "scenes": scenes}
                )
            }
        )
        actions = get_next_actions(state, scene)
        assert any(a.id == "scene_mismatch" for a in actions)

    def test_deterministic_ordering(self):
        scene = generate_scene_by_id("solar-system", seed="t")
        state = _fresh_state(research_points=100)
        a1 = get_next_actions(state, scene)
        a2 = get_next_actions(state, scene)
        assert [x.id for x in a1] == [x.id for x in a2]


class TestCLINextActions:
    def test_status_contains_next_actions(self):
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
            runner.invoke(main, ["game", "generate-scene", "--scene", "solar-system"])
            result = runner.invoke(main, ["game", "status", "--state", str(out)])
            assert result.exit_code == 0
            assert "Next actions" in result.output

    def test_scenes_shows_generate_and_set(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            out = Path("state.json")
            runner.invoke(
                main,
                ["game", "init", "--name", "X", "--entity-type", "custom", "--out", str(out)],
            )
            result = runner.invoke(main, ["game", "scenes", "--state", str(out)])
            assert "set-scene" in result.output
            assert "generate-scene" in result.output

    def test_objectives_shows_active(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            out = Path("state.json")
            runner.invoke(
                main,
                ["game", "init", "--name", "Obj", "--entity-type", "custom", "--out", str(out)],
            )
            result = runner.invoke(main, ["game", "objectives", "--state", str(out)])
            assert "ACTIVE" in result.output or "Observe" in result.output

    def test_transients_blocked_reason(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            out = Path("state.json")
            runner.invoke(
                main, ["game", "init", "--name", "T", "--entity-type", "custom", "--out", str(out)]
            )
            result = runner.invoke(
                main,
                ["game", "transients", "--state", str(out), "--scene", "solar-system"],
            )
            assert "Upcoming" in result.output or "Active" in result.output

    def test_report_has_recommended_next_step(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            out = Path("state.json")
            runner.invoke(
                main, ["game", "init", "--name", "R", "--entity-type", "custom", "--out", str(out)]
            )
            runner.invoke(main, ["game", "generate-scene", "--scene", "solar-system"])
            scene = Path("data/generated/solar-system/scene.json")
            report = Path("report.md")
            result = runner.invoke(
                main,
                ["game", "report", "--scene", str(scene), "--state", str(out), "--out", str(report)],
            )
            assert result.exit_code == 0
            assert "Recommended Next Step" in report.read_text()


class TestHTMLUX:
    def test_html_embeds_next_action_and_campaign_note(self):
        from universe.game.telescope_ui import export_telescope_ui

        scene = generate_scene_by_id("solar-system", seed="ux")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=path)
            html = path.read_text(encoding="utf-8")
            assert "h-next-action" in html or "Next action" in html
            assert "cannot hot-swap" in html.lower() or "hot-swap" in html.lower()
            assert "active/upcoming/expired" in html.lower() or "Upcoming" in html
            assert "renderObjectives" in html


class TestGodotUXPolish:
    def test_godot_scripts_contain_next_action_strings(self):
        root = Path(__file__).resolve().parents[1] / "frontends" / "godot"
        console = (root / "scripts" / "TelescopeConsole.gd").read_text(encoding="utf-8")
        assert "Next action" in console or "_next_action_summary" in console
        assert "Scene mismatch" in console
        main = (root / "scripts" / "Main.gd").read_text(encoding="utf-8")
        assert "Reloaded scene" in main

    def test_manual_playtest_doc_exists(self):
        doc = Path(__file__).resolve().parents[1] / "docs" / "manual-playtest.md"
        text = doc.read_text(encoding="utf-8")
        assert "Bug report template" in text
        assert "generate-scene" in text
