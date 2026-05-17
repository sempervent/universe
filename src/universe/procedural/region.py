"""Scene 001 region assembler.

Orchestrates cosmic_web and objects generators into a complete SceneRegion.
"""

from __future__ import annotations

from universe.models import (
    NodeClass,
    SceneMetadata,
    SceneRegion,
    VisualMode,
)
from universe.procedural.cosmic_web import generate_filaments, generate_nodes
from universe.procedural.objects import (
    generate_cmb_background,
    generate_galaxies,
    generate_lyman_alpha_blob,
    generate_magnetar,
    generate_quasar_system,
    generate_speculative_anomaly,
    generate_void,
)
from universe.units import SCENE_001_REDSHIFT, SCENE_001_REGION_SIZE_MPC


def generate_scene_001(
    seed: str = "lyman-alpha-furnace",
    num_nodes: int = 12,
    num_galaxies: int = 80,
    region_size: float = SCENE_001_REGION_SIZE_MPC,
    redshift: float = SCENE_001_REDSHIFT,
) -> SceneRegion:
    """Build the complete 'Lyman-alpha Furnace' scene deterministically."""

    nodes = generate_nodes(seed, count=num_nodes, region_size=region_size)
    filaments = generate_filaments(seed, nodes, max_distance_mpc=region_size * 0.45)

    galaxies = generate_galaxies(seed, nodes, filaments, redshift, count=num_galaxies)

    core = next((n for n in nodes if n.node_class == NodeClass.PROTOCLUSTER_CORE), nodes[0])

    # Find galaxies near the core for LAB embedding
    core_pos = core.position_mpc
    nearby_gals = sorted(galaxies, key=lambda g: g.position_mpc.distance_to(core_pos))
    nearby_ids = [g.id for g in nearby_gals[:8]]

    lab = generate_lyman_alpha_blob(seed, core, nearby_ids, redshift)
    quasar, black_hole = generate_quasar_system(seed, core, redshift)

    # Magnetar inside the nearest galaxy to the core
    host_galaxy = nearby_gals[0] if nearby_gals else galaxies[0]
    magnetar = generate_magnetar(seed, host_galaxy, redshift)

    cmb = generate_cmb_background(redshift)
    voids = [generate_void(seed, region_size, redshift, i) for i in range(2)]
    anomaly = generate_speculative_anomaly(seed, redshift)

    all_objects = [lab, quasar, black_hole, magnetar, cmb, anomaly] + voids + galaxies

    return SceneRegion(
        id="scene-001",
        name="The Lyman-alpha Furnace",
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
                "A high-redshift protocluster scene at z≈3.1 containing cosmic web "
                "structure, a luminous Lyman-alpha blob, a quasar/black-hole system, "
                "young galaxies, and a magnetar."
            ),
            scientific_caveats=[
                "Positions use simplified random placement, not N-body simulation.",
                "Galaxy properties are order-of-magnitude estimates, not catalog-derived.",
                "Cosmic web topology is a proximity graph, not a Delaunay/Voronoi tessellation.",
                "Redshift perturbations are cosmetic, not from peculiar velocities.",
                "Lyman-alpha blob luminosity is representative, not radiative-transfer modeled.",
            ],
            scene_class="deep_field",
            recommended_camera_target_object_id=lab.id,
            recommended_initial_signal_mode="visible_light",
            featured_object_ids=[
                lab.id,
                quasar.id,
                black_hole.id,
                magnetar.id,
                host_galaxy.id,
                anomaly.id,
            ],
            teaching_summary=(
                "Scene 001 is a deep-field protocluster: use signal modes to stress "
                "different physics (radio jets, X-ray accretion, weak lensing structure). "
                "LAB rendering is a false-color placeholder, not a radiative-transfer volume."
            ),
            scale_description=(
                "Comoving positions in Mpc; Godot normalizes by scene size_mpc for navigation."
            ),
        ),
        visual_modes=[m.value for m in VisualMode],
    )
