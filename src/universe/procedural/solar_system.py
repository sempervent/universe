"""Starter solar system scene generator.

Produces a simplified scene containing the Sun, Moon, planets, and
optionally minor bodies.  Positions are in AU converted to Mpc for
consistency with the scene format (1 AU ≈ 4.848e-12 Mpc).

This is NOT an orbital mechanics simulator.  Positions are representative
average distances placed along a single plane for visualization simplicity.
"""

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

AU_TO_MPC: float = 4.848e-12


def _au_pos(au: float, angle_deg: float = 0.0) -> Vector3:
    """Place an object at *au* AU from origin along angle in the ecliptic."""
    import math

    rad = math.radians(angle_deg)
    return Vector3(
        x=au * AU_TO_MPC * math.cos(rad),
        y=0.0,
        z=au * AU_TO_MPC * math.sin(rad),
    )


def generate_solar_system(seed: str = "local-sky") -> SceneRegion:
    """Generate a starter solar system scene."""
    objects: list[CosmicObject] = []

    # Observatory / Earth origin
    objects.append(
        CosmicObject(
            id="obs-earth",
            name="Earth Observatory",
            type=ObjectType.OBSERVATORY,
            position_mpc=Vector3(x=0, y=0, z=0),
            redshift=0.0,
            description="The player's starting observation point on Earth.",
            properties={"type": "ground_observatory", "altitude_m": 2400},
            visual=VisualHints(color="#4488ff", scale=0.1, label="Earth Observatory"),
        )
    )

    # Sun
    objects.append(
        CosmicObject(
            id="sun",
            name="Sun",
            type=ObjectType.STAR,
            position_mpc=_au_pos(0.0),
            redshift=0.0,
            description="G2V main-sequence star. The closest star to Earth.",
            properties={
                "spectral_type": "G2V",
                "apparent_magnitude": -26.74,
                "absolute_magnitude": 4.83,
                "mass_msun": 1.0,
                "radius_rsun": 1.0,
                "distance_au": 1.0,
                "angular_size_arcsec": 1920,
                "discovery_difficulty": 0,
            },
            visual=VisualHints(color="#ffffaa", emissive=True, scale=2.0, glow=True, label="Sun"),
        )
    )

    # Moon
    objects.append(
        CosmicObject(
            id="moon",
            name="Moon",
            type=ObjectType.MOON,
            position_mpc=_au_pos(0.00257, 15),
            redshift=0.0,
            description="Earth's natural satellite. ~384,400 km away.",
            properties={
                "parent": "Earth",
                "apparent_magnitude": -12.7,
                "distance_au": 0.00257,
                "angular_size_arcsec": 1870,
                "orbital_period_days": 27.3,
                "discovery_difficulty": 0,
            },
            visual=VisualHints(color="#cccccc", scale=0.5, label="Moon"),
        )
    )

    # Planets
    planet_data = [
        ("mercury", "Mercury", 0.387, 30, -1.9, 10, "Innermost planet. Difficult to observe due to proximity to Sun.", 1),
        ("venus", "Venus", 0.723, 60, -4.6, 60, "Brightest planet. Thick cloud cover.", 0),
        ("mars", "Mars", 1.524, 120, -2.9, 25, "The red planet. Visible color with naked eye.", 0),
        ("jupiter", "Jupiter", 5.203, 150, -2.9, 50, "Gas giant. Four Galilean moons visible with binoculars.", 0),
        ("saturn", "Saturn", 9.537, 180, 0.5, 20, "Ringed gas giant. Rings visible with small telescope.", 0),
        ("uranus", "Uranus", 19.19, 210, 5.7, 4, "Ice giant. Discovered telescopically in 1781.", 1),
        ("neptune", "Neptune", 30.07, 240, 7.8, 2, "Ice giant. Discovered via mathematical prediction in 1846.", 2),
    ]

    for pid, name, au, angle, mag, ang_size, desc, difficulty in planet_data:
        objects.append(
            CosmicObject(
                id=f"planet-{pid}",
                name=name,
                type=ObjectType.PLANET,
                position_mpc=_au_pos(au, angle),
                redshift=0.0,
                description=desc,
                properties={
                    "apparent_magnitude": mag,
                    "distance_au": au,
                    "angular_size_arcsec": ang_size,
                    "orbital_period_days": round(365.25 * au**1.5, 1),
                    "discovery_difficulty": difficulty,
                },
                visual=VisualHints(
                    color={
                        "mercury": "#aaaaaa", "venus": "#eeeecc", "mars": "#dd6644",
                        "jupiter": "#ddaa77", "saturn": "#ddcc88",
                        "uranus": "#88ccdd", "neptune": "#4466dd",
                    }.get(pid, "#888888"),
                    emissive=False,
                    scale=0.3 + au * 0.01,
                    label=name,
                ),
            )
        )

    # Galilean moons of Jupiter
    galilean = [
        ("io", "Io", 5.203, 152, 5.0, "Volcanic moon of Jupiter."),
        ("europa", "Europa", 5.203, 148, 5.3, "Icy moon of Jupiter. Possible subsurface ocean."),
        ("ganymede", "Ganymede", 5.203, 154, 4.6, "Largest moon in the solar system."),
        ("callisto", "Callisto", 5.203, 146, 5.6, "Heavily cratered moon of Jupiter."),
    ]
    for mid, name, au, angle, mag, desc in galilean:
        objects.append(
            CosmicObject(
                id=f"moon-{mid}",
                name=name,
                type=ObjectType.MOON,
                position_mpc=_au_pos(au, angle),
                redshift=0.0,
                description=desc,
                properties={
                    "parent": "Jupiter",
                    "apparent_magnitude": mag,
                    "distance_au": au,
                    "angular_size_arcsec": 1.5,
                    "discovery_difficulty": 1,
                },
                visual=VisualHints(color="#ccccaa", scale=0.15, label=name),
            )
        )

    # An asteroid
    objects.append(
        CosmicObject(
            id="asteroid-ceres",
            name="Ceres",
            type=ObjectType.ASTEROID,
            position_mpc=_au_pos(2.77, 135),
            redshift=0.0,
            description="Largest object in the asteroid belt. Dwarf planet.",
            properties={
                "apparent_magnitude": 6.9,
                "distance_au": 2.77,
                "angular_size_arcsec": 0.8,
                "orbital_period_days": 1681,
                "discovery_difficulty": 2,
            },
            visual=VisualHints(color="#999999", scale=0.1, label="Ceres"),
        )
    )

    # A comet
    objects.append(
        CosmicObject(
            id="comet-halley",
            name="Halley's Comet",
            type=ObjectType.COMET,
            position_mpc=_au_pos(17.8, 270),
            redshift=0.0,
            description="Periodic comet visible every ~75 years. Famous since antiquity.",
            properties={
                "apparent_magnitude": 3.0,
                "distance_au": 17.8,
                "angular_size_arcsec": 5,
                "orbital_period_days": 27510,
                "discovery_difficulty": 1,
            },
            visual=VisualHints(color="#aaddff", emissive=True, scale=0.15, glow=True, label="Halley's Comet"),
        )
    )

    return SceneRegion(
        id="solar-system",
        name="Local Solar System",
        seed=seed,
        redshift=0.0,
        size_mpc=round(40 * AU_TO_MPC, 15),
        objects=objects,
        nodes=[],
        filaments=[],
        metadata=SceneMetadata(
            schema_version="0.1.0",
            generator="universe",
            description=(
                "Simplified solar system scene for the starter game experience. "
                "Positions are average orbital distances, not ephemeris-computed."
            ),
            scientific_caveats=[
                "Positions are average distances, not current orbital positions.",
                "No orbital mechanics or time evolution.",
                "Angular sizes are representative averages.",
                "Apparent magnitudes are approximate mean opposition values.",
            ],
        ),
        visual_modes=[m.value for m in VisualMode],
    )
