"""Procedural object generators for Scene 001.

Each factory places one or more CosmicObjects with scientifically-motivated
positions and metadata.  All factories accept a deterministic RNG.
"""

from __future__ import annotations

import hashlib
import random

from universe.models import (
    CosmicObject,
    CosmicWebFilament,
    CosmicWebNode,
    NodeClass,
    ObjectType,
    Relationship,
    Vector3,
    VisualHints,
)


def _seed_rng(seed: str, salt: str) -> random.Random:
    digest = hashlib.sha256(f"{seed}:{salt}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _jitter(rng: random.Random, pos: Vector3, sigma: float = 1.0) -> Vector3:
    return Vector3(
        x=pos.x + rng.gauss(0, sigma),
        y=pos.y + rng.gauss(0, sigma),
        z=pos.z + rng.gauss(0, sigma),
    )


# ---------------------------------------------------------------------------
# Galaxies
# ---------------------------------------------------------------------------

_GALAXY_NAMES = [
    "Aethon", "Borealis", "Calyx", "Dione", "Elara", "Ferox", "Gaius",
    "Helios", "Ionis", "Juno", "Kaelen", "Lyra", "Mira", "Nyx", "Oriel",
    "Pallas", "Quorra", "Rhea", "Selene", "Theron", "Umbra", "Vesta",
    "Wren", "Xanthe", "Yara", "Zephyr",
]


def generate_galaxies(
    seed: str,
    nodes: list[CosmicWebNode],
    filaments: list[CosmicWebFilament],
    redshift: float,
    count: int = 80,
) -> list[CosmicObject]:
    rng = _seed_rng(seed, "galaxies")

    node_map = {n.id: n for n in nodes}
    spawn_positions: list[Vector3] = []

    # Distribute spawn positions along filaments proportional to galaxy_count_hint
    for fil in filaments:
        start = node_map[fil.start_node_id].position_mpc
        end = node_map[fil.end_node_id].position_mpc
        n = min(fil.galaxy_count_hint, max(1, count // len(filaments)))
        for _ in range(n):
            t = rng.random()
            base = Vector3(
                x=start.x + t * (end.x - start.x),
                y=start.y + t * (end.y - start.y),
                z=start.z + t * (end.z - start.z),
            )
            spawn_positions.append(_jitter(rng, base, sigma=fil.radius_mpc * 2))

    # Add cluster around protocluster core
    core = next((n for n in nodes if n.node_class == NodeClass.PROTOCLUSTER_CORE), nodes[0])
    for _ in range(count // 4):
        spawn_positions.append(_jitter(rng, core.position_mpc, sigma=3.0))

    rng.shuffle(spawn_positions)
    spawn_positions = spawn_positions[:count]

    galaxies: list[CosmicObject] = []
    for i, pos in enumerate(spawn_positions):
        name_base = _GALAXY_NAMES[i % len(_GALAXY_NAMES)]
        stellar_mass = round(10 ** rng.uniform(8.5, 11.5), 0)
        sfr = round(10 ** rng.uniform(0.5, 3.0), 1)
        galaxies.append(
            CosmicObject(
                id=f"gal-{i:03d}",
                name=f"{name_base}-{i:03d}",
                type=ObjectType.GALAXY,
                position_mpc=pos,
                redshift=redshift + rng.gauss(0, 0.01),
                description=f"Young galaxy along cosmic web at z≈{redshift:.1f}",
                properties={
                    "stellar_mass_msun": stellar_mass,
                    "star_formation_rate_msun_yr": sfr,
                    "morphology": rng.choice(["irregular", "proto-spiral", "compact"]),
                },
                visual=VisualHints(
                    color="#6688ff",
                    emissive=True,
                    scale=0.3 + rng.random() * 0.7,
                    label=f"{name_base}-{i:03d}",
                ),
            )
        )
    return galaxies


# ---------------------------------------------------------------------------
# Lyman-alpha blob
# ---------------------------------------------------------------------------


def generate_lyman_alpha_blob(
    seed: str,
    core_node: CosmicWebNode,
    nearby_galaxy_ids: list[str],
    redshift: float,
) -> CosmicObject:
    rng = _seed_rng(seed, "lab")
    pos = _jitter(rng, core_node.position_mpc, sigma=2.0)

    relationships = [
        Relationship(target_id=gid, relation="embeds", description="Embedded young galaxy")
        for gid in nearby_galaxy_ids[:8]
    ]

    return CosmicObject(
        id="lab-001",
        name="The Furnace",
        type=ObjectType.LYMAN_ALPHA_BLOB,
        position_mpc=pos,
        redshift=redshift,
        description=(
            "A luminous Lyman-alpha blob (~300 ckpc across) powered by gas accretion, "
            "starburst activity, and possibly AGN feedback in a protocluster core."
        ),
        properties={
            "diameter_ckpc": round(rng.uniform(200, 400), 0),
            "lyman_alpha_luminosity_erg_s": f"{rng.uniform(1, 9):.1f}e44",
            "gas_temperature_K": round(rng.uniform(1e4, 5e4), 0),
            "embedded_galaxy_count": len(nearby_galaxy_ids[:8]),
        },
        visual=VisualHints(
            color="#44ffaa",
            emissive=True,
            opacity=0.35,
            scale=8.0,
            glow=True,
            label="The Furnace (LAB)",
        ),
        relationships=relationships,
    )


# ---------------------------------------------------------------------------
# Quasar + black hole
# ---------------------------------------------------------------------------


def generate_quasar_system(
    seed: str,
    core_node: CosmicWebNode,
    redshift: float,
) -> tuple[CosmicObject, CosmicObject]:
    rng = _seed_rng(seed, "quasar")
    bh_pos = _jitter(rng, core_node.position_mpc, sigma=1.5)
    q_pos = Vector3(x=bh_pos.x, y=bh_pos.y, z=bh_pos.z)

    bh_mass = round(10 ** rng.uniform(8.0, 10.0), 0)

    black_hole = CosmicObject(
        id="bh-001",
        name="Tenebris",
        type=ObjectType.BLACK_HOLE,
        position_mpc=bh_pos,
        redshift=redshift,
        description="Supermassive black hole powering the protocluster quasar.",
        properties={
            "mass_msun": bh_mass,
            "schwarzschild_radius_au": round(bh_mass * 0.0987, 1),
            "spin": round(rng.uniform(0.1, 0.998), 3),
        },
        visual=VisualHints(
            color="#000000",
            emissive=False,
            scale=0.5,
            glow=False,
            label="Tenebris (SMBH)",
            extras={"lensing_strength": round(rng.uniform(0.5, 2.0), 2)},
        ),
        relationships=[
            Relationship(
                target_id="qso-001",
                relation="powers",
                description="Powers quasar Lucerna via accretion",
            )
        ],
    )

    quasar = CosmicObject(
        id="qso-001",
        name="Lucerna",
        type=ObjectType.QUASAR,
        position_mpc=q_pos,
        redshift=redshift,
        description="High-redshift quasar with relativistic jets, powered by Tenebris.",
        properties={
            "bolometric_luminosity_erg_s": f"{rng.uniform(1, 9):.1f}e47",
            "jet_opening_angle_deg": round(rng.uniform(5, 30), 1),
            "jet_length_ckpc": round(rng.uniform(50, 500), 0),
            "accretion_rate_msun_yr": round(10 ** rng.uniform(-1, 2), 2),
        },
        visual=VisualHints(
            color="#ffffff",
            emissive=True,
            scale=1.5,
            glow=True,
            label="Lucerna (QSO)",
            extras={"jet_color": "#ff4400", "accretion_disk_color": "#ffaa22"},
        ),
        relationships=[
            Relationship(
                target_id="bh-001",
                relation="powered_by",
                description="Accretion onto supermassive black hole Tenebris",
            )
        ],
    )

    return quasar, black_hole


# ---------------------------------------------------------------------------
# Magnetar
# ---------------------------------------------------------------------------


def generate_magnetar(
    seed: str,
    host_galaxy: CosmicObject,
    redshift: float,
) -> CosmicObject:
    rng = _seed_rng(seed, "magnetar")
    pos = _jitter(rng, host_galaxy.position_mpc, sigma=0.01)

    return CosmicObject(
        id="mag-001",
        name="Pulsar Ignis",
        type=ObjectType.MAGNETAR,
        position_mpc=pos,
        redshift=redshift,
        description="A magnetar embedded in a young galaxy — remnant of a massive star.",
        properties={
            "magnetic_field_gauss": f"{rng.uniform(1, 9):.1f}e15",
            "period_seconds": round(rng.uniform(1, 12), 2),
            "age_years": round(10 ** rng.uniform(3, 5), 0),
        },
        visual=VisualHints(
            color="#ff00ff",
            emissive=True,
            scale=0.1,
            glow=True,
            label="Pulsar Ignis (Magnetar)",
        ),
        relationships=[
            Relationship(
                target_id=host_galaxy.id,
                relation="hosted_by",
                description=f"Embedded in galaxy {host_galaxy.name}",
            )
        ],
    )


# ---------------------------------------------------------------------------
# CMB background + void
# ---------------------------------------------------------------------------


def generate_cmb_background(redshift: float) -> CosmicObject:
    return CosmicObject(
        id="cmb-001",
        name="CMB Shell",
        type=ObjectType.CMB_BACKGROUND,
        position_mpc=Vector3(x=0, y=0, z=0),
        redshift=1100.0,
        description="Cosmic microwave background — last scattering surface at z≈1100.",
        properties={
            "temperature_K": 2.725 * (1 + 1100) / (1 + redshift),
            "observed_temperature_K": 2.725,
        },
        visual=VisualHints(
            color="#110808",
            opacity=0.15,
            scale=1000.0,
            label="CMB Background",
        ),
    )


def generate_void(
    seed: str,
    region_size: float,
    redshift: float,
    index: int = 0,
) -> CosmicObject:
    rng = _seed_rng(seed, f"void-{index}")
    half = region_size / 2.0
    pos = Vector3(
        x=rng.uniform(-half, -half * 0.3) if rng.random() > 0.5 else rng.uniform(half * 0.3, half),
        y=rng.uniform(-half, -half * 0.3) if rng.random() > 0.5 else rng.uniform(half * 0.3, half),
        z=rng.uniform(-half, -half * 0.3) if rng.random() > 0.5 else rng.uniform(half * 0.3, half),
    )
    return CosmicObject(
        id=f"void-{index:03d}",
        name=f"Void {index}",
        type=ObjectType.VOID,
        position_mpc=pos,
        redshift=redshift,
        description="Low-density void region with minimal galaxy presence.",
        properties={
            "diameter_mpc": round(rng.uniform(15, 40), 1),
            "underdensity_delta": round(rng.uniform(-0.9, -0.5), 2),
        },
        visual=VisualHints(
            color="#000022",
            opacity=0.08,
            scale=15.0,
            label=f"Void {index}",
        ),
    )
