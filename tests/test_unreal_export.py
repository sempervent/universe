"""Tests for the Unreal frontend scaffold and optional data export."""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from universe.cli import main
from universe.export.unreal_data import build_unreal_bundle, export_unreal_data
from universe.procedural.region import generate_scene_001

REPO_ROOT = Path(__file__).resolve().parent.parent
UNREAL_ROOT = REPO_ROOT / "frontends" / "unreal"
SOURCE_ROOT = UNREAL_ROOT / "Source" / "Universe"


class TestUnrealScaffold:
    def test_uproject_exists(self):
        assert (UNREAL_ROOT / "Universe.uproject").exists()

    def test_readme_mentions_scene_001(self):
        readme = (UNREAL_ROOT / "README.md").read_text(encoding="utf-8")
        assert "scene-001" in readme or "Scene 001" in readme
        assert "Universe.uproject" in readme

    def test_gitignore_excludes_unreal_artifacts(self):
        gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        for fragment in ["Binaries/", "Intermediate/", "DerivedDataCache/", "frontends/unreal/"]:
            assert fragment in gi

    def test_importer_source_exists(self):
        assert (SOURCE_ROOT / "Public" / "UniverseSceneImporter.h").exists()
        assert (SOURCE_ROOT / "Private" / "UniverseSceneImporter.cpp").exists()

    def test_signal_mode_subsystem_lists_modes(self):
        text = (SOURCE_ROOT / "Public" / "UniverseSignalModeSubsystem.h").read_text(
            encoding="utf-8"
        )
        assert "EUniverseSignalMode" in text
        assert "SpeculativeNowSignal" in text
        assert "WeakLensing" in text

    def test_renderer_mentions_key_object_types(self):
        obj_cpp = (SOURCE_ROOT / "Private" / "UniverseObjectActor.cpp").read_text(
            encoding="utf-8"
        )
        for needle in [
            "lyman_alpha_blob",
            "quasar",
            "black_hole",
            "magnetar",
        ]:
            assert needle in obj_cpp

    def test_filament_uses_control_points_path(self):
        scene_cpp = (SOURCE_ROOT / "Private" / "UniverseSceneActor.cpp").read_text(
            encoding="utf-8"
        )
        assert "ControlPointsMpc" in scene_cpp
        assert "cosmic_web_filament" in (SOURCE_ROOT / "Private" / "UniverseSignalModeSubsystem.cpp").read_text(
            encoding="utf-8"
        )

    def test_cosmic_materials_subsystem_exists(self):
        assert (SOURCE_ROOT / "Public" / "UniverseCosmicMaterials.h").exists()
        readme = (UNREAL_ROOT / "Content/Docs/Materials.md").read_text(encoding="utf-8")
        assert "UUniverseCosmicMaterials" in readme

    def test_click_selection_in_pawn(self):
        pawn = (SOURCE_ROOT / "Private" / "UniverseTelescopePawn.cpp").read_text(encoding="utf-8")
        assert "SelectObjectUnderCursor" in pawn
        assert "GetHitResultUnderCursor" in pawn

    def test_scene_metadata_camera_and_signal(self):
        scene_cpp = (SOURCE_ROOT / "Private" / "UniverseSceneActor.cpp").read_text(encoding="utf-8")
        assert "RecommendedInitialSignalMode" in scene_cpp
        assert "RecommendedCameraTargetObjectId" in scene_cpp
        assert "SetModeFromString" in scene_cpp

    def test_signal_visual_struct_and_apply(self):
        assert (SOURCE_ROOT / "Public" / "UniverseSignalVisual.h").exists()
        obj_cpp = (SOURCE_ROOT / "Private" / "UniverseObjectActor.cpp").read_text(encoding="utf-8")
        assert "ApplySignalVisual" in obj_cpp
        assert "GetVisualForType" in (SOURCE_ROOT / "Private" / "UniverseSignalModeSubsystem.cpp").read_text(
            encoding="utf-8"
        )

    def test_readme_controls_click_and_tab(self):
        readme = (UNREAL_ROOT / "README.md").read_text(encoding="utf-8")
        assert "Click" in readme or "click" in readme
        assert "Tab" in readme
        assert "recommended" in readme.lower()


class TestUnrealDocs:
    def test_unreal_frontend_doc_exists(self):
        assert (REPO_ROOT / "docs" / "unreal-frontend.md").exists()

    def test_readme_links_unreal(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "unreal-frontend.md" in readme or "frontends/unreal" in readme

    def test_roadmap_mentions_unreal_prototype(self):
        roadmap = (REPO_ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")
        assert "frontends/unreal" in roadmap


class TestExportUnrealData:
    def test_build_bundle_has_metadata_and_featured(self):
        scene = generate_scene_001(seed="unreal-test", num_galaxies=5, num_nodes=4)
        bundle = build_unreal_bundle(scene)
        assert bundle["scene"]["metadata"]["scene_class"] == "deep_field"
        assert len(bundle["featured_objects"]) > 0
        assert "lyman_alpha_blob" in bundle["signal_modes"] or "visible_light" in bundle["signal_modes"]

    def test_cli_writes_files(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            scene_dir = Path(tmp) / "scene-001"
            scene_dir.mkdir()
            scene = generate_scene_001(seed="cli-unreal", num_galaxies=5, num_nodes=4)
            scene_path = scene_dir / "scene.json"
            from universe.export.scene_json import export_scene

            export_scene(scene, scene_dir)
            out = Path(tmp) / "unreal-data"
            result = runner.invoke(
                main,
                [
                    "game",
                    "export-unreal-data",
                    "--scene",
                    str(scene_path),
                    "--out",
                    str(out),
                ],
            )
            assert result.exit_code == 0, result.output
            for fname in [
                "scene_unreal.json",
                "manifest.json",
                "material_hints.json",
                "featured_objects.json",
                "signal_mode_emphasis.json",
                "signal_mode_palettes.json",
            ]:
                assert (out / fname).exists()
                json.loads((out / fname).read_text(encoding="utf-8"))

    def test_manifest_lists_scene_id(self):
        scene = generate_scene_001(seed="manifest", num_galaxies=3, num_nodes=3)
        with tempfile.TemporaryDirectory() as tmp:
            paths = export_unreal_data(scene, tmp)
            manifest = json.loads(paths["manifest.json"].read_text(encoding="utf-8"))
            assert manifest["scene_id"] == "scene-001"
            assert "scene_unreal.json" in manifest["files"]
            assert manifest.get("recommended_camera_target_object_id", "") != ""
            assert "signal_mode_emphasis.json" in manifest["files"]
