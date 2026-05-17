"""Godot project file and res:// reference integrity."""

from __future__ import annotations

from pathlib import Path

from universe.godot_integrity import (
    REQUIRED_GODOT_SCRIPTS,
    extract_res_paths,
    godot_project_root,
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

    def test_main_tscn_references_main_gd(self):
        tscn = (GODOT_ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        paths = extract_res_paths(tscn)
        assert "res://scripts/Main.gd" in paths
        assert (GODOT_ROOT / "scripts" / "Main.gd").is_file()


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
