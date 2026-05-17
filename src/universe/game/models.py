"""Game data models for the telescope progression and discovery loop.

These models are separate from the scene/simulation models.  The game
layer reads SceneRegion data and evaluates it against a ResearchState.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from universe.game.entity import ResearchEntity
from universe.game.milestones import MilestoneRecord
from universe.game.observatory_time import ObservatoryTimeState, default_observatory_time
from universe.game.surveys import SurveyProgress


# ---------------------------------------------------------------------------
# Signal and instrument enums
# ---------------------------------------------------------------------------


class SignalType(str, Enum):
    VISIBLE_LIGHT = "visible_light"
    INFRARED = "infrared"
    ULTRAVIOLET = "ultraviolet"
    RADIO = "radio"
    MICROWAVE = "microwave"
    XRAY = "xray"
    GAMMA_RAY = "gamma_ray"
    GRAVITATIONAL_WAVE = "gravitational_wave"
    NEUTRINO = "neutrino"
    COSMIC_RAY = "cosmic_ray"
    WEAK_LENSING = "weak_lensing"
    DARK_MATTER_INFERENCE = "dark_matter_inference"
    SPECULATIVE_NOW_SIGNAL = "speculative_now_signal"


class InstrumentType(str, Enum):
    NAKED_EYE = "naked_eye"
    OPTICAL_TELESCOPE = "optical_telescope"
    SPACE_TELESCOPE = "space_telescope"
    RADIO_TELESCOPE = "radio_telescope"
    XRAY_OBSERVATORY = "xray_observatory"
    GAMMA_OBSERVATORY = "gamma_observatory"
    INTERFEROMETER = "interferometer"
    GRAVITATIONAL_WAVE_DETECTOR = "gravitational_wave_detector"
    NEUTRINO_DETECTOR = "neutrino_detector"
    COSMIC_RAY_DETECTOR = "cosmic_ray_detector"
    WEAK_LENSING_MAPPER = "weak_lensing_mapper"
    DARK_MATTER_OBSERVATORY = "dark_matter_observatory"
    NOW_SCOPE = "now_scope"


# ---------------------------------------------------------------------------
# Telescope tier
# ---------------------------------------------------------------------------


class TelescopeTier(BaseModel):
    id: str
    name: str
    tier_index: int
    instrument_types: list[InstrumentType]
    signal_types: list[SignalType]
    description: str = ""
    research_cost: int = 0
    prerequisites: list[str] = Field(default_factory=list)
    unlocks: list[str] = Field(default_factory=list)
    resolution_arcsec: float = 60.0
    sensitivity: float = 0.1
    max_effective_distance_mpc: float = 0.001
    atmosphere_penalty: float = 0.5
    speculative: bool = False


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


class DiscoveryRequirement(BaseModel):
    """What signals/capabilities are needed to detect a given object type."""

    object_type: str
    required_signal_types: list[SignalType]
    optional_signal_types: list[SignalType] = Field(default_factory=list)
    minimum_telescope_tier: int = 0
    minimum_sensitivity: float = 0.0
    minimum_resolution_arcsec: float = 3600.0
    base_research_points: int = 5
    notes: str = ""
    speculative: bool = False


class DiscoveryRecord(BaseModel):
    """Persistent record of a discovered object."""

    object_id: str
    object_type: str
    confidence: float = 0.0
    detected_signals: list[str] = Field(default_factory=list)
    research_points_earned: int = 0
    first_detected_tier: str = ""


class DiscoveryResult(BaseModel):
    """Transient result of a single observation attempt."""

    object_id: str
    object_type: str
    detected_signals: list[str] = Field(default_factory=list)
    identification_confidence: float = 0.0
    newly_discovered: bool = False
    confidence_upgraded: bool = False
    research_points_awarded: int = 0
    message: str = ""


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------


class CampaignSceneState(BaseModel):
    scene_id: str
    unlocked: bool = False
    visited: bool = False
    first_unlocked_turn: int | None = None
    first_visited_turn: int | None = None
    completed: bool = False
    metadata: dict = Field(default_factory=dict)


class CampaignState(BaseModel):
    active_scene_id: str = "solar-system"
    scenes: dict[str, CampaignSceneState] = Field(default_factory=dict)
    completed_scene_ids: list[str] = Field(default_factory=list)


class TransientEventState(BaseModel):
    """Per-player record for a catalog transient event."""

    event_id: str
    active: bool = False
    discovered: bool = False
    observed_turns: list[int] = Field(default_factory=list)
    first_observed_turn: int | None = None
    expired: bool = False
    reward_claimed: bool = False


class ObjectiveStatus(str, Enum):
    LOCKED = "locked"
    ACTIVE = "active"
    COMPLETED = "completed"


class ObjectiveProgress(BaseModel):
    """Per-player tutorial objective progress."""

    objective_id: str
    status: ObjectiveStatus = ObjectiveStatus.LOCKED
    completed_turn: int | None = None
    reward_claimed: bool = False
    metadata: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Player state
# ---------------------------------------------------------------------------


def _empty_campaign() -> CampaignState:
    return CampaignState(active_scene_id="solar-system", scenes={})


class ResearchState(BaseModel):
    research_points: int = 0
    unlocked_tiers: list[str] = Field(default_factory=lambda: ["naked_eye"])
    active_telescope_tier: str = "naked_eye"
    known_signal_types: list[str] = Field(default_factory=lambda: ["visible_light"])
    discoveries: dict[str, DiscoveryRecord] = Field(default_factory=dict)
    research_entity: ResearchEntity = Field(default_factory=ResearchEntity)

    # ── Survey programs ───────────────────────────────────────────────
    active_survey_id: str | None = None
    survey_progress: dict[str, SurveyProgress] = Field(default_factory=dict)

    # ── Milestones / progression bookkeeping ─────────────────────────
    milestones: dict[str, MilestoneRecord] = Field(default_factory=dict)
    turn: int = 0

    # ── Follow-up / pacing bookkeeping ───────────────────────────────
    followup_observation_counts: dict[str, int] = Field(default_factory=dict)
    last_observation_tier_by_object: dict[str, str] = Field(default_factory=dict)
    consecutive_no_rp_turns: int = 0

    # ── Campaign / multi-scene progression ───────────────────────────
    campaign: CampaignState = Field(default_factory=_empty_campaign)

    # ── Turn-window transient events ─────────────────────────────────
    transient_events: dict[str, TransientEventState] = Field(default_factory=dict)

    # ── First-run tutorial objectives ──────────────────────────────────
    objectives: dict[str, ObjectiveProgress] = Field(default_factory=dict)
    active_objective_ids: list[str] = Field(default_factory=list)

    # ── Observatory time (local sky clock) ─────────────────────────────
    observatory_time: ObservatoryTimeState = Field(default_factory=default_observatory_time)

    # ── Imaging archive ────────────────────────────────────────────────
    unlocked_camera_ids: list[str] = Field(default_factory=lambda: ["naked_eye_memory"])
    captured_images: dict[str, dict] = Field(default_factory=dict)

    @property
    def discovered_object_ids(self) -> set[str]:
        return set(self.discoveries.keys())

    @property
    def completed_discoveries(self) -> int:
        return sum(1 for d in self.discoveries.values() if d.confidence >= 0.75)
