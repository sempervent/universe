"""Tests for telescope UI export."""

import tempfile
from pathlib import Path

from universe.game.models import ResearchState
from universe.game.telescope_ui import export_telescope_ui
from universe.procedural.solar_system import generate_solar_system


def _solar_scene():
    return generate_solar_system(seed="test-ui")


class TestExportTelescopeUI:
    def test_creates_html_file(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            result = export_telescope_ui(scene, out_path=out)
            assert result.exists()
            assert result.stat().st_size > 0

    def test_html_is_non_empty(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert len(content) > 1000
            assert "ENTITY_MODIFIERS" in content
            assert "backyard_observatory" in content

    def test_embeds_scene_data(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert scene.name in content
            assert scene.id in content

    def test_embeds_all_scene_objects(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            for obj in scene.objects:
                assert obj.id in content, f"Object {obj.id} not found in HTML"

    def test_embeds_tech_tree(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "naked_eye" in content
            assert "ground_optical" in content
            assert "now_scope" in content

    def test_embeds_discovery_requirements(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "base_research_points" in content
            assert "required_signal_types" in content

    def test_embeds_game_state(self):
        scene = _solar_scene()
        state = ResearchState(research_points=42)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, state=state, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert '"research_points": 42' in content or '"research_points":42' in content

    def test_default_state_if_none(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, state=None, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "research_points" in content
            assert "unlocked_tiers" in content

    def test_all_twelve_tiers_in_html(self):
        scene = _solar_scene()
        from universe.game.tech_tree import get_default_tech_tree

        tree = get_default_tech_tree()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            for tier in tree:
                assert tier.id in content, f"Tier {tier.id} not found in HTML"

    def test_solar_system_objects_in_ui(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "sun" in content.lower()
            assert "planet-mars" in content
            assert "planet-jupiter" in content

    def test_creates_parent_directories(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "deep" / "nested" / "dir" / "ui.html"
            result = export_telescope_ui(scene, out_path=out)
            assert result.exists()

    def test_html_has_observatory_console(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "Observatory Console" in content

    def test_html_has_game_controls(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "btn-observe" in content
            assert "btn-survey" in content
            assert "btn-reset" in content
            assert "btn-export" in content

    def test_html_has_sky_canvas(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "sky-canvas" in content

    def test_html_has_localstorage_persistence(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "telescope-ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "localStorage" in content


class TestSurveyMilestoneEmbedding:
    def test_html_embeds_survey_data(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "local_sky_survey" in content
            assert "deep_field_survey" in content
            assert "now_scope_first_light" in content
            assert "First Light Survey" in content
            assert "const SURVEYS" in content

    def test_html_embeds_milestone_data(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "first_light" in content
            assert "First Light" in content
            assert "named_entity" in content
            assert "Founding Charter" in content
            assert "const MILESTONES" in content

    def test_html_has_survey_and_milestone_tabs(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert 'data-tab="surveys"' in content
            assert 'data-tab="milestones"' in content
            assert 'id="tab-surveys"' in content
            assert 'id="tab-milestones"' in content

    def test_html_includes_survey_and_milestone_renderers(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "function renderSurveys" in content
            assert "function renderMilestones" in content
            assert "function evaluateMilestonesJS" in content
            assert "function applySurveyProgress" in content
            assert "doStartSurvey" in content
            assert "doClaimSurvey" in content

    def test_speculative_marker_present(self):
        scene = _solar_scene()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert "SPECULATIVE" in content

    def test_state_with_active_survey_embeds_in_html(self):
        from universe.game.surveys import start_survey

        scene = _solar_scene()
        state = ResearchState()
        state, _ = start_survey(state, "local_sky_survey")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui.html"
            export_telescope_ui(scene, state=state, out_path=out)
            content = out.read_text(encoding="utf-8")
            assert '"active_survey_id":"local_sky_survey"' in content
