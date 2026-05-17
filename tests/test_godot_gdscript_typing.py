"""Conservative GDScript typing guardrails (no Godot binary required)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GODOT_SCRIPTS = REPO_ROOT / "frontends" / "godot" / "scripts"

RISKY_INFERENCE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*var\s+\w+\s*:=\s*\w+\.get\("), "Dictionary.get()"),
    (re.compile(r"^\s*var\s+\w+\s*:=\s*get_node_or_null\("), "get_node_or_null()"),
    (re.compile(r"^\s*var\s+\w+\s*:=\s*\w+\.get_meta\("), "get_meta()"),
    (re.compile(r"^\s*var\s+\w+\s*:=\s*\w+\.get_parent\("), "get_parent()"),
    (re.compile(r"^\s*var\s+\w+\s*:=\s*\w+\.find_child\("), "find_child()"),
)

ALLOWLIST: tuple[tuple[str, int], ...] = ()


def find_risky_gdscript_inferences(scripts_dir: Path | None = None) -> list[str]:
    """Return human-readable violations for risky `:=` inference patterns."""
    root = scripts_dir or GODOT_SCRIPTS
    violations: list[str] = []
    for path in sorted(root.glob("*.gd")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if (path.name, lineno) in ALLOWLIST:
                continue
            for pattern, reason in RISKY_INFERENCE_PATTERNS:
                if pattern.search(line):
                    rel = path.relative_to(REPO_ROOT)
                    violations.append(
                        f"{rel}:{lineno}: do not infer type from {reason}; "
                        f"use `var name: Type = ...` — {line.strip()}"
                    )
                    break
    return violations


class TestGodotGdscriptTypingGuard:
    def test_no_risky_inference_patterns_in_scripts(self):
        violations = find_risky_gdscript_inferences()
        assert not violations, (
            "Do not infer local variable type from Dictionary/Variant/Node lookup "
            "in GDScript. Use `var name: Type = ...`.\n"
            + "\n".join(violations[:20])
        )
