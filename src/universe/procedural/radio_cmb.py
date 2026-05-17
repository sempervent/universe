"""Radio / microwave survey scene — CMB, radio galaxies, jet quasars."""

from __future__ import annotations

from universe.models import (
    CosmicObject,
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
    generate_cmb_background,
    generate_quasar_system,
)


def generate_radio_cmb_survey(seed: str = "radio-first-light") -> SceneRegion:
    """Deterministic radio-sky campaign scene."""
    rng = _seed_rng(seed, "radio-cmb")
    region_size = 35.0
    redshift = 0.12

    cmb = generate_cmb_background(redshift)
    cmb.properties["required_signal_types"] = ["microwave"]
    cmb.properties["optional_signal_types"] = ["radio"]

    from universe.models import CosmicWebNode, NodeClass

    core = CosmicWebNode(
        id="node-000",
        position_mpc=Vector3(x=0, y=0, z=0),
        density=1.8,
        node_class=NodeClass.FILAMENT_INTERSECTION,
    )
    quasar, black_hole = generate_quasar_system(seed, core, redshift)
    for obj in (quasar, black_hole):
        obj.properties["required_signal_types"] = ["radio"]
        obj.properties["optional_signal_types"] = ["microwave", "xray"]
        obj.properties["radio_loud"] = True

    radio_galaxies: list[CosmicObject] = []
    names = ["Sagittarius A*", "Centaurus A", "Cygnus A", "Virgo A", "Fornax A"]
    for i, nm in enumerate(names):
        pos = Vector3(
            x=rng.uniform(-region_size * 0.35, region_size * 0.35),
            y=rng.uniform(-region_size * 0.2, region_size * 0.2),
            z=rng.uniform(-region_size * 0.35, region_size * 0.35),
        )
        radio_galaxies.append(
            CosmicObject(
                id=f"rgal-{i:03d}",
                name=nm,
                type=ObjectType.GALAXY,
                position_mpc=pos,
                redshift=redshift + rng.gauss(0, 0.02),
                description="Radio-loud galaxy — synchrotron lobes dominate over optical disk.",
                properties={
                    "radio_loud": True,
                    "required_signal_types": ["radio"],
                    "optional_signal_types": ["microwave"],
                    "flux_jy_1ghz": round(rng.uniform(0.5, 12.0), 2),
                },
                visual=VisualHints(
                    color="#ff8844",
                    emissive=True,
                    scale=0.6 + rng.random() * 0.4,
                    label=nm,
                    extras={"jet_color": "#ff6600"},
                ),
            )
        )

    half = region_size / 2.0
    magnetar_pos = _jitter(rng, Vector3(x=half * 0.15, y=0, z=half * 0.1), sigma=0.5)
    pulsar = CosmicObject(
        id="psr-001",
        name="Vela Pulsar",
        type=ObjectType.MAGNETAR,
        position_mpc=magnetar_pos,
        redshift=0.0,
        description="Nearby pulsar-like compact source — bright in radio, faint optically.",
        properties={
            "required_signal_types": ["radio"],
            "optional_signal_types": ["xray", "gamma_ray"],
            "period_seconds": 0.089,
        },
        visual=VisualHints(color="#ffaa00", emissive=True, scale=0.2, label="Vela Pulsar"),
    )

    faint_galaxies: list[CosmicObject] = []
    for i in range(6):
        faint_galaxies.append(
            CosmicObject(
                id=f"fgal-{i:03d}",
                name=f"Faint Field {i}",
                type=ObjectType.GALAXY,
                position_mpc=Vector3(
                    x=rng.uniform(-half, half),
                    y=rng.uniform(-half * 0.3, half * 0.3),
                    z=rng.uniform(-half, half),
                ),
                redshift=redshift + rng.uniform(0, 0.3),
                description="Distant galaxy — marginal in optical, catalogued in radio survey.",
                properties={
                    "required_signal_types": ["radio"],
                    "optional_signal_types": ["visible_light"],
                    "discovery_difficulty": 0.5,
                },
                visual=VisualHints(color="#446688", scale=0.25, label=f"Faint {i}"),
            )
        )

    all_objects = [cmb, quasar, black_hole, pulsar] + radio_galaxies + faint_galaxies
    featured = [cmb.id, quasar.id, radio_galaxies[0].id, pulsar.id]

    return SceneRegion(
        id="radio-cmb-survey",
        name="Radio CMB Survey",
        seed=seed,
        redshift=redshift,
        size_mpc=region_size,
        objects=all_objects,
        nodes=[],
        filaments=[],
        metadata=SceneMetadata(
            schema_version="0.1.0",
            generator="universe",
            description=(
                "Low-redshift radio survey: CMB shell, radio-loud galaxies, "
                "jet quasars, and a nearby pulsar."
            ),
            scientific_caveats=[
                "CMB redshift is schematic; scene uses mixed abstraction scales.",
                "Radio-loud flags are narrative, not full spectral energy distributions.",
            ],
            scene_class="radio_survey",
            recommended_camera_target_object_id=cmb.id,
            recommended_initial_signal_mode="radio",
            featured_object_ids=featured,
            teaching_summary=(
                "Radio and microwave instruments reveal the cold CMB background, "
                "synchrotron lobes, and relativistic jets invisible in ordinary light."
            ),
            scale_description="Regional survey ~35 cMpc; positions are schematic layout.",
        ),
        visual_modes=[VisualMode.RADIO.value, VisualMode.CMB.value, VisualMode.BEAUTY.value],
    )
