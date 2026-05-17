"""Tests for demo preparation commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from universe.cli import main
from universe.demo import (
    create_game_state,
    detect_godot_binary,
    ensure_all_campaign_scenes,
    format_godot_prep_message,
    html_output_path,
    prepare_godot_demo,
    prepare_html_demo,
    run_demo_check,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestDemoHelpers:
    def test_detect_godot_binary_missing_graceful(self, monkeypatch):
        monkeypatch.delenv("GODOT_BIN", raising=False)
        with patch("universe.demo.shutil.which", return_value=None):
            with patch.object(Path, "is_file", return_value=False):
                assert detect_godot_binary() is None

    def test_detect_godot_binary_from_env(self, monkeypatch, tmp_path):
        fake = tmp_path / "godot"
        fake.write_text("", encoding="utf-8")
        fake.chmod(0o755)
        monkeypatch.setenv("GODOT_BIN", str(fake))
        assert detect_godot_binary() == fake

    def test_format_godot_message_mentions_project_and_overrides(self):
        from universe.demo import DemoPreparationResult

        msg = format_godot_prep_message(
            DemoPreparationResult(success=True, repo_root=REPO_ROOT)
        )
        assert "frontends/godot/project.godot" in msg
        assert "overrides.json" in msg

    def test_html_output_path_solar_and_other(self, tmp_path):
        assert html_output_path(tmp_path, "solar-system").name == "tutorial-ui.html"
        assert html_output_path(tmp_path, "scene-001").name == "scene-001-ui.html"


class TestPrepareGodotDemo:
    def test_creates_six_scenes_in_tmp_repo(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        (tmp_path / "frontends" / "godot" / "data").mkdir(parents=True)
        (tmp_path / "frontends" / "godot" / "project.godot").write_text(
            'config/name="test"\n', encoding="utf-8"
        )

        paths = ensure_all_campaign_scenes(tmp_path)
        assert len(paths) == 6
        for p in paths:
            assert p.is_file()
            data = json.loads(p.read_text(encoding="utf-8"))
            assert "objects" in data

    def test_reset_writes_game_state(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        (tmp_path / "frontends" / "godot" / "data").mkdir(parents=True)
        (tmp_path / "frontends" / "godot" / "project.godot").write_text(
            'config/name="test"\n', encoding="utf-8"
        )
        ensure_all_campaign_scenes(tmp_path)

        state = create_game_state(
            tmp_path,
            entity_name="Test Institute",
            entity_type="private_institute",
            motto="Test motto.",
        )
        assert state.is_file()
        payload = json.loads(state.read_text(encoding="utf-8"))
        assert payload["research_entity"]["name"] == "Test Institute"

        state.write_text("{}", encoding="utf-8")
        result = prepare_godot_demo(repo_root=tmp_path, reset=True)
        assert result.success
        assert result.state_path is not None
        payload2 = json.loads(result.state_path.read_text(encoding="utf-8"))
        assert payload2["research_entity"]["name"] == "Hydrogen Ghost Institute"

    def test_prepare_exports_godot_data(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        (tmp_path / "frontends" / "godot" / "data").mkdir(parents=True)
        (tmp_path / "frontends" / "godot" / "project.godot").write_text(
            'config/name="test"\n', encoding="utf-8"
        )
        result = prepare_godot_demo(repo_root=tmp_path, reset=True)
        assert result.success
        manifest = tmp_path / "frontends" / "godot" / "data" / "manifest.json"
        assert manifest.is_file()
        catalog = json.loads(
            (tmp_path / "frontends" / "godot" / "data" / "scene_catalog.json").read_text()
        )
        assert len(catalog) == 6


class TestPrepareHtmlDemo:
    def test_writes_html_file(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        result = prepare_html_demo(repo_root=tmp_path, scene_id="solar-system", reset=True)
        assert result.success
        assert result.html_path is not None
        assert result.html_path.is_file()
        text = result.html_path.read_text(encoding="utf-8")
        assert "<html" in text.lower() or "DOCTYPE" in text


class TestDemoCheck:
    def test_passes_after_preparation(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        (tmp_path / "frontends" / "godot" / "data").mkdir(parents=True)
        (tmp_path / "frontends" / "godot" / "project.godot").write_text(
            'config/name="test"\n', encoding="utf-8"
        )
        prepare_godot_demo(repo_root=tmp_path, reset=True)
        check = run_demo_check(tmp_path)
        assert check.ok

    def test_fails_when_files_missing(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        check = run_demo_check(tmp_path)
        assert not check.ok


class TestDemoCli:
    def test_demo_godot_cli_smoke(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        (tmp_path / "frontends" / "godot" / "data").mkdir(parents=True)
        (tmp_path / "frontends" / "godot" / "project.godot").write_text(
            'config/name="test"\n', encoding="utf-8"
        )
        runner = CliRunner()
        with patch("universe.demo.find_repo_root", return_value=tmp_path):
            result = runner.invoke(
                main,
                ["demo", "godot", "--reset"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0, result.output
        assert "frontends/godot/project.godot" in result.output
        assert "overrides.json" in result.output

    def test_demo_html_cli(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        runner = CliRunner()
        with patch("universe.demo.find_repo_root", return_value=tmp_path):
            result = runner.invoke(
                main,
                ["demo", "html", "--scene", "solar-system", "--reset"],
            )
        assert result.exit_code == 0, result.output
        assert "tutorial-ui.html" in result.output
        assert "hot-swap" in result.output.lower() or "hot-swap" in result.output

    def test_demo_check_exit_code(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        runner = CliRunner()
        with patch("universe.demo.find_repo_root", return_value=tmp_path):
            fail = runner.invoke(main, ["demo", "check"])
        assert fail.exit_code != 0

    def test_demo_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["demo", "--help"])
        assert result.exit_code == 0
        assert "godot" in result.output
        assert "html" in result.output
        assert "check" in result.output

    def test_launch_fails_without_godot(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        (tmp_path / "frontends" / "godot" / "data").mkdir(parents=True)
        (tmp_path / "frontends" / "godot" / "project.godot").write_text(
            'config/name="test"\n', encoding="utf-8"
        )
        runner = CliRunner()
        with patch("universe.demo.find_repo_root", return_value=tmp_path):
            with patch("universe.demo.detect_godot_binary", return_value=None):
                result = runner.invoke(
                    main,
                    ["demo", "godot", "--reset", "--launch"],
                )
        assert result.exit_code != 0
        assert "Godot binary" in result.output


class TestJustfile:
    def test_justfile_has_godot_demo_target(self):
        justfile = REPO_ROOT / "justfile"
        assert justfile.is_file()
        text = justfile.read_text(encoding="utf-8")
        assert "godot-demo:" in text
        assert "universe demo godot" in text
