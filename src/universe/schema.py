"""JSON Schema utilities for scene.json validation and documentation."""

from __future__ import annotations

import json

from universe.models import SceneRegion


def generate_json_schema() -> dict:
    """Return the JSON Schema for a SceneRegion (the root of scene.json)."""
    return SceneRegion.model_json_schema()


def schema_as_json(indent: int = 2) -> str:
    return json.dumps(generate_json_schema(), indent=indent)
