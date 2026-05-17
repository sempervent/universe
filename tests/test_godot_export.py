"""Tests for the Godot frontend data export and project scaffold."""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from universe.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent
GODOT_ROOT = REPO_ROOT / "frontends" / "godot"


# ── Export command ────────────────────────────────────────────────────


class TestExportGodotData:
    def test_writes_all_files(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "godot-data"
            result = runner.invoke(main, ["game", "export-godot-data", "--out", str(out)])
            assert result.exit_code == 0, result.output
            for fname in [
                "tech_tree.json",
                "surveys.json",
                "milestones.json",
                "discovery_requirements.json",
                "signal_types.json",
                "entity_types.json",
                "random_entity_names.json",
                "manifest.json",
                "entity_modifiers.json",
                "scene_catalog.json",
            ]:
                p = out / fname
                assert p.exists(), f"missing {fname}"
                assert p.stat().st_size > 0

    def test_files_are_valid_json(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "godot-data"
            runner.invoke(main, ["game", "export-godot-data", "--out", str(out)])
            for f in out.glob("*.json"):
                json.loads(f.read_text(encoding="utf-8"))

    def test_tech_tree_contains_known_tier_ids(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "godot-data"
            runner.invoke(main, ["game", "export-godot-data", "--out", str(out)])
            data = json.loads((out / "tech_tree.json").read_text())
            ids = {t["id"] for t in data}
            for required in ["naked_eye", "ground_optical", "space_optical", "now_scope"]:
                assert required in ids

    def test_surveys_contains_known_ids(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "godot-data"
            runner.invoke(main, ["game", "export-godot-data", "--out", str(out)])
            data = json.loads((out / "surveys.json").read_text())
            ids = {s["id"] for s in data}
            for required in [
                "local_sky_survey",
                "deep_field_survey",
                "now_scope_first_light",
            ]:
                assert required in ids

    def test_milestones_contains_known_ids(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "godot-data"
            runner.invoke(main, ["game", "export-godot-data", "--out", str(out)])
            data = json.loads((out / "milestones.json").read_text())
            ids = {m["id"] for m in data}
            for required in [
                "first_light",
                "named_entity",
                "first_planet",
                "now_scope_first_light",
            ]:
                assert required in ids

    def test_discovery_requirements_keyed_by_object_type(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "godot-data"
            runner.invoke(main, ["game", "export-godot-data", "--out", str(out)])
            data = json.loads((out / "discovery_requirements.json").read_text())
            types = {r["object_type"] for r in data}
            for t in ["star", "planet", "moon", "galaxy", "quasar", "black_hole"]:
                assert t in types

    def test_manifest_lists_files(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "godot-data"
            runner.invoke(main, ["game", "export-godot-data", "--out", str(out)])
            manifest = json.loads((out / "manifest.json").read_text())
            assert "files" in manifest
            assert "schema_version" in manifest
            assert "tech_tree.json" in manifest["files"]


# ── Project scaffold presence ─────────────────────────────────────────


class TestGodotScaffold:
    def test_project_godot_exists(self):
        assert (GODOT_ROOT / "project.godot").exists()

    def test_main_scene_exists(self):
        assert (GODOT_ROOT / "scenes" / "Main.tscn").exists()

    def test_required_scripts_exist(self):
        for name in [
            "Main.gd",
            "FilePaths.gd",
            "SceneLoader.gd",
            "GameState.gd",
            "TechTree.gd",
            "DiscoveryEngine.gd",
            "SurveyEngine.gd",
            "MilestoneEngine.gd",
            "SkyRenderer.gd",
            "TelescopeCamera.gd",
            "TelescopeConsole.gd",
            "EntityModifiers.gd",
        ]:
            assert (GODOT_ROOT / "scripts" / name).exists(), f"missing scripts/{name}"

    def test_sky_renderer_has_picking_and_signals(self):
        text = (GODOT_ROOT / "scripts" / "SkyRenderer.gd").read_text(encoding="utf-8")
        assert "signal object_picked" in text
        assert "Area3D" in text
        assert "SphereShape3D" in text

    def test_sky_renderer_deep_field_and_filament_path(self):
        text = (GODOT_ROOT / "scripts" / "SkyRenderer.gd").read_text(encoding="utf-8")
        assert "is_deep_field_scene" in text
        assert "control_points_mpc" in text
        assert "_render_lab_visual" in text or "LABShell" in text
        assert "QuasarJet" in text
        assert "AccretionRing" in text

    def test_scene_loader_scene_classification(self):
        text = (GODOT_ROOT / "scripts" / "SceneLoader.gd").read_text(encoding="utf-8")
        assert "is_deep_field_scene" in text
        assert "is_solar_system_scene" in text

    def test_telescope_console_deep_field_ui(self):
        text = (GODOT_ROOT / "scripts" / "TelescopeConsole.gd").read_text(encoding="utf-8")
        assert "render_survey_hint" in text
        assert "Deep Field" in text
        assert "render_signal_mode_help" in text and "deep_field" in text

    def test_entity_modifiers_script_exists(self):
        text = (GODOT_ROOT / "scripts" / "EntityModifiers.gd").read_text(encoding="utf-8")
        assert "effective_tier_cost" in text
        assert "modifier_for_state" in text

    def test_telescope_camera_has_orbit_and_pick_signals(self):
        text = (GODOT_ROOT / "scripts" / "TelescopeCamera.gd").read_text(encoding="utf-8")
        assert "signal pick_attempt" in text
        assert "signal focus_requested" in text

    def test_telescope_console_has_signal_mode_ui(self):
        text = (GODOT_ROOT / "scripts" / "TelescopeConsole.gd").read_text(encoding="utf-8")
        assert "action_signal_mode_changed" in text
        assert "OptionButton" in text
        assert "setup_signal_modes" in text

    def test_data_bundle_committed(self):
        for fname in [
            "tech_tree.json",
            "surveys.json",
            "milestones.json",
            "discovery_requirements.json",
            "manifest.json",
            "entity_modifiers.json",
        ]:
            assert (GODOT_ROOT / "data" / fname).exists(), f"missing data/{fname}"

    def test_project_godot_points_to_main_scene(self):
        contents = (GODOT_ROOT / "project.godot").read_text(encoding="utf-8")
        assert 'run/main_scene="res://scenes/Main.tscn"' in contents

    def test_filepaths_autoload_registered(self):
        contents = (GODOT_ROOT / "project.godot").read_text(encoding="utf-8")
        assert "FilePaths=" in contents
        assert "scripts/FilePaths.gd" in contents

    def test_readme_explains_how_to_run(self):
        readme = (GODOT_ROOT / "README.md").read_text(encoding="utf-8")
        assert "Godot 4" in readme
        assert "project.godot" in readme
        assert "F5" in readme

    def test_readme_mentions_scene_001_switching(self):
        readme = (GODOT_ROOT / "README.md").read_text(encoding="utf-8")
        assert "scene-001" in readme
        assert "overrides.json" in readme

    def test_main_gd_references_engines(self):
        main_gd = (GODOT_ROOT / "scripts" / "Main.gd").read_text(encoding="utf-8")
        for needle in [
            "SceneLoader",
            "GameState",
            "DiscoveryEngine",
            "SurveyEngine",
            "MilestoneEngine",
            "SkyRenderer",
            "TelescopeConsole",
            "TelescopeCamera",
        ]:
            assert needle in main_gd


# ── Docs presence ─────────────────────────────────────────────────────


class TestGodotDocs:
    def test_godot_frontend_doc_exists(self):
        assert (REPO_ROOT / "docs" / "godot-frontend.md").exists()

    def test_godot_frontend_doc_mentions_camera_controls(self):
        doc = (REPO_ROOT / "docs" / "godot-frontend.md").read_text(encoding="utf-8")
        assert "TelescopeCamera" in doc
        assert "Orbit" in doc or "orbit" in doc

    def test_godot_frontend_doc_mentions_deep_field_scene_001(self):
        doc = (REPO_ROOT / "docs" / "godot-frontend.md").read_text(encoding="utf-8")
        assert "scene-001" in doc or "Scene 001" in doc
        assert "deep field" in doc.lower() or "Deep Field" in doc
        assert "signal" in doc.lower()

    def test_readme_links_godot_doc(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "godot-frontend.md" in readme or "Godot" in readme
