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
