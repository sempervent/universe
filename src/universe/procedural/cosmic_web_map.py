"""Cosmic web mapping scene — filaments, nodes, voids, lensing tracers."""

from __future__ import annotations

from universe.models import (
    CosmicObject,
    ObjectType,
    SceneMetadata,
    SceneRegion,
    VisualHints,
    VisualMode,
)
from universe.procedural.cosmic_web import generate_filaments, generate_nodes
from universe.procedural.objects import generate_galaxies, generate_void
from universe.units import SCENE_001_REDSHIFT


def generate_cosmic_web_map(seed: str = "invisible-architecture") -> SceneRegion:
    region_size = 60.0
    redshift = SCENE_001_REDSHIFT
    num_nodes = 10

    nodes = generate_nodes(seed, count=num_nodes, region_size=region_size)
    filaments = generate_filaments(seed, nodes, max_distance_mpc=region_size * 0.4)
    galaxies = generate_galaxies(seed, nodes, filaments, redshift, count=24)

    lensing_props = {
        "required_signal_types": ["weak_lensing"],
        "optional_signal_types": ["dark_matter_inference", "visible_light"],
    }
    for gal in galaxies[:12]:
        gal.properties.update(lensing_props)
        gal.properties["mass_tracer"] = True

    voids = [generate_void(seed, region_size, redshift, i) for i in range(3)]
    for v in voids:
        v.properties.update(lensing_props)

    core_node = nodes[0]
    dm_marker = CosmicObject(
        id="dm-inference-001",
        name="Dark Matter Ridge",
        type=ObjectType.COSMIC_WEB_FILAMENT,
        position_mpc=core_node.position_mpc,
        redshift=redshift,
        description=(
            "Inferred overdensity along a filament — visible only through weak lensing "
            "and dark-matter mass maps."
        ),
        properties={
            **lensing_props,
            "inferred_mass_msun": 1e14,
        },
        visual=VisualHints(
            color="#6644aa",
            opacity=0.25,
            scale=12.0,
            label="DM Ridge [inferred]",
        ),
    )

    all_objects = galaxies + voids + [dm_marker]
    featured = [dm_marker.id, voids[0].id]
    if galaxies:
        featured.append(galaxies[0].id)

    return SceneRegion(
        id="cosmic-web-map",
        name="Cosmic Web Map",
        seed=seed,
        redshift=redshift,
        size_mpc=region_size,
        objects=all_objects,
        nodes=nodes,
        filaments=filaments,
        metadata=SceneMetadata(
            schema_version="0.1.0",
            generator="universe",
            description=(
                "Large-scale structure map: filaments, voids, and galaxies as tracers "
                "for weak lensing and dark-matter inference."
            ),
            scientific_caveats=[
                "Cosmic web graph is proximity-based scaffolding, not simulation output.",
                "Dark-matter ridge is a narrative inference marker, not a direct detection.",
            ],
            scene_class="deep_field",
            recommended_camera_target_object_id=dm_marker.id,
            recommended_initial_signal_mode="weak_lensing",
            featured_object_ids=featured,
            teaching_summary=(
                "Weak lensing and galaxy distributions infer invisible mass in filaments "
                "and voids — structure you cannot see in visible light alone."
            ),
            scale_description=f"~{region_size:.0f} cMpc region with embedded web graph.",
        ),
        visual_modes=[VisualMode.DENSITY.value, VisualMode.BEAUTY.value],
    )
