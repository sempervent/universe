"""Export JSON data bundle for the Godot frontend."""

from __future__ import annotations

import json
from pathlib import Path

from universe.game.discovery import get_discovery_requirements
from universe.game.entity import ENTITY_TYPE_LABELS, RANDOM_ENTITY_NAMES, get_all_entity_modifiers
from universe.game.milestones import get_default_milestones
from universe.game.models import SignalType
from universe.game.objectives import objectives_for_export
from universe.game.scenes import catalog_for_export
from universe.game.surveys import get_default_survey_programs
from universe.game.tech_tree import get_default_tech_tree
from universe.game.transients import transients_for_export


def export_godot_data_bundle(out_dir: Path) -> dict[str, Path]:
    """Write Godot frontend JSON bundle; return filename → path map."""
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle: dict[str, object] = {
        "tech_tree.json": [t.model_dump(mode="json") for t in get_default_tech_tree()],
        "surveys.json": [s.model_dump(mode="json") for s in get_default_survey_programs()],
        "milestones.json": [m.model_dump(mode="json") for m in get_default_milestones()],
        "discovery_requirements.json": [
            r.model_dump(mode="json") for r in get_discovery_requirements()
        ],
        "signal_types.json": [s.value for s in SignalType],
        "entity_types.json": ENTITY_TYPE_LABELS,
        "random_entity_names.json": RANDOM_ENTITY_NAMES,
        "entity_modifiers.json": [m.model_dump(mode="json") for m in get_all_entity_modifiers()],
        "scene_catalog.json": catalog_for_export(),
        "transient_events.json": transients_for_export(),
        "objectives.json": objectives_for_export(),
    }
    manifest = {"files": list(bundle.keys()), "schema_version": "0.5.0"}
    bundle["manifest.json"] = manifest

    written: dict[str, Path] = {}
    for filename, payload in bundle.items():
        path = out_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written[filename] = path
    return written
