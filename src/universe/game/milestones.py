"""Milestones — discovery and progression achievements.

Milestones recognise meaningful firsts in the Research Entity's history.
They award research points exactly once per achievement.  Evaluation is a
straightforward Python predicate over the current ResearchState.
"""

from __future__ import annotations

from typing import NamedTuple

from pydantic import BaseModel

from universe.game.entity import DEFAULT_ENTITY_NAME, get_entity_modifier

# Confidence thresholds reused from the discovery loop.
CANDIDATE = 0.5
CONFIRMED = 0.75


class Milestone(BaseModel):
    """Static definition of a milestone."""

    id: str
    name: str
    description: str = ""
    reward_research_points: int = 0
    condition_type: str = ""  # short tag for UI grouping
    hidden: bool = False
    speculative: bool = False


class MilestoneRecord(BaseModel):
    """Per-player record of a milestone's status."""

    milestone_id: str
    achieved: bool = False
    achieved_at_turn: int = 0
    reward_claimed: bool = False


class MilestoneAward(NamedTuple):
    """Milestone plus RP actually credited (after entity modifiers)."""

    milestone: Milestone
    research_points: int


def effective_milestone_reward(milestone: Milestone, state) -> int:
    """RP granted for this milestone, including entity background multipliers."""
    mod = get_entity_modifier(state.research_entity.entity_type)
    mult = float(mod.milestone_rp_multiplier)
    if mod.speculative_bonus and milestone.speculative:
        mult *= 1.1
    return max(0, int(round(float(milestone.reward_research_points) * mult)))


# ---------------------------------------------------------------------------
# Default catalogue
# ---------------------------------------------------------------------------


def get_default_milestones() -> list[Milestone]:
    return [
        Milestone(
            id="first_light",
            name="First Light",
            description="Complete the entity's first observation pass.",
            reward_research_points=5,
            condition_type="observation",
        ),
        Milestone(
            id="named_entity",
            name="Founding Charter",
            description="Give the research entity a real name.",
            reward_research_points=5,
            condition_type="entity",
        ),
        Milestone(
            id="first_planet",
            name="First Planet Confirmed",
            description="Confirm a planetary detection.",
            reward_research_points=5,
            condition_type="discovery",
        ),
        Milestone(
            id="first_moon",
            name="First Moon Confirmed",
            description="Confirm a lunar detection.",
            reward_research_points=5,
            condition_type="discovery",
        ),
        Milestone(
            id="first_comet",
            name="First Comet Detected",
            description="Detect a comet.",
            reward_research_points=10,
            condition_type="discovery",
        ),
        Milestone(
            id="first_upgrade",
            name="First Telescope Upgrade",
            description="Unlock a telescope tier beyond the naked eye.",
            reward_research_points=10,
            condition_type="progression",
        ),
        Milestone(
            id="first_deep_field_ready",
            name="Deep Field Instruments Ready",
            description=(
                "Your instruments can now attempt deep-field observations. "
                "Generate Scene 001 and start the Deep Field Survey."
            ),
            reward_research_points=15,
            condition_type="progression",
        ),
        Milestone(
            id="radio_first_light",
            name="Radio First Light",
            description="Make a radio-band observation.",
            reward_research_points=20,
            condition_type="signal",
        ),
        Milestone(
            id="first_deep_sky_object",
            name="First Deep-Sky Object",
            description="Discover a galaxy, quasar, or Lyman-alpha blob.",
            reward_research_points=40,
            condition_type="discovery",
        ),
        Milestone(
            id="first_black_hole_candidate",
            name="First Black Hole Candidate",
            description="Identify a candidate black hole.",
            reward_research_points=75,
            condition_type="discovery",
        ),
        Milestone(
            id="first_magnetar",
            name="First Magnetar Confirmed",
            description="Confirm a magnetar detection.",
            reward_research_points=75,
            condition_type="discovery",
        ),
        Milestone(
            id="multi_messenger_confirmation",
            name="Multi-Messenger Confirmation",
            description="Confirm an object with three or more independent signal types.",
            reward_research_points=100,
            condition_type="signal",
        ),
        Milestone(
            id="cosmic_web_mapped",
            name="Cosmic Web Mapped",
            description="Confirm a cosmic web filament or node.",
            reward_research_points=150,
            condition_type="discovery",
        ),
        Milestone(
            id="dark_matter_inferred",
            name="Dark Matter Inferred",
            description="Use a dark matter inference to characterise an object.",
            reward_research_points=200,
            condition_type="signal",
        ),
        Milestone(
            id="dark_matter_instrument_online",
            name="Dark Matter Instrument Online",
            description="Unlock the weak-lensing / dark-matter mapper tier.",
            reward_research_points=120,
            condition_type="tier",
        ),
        Milestone(
            id="first_dark_matter_map_complete",
            name="First Cosmic-Web Survey Complete",
            description=(
                "Complete the Cosmic Web Mapping or Dark Matter Inference survey program."
            ),
            reward_research_points=200,
            condition_type="survey",
        ),
        Milestone(
            id="now_scope_first_light",
            name="Now-Scope First Light",
            description="Make a first observation through the speculative now-scope.",
            reward_research_points=300,
            condition_type="speculative",
            speculative=True,
        ),
    ]


_MILESTONES_CACHE: list[Milestone] | None = None


def _all_milestones() -> list[Milestone]:
    global _MILESTONES_CACHE
    if _MILESTONES_CACHE is None:
        _MILESTONES_CACHE = get_default_milestones()
    return _MILESTONES_CACHE


def get_milestone_by_id(mid: str) -> Milestone | None:
    return next((m for m in _all_milestones() if m.id == mid), None)


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def _has_discovery(state, type_set: set[str], min_conf: float) -> bool:
    return any(
        d.object_type in type_set and d.confidence >= min_conf
        for d in state.discoveries.values()
    )


def _has_signal_in_discoveries(state, signal: str) -> bool:
    return any(signal in d.detected_signals for d in state.discoveries.values())


def _milestone_condition(milestone_id: str, state) -> bool:
    if milestone_id == "first_light":
        return state.turn >= 1 or len(state.discoveries) > 0
    if milestone_id == "named_entity":
        n = state.research_entity.name
        return bool(n) and n != DEFAULT_ENTITY_NAME
    if milestone_id == "first_planet":
        return _has_discovery(state, {"planet"}, CONFIRMED)
    if milestone_id == "first_moon":
        return _has_discovery(state, {"moon"}, CONFIRMED)
    if milestone_id == "first_comet":
        return _has_discovery(state, {"comet"}, CANDIDATE)
    if milestone_id == "first_upgrade":
        return len([t for t in state.unlocked_tiers if t != "naked_eye"]) >= 1
    if milestone_id == "first_deep_field_ready":
        if "space_optical" not in state.unlocked_tiers:
            return False
        prog = state.survey_progress.get("local_sky_survey")
        if prog is not None and prog.completed:
            return True
        solar_types = {"star", "planet", "moon", "asteroid", "comet"}
        solar_hits = sum(
            1
            for d in state.discoveries.values()
            if d.object_type in solar_types and d.confidence >= CANDIDATE
        )
        return solar_hits >= 8
    if milestone_id == "radio_first_light":
        if "radio" in state.known_signal_types:
            return True
        return _has_signal_in_discoveries(state, "radio")
    if milestone_id == "first_deep_sky_object":
        return _has_discovery(state, {"galaxy", "quasar", "lyman_alpha_blob"}, CANDIDATE)
    if milestone_id == "first_black_hole_candidate":
        return _has_discovery(state, {"black_hole"}, CANDIDATE)
    if milestone_id == "first_magnetar":
        return _has_discovery(state, {"magnetar"}, CONFIRMED)
    if milestone_id == "multi_messenger_confirmation":
        return any(
            len(d.detected_signals) >= 3 and d.confidence >= CONFIRMED
            for d in state.discoveries.values()
        )
    if milestone_id == "cosmic_web_mapped":
        return _has_discovery(state, {"cosmic_web_filament", "cosmic_web_node"}, CONFIRMED)
    if milestone_id == "dark_matter_inferred":
        return _has_signal_in_discoveries(state, "dark_matter_inference")
    if milestone_id == "dark_matter_instrument_online":
        return "dark_matter_mapper" in state.unlocked_tiers
    if milestone_id == "first_dark_matter_map_complete":
        for sid in ("cosmic_web_mapping", "dark_matter_inference_program"):
            prog = state.survey_progress.get(sid)
            if prog is not None and prog.completed:
                return True
        return False
    if milestone_id == "now_scope_first_light":
        if _has_signal_in_discoveries(state, "speculative_now_signal"):
            return True
        return any(
            d.first_detected_tier == "now_scope" for d in state.discoveries.values()
        )
    return False


# ---------------------------------------------------------------------------
# Evaluation (auto-claim)
# ---------------------------------------------------------------------------


def evaluate_milestones(state) -> tuple[object, list[MilestoneAward]]:
    """Check every milestone, mark newly-achieved ones, auto-credit RP.

    Returns (new_state, newly_achieved).  Already-achieved milestones are
    untouched; rewards are not double-counted.
    """
    new_records = dict(state.milestones)
    newly_achieved: list[MilestoneAward] = []
    extra_rp = 0

    for milestone in _all_milestones():
        existing = new_records.get(milestone.id)
        if existing and existing.achieved:
            continue
        if not _milestone_condition(milestone.id, state):
            continue

        rp = effective_milestone_reward(milestone, state)
        record = MilestoneRecord(
            milestone_id=milestone.id,
            achieved=True,
            achieved_at_turn=state.turn,
            reward_claimed=True,
        )
        new_records[milestone.id] = record
        newly_achieved.append(MilestoneAward(milestone=milestone, research_points=rp))
        extra_rp += rp

    if not newly_achieved:
        return state, []

    new_state = state.model_copy(
        update={
            "milestones": new_records,
            "research_points": state.research_points + extra_rp,
        }
    )
    return new_state, newly_achieved


def claim_milestone_rewards(state) -> tuple[object, list[MilestoneAward]]:
    """Alias for evaluate_milestones — idempotent claim pass."""
    return evaluate_milestones(state)
