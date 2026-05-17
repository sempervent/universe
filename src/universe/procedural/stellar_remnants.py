"""High-energy stellar remnant field — magnetars, black holes, accretion sources."""

from __future__ import annotations

from universe.models import (
    CosmicObject,
    CosmicWebNode,
    NodeClass,
    ObjectType,
    SceneMetadata,
    SceneRegion,
    Vector3,
    VisualHints,
    VisualMode,
)
from universe.procedural.objects import (
    _jitter,
    _seed_rng,
    generate_magnetar,
    generate_quasar_system,
)


def generate_stellar_remnant_field(seed: str = "high-energy-remnants") -> SceneRegion:
    rng = _seed_rng(seed, "stellar-remnants")
    region_size = 28.0
    redshift = 0.45

    core = CosmicWebNode(
        id="node-000",
        position_mpc=Vector3(x=2.0, y=-1.0, z=0.5),
        density=2.0,
        node_class=NodeClass.PROTOCLUSTER_CORE,
    )
    quasar, black_hole = generate_quasar_system(seed, core, redshift)
    for obj in (quasar, black_hole):
        obj.properties["required_signal_types"] = ["xray"]
        obj.properties["optional_signal_types"] = ["gamma_ray", "radio"]

    host = CosmicObject(
        id="gal-host-001",
        name="Remnant Host",
        type=ObjectType.GALAXY,
        position_mpc=_jitter(rng, core.position_mpc, sigma=1.0),
        redshift=redshift,
        description="Star-forming host galaxy hosting compact remnants.",
        properties={"stellar_mass_msun": 1e10},
        visual=VisualHints(color="#8899cc", scale=0.5, label="Remnant Host"),
    )
    mag1 = generate_magnetar(seed, host, redshift)
    mag1.id = "mag-001"
    mag1.name = "Magnetar XR-1"
    mag1.properties["required_signal_types"] = ["xray"]
    mag1.properties["optional_signal_types"] = ["gamma_ray", "radio"]

    mag2 = generate_magnetar(seed + ":b", host, redshift)
    mag2.id = "mag-002"
    mag2.name = "Magnetar XR-2"
    mag2.position_mpc = _jitter(rng, host.position_mpc, sigma=0.02)
    mag2.properties["required_signal_types"] = ["xray", "gamma_ray"]
    mag2.properties["optional_signal_types"] = ["radio"]

    bh_candidate = CosmicObject(
        id="bh-cand-001",
        name="Accretion Shadow",
        type=ObjectType.BLACK_HOLE,
        position_mpc=_jitter(rng, Vector3(x=-4.0, y=3.0, z=-1.0), sigma=0.3),
        redshift=redshift,
        description="X-ray bright black-hole candidate without optical counterpart.",
        properties={
            "mass_msun": 4e6,
            "required_signal_types": ["xray"],
            "optional_signal_types": ["gamma_ray", "gravitational_wave"],
        },
        visual=VisualHints(color="#220033", emissive=True, scale=0.4, label="BH Candidate"),
    )

    grb_remnant = CosmicObject(
        id="snr-001",
        name="GRB Afterglow Shell",
        type=ObjectType.GALAXY,
        position_mpc=Vector3(x=6.0, y=-2.0, z=4.0),
        redshift=redshift,
        description="Supernova / GRB afterglow marker — extended X-ray emission.",
        properties={
            "required_signal_types": ["xray", "gamma_ray"],
            "optional_signal_types": ["radio"],
            "morphology": "shell",
        },
        visual=VisualHints(color="#ff4488", emissive=True, scale=0.8, label="GRB Shell"),
    )

    all_objects = [host, quasar, black_hole, mag1, mag2, bh_candidate, grb_remnant]
    featured = [mag1.id, bh_candidate.id, quasar.id]

    return SceneRegion(
        id="stellar-remnant-field",
        name="Stellar Remnant Field",
        seed=seed,
        redshift=redshift,
        size_mpc=region_size,
        objects=all_objects,
        nodes=[],
        filaments=[],
        metadata=SceneMetadata(
            schema_version="0.1.0",
            generator="universe",
            description="Compact remnants and accretion-powered sources in a high-energy survey field.",
            scientific_caveats=[
                "Positions are schematic; not a catalog cross-match.",
            ],
            scene_class="high_energy",
            recommended_camera_target_object_id=mag1.id,
            recommended_initial_signal_mode="xray",
            featured_object_ids=featured,
            teaching_summary=(
                "High-energy astronomy reveals magnetars, accretion disks, and black-hole "
                "candidates through X-ray and gamma-ray emission."
            ),
            scale_description="~28 cMpc survey volume with compact-source emphasis.",
        ),
        visual_modes=[VisualMode.XRAY.value, VisualMode.BEAUTY.value],
    )
