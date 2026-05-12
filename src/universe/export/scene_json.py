"""Export a SceneRegion to scene.json, summary.md, and preview.html."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from universe.models import SceneRegion
from universe.preview.static_html import render_preview_html
from universe.units import UNIT_CONVENTIONS


def export_scene(scene: SceneRegion, out_dir: str | Path) -> dict[str, Path]:
    """Write scene.json, summary.md, and preview.html to *out_dir*.

    Returns a dict of artifact name -> path.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    scene_path = out / "scene.json"
    summary_path = out / "summary.md"
    preview_path = out / "preview.html"

    scene_dict = json.loads(scene.model_dump_json())
    scene_dict["_units"] = UNIT_CONVENTIONS

    scene_path.write_text(json.dumps(scene_dict, indent=2), encoding="utf-8")
    summary_path.write_text(_build_summary(scene), encoding="utf-8")
    preview_path.write_text(render_preview_html(scene), encoding="utf-8")

    return {
        "scene.json": scene_path,
        "summary.md": summary_path,
        "preview.html": preview_path,
    }


def _build_summary(scene: SceneRegion) -> str:
    counts = Counter(obj.type.value for obj in scene.objects)
    notable = [o for o in scene.objects if o.type.value in (
        "lyman_alpha_blob", "quasar", "black_hole", "magnetar",
    )]

    lines = [
        f"# {scene.name}",
        "",
        f"**Seed:** `{scene.seed}`  ",
        f"**Redshift:** z = {scene.redshift}  ",
        f"**Region size:** {scene.size_mpc} cMpc  ",
        f"**Schema version:** {scene.metadata.schema_version}  ",
        "",
        "## Object counts",
        "",
    ]
    for otype, cnt in sorted(counts.items()):
        lines.append(f"- {otype}: {cnt}")

    lines += [
        f"- cosmic_web_node: {len(scene.nodes)}",
        f"- cosmic_web_filament: {len(scene.filaments)}",
        "",
        "## Notable objects",
        "",
    ]
    for obj in notable:
        lines.append(f"### {obj.name} ({obj.type.value})")
        lines.append("")
        lines.append(f"{obj.description}")
        lines.append("")
        for k, v in obj.properties.items():
            lines.append(f"- **{k}:** {v}")
        lines.append("")

    lines += [
        "## Scientific caveats",
        "",
    ]
    for caveat in scene.metadata.scientific_caveats:
        lines.append(f"- {caveat}")

    lines += [
        "",
        "## Units",
        "",
    ]
    for k, v in UNIT_CONVENTIONS.items():
        lines.append(f"- **{k}:** {v}")

    lines.append("")
    return "\n".join(lines)
