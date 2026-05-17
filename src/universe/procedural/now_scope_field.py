"""Speculative now-scope anomaly field — fictional endgame observation."""

from __future__ import annotations

from universe.models import (
    SceneMetadata,
    SceneRegion,
    VisualMode,
)
from universe.procedural.cosmic_web import generate_nodes
from universe.procedural.objects import (
    generate_cmb_background,
    generate_speculative_anomaly,
    generate_void,
)


def generate_now_scope_anomaly_field(seed: str = "impossible-now") -> SceneRegion:
    region_size = 40.0
    redshift = 1.5

    nodes = generate_nodes(seed, count=6, region_size=region_size)
    cmb = generate_cmb_background(redshift)
    void = generate_void(seed, region_size, redshift, 0)

    anomaly1 = generate_speculative_anomaly(seed, redshift)
    anomaly1.id = "spec-now-001"
    anomaly1.name = "Present-Tense Echo"
    anomaly1.properties["required_signal_types"] = ["speculative_now_signal"]
    anomaly1.properties["optional_signal_types"] = []

    anomaly2 = generate_speculative_anomaly(seed + ":b", redshift)
    anomaly2.id = "spec-now-002"
    anomaly2.name = "Causality Shear"
    anomaly2.position_mpc.x += 3.0
    anomaly2.properties["required_signal_types"] = ["speculative_now_signal"]

    all_objects = [cmb, void, anomaly1, anomaly2]
    featured = [anomaly1.id, anomaly2.id]

    return SceneRegion(
        id="now-scope-anomaly-field",
        name="Now-Scope Anomaly Field",
        seed=seed,
        redshift=redshift,
        size_mpc=region_size,
        objects=all_objects,
        nodes=nodes,
        filaments=[],
        metadata=SceneMetadata(
            schema_version="0.1.0",
            generator="universe",
            description=(
                "Speculative endgame field: fictional now-scope anomalies amid "
                "cosmic web context. Not physically real."
            ),
            scientific_caveats=[
                "All now-scope targets are fictional placeholders.",
                "Does not represent real astrophysics or causality-violating observation.",
            ],
            scene_class="speculative",
            recommended_camera_target_object_id=anomaly1.id,
            recommended_initial_signal_mode="speculative_now_signal",
            featured_object_ids=featured,
            teaching_summary=(
                "Fictional endgame 'now-scope' mode — causality-independent observation "
                "beyond light-cone constraints. Speculative flavor only."
            ),
            scale_description="Schematic speculative field; not a survey catalog.",
        ),
        visual_modes=[VisualMode.BEAUTY.value],
    )
