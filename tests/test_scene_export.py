"""Tests for scene export (JSON, summary, preview)."""

import json
import tempfile

from universe.export.scene_json import export_scene
from universe.models import SceneRegion
from universe.procedural.region import generate_scene_001


SEED = "lyman-alpha-furnace"


class TestExport:
    def test_artifacts_written(self):
        scene = generate_scene_001(seed=SEED)
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = export_scene(scene, tmp)
            assert "scene.json" in artifacts
            assert "summary.md" in artifacts
            assert "preview.html" in artifacts
            for path in artifacts.values():
                assert path.exists()
                assert path.stat().st_size > 0

    def test_scene_json_valid(self):
        scene = generate_scene_001(seed=SEED)
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = export_scene(scene, tmp)
            data = json.loads(artifacts["scene.json"].read_text())
            assert data["id"] == "scene-001"
            assert data["name"] == "The Lyman-alpha Furnace"
            assert "_units" in data
            assert len(data["objects"]) > 0
            assert len(data["nodes"]) > 0
            assert len(data["filaments"]) > 0
            meta = data.get("metadata", {})
            assert meta.get("scene_class") == "deep_field"
            assert meta.get("recommended_camera_target_object_id", "") != ""
            assert isinstance(meta.get("featured_object_ids", []), list)
            rec = meta["recommended_camera_target_object_id"]
            by_id = {o["id"]: o for o in data["objects"]}
            assert by_id[rec]["type"] == "lyman_alpha_blob"

    def test_scene_json_roundtrip(self):
        scene = generate_scene_001(seed=SEED)
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = export_scene(scene, tmp)
            data = json.loads(artifacts["scene.json"].read_text())
            # Remove _units (not part of model)
            data.pop("_units", None)
            restored = SceneRegion.model_validate(data)
            assert restored.id == scene.id
            assert len(restored.objects) == len(scene.objects)

    def test_summary_contains_key_info(self):
        scene = generate_scene_001(seed=SEED)
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = export_scene(scene, tmp)
            summary = artifacts["summary.md"].read_text()
            assert "Lyman-alpha" in summary
            assert "quasar" in summary or "Lucerna" in summary
            assert SEED in summary

    def test_preview_html_structure(self):
        scene = generate_scene_001(seed=SEED)
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = export_scene(scene, tmp)
            html = artifacts["preview.html"].read_text()
            assert "<!DOCTYPE html>" in html
            assert "three" in html.lower() or "THREE" in html
            assert scene.name in html


class TestCLISmoke:
    def test_generate_via_module(self):
        """Smoke test: ensure generation + export runs without error."""
        scene = generate_scene_001(seed=SEED)
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = export_scene(scene, tmp)
            scene_path = artifacts["scene.json"]
            data = json.loads(scene_path.read_text())
            assert data["seed"] == SEED
