"""Export a convenience bundle for the Unreal frontend.

The canonical scene contract remains ``scene.json`` from ``export_scene``.
This transform adds normalized render coordinates and material hints only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from universe.models import SceneRegion, Vector3


def _vec_dict(v: Vector3) -> dict[str, float]:
    return {"x": v.x, "y": v.y, "z": v.z}


def _normalize_deep_field(scene: SceneRegion) -> tuple[Vector3, float]:
    """Return (centroid_mpc, world_scale) matching Godot deep-field layout."""
    featured = scene.metadata.featured_object_ids
    positions: list[Vector3] = []
    if featured:
        by_id = {o.id: o for o in scene.objects}
        for oid in featured:
            if oid in by_id:
                positions.append(by_id[oid].position_mpc)
    if not positions:
        for o in scene.objects:
            if o.type.value in ("lyman_alpha_blob", "quasar", "black_hole"):
                positions.append(o.position_mpc)
    if not positions:
        positions = [o.position_mpc for o in scene.objects[:1]]
    cx = sum(p.x for p in positions) / len(positions)
    cy = sum(p.y for p in positions) / len(positions)
    cz = sum(p.z for p in positions) / len(positions)
    centroid = Vector3(x=cx, y=cy, z=cz)
    scale = 32.0 / max(scene.size_mpc, 1e-6)
    return centroid, scale


def _to_render_space(pos: Vector3, centroid: Vector3, scale: float, solar: bool) -> dict[str, float]:
    if solar:
        return _vec_dict(pos)
    return {
        "x": (pos.x - centroid.x) * scale,
        "y": (pos.y - centroid.y) * scale,
        "z": (pos.z - centroid.z) * scale,
    }


def _material_hint_for_type(object_type: str) -> dict[str, Any]:
    hints: dict[str, dict[str, Any]] = {
        "lyman_alpha_blob": {
            "profile": "volumetric_shell",
            "emissive_scale": 1.4,
            "opacity": 0.35,
            "pulse": True,
        },
        "quasar": {
            "profile": "compact_jets",
            "emissive_scale": 2.5,
            "jet_length_units": 14.0,
        },
        "black_hole": {
            "profile": "accretion_placeholder",
            "emissive_scale": 0.15,
            "indirect_detection": True,
        },
        "magnetar": {
            "profile": "pulsar_compact",
            "emissive_scale": 1.8,
            "pulse": True,
        },
        "galaxy": {"profile": "instanced_point", "emissive_scale": 0.6},
        "cosmic_web_filament": {"profile": "spline_tube", "emissive_scale": 0.5},
        "cosmic_web_node": {"profile": "cluster_marker", "emissive_scale": 0.7},
        "void": {"profile": "translucent_volume", "opacity": 0.2},
        "cmb_background": {"profile": "sky_shell", "emissive_scale": 0.25},
    }
    return hints.get(object_type, {"profile": "default_sphere", "emissive_scale": 0.5})


def _signal_mode_emphasis_table() -> dict[str, dict[str, float]]:
    """Illustrative per-type emphasis for Unreal (0..1); C++ is authoritative at runtime."""
    types = [
        "galaxy",
        "lyman_alpha_blob",
        "quasar",
        "black_hole",
        "magnetar",
        "cosmic_web_filament",
        "cosmic_web_node",
        "void",
        "cmb_background",
    ]
    modes = [
        "visible_light",
        "radio",
        "microwave",
        "xray",
        "gamma_ray",
        "gravitational_wave",
        "neutrino",
        "weak_lensing",
        "dark_matter_inference",
        "speculative_now_signal",
    ]
    # Representative deep-field emphasis (matches Unreal UUniverseSignalModeSubsystem).
    table: dict[str, dict[str, float]] = {m: {} for m in modes}
    table["visible_light"] = {
        "galaxy": 1.0,
        "quasar": 1.0,
        "lyman_alpha_blob": 0.48,
        "black_hole": 0.1,
        "cosmic_web_filament": 0.22,
        "cmb_background": 0.15,
    }
    table["radio"] = {
        "quasar": 1.0,
        "magnetar": 1.0,
        "cmb_background": 0.45,
        "galaxy": 0.32,
        "cosmic_web_filament": 0.28,
    }
    table["microwave"] = {"cmb_background": 1.0, "galaxy": 0.18}
    table["xray"] = {"magnetar": 1.0, "black_hole": 1.0, "quasar": 1.0}
    table["gamma_ray"] = table["xray"]
    table["gravitational_wave"] = {
        "black_hole": 0.88,
        "magnetar": 0.88,
        "quasar": 0.88,
        "galaxy": 0.1,
    }
    table["neutrino"] = {
        "black_hole": 0.82,
        "magnetar": 0.82,
        "quasar": 0.82,
        "galaxy": 0.11,
    }
    table["weak_lensing"] = {
        "cosmic_web_filament": 1.0,
        "cosmic_web_node": 0.85,
        "void": 0.92,
        "galaxy": 0.92,
    }
    table["dark_matter_inference"] = {
        "cosmic_web_filament": 1.0,
        "void": 1.0,
        "cosmic_web_node": 0.95,
        "galaxy": 0.55,
        "quasar": 0.12,
    }
    table["speculative_now_signal"] = {
        "quasar": 0.92,
        "lyman_alpha_blob": 0.92,
        "black_hole": 0.92,
    }
    for mode in modes:
        for t in types:
            table[mode].setdefault(t, 0.2)
    return table


def _signal_mode_palettes() -> dict[str, dict[str, list[float]]]:
    return {
        "visible_light": {"ambient_tint": [0.25, 0.3, 0.42]},
        "radio": {"ambient_tint": [0.35, 0.22, 0.45]},
        "microwave": {"ambient_tint": [0.45, 0.25, 0.35]},
        "xray": {"ambient_tint": [0.2, 0.35, 0.55]},
        "speculative_now_signal": {"ambient_tint": [0.5, 0.2, 0.45]},
    }


def build_unreal_bundle(scene: SceneRegion) -> dict[str, Any]:
    solar = scene.metadata.scene_class == "solar_system" or scene.id == "solar-system"
    centroid, scale = (Vector3(), 1.0) if solar else _normalize_deep_field(scene)

    objects_out: list[dict[str, Any]] = []
    for obj in scene.objects:
        objects_out.append(
            {
                "id": obj.id,
                "name": obj.name,
                "type": obj.type.value,
                "position_mpc": _vec_dict(obj.position_mpc),
                "position_render": _to_render_space(obj.position_mpc, centroid, scale, solar),
                "redshift": obj.redshift,
                "description": obj.description,
                "visual": obj.visual.model_dump(mode="json"),
                "material_hint": _material_hint_for_type(obj.type.value),
                "relationships": [r.model_dump(mode="json") for r in obj.relationships],
            }
        )

    nodes_out: list[dict[str, Any]] = []
    node_mpc: dict[str, Vector3] = {}
    for node in scene.nodes:
        node_mpc[node.id] = node.position_mpc
        nodes_out.append(
            {
                "id": node.id,
                "position_mpc": _vec_dict(node.position_mpc),
                "position_render": _to_render_space(node.position_mpc, centroid, scale, solar),
                "density": node.density,
                "node_class": node.node_class.value,
            }
        )

    filaments_out: list[dict[str, Any]] = []
    for fil in scene.filaments:
        path_mpc: list[dict[str, float]] = []
        if fil.start_node_id in node_mpc:
            path_mpc.append(_vec_dict(node_mpc[fil.start_node_id]))
        for cp in fil.control_points_mpc:
            path_mpc.append(_vec_dict(cp))
        if fil.end_node_id in node_mpc:
            path_mpc.append(_vec_dict(node_mpc[fil.end_node_id]))
        path_render = [
            _to_render_space(
                Vector3(x=p["x"], y=p["y"], z=p["z"]),
                centroid,
                scale,
                solar,
            )
            for p in path_mpc
        ]
        filaments_out.append(
            {
                "id": fil.id,
                "start_node_id": fil.start_node_id,
                "end_node_id": fil.end_node_id,
                "control_points_mpc": [_vec_dict(cp) for cp in fil.control_points_mpc],
                "path_mpc": path_mpc,
                "path_render": path_render,
                "density": fil.density,
                "radius_mpc": fil.radius_mpc,
            }
        )

    featured: list[dict[str, Any]] = []
    by_id = {o.id: o for o in scene.objects}
    for oid in scene.metadata.featured_object_ids:
        if oid in by_id:
            o = by_id[oid]
            featured.append({"id": o.id, "name": o.name, "type": o.type.value})

    return {
        "schema_version": "0.1.0",
        "source": "universe.export.unreal_data",
        "canonical_scene_json": True,
        "scene": {
            "id": scene.id,
            "name": scene.name,
            "seed": scene.seed,
            "redshift": scene.redshift,
            "size_mpc": scene.size_mpc,
            "metadata": scene.metadata.model_dump(mode="json"),
            "layout": {
                "scene_class": scene.metadata.scene_class or ("solar_system" if solar else "deep_field"),
                "centroid_mpc": _vec_dict(centroid),
                "render_scale_from_mpc": scale,
                "coordinate_note": "position_render uses Godot-aligned normalization for deep field",
            },
            "objects": objects_out,
            "nodes": nodes_out,
            "filaments": filaments_out,
        },
        "featured_objects": featured,
        "signal_modes": [
            "visible_light",
            "radio",
            "microwave",
            "xray",
            "gamma_ray",
            "gravitational_wave",
            "neutrino",
            "weak_lensing",
            "dark_matter_inference",
            "speculative_now_signal",
            "ultraviolet",
            "infrared",
        ],
    }


def export_unreal_data(scene: SceneRegion, out_dir: str | Path) -> dict[str, Path]:
    """Write Unreal convenience JSON files under *out_dir*."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    bundle = build_unreal_bundle(scene)
    material_hints = {
        o["type"]: o["material_hint"] for o in bundle["scene"]["objects"]
    }
    # dedupe by type
    by_type: dict[str, Any] = {}
    for t, hint in material_hints.items():
        by_type.setdefault(t, hint)

    paths: dict[str, Path] = {}
    scene_path = out / "scene_unreal.json"
    scene_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    paths["scene_unreal.json"] = scene_path

    featured_path = out / "featured_objects.json"
    featured_path.write_text(
        json.dumps(
            {
                "featured_object_ids": scene.metadata.featured_object_ids,
                "objects": bundle["featured_objects"],
                "recommended_camera_target_object_id": scene.metadata.recommended_camera_target_object_id,
                "recommended_initial_signal_mode": scene.metadata.recommended_initial_signal_mode,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    paths["featured_objects.json"] = featured_path

    hints_path = out / "material_hints.json"
    hints_path.write_text(json.dumps(by_type, indent=2), encoding="utf-8")
    paths["material_hints.json"] = hints_path

    emphasis_path = out / "signal_mode_emphasis.json"
    emphasis_path.write_text(json.dumps(_signal_mode_emphasis_table(), indent=2), encoding="utf-8")
    paths["signal_mode_emphasis.json"] = emphasis_path

    palettes_path = out / "signal_mode_palettes.json"
    palettes_path.write_text(json.dumps(_signal_mode_palettes(), indent=2), encoding="utf-8")
    paths["signal_mode_palettes.json"] = palettes_path

    manifest_path = out / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "files": sorted(list(paths.keys()) + ["manifest.json"]),
                "scene_id": scene.id,
                "scene_name": scene.name,
                "recommended_camera_target_object_id": scene.metadata.recommended_camera_target_object_id,
                "recommended_initial_signal_mode": scene.metadata.recommended_initial_signal_mode,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    paths["manifest.json"] = manifest_path
    return paths
