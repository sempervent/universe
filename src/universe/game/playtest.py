"""Deterministic playtest scenarios, autoplay strategies, and balance reports."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

from universe.game.discovery import observe_scene
from universe.game.entity import (
    ENTITY_TYPE_LABELS,
    get_all_entity_modifiers,
    make_research_entity,
)
from universe.game.models import DiscoveryResult, ResearchState
from universe.game.guidance import get_guidance_hints
from universe.game.milestones import get_default_milestones
from universe.game.campaign_balance import (
    SceneMetricsTracker,
    alignment_summary_markdown,
    collect_ladder_warnings,
    generate_campaign_ladder_analysis,
    pick_next_scene_in_order,
    preferred_survey_id,
    run_campaign_alignment_checks,
    scene_max_turns,
    scene_ready_to_advance,
    should_switch_to_recommended_survey,
)
from universe.game.scenes import (
    campaign_advance_active_scene,
    ensure_campaign_state,
    set_active_scene,
    update_scene_unlocks,
)
from universe.game.surveys import (
    available_surveys,
    get_default_survey_programs,
    start_survey,
)
from universe.game.tech_tree import (
    available_upgrades,
    can_unlock_tier,
    effective_tier_research_cost,
    get_tier_by_id,
    unlock_tier,
)
from universe.game.telemetry import PlaytestEvent, PlaytestRun
from universe.models import SceneRegion
from universe.procedural.registry import CAMPAIGN_SCENE_IDS

# ---------------------------------------------------------------------------
# Scenario model
# ---------------------------------------------------------------------------

KNOWN_SCENE_IDS = CAMPAIGN_SCENE_IDS

DEFAULT_MATRIX_ENTITY_TYPES: list[str] = [
    m.entity_type
    for m in get_all_entity_modifiers()
    if m.entity_type != "custom"
]


class PlaytestScenario(BaseModel):
    id: str
    name: str
    description: str = ""
    scene_sequence: list[str] = Field(default_factory=lambda: ["solar-system"])
    entity_types: list[str] = Field(default_factory=list)
    strategy: str = "greedy_research"
    use_campaign_progression: bool = False
    campaign_advance_max_order: int | None = None
    max_turns: int = 60
    target_tier_id: str | None = None
    stop_when_target_reached: bool = False
    initial_unlocked_tiers: list[str] = Field(default_factory=list)
    initial_research_points: int = 0
    initial_active_tier: str | None = None
    scene_seeds: dict[str, str] = Field(default_factory=dict)


def get_default_scenarios() -> list[PlaytestScenario]:
    return [
        PlaytestScenario(
            id="solar_tutorial_basic",
            name="Solar Tutorial (Basic)",
            description="Tutorial pacing: observe solar system, cheapest upgrades.",
            scene_sequence=["solar-system"],
            strategy="greedy_research",
            max_turns=50,
            scene_seeds={"solar-system": "local-sky"},
        ),
        PlaytestScenario(
            id="solar_to_deep_field_campaign",
            name="Solar → Deep Field Campaign",
            description=(
                "Greedy solar tutorial until scene-001 unlocks, then switch campaign "
                "scene and observe deep field."
            ),
            scene_sequence=["solar-system", "scene-001"],
            strategy="campaign_greedy",
            use_campaign_progression=True,
            max_turns=80,
            target_tier_id="space_optical",
            campaign_advance_max_order=1,
            scene_seeds={"solar-system": "local-sky", "scene-001": "lyman-alpha-furnace"},
        ),
        PlaytestScenario(
            id="campaign_instrument_ladder",
            name="Campaign Instrument Ladder",
            description=(
                "Progress through campaign scenes as instrument tiers unlock: "
                "solar → deep field → radio → high-energy → cosmic web → now-scope."
            ),
            scene_sequence=[
                "solar-system",
                "scene-001",
                "radio-cmb-survey",
                "stellar-remnant-field",
                "cosmic-web-map",
                "now-scope-anomaly-field",
            ],
            strategy="campaign_ordered",
            use_campaign_progression=True,
            max_turns=250,
            stop_when_target_reached=False,
            scene_seeds={
                "solar-system": "local-sky",
                "scene-001": "lyman-alpha-furnace",
                "radio-cmb-survey": "radio-first-light",
                "stellar-remnant-field": "high-energy-remnants",
                "cosmic-web-map": "invisible-architecture",
                "now-scope-anomaly-field": "impossible-now",
            },
        ),
        PlaytestScenario(
            id="solar_to_space_optical",
            name="Solar → Space Optical",
            description="Can the player reach space_optical from solar-system play?",
            scene_sequence=["solar-system"],
            strategy="greedy_research",
            max_turns=120,
            target_tier_id="space_optical",
            stop_when_target_reached=True,
            scene_seeds={"solar-system": "local-sky"},
        ),
        PlaytestScenario(
            id="deep_field_first_contact",
            name="Deep Field First Contact",
            description="Discover first galaxy/quasar/LAB with space optics.",
            scene_sequence=["scene-001"],
            strategy="greedy_research",
            max_turns=80,
            initial_unlocked_tiers=[
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
            ],
            initial_active_tier="space_optical",
            scene_seeds={"scene-001": "lyman-alpha-furnace"},
        ),
        PlaytestScenario(
            id="radio_transition",
            name="Radio Transition",
            description="Radio sky survey, CMB, quasar jets from radio tier.",
            scene_sequence=["scene-001"],
            strategy="greedy_research",
            max_turns=100,
            initial_unlocked_tiers=[
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
                "radio",
            ],
            initial_active_tier="radio",
            scene_seeds={"scene-001": "lyman-alpha-furnace"},
        ),
        PlaytestScenario(
            id="compact_object_transition",
            name="Compact Object Transition",
            description="X-ray/gamma tier: magnetar / black hole candidates.",
            scene_sequence=["scene-001"],
            strategy="greedy_research",
            max_turns=100,
            initial_unlocked_tiers=[
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
                "radio",
                "xray_gamma",
            ],
            initial_active_tier="xray_gamma",
            scene_seeds={"scene-001": "lyman-alpha-furnace"},
        ),
        PlaytestScenario(
            id="late_game_inference",
            name="Late Game Inference",
            description="Weak lensing / dark matter cosmic web inference.",
            scene_sequence=["scene-001"],
            strategy="greedy_research",
            max_turns=80,
            initial_unlocked_tiers=[
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
                "radio",
                "xray_gamma",
                "interferometer",
                "gravitational_wave",
                "neutrino_cosmic_ray",
                "multi_messenger",
                "dark_matter_mapper",
            ],
            initial_active_tier="dark_matter_mapper",
            scene_seeds={"scene-001": "lyman-alpha-furnace"},
        ),
        PlaytestScenario(
            id="now_scope_smoke",
            name="Now-Scope Smoke",
            description="Speculative endgame tier wiring does not crash.",
            scene_sequence=["scene-001"],
            strategy="greedy_research",
            max_turns=30,
            initial_unlocked_tiers=[
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
                "radio",
                "xray_gamma",
                "interferometer",
                "gravitational_wave",
                "neutrino_cosmic_ray",
                "multi_messenger",
                "dark_matter_mapper",
                "now_scope",
            ],
            initial_active_tier="now_scope",
            initial_research_points=500,
            scene_seeds={"scene-001": "lyman-alpha-furnace"},
        ),
    ]


_SCENARIO_MAP: dict[str, PlaytestScenario] | None = None


def get_scenario_by_id(scenario_id: str) -> PlaytestScenario | None:
    global _SCENARIO_MAP
    if _SCENARIO_MAP is None:
        _SCENARIO_MAP = {s.id: s for s in get_default_scenarios()}
    return _SCENARIO_MAP.get(scenario_id)


def deep_field_scenario_ids() -> frozenset[str]:
    return frozenset(
        {
            "deep_field_first_contact",
            "radio_transition",
            "compact_object_transition",
            "late_game_inference",
            "now_scope_smoke",
        }
    )


# ---------------------------------------------------------------------------
# Scene loading
# ---------------------------------------------------------------------------


def load_scene(scene_id: str, seed: str) -> SceneRegion:
    from universe.procedural.registry import generate_scene_by_id

    try:
        return generate_scene_by_id(scene_id, seed=seed)
    except ValueError as exc:
        raise ValueError(
            f"Unknown scene id: {scene_id}. Known: {sorted(KNOWN_SCENE_IDS)}"
        ) from exc


def scene_seed_for(scenario: PlaytestScenario, scene_id: str, run_seed: str) -> str:
    return scenario.scene_seeds.get(scene_id, run_seed)


def current_scene_id(
    scenario: PlaytestScenario,
    turn: int,
    state: ResearchState | None = None,
) -> str:
    if scenario.use_campaign_progression and state is not None:
        return state.campaign.active_scene_id
    seq = scenario.scene_sequence
    if not seq:
        return "solar-system"
    if len(seq) == 1:
        return seq[0]
    idx = min(turn // 25, len(seq) - 1)
    return seq[idx]


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def make_run_id(scenario_id: str, entity_type: str, seed: str) -> str:
    raw = f"{scenario_id}:{entity_type}:{seed}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def bootstrap_unlocked_tiers(state: ResearchState, tier_ids: list[str]) -> ResearchState:
    """Grant tiers without spending RP (playtest bootstrap only)."""
    unlocked = list(state.unlocked_tiers)
    signals: set[str] = set(state.known_signal_types)
    ordered = sorted(
        tier_ids,
        key=lambda tid: (get_tier_by_id(tid).tier_index if get_tier_by_id(tid) else 99, tid),
    )
    for tid in ordered:
        tier = get_tier_by_id(tid)
        if tier is None:
            continue
        if tid not in unlocked:
            unlocked.append(tid)
        signals.update(s.value for s in tier.signal_types)
    return state.model_copy(
        update={
            "unlocked_tiers": unlocked,
            "known_signal_types": sorted(signals),
        }
    )


def initial_state(
    scenario: PlaytestScenario,
    entity_type: str,
    seed: str,
) -> ResearchState:
    entity = make_research_entity(
        name=f"Playtest {ENTITY_TYPE_LABELS.get(entity_type, entity_type)}",
        entity_type=entity_type,
    )
    state = ensure_campaign_state(
        ResearchState(
            research_points=scenario.initial_research_points,
            research_entity=entity,
        )
    )
    if scenario.initial_unlocked_tiers:
        state = bootstrap_unlocked_tiers(state, scenario.initial_unlocked_tiers)
    if scenario.initial_active_tier:
        state = state.model_copy(update={"active_telescope_tier": scenario.initial_active_tier})
    elif scenario.initial_unlocked_tiers:
        best = max(
            scenario.initial_unlocked_tiers,
            key=lambda tid: (
                get_tier_by_id(tid).tier_index if get_tier_by_id(tid) else -1
            ),
        )
        state = state.model_copy(update={"active_telescope_tier": best})
    return ensure_campaign_state(state)


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------


def _discovery_event_type(result: DiscoveryResult) -> str:
    c = result.identification_confidence
    if c >= 0.95:
        return "characterize_object"
    if c >= 0.75:
        return "confirm_object"
    if result.newly_discovered:
        return "discover_object"
    return "observe_object"


def _record_event(
    events: list[PlaytestEvent],
    *,
    state_before: ResearchState,
    state_after: ResearchState,
    turn: int,
    event_type: str,
    entity_type: str,
    message: str = "",
    **kwargs: Any,
) -> None:
    events.append(
        PlaytestEvent.from_state_delta(
            turn=turn,
            event_type=event_type,
            entity_type=entity_type,
            state_before=state_before,
            state_after=state_after,
            message=message,
            **kwargs,
        )
    )


def _parse_survey_id(message: str) -> str | None:
    m = re.search(r"Survey '([^']+)'", message)
    if not m:
        return None
    name = m.group(1)
    for survey in get_default_survey_programs():
        if survey.name == name:
            return survey.id
    return None


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def _autoplay_observe_transients(
    scene: SceneRegion,
    state: ResearchState,
    events: list[PlaytestEvent],
    entity_type: str,
    *,
    before_state: ResearchState | None = None,
) -> ResearchState:
    from universe.game.transients import (
        available_transient_events_for_scene,
        observe_transient_event,
        update_transient_event_states,
    )

    state = update_transient_event_states(state)
    for defn in available_transient_events_for_scene(scene, state):
        prev = state
        state, result, err = observe_transient_event(scene, state, defn.id)
        if result is None:
            continue
        _record_event(
            events,
            state_before=prev,
            state_after=state,
            turn=state.turn,
            event_type="transient_observed",
            entity_type=entity_type,
            message=result.message,
            object_id=f"__transient__:{defn.id}",
            object_type="transient_event",
            metadata={
                "event_id": defn.id,
                "reward_rp": result.research_points,
                "speculative": defn.speculative,
            },
        )
    return state


def _cheapest_upgrade(state: ResearchState):
    upgrades = available_upgrades(state)
    if not upgrades:
        return None
    return min(upgrades, key=lambda t: effective_tier_research_cost(t, state))


def _highest_unlocked_tier_id(state: ResearchState) -> str:
    best_id = state.active_telescope_tier
    best_idx = -1
    for tid in state.unlocked_tiers:
        tier = get_tier_by_id(tid)
        if tier and tier.tier_index > best_idx:
            best_idx = tier.tier_index
            best_id = tid
    return best_id


def _greedy_turn(
    state: ResearchState,
    scene: SceneRegion,
    events: list[PlaytestEvent],
    entity_type: str,
    *,
    tier_unlock_turns: dict[str, int],
    survey_complete_turns: dict[str, int],
    milestone_turns: dict[str, int],
    **kwargs: Any,
) -> ResearchState:
    turn = state.turn + 1
    scene_id = scene.id

    # Start survey if none active.
    if not state.active_survey_id:
        preferred = kwargs.get("preferred_survey_id")
        if preferred:
            before = state
            state, msg = start_survey(state, preferred)
            _record_event(
                events,
                state_before=before,
                state_after=state,
                turn=turn,
                event_type="survey_started",
                entity_type=entity_type,
                message=msg,
                survey_id=preferred,
            )
        else:
            candidates = available_surveys(state, scene_id=scene_id)
            if candidates:
                before = state
                state, msg = start_survey(state, candidates[0].id)
                _record_event(
                    events,
                    state_before=before,
                    state_after=state,
                    turn=turn,
                    event_type="survey_started",
                    entity_type=entity_type,
                    message=msg,
                    survey_id=candidates[0].id,
                )

    before_observe = state
    state, results = observe_scene(scene, state)
    state = _autoplay_observe_transients(
        scene, state, events, entity_type, before_state=before_observe
    )

    for r in results:
        if r.object_id == "__survey__":
            sid = _parse_survey_id(r.message) or state.active_survey_id
            if "complete" in r.message.lower():
                if sid and sid not in survey_complete_turns:
                    survey_complete_turns[sid] = state.turn
                _record_event(
                    events,
                    state_before=before_observe,
                    state_after=state,
                    turn=state.turn,
                    event_type="survey_completed",
                    entity_type=entity_type,
                    message=r.message,
                    survey_id=sid,
                )
            else:
                _record_event(
                    events,
                    state_before=before_observe,
                    state_after=state,
                    turn=state.turn,
                    event_type="survey_progressed",
                    entity_type=entity_type,
                    message=r.message,
                    survey_id=sid,
                )
            continue
        if r.object_id == "__milestone__":
            mid = None
            for milestone in get_default_milestones():
                if milestone.name in r.message:
                    mid = milestone.id
                    break
            if mid and mid not in milestone_turns:
                milestone_turns[mid] = state.turn
            _record_event(
                events,
                state_before=before_observe,
                state_after=state,
                turn=state.turn,
                event_type="milestone_achieved",
                entity_type=entity_type,
                message=r.message,
                milestone_id=mid,
            )
            continue

        if r.object_id == "__reward_cap__":
            uncapped = capped = cap_val = None
            m = re.search(
                r"(\d+) awarded of (\d+) uncapped \(cap (\d+)\)", r.message
            )
            if m:
                capped, uncapped, cap_val = int(m.group(1)), int(m.group(2)), int(m.group(3))
            _record_event(
                events,
                state_before=before_observe,
                state_after=state,
                turn=state.turn,
                event_type="reward_cap_applied",
                entity_type=entity_type,
                message=r.message,
                object_id=r.object_id,
                object_type=r.object_type,
                metadata={
                    "reward_cap_applied": True,
                    "uncapped_rp": uncapped,
                    "capped_rp": capped,
                    "cap_value": cap_val,
                    "scene_id": scene_id,
                },
            )
            continue

        if r.object_id.startswith("__"):
            continue

        ev_type = (
            "followup_research_awarded"
            if r.message.startswith("Follow-up:")
            else _discovery_event_type(r)
        )
        _record_event(
            events,
            state_before=before_observe,
            state_after=state,
            turn=state.turn,
            event_type=ev_type,
            entity_type=entity_type,
            message=r.message,
            object_id=r.object_id,
            object_type=r.object_type,
            confidence=r.identification_confidence,
        )

    if not any(
        r.object_id not in ("__survey__", "__milestone__") and not r.object_id.startswith("__")
        for r in results
    ):
        _record_event(
            events,
            state_before=before_observe,
            state_after=state,
            turn=state.turn,
            event_type="no_observable_targets",
            entity_type=entity_type,
            message="No new discoveries or upgrades this turn.",
        )

    # Cheapest upgrade.
    cheapest = _cheapest_upgrade(state)
    if cheapest:
        ok, reason = can_unlock_tier(state, cheapest.id)
        if ok:
            before = state
            state, msg = unlock_tier(state, cheapest.id)
            if cheapest.id not in tier_unlock_turns:
                tier_unlock_turns[cheapest.id] = state.turn
            _record_event(
                events,
                state_before=before,
                state_after=state,
                turn=state.turn,
                event_type="telescope_unlocked",
                entity_type=entity_type,
                message=msg,
                tier_id=cheapest.id,
            )
        else:
            _record_event(
                events,
                state_before=state,
                state_after=state,
                turn=state.turn,
                event_type="blocked_upgrade",
                entity_type=entity_type,
                message=reason,
                tier_id=cheapest.id,
                metadata={"needed_rp": effective_tier_research_cost(cheapest, state)},
            )

    # Set active to highest unlocked tier.
    best = _highest_unlocked_tier_id(state)
    if best != state.active_telescope_tier:
        before = state
        state = state.model_copy(update={"active_telescope_tier": best})
        _record_event(
            events,
            state_before=before,
            state_after=state,
            turn=state.turn,
            event_type="telescope_set_active",
            entity_type=entity_type,
            message=f"Active telescope set to {best}",
            tier_id=best,
        )

    return state


def _campaign_greedy_turn(
    state: ResearchState,
    scene: SceneRegion,
    events: list[PlaytestEvent],
    entity_type: str,
    *,
    tier_unlock_turns: dict[str, int],
    survey_complete_turns: dict[str, int],
    milestone_turns: dict[str, int],
    scene_unlock_turns: dict[str, int],
    scenario: PlaytestScenario,
    seed: str = "local-sky",
) -> ResearchState:
    before = state
    state, newly_unlocked = update_scene_unlocks(state)
    for sid in newly_unlocked:
        if sid not in scene_unlock_turns:
            scene_unlock_turns[sid] = state.turn
        _record_event(
            events,
            state_before=before,
            state_after=state,
            turn=state.turn,
            event_type="scene_unlocked",
            entity_type=entity_type,
            message=f"Campaign scene unlocked: {sid}",
            metadata={"scene_id": sid},
        )

    if scenario.use_campaign_progression:
        before_switch = state
        state, msg, new_sid = campaign_advance_active_scene(
            state,
            newly_unlocked=newly_unlocked,
            max_order_index=scenario.campaign_advance_max_order,
        )
        if new_sid and msg:
            _record_event(
                events,
                state_before=before_switch,
                state_after=state,
                turn=state.turn,
                event_type="active_scene_changed",
                entity_type=entity_type,
                message=msg,
                metadata={"scene_id": new_sid},
            )

    scene_id = state.campaign.active_scene_id
    if scene.id != scene_id:
        scene = load_scene(scene_id, scene_seed_for(scenario, scene_id, seed))

    return _greedy_turn(
        state,
        scene,
        events,
        entity_type,
        tier_unlock_turns=tier_unlock_turns,
        survey_complete_turns=survey_complete_turns,
        milestone_turns=milestone_turns,
    )


def _campaign_ordered_turn(
    state: ResearchState,
    scene: SceneRegion,
    events: list[PlaytestEvent],
    entity_type: str,
    *,
    tier_unlock_turns: dict[str, int],
    survey_complete_turns: dict[str, int],
    milestone_turns: dict[str, int],
    scene_unlock_turns: dict[str, int],
    scene_turns: dict[str, int],
    scenario: PlaytestScenario,
    seed: str = "local-sky",
) -> ResearchState:
    """Campaign autoplay: catalog order, advance when scene is mostly exhausted."""
    before = state
    state, newly_unlocked = update_scene_unlocks(state)
    for sid in newly_unlocked:
        if sid not in scene_unlock_turns:
            scene_unlock_turns[sid] = state.turn
        _record_event(
            events,
            state_before=before,
            state_after=state,
            turn=state.turn,
            event_type="scene_unlocked",
            entity_type=entity_type,
            message=f"Campaign scene unlocked: {sid}",
            metadata={"scene_id": sid},
        )

    scene_id = state.campaign.active_scene_id
    if scene.id != scene_id:
        scene = load_scene(scene_id, scene_seed_for(scenario, scene_id, seed))

    turns_in_scene = scene_turns.get(scene_id, 0)
    next_sid = pick_next_scene_in_order(state)
    if next_sid and scene_ready_to_advance(
        state,
        scene,
        turns_in_scene=turns_in_scene,
        max_turns=scene_max_turns(scene_id),
    ):
        before_switch = state
        state, msg = set_active_scene(state, next_sid)
        if state.campaign.active_scene_id == next_sid:
            _record_event(
                events,
                state_before=before_switch,
                state_after=state,
                turn=state.turn,
                event_type="active_scene_changed",
                entity_type=entity_type,
                message=msg,
                metadata={"scene_id": next_sid},
            )
            scene_id = next_sid
            scene = load_scene(scene_id, scene_seed_for(scenario, scene_id, seed))
            turns_in_scene = scene_turns.get(scene_id, 0)

    survey_pref = preferred_survey_id(state, scene_id)
    if survey_pref and should_switch_to_recommended_survey(state, scene_id, survey_pref):
        before_survey = state
        state, msg = start_survey(state, survey_pref)
        _record_event(
            events,
            state_before=before_survey,
            state_after=state,
            turn=state.turn + 1,
            event_type="survey_started",
            entity_type=entity_type,
            message=msg,
            survey_id=survey_pref,
        )

    state = _greedy_turn(
        state,
        scene,
        events,
        entity_type,
        tier_unlock_turns=tier_unlock_turns,
        survey_complete_turns=survey_complete_turns,
        milestone_turns=milestone_turns,
        preferred_survey_id=survey_pref,
    )
    scene_turns[scene_id] = turns_in_scene + 1
    return state


def _apply_new_events_to_tracker(
    events: list[PlaytestEvent],
    start_idx: int,
    tracker: SceneMetricsTracker,
    active_scene_id: str,
) -> None:
    meaningful_discovery = {
        "discover_object",
        "confirm_object",
        "characterize_object",
    }
    for e in events[start_idx:]:
        if e.event_type == "telescope_unlocked" and e.tier_id:
            cost = max(0, -e.delta_research_points)
            tracker.record_tier_unlock(
                e.tier_id, e.turn, active_scene_id, cost
            )
        elif e.event_type in meaningful_discovery and e.object_id:
            rp_match = re.search(r"\+(\d+) RP", e.message)
            delta = int(rp_match.group(1)) if rp_match else max(0, e.delta_research_points)
            tracker.record_discovery_event(
                active_scene_id=active_scene_id,
                turn=e.turn,
                confidence=e.confidence or 0.0,
                delta_rp=delta,
            )
        elif e.event_type == "survey_completed" and e.survey_id:
            tracker.record_survey_complete(active_scene_id, e.survey_id)
        elif e.event_type == "milestone_achieved" and e.milestone_id:
            tracker.record_milestone(active_scene_id, e.milestone_id)


STRATEGIES: dict[str, Callable[..., ResearchState]] = {
    "greedy_research": _greedy_turn,
    "campaign_greedy": _campaign_greedy_turn,
    "campaign_ordered": _campaign_ordered_turn,
}


def _survey_first_turn(*args, **kwargs) -> ResearchState:
    """Prefer surveys before observing (variant of greedy)."""
    state = args[0]
    scene = args[1]
    events = args[2]
    entity_type = args[3]
    if not state.active_survey_id:
        candidates = available_surveys(state, scene_id=scene.id)
        if candidates:
            before = state
            state, msg = start_survey(state, candidates[0].id)
            _record_event(
                events,
                state_before=before,
                state_after=state,
                turn=state.turn + 1,
                event_type="survey_started",
                entity_type=entity_type,
                message=msg,
                survey_id=candidates[0].id,
            )
    scenario = kwargs.get("scenario")
    if scenario and scenario.strategy == "campaign_greedy":
        return _campaign_greedy_turn(*args, **kwargs)
    if scenario and scenario.strategy == "campaign_ordered":
        return _campaign_ordered_turn(*args, **kwargs)
    return _greedy_turn(*args, **kwargs)


STRATEGIES["survey_first"] = _survey_first_turn


# ---------------------------------------------------------------------------
# Run playtest
# ---------------------------------------------------------------------------


def _build_summary(
    state: ResearchState,
    *,
    turns_played: int,
    tier_unlock_turns: dict[str, int],
    survey_complete_turns: dict[str, int],
    milestone_turns: dict[str, int],
    warnings: list[str],
    target_reached: bool,
    stuck_turns: int,
    rp_by_turn: list[int],
    dead_turn_count: int,
    first_no_rp_turn: int | None,
    guidance_hint_ids: list[str],
    followup_rp_earned: int,
    space_optical_turn: int | None,
    scene_unlock_turns: dict[str, int],
    campaign_transition_turn: int | None,
    first_deep_field_discovery_turn: int | None,
    has_now_scope_exclusive: bool,
    scene_tracker: SceneMetricsTracker | None = None,
    entity_type: str = "",
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "turns_played": turns_played,
        "final_rp": state.research_points,
        "final_tier": state.active_telescope_tier,
        "unlocked_tiers": list(state.unlocked_tiers),
        "tier_unlock_turn": dict(tier_unlock_turns),
        "survey_complete_turn": dict(survey_complete_turns),
        "milestone_turn": dict(milestone_turns),
        "discoveries_count": len(state.discoveries),
        "completed_discoveries": state.completed_discoveries,
        "warnings": warnings,
        "target_reached": target_reached,
        "stuck_turns": stuck_turns,
        "rp_by_turn": rp_by_turn,
        "dead_turn_count": dead_turn_count,
        "first_no_rp_turn": first_no_rp_turn,
        "guidance_hints_triggered": guidance_hint_ids,
        "followup_rp_earned": followup_rp_earned,
        "space_optical_unlock_turn": space_optical_turn,
        "first_deep_field_discovery_turn": first_deep_field_discovery_turn,
        "now_scope_exclusive_discovery": has_now_scope_exclusive,
        "active_scene_id": state.campaign.active_scene_id,
        "scene_unlock_turn": dict(scene_unlock_turns or {}),
        "campaign_transition_turn": campaign_transition_turn,
    }
    if scene_tracker is not None:
        ladder = scene_tracker.to_summary_dict()
        out.update(ladder)
        out["entity_type"] = entity_type
        out["scene_visit_sequence"] = ladder.get("scene_visit_sequence", [])
    return out


def _collect_warnings(
    state: ResearchState,
    events: list[PlaytestEvent],
    scenario: PlaytestScenario,
    *,
    stuck_turns: int,
    tier_unlock_turns: dict[str, int],
    survey_complete_turns: dict[str, int],
    guidance_hint_ids: list[str],
    has_now_scope_exclusive: bool,
    campaign_transition_turn: int | None = None,
    run_summary: dict[str, Any] | None = None,
) -> list[str]:
    warnings: list[str] = []

    if stuck_turns > 5:
        warnings.append(
            f"No RP progress for {stuck_turns} consecutive turns — player may be stuck."
        )

    if scenario.id == "solar_to_deep_field_campaign":
        if campaign_transition_turn is None and state.turn >= 10:
            warnings.append(
                "Campaign scenario: scene-001 unlocked but transition never occurred."
            )
        elif campaign_transition_turn is not None and campaign_transition_turn > 15:
            warnings.append(
                f"Campaign transition to scene-001 was late (turn {campaign_transition_turn})."
            )

    if scenario.id == "solar_to_space_optical" and "space_optical" not in state.unlocked_tiers:
        warnings.append(
            "Could not reach space_optical from solar-system-only loop within max turns."
        )

    local_turn = survey_complete_turns.get("local_sky_survey")
    if local_turn is not None and local_turn <= 1:
        warnings.append(
            "INFO: First Light Survey (local_sky_survey) completed turn 1 — "
            "intended tutorial pacing."
        )

    if "now_scope" in state.unlocked_tiers and state.turn <= 5:
        warnings.append("Now-scope reached very quickly — check bootstrap assumptions.")

    deep_rp = sum(
        e.delta_research_points
        for e in events
        if e.event_type in ("discover_object", "confirm_object", "characterize_object", "observe_object")
        and e.turn > 0
    )
    if scenario.id == "deep_field_first_contact" and deep_rp == 0 and state.turn >= 10:
        warnings.append("Deep-field scene yielded no discovery RP in extended play.")

    if (
        "space_optical" in state.unlocked_tiers
        and scenario.id in (
            "solar_tutorial_basic",
            "solar_to_space_optical",
            "solar_to_deep_field_campaign",
        )
        and "solar_exhausted_deep_field_ready" not in guidance_hint_ids
        and stuck_turns >= 3
        and campaign_transition_turn is None
    ):
        warnings.append(
            "space_optical unlocked but deep-field-ready guidance never shown — "
            "check solar exhaustion detection."
        )

    if "now_scope" in state.unlocked_tiers and not has_now_scope_exclusive:
        warnings.append(
            "Now-scope unlocked but no speculative_anomaly detection in this run."
        )

    if scenario.id == "campaign_instrument_ladder" and run_summary:
        warnings.extend(collect_ladder_warnings(run_summary, state))

    return warnings


def run_playtest(
    scenario: PlaytestScenario,
    *,
    entity_type: str,
    seed: str,
    max_turns: int | None = None,
) -> PlaytestRun:
    """Execute one deterministic autoplay session."""
    strategy_name = scenario.strategy
    turn_fn = STRATEGIES.get(strategy_name)
    if turn_fn is None:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    limit = max_turns if max_turns is not None else scenario.max_turns
    state = initial_state(scenario, entity_type, seed)
    events: list[PlaytestEvent] = []
    tier_unlock_turns: dict[str, int] = {tid: 0 for tid in state.unlocked_tiers}
    survey_complete_turns: dict[str, int] = {}
    milestone_turns: dict[str, int] = {}
    rp_by_turn: list[int] = [state.research_points]
    warnings: list[str] = []
    stuck_turns = 0
    max_stuck_turns = 0
    first_no_rp_turn: int | None = None
    target_reached = False
    guidance_hint_ids: set[str] = set()
    followup_rp_earned = 0
    space_optical_turn = tier_unlock_turns.get("space_optical")
    first_deep_field_discovery_turn: int | None = None
    deep_types = {"galaxy", "quasar", "lyman_alpha_blob", "speculative_anomaly"}

    scene_cache: dict[str, SceneRegion] = {}
    scene_unlock_turns: dict[str, int] = {}
    scene_turns: dict[str, int] = {}
    campaign_transition_turn: int | None = None
    scene_tracker: SceneMetricsTracker | None = None
    reward_cap_events: list[dict[str, Any]] = []
    if scenario.use_campaign_progression:
        scene_tracker = SceneMetricsTracker()

    for _ in range(limit):
        scene_id = current_scene_id(scenario, state.turn, state)
        if scene_id not in scene_cache:
            scene_cache[scene_id] = load_scene(
                scene_id, scene_seed_for(scenario, scene_id, seed)
            )
        scene = scene_cache[scene_id]

        rp_before = state.research_points
        prev_active = state.campaign.active_scene_id
        event_cursor = len(events)
        state = turn_fn(
            state,
            scene,
            events,
            entity_type,
            tier_unlock_turns=tier_unlock_turns,
            survey_complete_turns=survey_complete_turns,
            milestone_turns=milestone_turns,
            scenario=scenario,
            seed=seed,
            scene_unlock_turns=scene_unlock_turns,
            **(
                {"scene_turns": scene_turns}
                if strategy_name == "campaign_ordered"
                else {}
            ),
        )
        for e in events[event_cursor:]:
            if e.event_type == "survey_started" and e.survey_id:
                if scene_tracker is not None:
                    scene_tracker.record_survey_started(
                        state.campaign.active_scene_id, e.survey_id
                    )
            if e.event_type == "reward_cap_applied":
                reward_cap_events.append(
                    {
                        "turn": e.turn,
                        "scene_id": state.campaign.active_scene_id,
                        "message": e.message,
                    }
                )
        if scene_tracker is not None:
            active = state.campaign.active_scene_id
            scene_tracker.sync_campaign_state(state, scene_unlock_turns)
            if prev_active != active:
                scene_tracker.record_visit(active, state.turn)
            scene_tracker.record_visit(active, state.turn)
            scene_tracker.record_turn(
                state,
                rp_before=rp_before,
                rp_after=state.research_points,
                active_scene_id=active,
            )
            _apply_new_events_to_tracker(
                events, event_cursor, scene_tracker, active
            )
        if (
            campaign_transition_turn is None
            and prev_active == "solar-system"
            and state.campaign.active_scene_id == "scene-001"
        ):
            campaign_transition_turn = state.turn
        rp_by_turn.append(state.research_points)

        if "space_optical" in tier_unlock_turns and space_optical_turn is None:
            space_optical_turn = tier_unlock_turns.get("space_optical")

        for hint in get_guidance_hints(scene, state):
            guidance_hint_ids.add(hint.id)

        if state.research_points == rp_before:
            stuck_turns += 1
            if first_no_rp_turn is None:
                first_no_rp_turn = state.turn
        else:
            stuck_turns = 0
        max_stuck_turns = max(max_stuck_turns, stuck_turns)

        if scenario.target_tier_id and scenario.target_tier_id in state.unlocked_tiers:
            target_reached = True
            if scenario.stop_when_target_reached:
                break

    followup_rp_earned = 0
    for e in events:
        if e.event_type != "followup_research_awarded":
            continue
        m = re.search(r"\+(\d+) RP", e.message)
        if m:
            followup_rp_earned += int(m.group(1))
    has_now_scope_exclusive = any(
        d.object_type == "speculative_anomaly" for d in state.discoveries.values()
    )
    for e in events:
        if e.object_type in deep_types and first_deep_field_discovery_turn is None:
            if e.event_type in (
                "discover_object",
                "confirm_object",
                "characterize_object",
                "observe_object",
            ):
                first_deep_field_discovery_turn = e.turn

    hint_list = sorted(guidance_hint_ids)
    pre_summary = _build_summary(
        state,
        turns_played=state.turn,
        tier_unlock_turns=tier_unlock_turns,
        survey_complete_turns=survey_complete_turns,
        milestone_turns=milestone_turns,
        warnings=[],
        target_reached=target_reached,
        stuck_turns=max_stuck_turns,
        rp_by_turn=rp_by_turn,
        dead_turn_count=max_stuck_turns,
        first_no_rp_turn=first_no_rp_turn,
        guidance_hint_ids=hint_list,
        followup_rp_earned=followup_rp_earned,
        space_optical_turn=space_optical_turn,
        scene_unlock_turns=scene_unlock_turns,
        campaign_transition_turn=campaign_transition_turn,
        first_deep_field_discovery_turn=first_deep_field_discovery_turn,
        has_now_scope_exclusive=has_now_scope_exclusive,
        scene_tracker=scene_tracker,
        entity_type=entity_type,
    )
    warnings.extend(
        _collect_warnings(
            state,
            events,
            scenario,
            stuck_turns=stuck_turns,
            tier_unlock_turns=tier_unlock_turns,
            survey_complete_turns=survey_complete_turns,
            guidance_hint_ids=hint_list,
            has_now_scope_exclusive=has_now_scope_exclusive,
            campaign_transition_turn=campaign_transition_turn,
            run_summary=pre_summary,
        )
    )

    summary = _build_summary(
        state,
        turns_played=state.turn,
        tier_unlock_turns=tier_unlock_turns,
        survey_complete_turns=survey_complete_turns,
        milestone_turns=milestone_turns,
        warnings=warnings,
        target_reached=target_reached,
        stuck_turns=max_stuck_turns,
        rp_by_turn=rp_by_turn,
        dead_turn_count=max_stuck_turns,
        first_no_rp_turn=first_no_rp_turn,
        guidance_hint_ids=hint_list,
        followup_rp_earned=followup_rp_earned,
        space_optical_turn=space_optical_turn,
        scene_unlock_turns=scene_unlock_turns,
        campaign_transition_turn=campaign_transition_turn,
        first_deep_field_discovery_turn=first_deep_field_discovery_turn,
        has_now_scope_exclusive=has_now_scope_exclusive,
        scene_tracker=scene_tracker,
        entity_type=entity_type,
    )
    summary["warnings"] = warnings
    summary["reward_cap_events"] = reward_cap_events
    summary["reward_cap_count"] = len(reward_cap_events)
    summary["now_scope_reached"] = "now_scope" in state.unlocked_tiers

    from universe.game.transients import get_default_transient_events, update_transient_event_states

    state = update_transient_event_states(state)
    transient_observed = [
        eid for eid, ts in state.transient_events.items() if ts.reward_claimed
    ]
    transient_missed = [
        d.id
        for d in get_default_transient_events()
        if state.transient_events.get(d.id) is not None
        and state.transient_events[d.id].expired
        and not state.transient_events[d.id].reward_claimed
    ]
    transient_rp = sum(
        e.metadata.get("reward_rp", 0)
        for e in events
        if e.event_type == "transient_observed"
    )
    first_transient_turn: int | None = None
    for e in events:
        if e.event_type == "transient_observed":
            first_transient_turn = e.turn
            break
    speculative_transient = any(
        e.metadata.get("speculative") for e in events if e.event_type == "transient_observed"
    )
    summary["transient_events_observed"] = transient_observed
    summary["transient_events_missed"] = transient_missed
    summary["transient_rp_total"] = transient_rp
    summary["first_transient_observed_turn"] = first_transient_turn
    summary["speculative_transient_observed"] = speculative_transient

    return PlaytestRun(
        id=make_run_id(scenario.id, entity_type, seed),
        seed=seed,
        entity_name=state.research_entity.name,
        entity_type=entity_type,
        scenario_id=scenario.id,
        started_at=PlaytestRun.utc_now_iso(),
        events=events,
        final_state=state,
        summary=summary,
    )


def write_playtest_run(run: PlaytestRun, out_path: Path, *, write_events: bool = True) -> dict[str, Path]:
    """Write run JSON and optional sidecar files."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
    written: dict[str, Path] = {"run": out_path}

    stem = out_path.with_suffix("")
    if write_events:
        events_path = Path(f"{stem}_events.jsonl")
        with events_path.open("w", encoding="utf-8") as fh:
            for ev in run.events:
                fh.write(ev.model_dump_json() + "\n")
        written["events"] = events_path

    summary_path = Path(f"{stem}_summary.md")
    summary_path.write_text(format_run_summary_md(run), encoding="utf-8")
    written["summary"] = summary_path
    return written


def format_run_summary_md(run: PlaytestRun) -> str:
    s = run.summary
    lines = [
        f"# Playtest: {run.scenario_id}",
        "",
        f"- **Run ID:** `{run.id}`",
        f"- **Entity:** {run.entity_name} (`{run.entity_type}`)",
        f"- **Seed:** `{run.seed}`",
        f"- **Turns:** {s.get('turns_played', 0)}",
        f"- **Final RP:** {s.get('final_rp', 0)}",
        f"- **Final tier:** `{s.get('final_tier', '')}`",
        "",
        "## Tier unlock turns",
        "",
    ]
    for tid, tturn in sorted(
        (s.get("tier_unlock_turn") or {}).items(),
        key=lambda x: (get_tier_by_id(x[0]).tier_index if get_tier_by_id(x[0]) else 99, x[0]),
    ):
        lines.append(f"- `{tid}`: turn {tturn}")
    lines.extend(["", "## Warnings", ""])
    for w in s.get("warnings") or []:
        lines.append(f"- {w}")
    if not s.get("warnings"):
        lines.append("- _(none)_")
    return "\n".join(lines) + "\n"


def run_playtest_matrix(
    out_dir: Path,
    *,
    scenario_ids: list[str] | None = None,
    entity_types: list[str] | None = None,
    seed: str = "local-sky",
    max_turns: int | None = None,
    include_deep_field: bool = True,
) -> dict[str, Any]:
    """Run scenario × entity matrix; write runs and matrix-summary.json."""
    out_dir = Path(out_dir)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    scenarios = get_default_scenarios()
    if scenario_ids:
        scenarios = [s for s in scenarios if s.id in scenario_ids]
    if not include_deep_field:
        df = deep_field_scenario_ids()
        scenarios = [s for s in scenarios if s.id not in df]

    entities = entity_types or DEFAULT_MATRIX_ENTITY_TYPES

    matrix_runs: list[dict[str, Any]] = []
    for scenario in scenarios:
        for etype in entities:
            if scenario.entity_types and etype not in scenario.entity_types:
                continue
            run = run_playtest(
                scenario,
                entity_type=etype,
                seed=seed,
                max_turns=max_turns,
            )
            fname = f"{scenario.id}_{etype}.json"
            run_path = runs_dir / fname
            write_playtest_run(run, run_path)
            matrix_runs.append(
                {
                    "run_id": run.id,
                    "scenario_id": run.scenario_id,
                    "entity_type": run.entity_type,
                    "seed": run.seed,
                    "path": str(run_path.relative_to(out_dir)),
                    "summary": run.summary,
                }
            )

    summary = {
        "seed": seed,
        "scenario_count": len(scenarios),
        "entity_count": len(entities),
        "run_count": len(matrix_runs),
        "runs": matrix_runs,
    }
    summary_path = out_dir / "matrix-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {"summary_path": summary_path, "runs": matrix_runs}


# ---------------------------------------------------------------------------
# Balance report
# ---------------------------------------------------------------------------


def load_runs_from_input(input_path: Path) -> list[PlaytestRun]:
    input_path = Path(input_path)
    runs: list[PlaytestRun] = []

    if input_path.is_file():
        data = json.loads(input_path.read_text())
        runs.append(PlaytestRun.model_validate(data))
        return runs

    summary_file = input_path / "matrix-summary.json"
    if summary_file.exists():
        summary = json.loads(summary_file.read_text())
        for entry in summary.get("runs", []):
            rel = entry.get("path")
            if rel:
                run_path = input_path / rel
                if run_path.exists():
                    runs.append(PlaytestRun.model_validate_json(run_path.read_text()))
        if runs:
            return runs

    for path in sorted(input_path.rglob("*.json")):
        if path.name == "matrix-summary.json":
            continue
        try:
            runs.append(PlaytestRun.model_validate_json(path.read_text()))
        except Exception:
            continue
    return runs


def generate_balance_report(runs: list[PlaytestRun]) -> str:
    """Build human-readable markdown balance report."""
    if not runs:
        return "# Balance Report\n\nNo playtest runs found.\n"

    by_scenario: dict[str, list[PlaytestRun]] = {}
    by_entity: dict[str, list[PlaytestRun]] = {}
    all_warnings: list[str] = []
    balance_flags: list[str] = []

    for run in runs:
        by_scenario.setdefault(run.scenario_id, []).append(run)
        by_entity.setdefault(run.entity_type, []).append(run)
        all_warnings.extend(run.summary.get("warnings") or [])

    lines = [
        "# Balance Playtest Report",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Runs analyzed:** {len(runs)}",
        f"- **Scenarios:** {', '.join(sorted(by_scenario))}",
        f"- **Entity types:** {', '.join(sorted(by_entity))}",
        "",
    ]

    # Quick findings
    solar_space = [
        r for r in runs
        if r.scenario_id == "solar_to_space_optical"
    ]
    reached = sum(1 for r in solar_space if r.summary.get("target_reached"))
    if solar_space:
        lines.append(
            f"- **Solar → space_optical:** {reached}/{len(solar_space)} runs reached target tier."
        )
    lines.append("")

    lines.extend(["## 2. Scenario Results", ""])
    for sid in sorted(by_scenario):
        group = by_scenario[sid]
        lines.append(f"### `{sid}`")
        lines.append("")
        for r in group:
            s = r.summary
            lines.append(
                f"- `{r.entity_type}`: {s.get('turns_played')} turns, "
                f"RP {s.get('final_rp')}, tier `{s.get('final_tier')}`, "
                f"discoveries {s.get('discoveries_count')}"
            )
        lines.append("")

    lines.extend(["## 3. Entity Type Comparison", ""])
    for etype in sorted(by_entity):
        group = by_entity[etype]
        avg_rp = sum(r.summary.get("final_rp", 0) for r in group) / len(group)
        lines.append(f"- **{etype}:** avg final RP {avg_rp:.0f} over {len(group)} runs")
    lines.append("")

    lines.extend(["## 4. Telescope Tier Unlock Timing", ""])
    tier_rows: dict[str, dict[str, int | None]] = {}
    for run in runs:
        for tid, tturn in (run.summary.get("tier_unlock_turn") or {}).items():
            tier_rows.setdefault(tid, {})[run.entity_type] = tturn
    for tid in sorted(
        tier_rows,
        key=lambda t: (get_tier_by_id(t).tier_index if get_tier_by_id(t) else 99, t),
    ):
        parts = [f"`{tid}`:"]
        for etype, tturn in sorted(tier_rows[tid].items()):
            parts.append(f" {etype}=turn {tturn}")
        lines.append("- " + ", ".join(parts))
    lines.append("")

    lines.extend(["## 5. Survey Completion Timing", ""])
    for run in runs:
        sc = run.summary.get("survey_complete_turn") or {}
        if sc:
            lines.append(
                f"- `{run.scenario_id}` / `{run.entity_type}`: "
                + ", ".join(f"{k}@t{v}" for k, v in sorted(sc.items()))
            )
    if not any(r.summary.get("survey_complete_turn") for r in runs):
        lines.append("- _(no surveys completed in sampled runs)_")
    lines.append("")

    lines.extend(["## 6. Milestone Timing", ""])
    for run in runs:
        mt = run.summary.get("milestone_turn") or {}
        if mt:
            lines.append(
                f"- `{run.scenario_id}` / `{run.entity_type}`: "
                + ", ".join(f"{k}@t{v}" for k, v in sorted(mt.items()))
            )
    lines.append("")

    lines.extend(["## 7. Research Point Economy", ""])
    for run in runs[:8]:
        rp_curve = run.summary.get("rp_by_turn") or []
        if rp_curve:
            lines.append(
                f"- `{run.scenario_id}` / `{run.entity_type}`: "
                f"RP curve starts {rp_curve[0]} → ends {rp_curve[-1]} "
                f"({len(rp_curve) - 1} turns)"
            )
    lines.append("")

    lines.extend(["## 7b. Dead Turns & Follow-up RP", ""])
    for run in runs:
        s = run.summary
        lines.append(
            f"- `{run.scenario_id}` / `{run.entity_type}`: "
            f"max dead streak {s.get('dead_turn_count', 0)}, "
            f"first no-RP turn {s.get('first_no_rp_turn', '—')}, "
            f"follow-up RP {s.get('followup_rp_earned', 0)}"
        )
    lines.append("")

    lines.extend(["## 7c. Guidance Hints Triggered", ""])
    for run in runs:
        hints = run.summary.get("guidance_hints_triggered") or []
        if hints:
            lines.append(
                f"- `{run.scenario_id}` / `{run.entity_type}`: "
                + ", ".join(hints)
            )
    if not any(r.summary.get("guidance_hints_triggered") for r in runs):
        lines.append("- _(none)_")
    lines.append("")

    lines.extend(["## 7d. Deep Field & Now-Scope", ""])
    for run in runs:
        s = run.summary
        lines.append(
            f"- `{run.scenario_id}` / `{run.entity_type}`: "
            f"space_optical@t{s.get('space_optical_unlock_turn', '—')}, "
            f"first deep discovery@t{s.get('first_deep_field_discovery_turn', '—')}, "
            f"now-scope exclusive={s.get('now_scope_exclusive_discovery', False)}"
        )
    lines.append("")

    lines.extend(["## 7e. Campaign Scene Progression", ""])
    campaign_runs = [
        r
        for r in runs
        if r.scenario_id in ("solar_to_deep_field_campaign", "campaign_instrument_ladder")
    ]
    if campaign_runs:
        for r in campaign_runs:
            s = r.summary
            su = s.get("scene_unlock_turn") or {}
            visited = [
                sid
                for sid, cs in (r.final_state.campaign.scenes or {}).items()
                if cs.visited
            ]
            lines.append(
                f"- `{r.scenario_id}` / `{r.entity_type}`: active `{s.get('active_scene_id')}`, "
                f"visited={visited}, transition@t{s.get('campaign_transition_turn', '—')}, "
                f"unlocks={', '.join(f'{k}@t{v}' for k, v in sorted(su.items()))}"
            )
        no_transition = [
            r
            for r in campaign_runs
            if r.scenario_id == "solar_to_deep_field_campaign"
            and r.summary.get("campaign_transition_turn") is None
            and r.summary.get("turns_played", 0) >= 10
        ]
        if no_transition:
            balance_flags.append(
                "Campaign scenario: scene-001 unlocked but active scene never switched to deep field."
            )
        ladder = [r for r in campaign_runs if r.scenario_id == "campaign_instrument_ladder"]
        if ladder:
            shallow = [
                r
                for r in ladder
                if len(
                    [
                        sid
                        for sid, cs in r.final_state.campaign.scenes.items()
                        if cs.visited
                    ]
                )
                < 3
            ]
            if shallow:
                balance_flags.append(
                    "Instrument ladder: fewer than 3 campaign scenes visited — "
                    "check tier pacing or scene auto-switch."
                )
            reached_now = sum(1 for r in ladder if r.summary.get("now_scope_reached"))
            if ladder and reached_now / len(ladder) < 0.5:
                balance_flags.append(
                    f"Now-scope reach rate {reached_now}/{len(ladder)} below 50% within "
                    f"{ladder[0].summary.get('turns_played', '?')} turns — tune late-game surveys/milestones."
                )
    else:
        lines.append("- _(no campaign progression runs in input)_")
    lines.append("")

    lines.extend(["## 7f. Campaign Ladder Analysis", ""])
    lines.append(generate_campaign_ladder_analysis(runs))

    lines.extend(["## 7h. Observation RP Cap Events", ""])
    ladder_caps = [
        r
        for r in runs
        if r.scenario_id == "campaign_instrument_ladder"
        and (r.summary.get("reward_cap_count") or 0) > 0
    ]
    if ladder_caps:
        for r in ladder_caps:
            lines.append(
                f"- `{r.entity_type}`: {r.summary.get('reward_cap_count')} cap(s); "
                f"now_scope={r.summary.get('now_scope_reached', False)}"
            )
    else:
        lines.append("- _(no cap events in campaign ladder runs — verify scene-001 observe)_")
    lines.append("")

    alignment_checks = run_campaign_alignment_checks()
    lines.extend(["## 7g. Campaign Scene / Survey Alignment", ""])
    lines.append(alignment_summary_markdown(alignment_checks))
    lines.append("")

    lines.extend(["## 7i. Transient Events", ""])
    ladder_transient = [
        r for r in runs if r.scenario_id == "campaign_instrument_ladder"
    ]
    if ladder_transient:
        for r in ladder_transient:
            obs = r.summary.get("transient_events_observed") or []
            miss = r.summary.get("transient_events_missed") or []
            lines.append(
                f"- `{r.entity_type}`: observed={obs}, missed={len(miss)}, "
                f"transient RP={r.summary.get('transient_rp_total', 0)}, "
                f"first@t{r.summary.get('first_transient_observed_turn', '—')}, "
                f"speculative={r.summary.get('speculative_transient_observed', False)}"
            )
        never_obs = [r for r in ladder_transient if not r.summary.get("transient_events_observed")]
        if never_obs:
            balance_flags.append(
                "Campaign ladder: some entity types observed no transient events."
            )
    else:
        lines.append("- _(no ladder runs for transient summary)_")
    lines.append("")

    lines.extend(["## 8. Warnings", ""])
    unique_warnings = sorted(set(all_warnings))
    if unique_warnings:
        for w in unique_warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- _(none triggered)_")
    lines.append("")

    # Heuristic balance flags
    solar_tutorial = [r for r in runs if r.scenario_id == "solar_tutorial_basic"]
    if solar_tutorial:
        avg_dead = sum(r.summary.get("dead_turn_count", 0) for r in solar_tutorial) / len(
            solar_tutorial
        )
        if avg_dead > 20:
            balance_flags.append(
                f"Solar tutorial still shows long dead streaks (avg {avg_dead:.0f} turns) — "
                "ensure players see deep-field guidance and follow-up RP."
            )

    backyard_early = [
        r for r in runs
        if r.entity_type == "backyard_observatory"
        and (r.summary.get("tier_unlock_turn") or {}).get("improved_ground", 99) <= 3
    ]
    citizen = [r for r in runs if r.entity_type == "citizen_science_network"]
    if backyard_early:
        balance_flags.append(
            "Backyard observatory reaches improved_ground very early compared to baseline — verify early_optical discount."
        )
    if citizen:
        fast_surveys = [
            r for r in citizen
            if any(v <= 2 for v in (r.summary.get("survey_complete_turn") or {}).values())
        ]
        if fast_surveys:
            balance_flags.append(
                "Citizen science survey progress bonus may complete small surveys too quickly."
            )

    if not reached and solar_space:
        balance_flags.append(
            "Player cannot reliably reach space_optical from solar-system-only loop — tutorial may need more RP sources."
        )

    lines.extend(["## 9. Suggested Balance Adjustments", ""])
    flags = balance_flags or [
        "Review tier costs and discovery RP curves using the tables above.",
        "Compare entity modifier runs side-by-side before changing values.",
    ]
    for f in flags:
        lines.append(f"- {f}")
    lines.append("")
    return "\n".join(lines)


def write_balance_report(input_path: Path, out_path: Path) -> Path:
    runs = load_runs_from_input(input_path)
    md = generate_balance_report(runs)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    return out_path
