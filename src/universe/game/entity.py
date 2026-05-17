"""Research Entity — player identity for the telescope game.

A Research Entity is the named observatory, institute, or research group
that the player represents.  ``EntityType`` selects a small mechanical
modifier (see ``EntityModifier``) — intentionally subtle, not a full RPG
talent tree.
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


class EntityModifier(BaseModel):
    """Small, serializable mechanical tint for a research entity background."""

    entity_type: str
    name: str
    description: str
    discovery_rp_multiplier: float = 1.0
    milestone_rp_multiplier: float = 1.0
    survey_rp_multiplier: float = 1.0
    upgrade_cost_multiplier: float = 1.0
    early_optical_upgrade_cost_multiplier: float = 1.0
    space_upgrade_cost_multiplier: float = 1.0
    confidence_bonus: float = 0.0
    survey_progress_bonus: int = 0
    speculative_bonus: bool = False
    notes: list[str] = Field(default_factory=list)


_NEUTRAL = EntityModifier(
    entity_type="custom",
    name="Custom Charter",
    description="No institutional background modifier — play as you like.",
)


def _modifiers_table() -> dict[str, EntityModifier]:
    return {
        "backyard_observatory": EntityModifier(
            entity_type="backyard_observatory",
            name="Backyard Persistence",
            description="Improvises early optical work cheaply.",
            early_optical_upgrade_cost_multiplier=0.85,
            notes=[
                "Applies early_optical_upgrade_cost_multiplier to "
                "ground_optical and improved_ground only.",
            ],
        ),
        "university_lab": EntityModifier(
            entity_type="university_lab",
            name="Peer Review Engine",
            description="Better at turning firsts into funded research.",
            milestone_rp_multiplier=1.10,
        ),
        "national_observatory": EntityModifier(
            entity_type="national_observatory",
            name="Institutional Survey Machine",
            description="Survey operations return slightly more RP when completed.",
            survey_rp_multiplier=1.10,
        ),
        "private_institute": EntityModifier(
            entity_type="private_institute",
            name="Flexible Funding",
            description="Slightly more RP from each discovery credit.",
            discovery_rp_multiplier=1.05,
        ),
        "orbital_consortium": EntityModifier(
            entity_type="orbital_consortium",
            name="Launch Infrastructure",
            description="Space-era telescope tiers cost a bit less RP.",
            space_upgrade_cost_multiplier=0.85,
            notes=[
                "Applies space_upgrade_cost_multiplier from space_optical onward "
                "(tier_index >= 3 in the default tree).",
            ],
        ),
        "ai_research_bureau": EntityModifier(
            entity_type="ai_research_bureau",
            name="Pattern Classifier",
            description="Slight boost to identification confidence when already detectable.",
            confidence_bonus=0.05,
            notes=[
                "confidence_bonus applies only if base confidence > 0; "
                "cannot conjure detections from nothing.",
            ],
        ),
        "citizen_science_network": EntityModifier(
            entity_type="citizen_science_network",
            name="Many Eyes",
            description="Each qualifying survey discovery adds one extra progress step.",
            survey_progress_bonus=1,
            notes=[
                "When a new object counts toward the active survey, progress "
                "increments by 1 + survey_progress_bonus (capped at completion_goal).",
            ],
        ),
        "occult_sky_society": EntityModifier(
            entity_type="occult_sky_society",
            name="The Stars Whisper Back",
            description="Speculative programs return a sliver more RP.",
            speculative_bonus=True,
            notes=[
                "+10% RP on speculative survey completion and speculative milestones.",
            ],
        ),
        "corporate_research_division": EntityModifier(
            entity_type="corporate_research_division",
            name="Procurement Department from Hell",
            description="Slightly cheaper upgrades, slightly leaner milestone payouts.",
            upgrade_cost_multiplier=0.95,
            milestone_rp_multiplier=0.95,
        ),
        "custom": _NEUTRAL,
    }


_MOD_CACHE: dict[str, EntityModifier] | None = None


def _all_modifiers_dict() -> dict[str, EntityModifier]:
    global _MOD_CACHE
    if _MOD_CACHE is None:
        _MOD_CACHE = _modifiers_table()
    return _MOD_CACHE


def get_entity_modifier(entity_type: str) -> EntityModifier:
    """Return the modifier for ``entity_type``; unknown types → neutral (custom)."""
    table = _all_modifiers_dict()
    if entity_type in table:
        return table[entity_type]
    return _NEUTRAL.model_copy()


def get_all_entity_modifiers() -> list[EntityModifier]:
    """All defined modifiers (one per known entity type key)."""
    return list(_all_modifiers_dict().values())


def format_entity_modifier_summary(entity_type: str) -> str:
    """One-line summary for CLI / UI headers."""
    m = get_entity_modifier(entity_type)
    parts = [f"{m.name}"]
    if m.discovery_rp_multiplier != 1.0:
        parts.append(f"discovery RP ×{m.discovery_rp_multiplier:g}")
    if m.confidence_bonus:
        parts.append(f"+{m.confidence_bonus:g} conf. when detectable")
    if m.upgrade_cost_multiplier != 1.0 or m.early_optical_upgrade_cost_multiplier != 1.0:
        parts.append("tier costs adjusted")
    if m.space_upgrade_cost_multiplier != 1.0:
        parts.append(f"space tiers ×{m.space_upgrade_cost_multiplier:g} cost")
    if m.survey_rp_multiplier != 1.0:
        parts.append(f"survey RP ×{m.survey_rp_multiplier:g}")
    if m.milestone_rp_multiplier != 1.0:
        parts.append(f"milestone RP ×{m.milestone_rp_multiplier:g}")
    if m.survey_progress_bonus:
        parts.append(f"+{m.survey_progress_bonus} survey progress / discovery")
    if m.speculative_bonus:
        parts.append("+10% speculative rewards")
    if m.entity_type == "custom":
        parts = [m.name, "no mechanical modifier"]
    return " · ".join(parts)


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
