"""Validate Godot project script/scene references without running the editor."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

RES_PATH_RE = re.compile(r"res://[^\s\"')}\]]+")

REQUIRED_GODOT_SCRIPTS: tuple[str, ...] = (
    "scripts/Main.gd",
    "scripts/FilePaths.gd",
    "scripts/GameState.gd",
    "scripts/SceneLoader.gd",
    "scripts/SkyRenderer.gd",
    "scripts/SkyProjection.gd",
    "scripts/ObservatoryRenderer.gd",
    "scripts/TelescopeCamera.gd",
    "scripts/TelescopeConsole.gd",
    "scripts/ObjectiveEngine.gd",
    "scripts/TransientEngine.gd",
    "scripts/DiscoveryEngine.gd",
    "scripts/SurveyEngine.gd",
    "scripts/MilestoneEngine.gd",
    "scripts/TechTree.gd",
    "scripts/EntityModifiers.gd",
)

REQUIRED_GODOT_PATHS: tuple[str, ...] = (
    "project.godot",
    "scenes/Main.tscn",
    *REQUIRED_GODOT_SCRIPTS,
)

# res:// paths that are generated at runtime (not shipped in repo).
RUNTIME_RES_PREFIXES: tuple[str, ...] = ()

GODOT_SCRIPT_ERROR_MARKERS: tuple[str, ...] = (
    "SCRIPT ERROR",
    "Parse Error",
    "Cannot infer the type",
    "Failed to load script",
    "Could not resolve script",
)


@dataclass
class GodotIntegrityResult:
    ok: bool
    godot_root: Path
    missing_paths: list[str] = field(default_factory=list)
    broken_references: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def godot_project_root(repo_root: Path) -> Path:
    return repo_root / "frontends" / "godot"


def godot_project_complete(repo_root: Path) -> bool:
    """True when the full Godot frontend scaffold is present (not a data-only stub)."""
    root = godot_project_root(repo_root)
    return (root / "scripts" / "Main.gd").is_file() and (root / "scenes" / "Main.tscn").is_file()


def extract_res_paths(text: str) -> set[str]:
    """Return res://... paths found in Godot project text."""
    found: set[str] = set()
    for match in RES_PATH_RE.finditer(text):
        path = match.group(0).rstrip(".,;")
        if path.endswith("*"):
            continue
        found.add(path)
    return found


def _is_runtime_res_path(res_path: str) -> bool:
    return any(res_path.startswith(prefix) for prefix in RUNTIME_RES_PREFIXES)


def validate_godot_project(repo_root: Path) -> GodotIntegrityResult:
    """Verify required Godot files exist and res:// references resolve."""
    root = godot_project_root(repo_root)
    result = GodotIntegrityResult(ok=True, godot_root=root)

    if not root.is_dir():
        result.ok = False
        result.missing_paths.append(str(root.relative_to(repo_root)))
        return result

    for rel in REQUIRED_GODOT_PATHS:
        p = root / rel
        if not p.is_file():
            result.ok = False
            result.missing_paths.append(rel)

    scan_suffixes = {".gd", ".tscn", ".godot", ".tres", ".res"}
    for path in root.rglob("*"):
        if path.suffix not in scan_suffixes:
            continue
        if ".godot" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel_file = str(path.relative_to(root))
        for res_path in extract_res_paths(text):
            if _is_runtime_res_path(res_path):
                continue
            if not res_path.endswith((".gd", ".tscn", ".json", ".tres", ".res", ".svg", ".import")):
                continue
            rel_target = res_path.removeprefix("res://")
            target = root / rel_target
            if not target.is_file():
                result.ok = False
                result.broken_references.append((rel_file, res_path))

    return result


@dataclass
class GodotHeadlessResult:
    ok: bool
    command: str
    output: str = ""
    errors: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


def build_godot_headless_command(binary: Path, godot_root: Path) -> list[str]:
    """Argv for a short headless editor pass that reloads all project scripts."""
    return [
        str(binary),
        "--headless",
        "--editor",
        "--path",
        str(godot_root),
        "--quit-after",
        "2",
    ]


def scan_godot_output_for_script_errors(output: str) -> list[str]:
    """Return output lines that indicate GDScript load/parse/type failures."""
    return [
        line.strip()
        for line in output.splitlines()
        if any(marker in line for marker in GODOT_SCRIPT_ERROR_MARKERS)
    ]


def run_godot_headless_validation(
    repo_root: Path,
    binary: Path,
    *,
    timeout: float = 45.0,
) -> GodotHeadlessResult:
    """Run Godot headless editor; fail on script parse/type errors in combined output."""
    godot_root = godot_project_root(repo_root)
    cmd = build_godot_headless_command(binary, godot_root)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(godot_root),
        )
    except subprocess.TimeoutExpired:
        return GodotHeadlessResult(
            ok=False,
            command=" ".join(cmd),
            output="",
            errors=[f"Godot headless validation timed out after {timeout}s"],
        )
    except OSError as exc:
        return GodotHeadlessResult(
            ok=False,
            command=" ".join(cmd),
            errors=[str(exc)],
        )

    combined = (proc.stdout or "") + (proc.stderr or "")
    errors = scan_godot_output_for_script_errors(combined)
    return GodotHeadlessResult(
        ok=len(errors) == 0,
        command=" ".join(cmd),
        output=combined,
        errors=errors,
    )


def format_integrity_message(result: GodotIntegrityResult) -> str:
    lines: list[str] = []
    if result.ok:
        lines.append("Godot project integrity: OK")
    else:
        lines.append("Godot project integrity: FAILED")
    for p in result.missing_paths:
        lines.append(f"  ✗ missing {p}")
    for src, ref in result.broken_references:
        lines.append(f"  ✗ {src}: unresolved {ref}")
    for w in result.warnings:
        lines.append(f"  Warning: {w}")
    return "\n".join(lines)
