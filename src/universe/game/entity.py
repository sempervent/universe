"""Research Entity — player identity for the telescope game.

A Research Entity is the named observatory, institute, or research group
that the player represents.  It has no mechanical effect yet; it is purely
identity and flavor.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    BACKYARD_OBSERVATORY = "backyard_observatory"
    UNIVERSITY_LAB = "university_lab"
    NATIONAL_OBSERVATORY = "national_observatory"
    PRIVATE_INSTITUTE = "private_institute"
    ORBITAL_CONSORTIUM = "orbital_consortium"
    AI_RESEARCH_BUREAU = "ai_research_bureau"
    CITIZEN_SCIENCE_NETWORK = "citizen_science_network"
    OCCULT_SKY_SOCIETY = "occult_sky_society"
    CORPORATE_RESEARCH_DIVISION = "corporate_research_division"
    CUSTOM = "custom"


ENTITY_TYPE_LABELS: dict[str, str] = {
    "backyard_observatory": "Backyard Observatory",
    "university_lab": "University Lab",
    "national_observatory": "National Observatory",
    "private_institute": "Private Institute",
    "orbital_consortium": "Orbital Consortium",
    "ai_research_bureau": "AI Research Bureau",
    "citizen_science_network": "Citizen Science Network",
    "occult_sky_society": "Occult Sky Society",
    "corporate_research_division": "Corporate Research Division",
    "custom": "Custom",
}

RANDOM_ENTITY_NAMES: list[str] = [
    "Hydrogen Ghost Institute",
    "The Bureau of Unreasonable Telescopes",
    "Backyard Event Horizon Project",
    "Appalachian Deep Field Survey",
    "Cosmic Waffle Research Cooperative",
    "The Last Photon Club",
    "Dark Matter Complaint Department",
    "Sempervent Observatory",
    "The Gravitational Eavesdropping Office",
    "Lyman-Alpha Breakfast Society",
    "Grant Deep Sky Survey",
    "Basement Array for Cosmic Nonsense",
    "Appalachian Radio Astronomy Bureau",
    "The Redshift Reading Room",
    "Void Cartography Initiative",
    "Filament Appreciation Society",
    "Quasar Forensics Lab",
    "The Neutrino Whisperers",
    "Magnetar Watch Collective",
    "Accretion Disk Enthusiasts Club",
]

DEFAULT_ENTITY_NAME = "Unnamed Research Entity"


class ResearchEntity(BaseModel):
    """The player's research identity."""

    id: str = ""
    name: str = DEFAULT_ENTITY_NAME
    entity_type: str = "custom"
    motto: str = ""
    founded_turn: int = 0
    description: str = ""
    style: str = ""
    created_at: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


def slugify_entity_name(name: str) -> str:
    """Convert an entity name to a URL/ID-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "unnamed"


def make_research_entity(
    name: str,
    entity_type: str = "custom",
    motto: str | None = None,
) -> ResearchEntity:
    """Create a ResearchEntity with auto-generated ID and timestamp."""
    clean_name = name.strip() if name else DEFAULT_ENTITY_NAME
    if not clean_name:
        clean_name = DEFAULT_ENTITY_NAME

    slug = slugify_entity_name(clean_name)
    stable_id = slug + "-" + hashlib.sha256(slug.encode()).hexdigest()[:8]

    return ResearchEntity(
        id=stable_id,
        name=clean_name,
        entity_type=entity_type,
        motto=motto or "",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def generate_random_entity_name(seed: str | None = None) -> str:
    """Pick a random entity name, deterministically if a seed is given."""
    if seed is not None:
        idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(RANDOM_ENTITY_NAMES)
        return RANDOM_ENTITY_NAMES[idx]
    import random

    return random.choice(RANDOM_ENTITY_NAMES)
