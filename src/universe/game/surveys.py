"""Survey programs — named research campaigns.

A survey program is a focused multi-target campaign with a goal count and
a research-point reward.  Surveys provide medium-term direction beyond
ad-hoc observation.  They never modify scene data and operate purely on
discovery records.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from universe.game.entity import get_entity_modifier


class SurveyProgramStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"


class SurveyScope(str, Enum):
    SOLAR_SYSTEM = "solar_system"
    DEEP_FIELD = "deep_field"
    ANY = "any"


# How confident a discovery must be to count toward the survey.
DEFAULT_MIN_CONFIDENCE = 0.5
HIGH_CONFIDENCE = 0.75


class SurveyProgram(BaseModel):
    """Static definition of a survey program.

    The full set of programs is returned by ``get_default_survey_programs``.
    Players see them dynamically gated by ``required_tier_ids`` and
    ``required_signal_types``.
    """

    id: str
    name: str
    description: str = ""
    required_tier_ids: list[str] = Field(default_factory=list)
    required_signal_types: list[str] = Field(default_factory=list)
    target_object_types: list[str] = Field(default_factory=list)
    scene_scope: str = SurveyScope.ANY.value
    completion_goal: int = 1
    reward_research_points: int = 0
    unlocks: list[str] = Field(default_factory=list)
    speculative: bool = False
    flavor: str = ""
    min_confidence: float = DEFAULT_MIN_CONFIDENCE


class SurveyProgress(BaseModel):
    """Per-player progress for a single survey program."""

    survey_id: str
    observations_completed: int = 0
    discoveries_completed: int = 0
    completed: bool = False
    claimed_reward: bool = False
    discovered_object_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Default catalogue
# ---------------------------------------------------------------------------


def get_default_survey_programs() -> list[SurveyProgram]:
    """Return the canonical list of survey programs."""
    return [
        SurveyProgram(
            id="local_sky_survey",
            name="First Light Survey",
            description=(
                "Tutorial program: catalogue bright local targets (Sun, Moon, planets). "
                "Teaches the observe → survey → upgrade loop before deep-field work."
            ),
            required_tier_ids=["naked_eye"],
            target_object_types=["star", "planet", "moon"],
            scene_scope=SurveyScope.SOLAR_SYSTEM.value,
            completion_goal=8,
            reward_research_points=8,
            flavor="Introductory survey — intentionally quick, not a long-term RP faucet.",
        ),
        SurveyProgram(
            id="planetary_census",
            name="Planetary Census",
            description="Resolve and confirm every planet and major moon in the system.",
            required_tier_ids=["ground_optical"],
            target_object_types=["planet", "moon"],
            scene_scope=SurveyScope.SOLAR_SYSTEM.value,
            completion_goal=8,
            reward_research_points=20,
        ),
        SurveyProgram(
            id="small_bodies_watch",
            name="Small Bodies Watch",
            description="Detect minor bodies — asteroids and comets crossing the inner system.",
            required_tier_ids=["improved_ground"],
            target_object_types=["asteroid", "comet"],
            scene_scope=SurveyScope.SOLAR_SYSTEM.value,
            completion_goal=2,
            reward_research_points=20,
        ),
        SurveyProgram(
            id="deep_field_survey",
            name="Deep Field Survey",
            description=(
                "Bridge from the solar tutorial to Scene 001 (Lyman-alpha Furnace): "
                "long-exposure imaging of distant galaxies, quasars, and Lyman-alpha blobs. "
                "Generate scene-001 after unlocking space_optical."
            ),
            required_tier_ids=["space_optical"],
            target_object_types=["galaxy", "quasar", "lyman_alpha_blob"],
            scene_scope=SurveyScope.DEEP_FIELD.value,
            completion_goal=10,
            reward_research_points=75,
            min_confidence=DEFAULT_MIN_CONFIDENCE,
            flavor="Start this when you load the deep-field scene — not while stuck on solar-system only.",
        ),
        SurveyProgram(
            id="radio_sky_survey",
            name="Radio Sky Survey",
            description="Map radio sources, hydrogen line emission, and the cosmic microwave background.",
            required_tier_ids=["radio"],
            required_signal_types=["radio"],
            target_object_types=["cmb_background", "quasar", "galaxy"],
            scene_scope=SurveyScope.ANY.value,
            completion_goal=5,
            reward_research_points=90,
        ),
        SurveyProgram(
            id="compact_object_search",
            name="Compact Object Search",
            description="Hunt for compact, high-energy sources: black holes and magnetars.",
            required_tier_ids=["xray_gamma"],
            required_signal_types=["xray"],
            target_object_types=["black_hole", "magnetar"],
            scene_scope=SurveyScope.DEEP_FIELD.value,
            completion_goal=2,
            reward_research_points=125,
        ),
        SurveyProgram(
            id="multi_messenger_event_program",
            name="Multi-Messenger Event Program",
            description="Cross-correlate signals across photon, gravitational, and particle channels.",
            required_tier_ids=["multi_messenger"],
            required_signal_types=["gravitational_wave"],
            target_object_types=["black_hole", "magnetar", "quasar"],
            scene_scope=SurveyScope.ANY.value,
            completion_goal=3,
            reward_research_points=175,
            min_confidence=HIGH_CONFIDENCE,
        ),
        SurveyProgram(
            id="cosmic_web_mapping",
            name="Cosmic Web Mapping Program",
            description="Trace large-scale structure: filaments, nodes, and voids.",
            required_tier_ids=["dark_matter_mapper"],
            required_signal_types=["weak_lensing"],
            target_object_types=["cosmic_web_filament", "cosmic_web_node", "void"],
            scene_scope=SurveyScope.DEEP_FIELD.value,
            completion_goal=3,
            reward_research_points=300,
        ),
        SurveyProgram(
            id="dark_matter_inference_program",
            name="Dark Matter Inference Program",
            description="Statistical inference of dark matter distribution via lensing and tracers.",
            required_tier_ids=["dark_matter_mapper"],
            required_signal_types=["dark_matter_inference", "weak_lensing"],
            target_object_types=["cosmic_web_filament", "void", "galaxy"],
            scene_scope=SurveyScope.DEEP_FIELD.value,
            completion_goal=4,
            reward_research_points=400,
        ),
        SurveyProgram(
            id="now_scope_first_light",
            name="Now-Scope First Light",
            description="First operational use of the speculative now-scope. Observes the present "
                        "state of distant objects rather than retarded light.",
            required_tier_ids=["now_scope"],
            required_signal_types=["speculative_now_signal"],
            target_object_types=[],  # any object visible via the now-signal
            scene_scope=SurveyScope.ANY.value,
            completion_goal=1,
            reward_research_points=500,
            speculative=True,
            flavor="Causality is, for the moment, considered optional.",
        ),
    ]


_PROGRAMS_CACHE: list[SurveyProgram] | None = None


def _all_programs() -> list[SurveyProgram]:
    global _PROGRAMS_CACHE
    if _PROGRAMS_CACHE is None:
        _PROGRAMS_CACHE = get_default_survey_programs()
    return _PROGRAMS_CACHE


def get_survey_by_id(survey_id: str) -> SurveyProgram | None:
    return next((p for p in _all_programs() if p.id == survey_id), None)


def effective_survey_reward(survey: SurveyProgram, state) -> int:
    """Survey completion RP after entity background modifiers."""
    mod = get_entity_modifier(state.research_entity.entity_type)
    mult = float(mod.survey_rp_multiplier)
    if mod.speculative_bonus and survey.speculative:
        mult *= 1.1
    return max(0, int(round(float(survey.reward_research_points) * mult)))


# ---------------------------------------------------------------------------
# Status / availability
# ---------------------------------------------------------------------------


def _scope_matches(survey: SurveyProgram, scene_id: str | None) -> bool:
    if survey.scene_scope == SurveyScope.ANY.value:
        return True
    if scene_id is None:
        return True  # optimistic when no scene context
    if survey.scene_scope == SurveyScope.SOLAR_SYSTEM.value:
        return scene_id == "solar-system"
    if survey.scene_scope == SurveyScope.DEEP_FIELD.value:
        return scene_id != "solar-system"
    return False


def survey_status(state, survey: SurveyProgram) -> SurveyProgramStatus:
    """Return the dynamic status of a survey for the given state."""
    progress = state.survey_progress.get(survey.id)
    if progress and progress.completed:
        return SurveyProgramStatus.COMPLETED
    if state.active_survey_id == survey.id:
        return SurveyProgramStatus.ACTIVE

    unlocked = set(state.unlocked_tiers)
    known_signals = set(state.known_signal_types)
    if not all(t in unlocked for t in survey.required_tier_ids):
        return SurveyProgramStatus.LOCKED
    if not all(s in known_signals for s in survey.required_signal_types):
        return SurveyProgramStatus.LOCKED
    return SurveyProgramStatus.AVAILABLE


def available_surveys(state, scene_id: str | None = None) -> list[SurveyProgram]:
    """Return surveys that are AVAILABLE (not locked, not active, not completed)."""
    out = []
    for survey in _all_programs():
        if survey_status(state, survey) != SurveyProgramStatus.AVAILABLE:
            continue
        if not _scope_matches(survey, scene_id):
            continue
        out.append(survey)
    return out


# ---------------------------------------------------------------------------
# Mutation helpers (return new state, never mutate)
# ---------------------------------------------------------------------------


def start_survey(state, survey_id: str) -> tuple[object, str]:
    """Mark a survey as the active one.  Returns (new_state, message)."""
    survey = get_survey_by_id(survey_id)
    if survey is None:
        return state, f"Unknown survey: {survey_id}"

    status = survey_status(state, survey)
    if status == SurveyProgramStatus.COMPLETED:
        return state, f"'{survey.name}' is already completed."
    if status == SurveyProgramStatus.LOCKED:
        return state, f"'{survey.name}' is locked. Missing tiers/signals."

    new_progress = dict(state.survey_progress)
    if survey_id not in new_progress:
        new_progress[survey_id] = SurveyProgress(survey_id=survey_id)

    new_state = state.model_copy(
        update={"active_survey_id": survey_id, "survey_progress": new_progress}
    )
    return new_state, f"Started survey: {survey.name}"


def _matches_survey(
    survey: SurveyProgram,
    object_type: str,
    detected_signals: list[str],
    confidence: float,
    scene_id: str | None,
) -> bool:
    if survey.target_object_types and object_type not in survey.target_object_types:
        # speculative now-scope program has empty target list = any object qualifies
        if not (survey.speculative and not survey.target_object_types):
            return False
    if confidence < survey.min_confidence:
        return False
    if not _scope_matches(survey, scene_id):
        return False
    if survey.required_signal_types:
        det = set(detected_signals)
        if not all(s in det for s in survey.required_signal_types):
            return False
    return True


def update_survey_progress_for_discovery(
    state,
    object_id: str,
    object_type: str,
    detected_signals: list[str],
    confidence: float,
    scene_id: str | None,
) -> tuple[object, list[str]]:
    """Update active survey progress for a single discovery.

    Returns (new_state, messages).  Messages describe progress/completion events.
    """
    if not state.active_survey_id:
        return state, []

    survey = get_survey_by_id(state.active_survey_id)
    if survey is None:
        return state, []

    if not _matches_survey(survey, object_type, detected_signals, confidence, scene_id):
        return state, []

    progress = state.survey_progress.get(state.active_survey_id) or SurveyProgress(
        survey_id=state.active_survey_id
    )
    if object_id in progress.discovered_object_ids:
        return state, []
    if progress.completed:
        return state, []

    mod = get_entity_modifier(state.research_entity.entity_type)
    progress_delta = 1
    if survey.completion_goal >= 8 and mod.survey_progress_bonus > 0:
        progress_delta = 1 + mod.survey_progress_bonus
    new_count = min(survey.completion_goal, progress.discoveries_completed + progress_delta)
    new_ids = list(progress.discovered_object_ids) + [object_id]
    just_completed = new_count >= survey.completion_goal and not progress.completed

    new_progress = SurveyProgress(
        survey_id=progress.survey_id,
        observations_completed=progress.observations_completed,
        discoveries_completed=new_count,
        completed=just_completed or progress.completed,
        claimed_reward=progress.claimed_reward,
        discovered_object_ids=new_ids,
    )

    new_dict = dict(state.survey_progress)
    new_dict[state.active_survey_id] = new_progress

    new_rp = state.research_points
    messages: list[str] = []
    if just_completed and not new_progress.claimed_reward:
        reward = effective_survey_reward(survey, state)
        new_rp += reward
        new_progress = new_progress.model_copy(update={"claimed_reward": True})
        new_dict[state.active_survey_id] = new_progress
        messages.append(
            f"Survey '{survey.name}' complete — +{reward} RP awarded."
        )
    else:
        messages.append(
            f"Survey '{survey.name}' progress: "
            f"{new_count}/{survey.completion_goal}"
        )

    new_state = state.model_copy(
        update={"research_points": new_rp, "survey_progress": new_dict}
    )
    return new_state, messages


def claim_survey_reward(state, survey_id: str) -> tuple[object, str]:
    """Idempotently claim the reward for a completed survey."""
    survey = get_survey_by_id(survey_id)
    if survey is None:
        return state, f"Unknown survey: {survey_id}"
    progress = state.survey_progress.get(survey_id)
    if progress is None or not progress.completed:
        return state, f"Survey '{survey.name}' is not yet complete."
    if progress.claimed_reward:
        return state, f"Survey '{survey.name}' reward already claimed."

    reward = effective_survey_reward(survey, state)
    new_progress = progress.model_copy(update={"claimed_reward": True})
    new_dict = dict(state.survey_progress)
    new_dict[survey_id] = new_progress
    new_state = state.model_copy(
        update={
            "research_points": state.research_points + reward,
            "survey_progress": new_dict,
        }
    )
    return new_state, (
        f"Claimed reward for '{survey.name}': +{reward} RP"
    )
