"""Single-command demo preparation and validation for playable frontends."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from universe.export.scene_json import export_scene
from universe.export.unreal_data import export_unreal_data
from universe.game.godot_export import export_godot_data_bundle
from universe.game.models import ResearchState
from universe.game.scenes import ensure_campaign_state, get_default_scene_catalog, get_scene_definition
from universe.game.telescope_ui import export_telescope_ui
from universe.models import SceneRegion
from universe.procedural.registry import generate_scene_by_id

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

GODOT_PROJECT = REPO_ROOT / "frontends" / "godot" / "project.godot"
GODOT_DATA_DIR = REPO_ROOT / "frontends" / "godot" / "data"
DEFAULT_STATE_REL = "data/generated/game-state.json"
UNREAL_PROJECT = REPO_ROOT / "frontends" / "unreal" / "Universe.uproject"
UNREAL_DATA_DIR = REPO_ROOT / "frontends" / "unreal" / "Data"

GODOT_REQUIRED_DATA_FILES = (
    "manifest.json",
    "scene_catalog.json",
    "tech_tree.json",
    "surveys.json",
    "milestones.json",
    "transient_events.json",
    "objectives.json",
    "entity_modifiers.json",
)

MACOS_GODOT_APP = Path("/Applications/Godot.app/Contents/MacOS/Godot")


@dataclass
class DemoPreparationResult:
    """Outcome of a demo prepare step."""

    success: bool
    repo_root: Path
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    generated_scenes: list[Path] = field(default_factory=list)
    state_path: Path | None = None
    godot_data_dir: Path | None = None
    html_path: Path | None = None
    godot_binary: Path | None = None
    godot_user_data_dir: Path | None = None
    overrides_path: Path | None = None
    launch_attempted: bool = False
    launch_command: str | None = None


@dataclass
class DemoCheckResult:
    """Outcome of `demo check`."""

    ok: bool
    repo_root: Path
    checks: list[tuple[str, bool, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    godot_binary: Path | None = None


def find_repo_root(start: Path | None = None) -> Path:
    """Locate repository root (directory containing pyproject.toml)."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    return REPO_ROOT


def _rel(repo_root: Path, path: str) -> Path:
    return repo_root / path


def scene_json_path(repo_root: Path, scene_id: str) -> Path | None:
    defn = get_scene_definition(scene_id)
    if defn is None:
        return None
    return _rel(repo_root, defn.default_output_path) / "scene.json"


def _parse_godot_project_name(project_godot: Path) -> str | None:
    if not project_godot.is_file():
        return None
    for line in project_godot.read_text(encoding="utf-8").splitlines():
        if line.startswith("config/name="):
            raw = line.split("=", 1)[1].strip().strip('"')
            return raw
    return None


def find_godot_user_data_dir(
    repo_root: Path | None = None,
    *,
    project_godot: Path | None = None,
) -> Path | None:
    """Best-effort Godot app_userdata directory for this project."""
    pg = project_godot or (find_repo_root(repo_root) / "frontends" / "godot" / "project.godot")
    name = _parse_godot_project_name(pg)
    if not name:
        return None
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "Godot" / "app_userdata"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        base = Path(appdata) / "Godot" / "app_userdata"
    else:
        base = Path.home() / ".local" / "share" / "godot" / "app_userdata"
    direct = base / name
    if direct.is_dir():
        return direct
    if not base.is_dir():
        return None
    slug = re.sub(r"[^\w\-]+", "-", name).strip("-").lower()
    for child in base.iterdir():
        if child.is_dir() and slug in child.name.lower().replace(" ", "-"):
            return child
    return direct if base.exists() else None


def detect_godot_binary() -> Path | None:
    """Return path to Godot executable if discoverable."""
    env = os.environ.get("GODOT_BIN")
    if env:
        p = Path(env).expanduser()
        if p.is_file() and os.access(p, os.X_OK):
            return p
    which = shutil.which("godot")
    if which:
        return Path(which)
    if MACOS_GODOT_APP.is_file() and os.access(MACOS_GODOT_APP, os.X_OK):
        return MACOS_GODOT_APP
    return None


def create_game_state(
    repo_root: Path,
    *,
    out_rel: str = DEFAULT_STATE_REL,
    entity_name: str = "Hydrogen Ghost Institute",
    entity_type: str = "private_institute",
    motto: str = "Listening for the old light.",
    starting_rp: int = 0,
) -> Path:
    """Initialize game state (same logic as `universe game init`)."""
    from universe.game.entity import make_research_entity
    from universe.game.objectives import ensure_objective_progress, evaluate_objectives
    from universe.game.transients import ensure_transient_states

    entity = make_research_entity(name=entity_name, entity_type=entity_type, motto=motto)
    state = ensure_objective_progress(
        ensure_transient_states(
            ensure_campaign_state(
                ResearchState(research_points=starting_rp, research_entity=entity)
            )
        )
    )
    state, _ = evaluate_objectives(state)
    out_path = _rel(repo_root, out_rel)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(ensure_campaign_state(state).model_dump_json(indent=2), encoding="utf-8")
    return out_path


def ensure_game_state(
    repo_root: Path,
    *,
    reset: bool = False,
    state_rel: str = DEFAULT_STATE_REL,
    **init_kwargs: object,
) -> Path:
    path = _rel(repo_root, state_rel)
    if reset or not path.is_file():
        return create_game_state(repo_root, out_rel=state_rel, **init_kwargs)  # type: ignore[arg-type]
    return path


def generate_campaign_scene(
    scene_id: str,
    repo_root: Path,
    *,
    seed: str | None = None,
    force: bool = False,
) -> Path:
    """Generate one campaign scene.json (catalog defaults)."""
    defn = get_scene_definition(scene_id)
    if defn is None:
        raise ValueError(f"Unknown campaign scene: {scene_id}")

    out_dir = _rel(repo_root, defn.default_output_path)
    scene_path = out_dir / "scene.json"
    if scene_path.is_file() and not force:
        return scene_path

    use_seed = seed or defn.default_seed
    gen = defn.generator_name or defn.id
    scene = generate_scene_by_id(gen, seed=use_seed)
    export_scene(scene, str(out_dir))
    return scene_path


def ensure_all_campaign_scenes(
    repo_root: Path,
    *,
    force: bool = False,
) -> list[Path]:
    """Generate every catalog scene if missing (or all if force)."""
    paths: list[Path] = []
    for defn in get_default_scene_catalog():
        paths.append(generate_campaign_scene(defn.id, repo_root, force=force))
    return paths


def clear_godot_overrides(repo_root: Path) -> tuple[bool, str]:
    """Remove user://overrides.json from Godot app_userdata if found."""
    user_dir = find_godot_user_data_dir(repo_root)
    if user_dir is None:
        return False, (
            "Could not locate Godot app_userdata folder. "
            "In Godot: Project → Open User Data Folder → delete overrides.json"
        )
    overrides = user_dir / "overrides.json"
    if not overrides.is_file():
        return True, f"No overrides.json at {overrides}"
    backup = user_dir / "overrides.json.bak"
    if backup.exists():
        backup.unlink()
    overrides.rename(backup)
    return True, f"Renamed {overrides} → {backup.name}"


def overrides_warning(repo_root: Path) -> str | None:
    user_dir = find_godot_user_data_dir(repo_root)
    if user_dir is None:
        return None
    overrides = user_dir / "overrides.json"
    if overrides.is_file():
        return (
            f"Stale overrides.json found at {overrides}. "
            "It can force wrong scene/state paths. "
            "Use --clear-overrides or delete via Project → Open User Data Folder."
        )
    return None


def validate_godot_demo_files(repo_root: Path) -> tuple[list[str], list[str]]:
    """Return (missing_paths, present_paths) for required Godot demo artifacts."""
    required: list[Path] = [
        repo_root / "frontends" / "godot" / "project.godot",
        _rel(repo_root, DEFAULT_STATE_REL),
    ]
    for defn in get_default_scene_catalog():
        required.append(_rel(repo_root, defn.default_output_path) / "scene.json")
    for fname in GODOT_REQUIRED_DATA_FILES:
        required.append(repo_root / "frontends" / "godot" / "data" / fname)

    missing: list[str] = []
    present: list[str] = []
    for p in required:
        rel = p.relative_to(repo_root) if p.is_relative_to(repo_root) else p
        if p.is_file():
            present.append(str(rel))
        else:
            missing.append(str(rel))
    return missing, present


def launch_godot(
    repo_root: Path,
    *,
    binary: Path,
    editor: bool = True,
    run_game: bool = False,
) -> tuple[bool, str]:
    """Start Godot non-blocking; return (ok, command_line)."""
    project_dir = repo_root / "frontends" / "godot"
    cmd: list[str] = [str(binary), "--path", str(project_dir)]
    if editor and not run_game:
        cmd.insert(1, "--editor")
    elif run_game:
        pass  # default: run main scene without forcing editor
    try:
        subprocess.Popen(
            cmd,
            cwd=str(project_dir),
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        return False, f"{' '.join(cmd)} ({exc})"
    return True, " ".join(cmd)


def html_output_path(repo_root: Path, scene_id: str) -> Path:
    if scene_id == "solar-system":
        return _rel(repo_root, "data/generated/tutorial-ui.html")
    return _rel(repo_root, f"data/generated/{scene_id}-ui.html")


def validate_godot_scripts_headless(
    repo_root: Path,
    *,
    binary: Path | None = None,
    required: bool = False,
) -> tuple[bool, list[str], list[str]]:
    """Run Godot headless editor validation. Returns (ok, errors, warnings)."""
    from universe.godot_integrity import godot_project_complete, run_godot_headless_validation

    bin_path = binary or detect_godot_binary()
    if not godot_project_complete(repo_root):
        msg = "Godot project scaffold incomplete (missing Main.gd or Main.tscn)"
        if required:
            return False, [msg], []
        return True, [], [msg]

    if bin_path is None:
        msg = (
            "Godot binary not found; skipped script parse validation. "
            "Set GODOT_BIN or install Godot, then re-run."
        )
        if required:
            return False, [msg.replace("skipped ", "")], []
        return True, [], [msg]

    hres = run_godot_headless_validation(repo_root, bin_path)
    if hres.ok:
        return True, [], []
    return False, hres.errors or ["Godot headless validation failed"], []


def prepare_godot_demo(
    *,
    repo_root: Path | None = None,
    entity_name: str = "Hydrogen Ghost Institute",
    entity_type: str = "private_institute",
    motto: str = "Listening for the old light.",
    reset: bool = False,
    clear_overrides: bool = False,
    launch: bool = False,
    editor: bool = True,
    run_game: bool = False,
    force_scenes: bool = False,
    skip_godot_validate: bool = False,
) -> DemoPreparationResult:
    root = find_repo_root(repo_root)
    result = DemoPreparationResult(success=True, repo_root=root)

    try:
        result.generated_scenes = ensure_all_campaign_scenes(root, force=force_scenes or reset)
    except ValueError as exc:
        result.success = False
        result.errors.append(str(exc))
        return result

    try:
        result.state_path = ensure_game_state(
            root,
            reset=reset,
            entity_name=entity_name,
            entity_type=entity_type,
            motto=motto,
        )
    except Exception as exc:  # noqa: BLE001 — surface init failures to CLI
        result.success = False
        result.errors.append(f"game state: {exc}")
        return result

    godot_out = root / "frontends" / "godot" / "data"
    try:
        export_godot_data_bundle(godot_out)
        result.godot_data_dir = godot_out
    except Exception as exc:  # noqa: BLE001
        result.success = False
        result.errors.append(f"export godot data: {exc}")
        return result

    missing, _ = validate_godot_demo_files(root)
    if missing:
        result.success = False
        result.errors.extend(f"Missing: {m}" for m in missing)

    from universe.godot_integrity import godot_project_complete, validate_godot_project

    if godot_project_complete(root):
        integrity = validate_godot_project(root)
        if not integrity.ok:
            result.success = False
            for p in integrity.missing_paths:
                result.errors.append(f"Missing Godot file: {p}")
            for src, ref in integrity.broken_references:
                result.errors.append(f"Broken Godot reference in {src}: {ref}")

    result.godot_binary = detect_godot_binary()
    result.godot_user_data_dir = find_godot_user_data_dir(root)
    if result.godot_user_data_dir:
        ov = result.godot_user_data_dir / "overrides.json"
        if ov.is_file():
            result.overrides_path = ov

    warn = overrides_warning(root)
    if warn:
        result.warnings.append(warn)

    if clear_overrides:
        ok, msg = clear_godot_overrides(root)
        if ok:
            result.warnings.append(msg)
        else:
            result.warnings.append(msg)

    if not skip_godot_validate:
        g_ok, g_errors, g_warnings = validate_godot_scripts_headless(
            root,
            binary=result.godot_binary,
            required=result.godot_binary is not None,
        )
        result.warnings.extend(g_warnings)
        if not g_ok:
            result.success = False
            result.errors.extend(g_errors)

    if launch:
        if result.godot_binary is None:
            result.success = False
            result.errors.append(
                "Godot binary not found. Set GODOT_BIN, install godot on PATH, "
                "or on macOS install Godot.app in /Applications."
            )
        else:
            ok, cmd = launch_godot(
                root,
                binary=result.godot_binary,
                editor=editor,
                run_game=run_game,
            )
            result.launch_attempted = True
            result.launch_command = cmd
            if not ok:
                result.success = False
                result.errors.append(f"Launch failed: {cmd}")

    return result


def prepare_html_demo(
    *,
    repo_root: Path | None = None,
    scene_id: str = "solar-system",
    entity_name: str = "Hydrogen Ghost Institute",
    entity_type: str = "private_institute",
    motto: str = "Listening for the old light.",
    reset: bool = False,
    open_browser: bool = False,
) -> DemoPreparationResult:
    root = find_repo_root(repo_root)
    result = DemoPreparationResult(success=True, repo_root=root)

    if get_scene_definition(scene_id) is None:
        result.success = False
        result.errors.append(f"Unknown scene: {scene_id}")
        return result

    try:
        scene_path = generate_campaign_scene(scene_id, root)
        result.generated_scenes = [scene_path]
    except ValueError as exc:
        result.success = False
        result.errors.append(str(exc))
        return result

    try:
        state_path = ensure_game_state(
            root,
            reset=reset,
            entity_name=entity_name,
            entity_type=entity_type,
            motto=motto,
        )
        result.state_path = state_path
    except Exception as exc:  # noqa: BLE001
        result.success = False
        result.errors.append(f"game state: {exc}")
        return result

    scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)
    state = ResearchState.model_validate_json(state_path.read_text(encoding="utf-8"))
    out = html_output_path(root, scene_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.html_path = Path(export_telescope_ui(scene, state=state, out_path=out))

    if open_browser and result.html_path.is_file():
        try:
            if platform.system() == "Darwin":
                subprocess.Popen(["open", str(result.html_path)], start_new_session=True)
            elif platform.system() == "Windows":
                os.startfile(str(result.html_path))  # noqa: S606
            else:
                subprocess.Popen(["xdg-open", str(result.html_path)], start_new_session=True)
        except OSError as exc:
            result.warnings.append(f"Could not open browser: {exc}")

    return result


def prepare_unreal_demo(
    *,
    repo_root: Path | None = None,
    launch: bool = False,
) -> DemoPreparationResult:
    root = find_repo_root(repo_root)
    result = DemoPreparationResult(success=True, repo_root=root)

    try:
        scene_path = generate_campaign_scene("scene-001", root)
        result.generated_scenes = [scene_path]
    except ValueError as exc:
        result.success = False
        result.errors.append(str(exc))
        return result

    scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
    scene_data.pop("_units", None)
    scene = SceneRegion.model_validate(scene_data)
    out_dir = root / "frontends" / "unreal" / "Data"
    try:
        export_unreal_data(scene, str(out_dir))
    except Exception as exc:  # noqa: BLE001
        result.success = False
        result.errors.append(f"unreal export: {exc}")
        return result

    for rel in ("Universe.uproject", "Data/scene_unreal.json"):
        if not (root / "frontends" / "unreal" / rel).is_file():
            result.success = False
            result.errors.append(f"Missing: frontends/unreal/{rel}")

    if launch:
        result.warnings.append(
            "Unreal launch is not automated. Open frontends/unreal/Universe.uproject "
            "in Unreal Editor 5.x."
        )

    return result


def run_demo_check(
    repo_root: Path | None = None,
    *,
    godot_headless: bool | None = None,
) -> DemoCheckResult:
    root = find_repo_root(repo_root)
    checks: list[tuple[str, bool, str]] = []
    warnings: list[str] = []

    def add(label: str, ok: bool, detail: str = "") -> None:
        checks.append((label, ok, detail))

    for defn in get_default_scene_catalog():
        p = _rel(root, defn.default_output_path) / "scene.json"
        add(f"scene {defn.id}", p.is_file(), str(p.relative_to(root)) if p.is_file() else "missing")

    state_p = _rel(root, DEFAULT_STATE_REL)
    if state_p.is_file():
        try:
            ResearchState.model_validate_json(state_p.read_text(encoding="utf-8"))
            add("game-state.json", True, str(state_p.relative_to(root)))
        except Exception as exc:  # noqa: BLE001
            add("game-state.json", False, f"parse error: {exc}")
    else:
        add("game-state.json", False, "missing")

    godot_data = root / "frontends" / "godot" / "data"
    if (godot_data / "manifest.json").is_file():
        try:
            manifest = json.loads((godot_data / "manifest.json").read_text(encoding="utf-8"))
            add("godot manifest", "files" in manifest, "")
        except json.JSONDecodeError as exc:
            add("godot manifest", False, str(exc))
    else:
        add("godot manifest", False, "missing")

    catalog_p = godot_data / "scene_catalog.json"
    if catalog_p.is_file():
        try:
            catalog = json.loads(catalog_p.read_text(encoding="utf-8"))
            scene_count = len(catalog)
            add("scene catalog (6 scenes)", scene_count == 6, f"{scene_count} entries")
        except json.JSONDecodeError as exc:
            add("scene catalog", False, str(exc))
    else:
        add("scene catalog", False, "missing")

    for fname in GODOT_REQUIRED_DATA_FILES:
        p = godot_data / fname
        add(f"godot data/{fname}", p.is_file(), "")

    pg = root / "frontends" / "godot" / "project.godot"
    add("Godot project", pg.is_file(), "frontends/godot/project.godot")

    from universe.godot_integrity import (
        REQUIRED_GODOT_SCRIPTS,
        godot_project_complete,
        validate_godot_project,
    )

    if godot_project_complete(root):
        main_tscn = root / "frontends" / "godot" / "scenes" / "Main.tscn"
        add("Godot Main.tscn", main_tscn.is_file(), "frontends/godot/scenes/Main.tscn")

        godot_root = root / "frontends" / "godot"
        for script_rel in REQUIRED_GODOT_SCRIPTS:
            sp = godot_root / script_rel
            add(
                f"godot {script_rel}",
                sp.is_file(),
                str(sp.relative_to(root)) if sp.is_file() else "missing",
            )

        integrity = validate_godot_project(root)
        if integrity.broken_references:
            for src, ref in integrity.broken_references[:5]:
                add(f"godot ref {ref}", False, f"from {src}")
            if len(integrity.broken_references) > 5:
                warnings.append(
                    f"{len(integrity.broken_references) - 5} more broken res:// references"
                )
        else:
            add("godot res:// script refs", True, "all resolved")
    else:
        warnings.append(
            "Godot script scaffold incomplete — ensure frontends/godot/ is fully checked out"
        )
        add("godot project scaffold", False, "missing Main.gd or Main.tscn")

    binary = detect_godot_binary()
    if binary:
        add("Godot binary", True, str(binary))
    else:
        add("Godot binary", True, "not found (optional)")
        warnings.append("Godot binary not on PATH — use demo godot --launch after installing.")

    run_headless = godot_headless
    if run_headless is None:
        run_headless = binary is not None and godot_project_complete(root)

    if run_headless:
        if binary is None:
            add("godot headless validation", False, "Godot binary not found (set GODOT_BIN)")
        else:
            g_ok, g_errors, g_warnings = validate_godot_scripts_headless(
                root, binary=binary, required=True
            )
            warnings.extend(g_warnings)
            detail = "no script errors" if g_ok else (g_errors[0] if g_errors else "failed")
            add("godot headless validation", g_ok, detail)
            if not g_ok:
                for err in g_errors[:5]:
                    warnings.append(err)
    elif binary is None:
        warnings.append(
            "Godot binary not found; skipping script parse validation. "
            "Set GODOT_BIN once Godot is installed."
        )

    ow = overrides_warning(root)
    if ow:
        warnings.append(ow)
        add("overrides.json", False, "present — may override scene/state paths")
    else:
        user_dir = find_godot_user_data_dir(root)
        if user_dir and (user_dir / "overrides.json").is_file():
            add("overrides.json", False, str(user_dir / "overrides.json"))
        else:
            add("overrides.json", True, "none detected")

    required_ok = all(
        c[1]
        for c in checks
        if c[0] not in ("Godot binary", "overrides.json")
    )
    return DemoCheckResult(
        ok=required_ok,
        repo_root=root,
        checks=checks,
        warnings=warnings,
        godot_binary=binary,
    )


def format_godot_prep_message(result: DemoPreparationResult) -> str:
    lines: list[str] = []
    if result.success:
        lines.append("Godot demo prepared.")
    else:
        lines.append("Godot demo preparation failed.")

    if result.generated_scenes:
        lines.append("Generated scenes:")
        for p in result.generated_scenes:
            rel = p.relative_to(result.repo_root) if p.is_relative_to(result.repo_root) else p
            mark = "✓" if p.is_file() else "✗"
            lines.append(f"  {mark} {rel}")

    if result.state_path:
        rel = (
            result.state_path.relative_to(result.repo_root)
            if result.state_path.is_relative_to(result.repo_root)
            else result.state_path
        )
        mark = "✓" if result.state_path.is_file() else "✗"
        lines.append("State:")
        lines.append(f"  {mark} {rel}")

    if result.godot_data_dir:
        lines.append("Godot data:")
        for fname in GODOT_REQUIRED_DATA_FILES:
            p = result.godot_data_dir / fname
            rel = p.relative_to(result.repo_root) if p.is_relative_to(result.repo_root) else p
            mark = "✓" if p.is_file() else "✗"
            lines.append(f"  {mark} {rel}")

    lines.append("Open:")
    lines.append(f"  {result.repo_root / 'frontends' / 'godot' / 'project.godot'}")
    lines.append("Then press F5.")
    lines.append(
        "If Godot loads the wrong scene, remove user://overrides.json:\n"
        "  Project → Open User Data Folder → delete overrides.json"
    )

    for w in result.warnings:
        lines.append(f"Warning: {w}")
    for e in result.errors:
        lines.append(f"Error: {e}")

    if result.launch_attempted and result.launch_command:
        if result.success or result.godot_binary:
            lines.append(f"Launched: {result.launch_command}")
        else:
            lines.append(f"Attempted: {result.launch_command}")

    if result.godot_binary is None and not result.launch_attempted:
        lines.append(
            "Godot binary not detected. Install Godot 4.x or set GODOT_BIN to use --launch."
        )

    return "\n".join(lines)


def format_html_prep_message(result: DemoPreparationResult) -> str:
    lines: list[str] = ["HTML demo prepared:"]
    if result.html_path:
        rel = (
            result.html_path.relative_to(result.repo_root)
            if result.html_path.is_relative_to(result.repo_root)
            else result.html_path
        )
        lines.append(f"  {rel}")
        lines.append("Open:")
        if platform.system() == "Darwin":
            lines.append(f"  open {rel}")
        else:
            lines.append(f"  xdg-open {rel}")
    lines.append("Note: Static HTML cannot hot-swap campaign scenes.")
    lines.append("Regenerate with another --scene, or use Godot for live switching.")
    for w in result.warnings:
        lines.append(f"Warning: {w}")
    for e in result.errors:
        lines.append(f"Error: {e}")
    return "\n".join(lines)


def format_unreal_prep_message(result: DemoPreparationResult) -> str:
    lines: list[str] = []
    if result.success:
        lines.append("Unreal Scene 001 data prepared.")
    else:
        lines.append("Unreal demo preparation failed.")
    if result.generated_scenes:
        for p in result.generated_scenes:
            rel = p.relative_to(result.repo_root) if p.is_relative_to(result.repo_root) else p
            lines.append(f"  ✓ {rel}")
    lines.append("Open:")
    lines.append(f"  {result.repo_root / 'frontends' / 'unreal' / 'Universe.uproject'}")
    lines.append("Import uses frontends/unreal/Data/scene_unreal.json (see docs/unreal-frontend.md).")
    for w in result.warnings:
        lines.append(f"Warning: {w}")
    for e in result.errors:
        lines.append(f"Error: {e}")
    return "\n".join(lines)


def format_check_message(check: DemoCheckResult) -> str:
    lines: list[str] = ["Demo check:" if check.ok else "Demo check FAILED:"]
    for label, ok, detail in check.checks:
        mark = "✓" if ok else "✗"
        suffix = f" — {detail}" if detail else ""
        lines.append(f"  {mark} {label}{suffix}")
    for w in check.warnings:
        lines.append(f"Warning: {w}")
    return "\n".join(lines)
