"""Godot project file and res:// reference integrity."""

from __future__ import annotations

from pathlib import Path

from universe.godot_integrity import (
    REQUIRED_GODOT_SCRIPTS,
    build_godot_headless_command,
    extract_res_paths,
    godot_project_root,
    run_godot_headless_validation,
    scan_godot_output_for_script_errors,
    validate_godot_project,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
GODOT_ROOT = godot_project_root(REPO_ROOT)


class TestGodotRequiredScripts:
    def test_godot_required_scripts_exist(self):
        for rel in REQUIRED_GODOT_SCRIPTS:
            path = GODOT_ROOT / rel
            assert path.is_file(), f"missing {rel}"

    def test_telescope_console_exact_casing(self):
        assert (GODOT_ROOT / "scripts" / "TelescopeConsole.gd").is_file()

    def test_main_tscn_exists(self):
        assert (GODOT_ROOT / "scenes" / "Main.tscn").is_file()

    def test_project_godot_exists(self):
        assert (GODOT_ROOT / "project.godot").is_file()


class TestGodotResReferences:
    def test_godot_res_script_references_resolve(self):
        result = validate_godot_project(REPO_ROOT)
        assert result.ok, (
            f"missing={result.missing_paths} broken={result.broken_references}"
        )

    def test_main_gd_preloads_telescope_console(self):
        main_gd = (GODOT_ROOT / "scripts" / "Main.gd").read_text(encoding="utf-8")
        assert 'preload("res://scripts/TelescopeConsole.gd")' in main_gd
        assert (GODOT_ROOT / "scripts" / "TelescopeConsole.gd").is_file()

    def test_observatory_view_wired_in_godot(self):
        main_gd = (GODOT_ROOT / "scripts" / "Main.gd").read_text(encoding="utf-8")
        console_gd = (GODOT_ROOT / "scripts" / "TelescopeConsole.gd").read_text(encoding="utf-8")
        assert (GODOT_ROOT / "scripts" / "ObservatoryRenderer.gd").is_file()
        assert "ObservatoryRenderer" in main_gd
        assert "Observatory View" in console_gd
        assert "Scene Map" in console_gd

    def test_docs_mention_observatory_and_scene_map(self):
        doc = (REPO_ROOT / "docs" / "godot-frontend.md").read_text(encoding="utf-8")
        manual = (REPO_ROOT / "docs" / "manual-playtest.md").read_text(encoding="utf-8")
        assert "Observatory" in doc
        assert "Scene Map" in doc
        assert "Observatory" in manual or "telescope view" in manual.lower()

    def test_main_tscn_references_main_gd(self):
        tscn = (GODOT_ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        paths = extract_res_paths(tscn)
        assert "res://scripts/Main.gd" in paths
        assert (GODOT_ROOT / "scripts" / "Main.gd").is_file()


class TestGodotHeadlessValidation:
    def test_build_godot_headless_command(self, tmp_path):
        binary = tmp_path / "godot"
        root = tmp_path / "frontends" / "godot"
        cmd = build_godot_headless_command(binary, root)
        assert cmd[0] == str(binary)
        assert "--headless" in cmd
        assert "--path" in cmd
        assert str(root) in cmd

    def test_scan_godot_output_for_script_errors(self):
        output = "OK\nSCRIPT ERROR: Parse Error: Cannot infer the type of \"oid\"\n"
        errs = scan_godot_output_for_script_errors(output)
        assert len(errs) == 1
        assert "Cannot infer" in errs[0]

    def test_run_godot_headless_validation_mock(self, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        godot = tmp_path / "frontends" / "godot"
        godot.mkdir(parents=True)
        binary = tmp_path / "godot-bin"

        class FakeProc:
            stdout = "Godot Engine\n"
            stderr = ""

        monkeypatch.setattr(
            "universe.godot_integrity.subprocess.run",
            lambda *a, **k: FakeProc(),
        )
        result = run_godot_headless_validation(tmp_path, binary)
        assert result.ok
        assert "godot-bin" in result.command

    def test_demo_check_help_lists_godot_headless(self):
        from click.testing import CliRunner

        from universe.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["demo", "check", "--help"])
        assert result.exit_code == 0
        assert "godot-headless" in result.output


class TestGodotIntegrityHelper:
    def test_validate_reports_missing_script(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        godot = tmp_path / "frontends" / "godot"
        godot.mkdir(parents=True)
        (godot / "project.godot").write_text("config/name=\"t\"\n", encoding="utf-8")
        (godot / "scenes").mkdir(parents=True)
        (godot / "scenes" / "Main.tscn").write_text(
            '[ext_resource type="Script" path="res://scripts/Missing.gd" id="1"]\n',
            encoding="utf-8",
        )
        result = validate_godot_project(tmp_path)
        assert not result.ok
        assert any(ref.endswith("Missing.gd") for _, ref in result.broken_references)

    def test_demo_check_integrity_includes_telescope_console(self):
        from universe.demo import run_demo_check

        check = run_demo_check(REPO_ROOT)
        labels = [c[0] for c in check.checks]
        assert any("TelescopeConsole.gd" in label for label in labels)
