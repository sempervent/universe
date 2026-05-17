"""Deterministic turn-window transient observation events."""

from __future__ import annotations

from typing import NamedTuple

from pydantic import BaseModel, Field

from universe.game.entity import get_entity_modifier
from universe.game.models import (
    DiscoveryResult,
    ResearchState,
    SignalType,
    TransientEventState,
)
from universe.game.tech_tree import get_tier_by_id
from universe.models import CosmicObject, SceneRegion


class TransientEventDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    scene_id: str
    event_type: str
    required_signal_types: list[SignalType] = Field(default_factory=list)
    optional_signal_types: list[SignalType] = Field(default_factory=list)
    minimum_telescope_tier: str = "naked_eye"
    start_turn: int = 1
    duration_turns: int = 4
    reward_research_points: int = 15
    target_object_types: list[str] = Field(default_factory=list)
    related_object_id: str | None = None
    speculative: bool = False
    repeatable: bool = False
    metadata: dict = Field(default_factory=dict)


class TransientObserveResult(NamedTuple):
    event: TransientEventDefinition
    research_points: int
    message: str
    detected_signals: list[str]


_CATALOG_CACHE: list[TransientEventDefinition] | None = None


def get_default_transient_events() -> list[TransientEventDefinition]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    S = SignalType
    _CATALOG_CACHE = [
        TransientEventDefinition(
            id="solar_flare_001",
            name="Solar Flare",
            description="A brief brightening on the Sun — visible and high-energy signatures.",
            scene_id="solar-system",
            event_type="solar_flare",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.RADIO, S.XRAY],
            minimum_telescope_tier="ground_optical",
            start_turn=2,
            duration_turns=4,
            reward_research_points=15,
            target_object_types=["star"],
            related_object_id="sun",
        ),
        TransientEventDefinition(
            id="comet_brightening_001",
            name="Comet Brightening",
            description="A comet in the inner system brightens enough for improved optics to catch.",
            scene_id="solar-system",
            event_type="comet_outburst",
            required_signal_types=[S.VISIBLE_LIGHT],
            minimum_telescope_tier="improved_ground",
            start_turn=3,
            duration_turns=6,
            reward_research_points=18,
            target_object_types=["comet"],
        ),
        TransientEventDefinition(
            id="quasar_outburst_001",
            name="Quasar Outburst",
            description="A distant quasar flares across radio and optical bands.",
            scene_id="scene-001",
            event_type="quasar_outburst",
            required_signal_types=[S.RADIO, S.XRAY, S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED],
            minimum_telescope_tier="space_optical",
            start_turn=6,
            duration_turns=8,
            reward_research_points=60,
            target_object_types=["quasar"],
        ),
        TransientEventDefinition(
            id="magnetar_flare_001",
            name="Magnetar Flare",
            description="A magnetar releases a high-energy burst.",
            scene_id="stellar-remnant-field",
            event_type="magnetar_flare",
            required_signal_types=[S.XRAY, S.GAMMA_RAY, S.RADIO],
            minimum_telescope_tier="xray_gamma",
            start_turn=8,
            duration_turns=5,
            reward_research_points=100,
            target_object_types=["magnetar"],
        ),
        TransientEventDefinition(
            id="gravitational_wave_candidate_001",
            name="Gravitational-Wave Candidate",
            description="A compact-object merger candidate in the GW network stream.",
            scene_id="stellar-remnant-field",
            event_type="gravitational_wave",
            required_signal_types=[S.GRAVITATIONAL_WAVE],
            minimum_telescope_tier="gravitational_wave",
            start_turn=12,
            duration_turns=6,
            reward_research_points=130,
            target_object_types=["black_hole", "magnetar", "quasar"],
        ),
        TransientEventDefinition(
            id="lensing_anomaly_001",
            name="Weak-Lensing Anomaly",
            description="A filament–void configuration shows an unusual lensing residual.",
            scene_id="cosmic-web-map",
            event_type="lensing_anomaly",
            required_signal_types=[S.WEAK_LENSING],
            optional_signal_types=[S.DARK_MATTER_INFERENCE],
            minimum_telescope_tier="dark_matter_mapper",
            start_turn=18,
            duration_turns=12,
            reward_research_points=180,
            target_object_types=["cosmic_web_filament", "void", "galaxy"],
        ),
        TransientEventDefinition(
            id="neutrino_burst_001",
            name="Neutrino Burst",
            description="A high-energy neutrino event coincident with a compact remnant.",
            scene_id="stellar-remnant-field",
            event_type="neutrino_burst",
            required_signal_types=[S.NEUTRINO],
            minimum_telescope_tier="neutrino_cosmic_ray",
            start_turn=20,
            duration_turns=5,
            reward_research_points=150,
            target_object_types=["magnetar", "black_hole"],
        ),
        TransientEventDefinition(
            id="causality_echo_001",
            name="Causality Echo",
            description=(
                "Fictional now-scope echo: a speculative anomaly flickers outside "
                "retarded-light constraints. Not a physical prediction."
            ),
            scene_id="now-scope-anomaly-field",
            event_type="speculative_now_event",
            required_signal_types=[S.SPECULATIVE_NOW_SIGNAL],
            minimum_telescope_tier="now_scope",
            start_turn=30,
            duration_turns=20,
            reward_research_points=320,
            target_object_types=["speculative_anomaly"],
            speculative=True,
        ),
    ]
    return _CATALOG_CACHE


def get_transient_event(event_id: str) -> TransientEventDefinition | None:
    return next((e for e in get_default_transient_events() if e.id == event_id), None)


def _tier_index(tier_id: str) -> int:
    tier = get_tier_by_id(tier_id)
    return tier.tier_index if tier else -1


def _tier_requirement_met(state: ResearchState, minimum_tier_id: str) -> bool:
    if minimum_tier_id in state.unlocked_tiers:
        return True
    min_idx = _tier_index(minimum_tier_id)
    active_idx = _tier_index(state.active_telescope_tier)
    return active_idx >= min_idx >= 0


def _signals_requirement_met(state: ResearchState, required: list[SignalType]) -> bool:
    if not required:
        return True
    known = set(state.known_signal_types)
    return any(s.value in known for s in required)


def _scene_has_targets(scene: SceneRegion, defn: TransientEventDefinition) -> bool:
    if not defn.target_object_types:
        return True
    types = {o.type.value for o in scene.objects}
    if defn.related_object_id:
        return any(o.id == defn.related_object_id for o in scene.objects)
    return bool(types & set(defn.target_object_types))


def _effective_reward(defn: TransientEventDefinition, state: ResearchState) -> int:
    mod = get_entity_modifier(state.research_entity.entity_type)
    mult = float(mod.discovery_rp_multiplier)
    if mod.speculative_bonus and defn.speculative:
        mult *= 1.1
    return max(0, int(round(defn.reward_research_points * mult)))


def ensure_transient_states(state: ResearchState) -> ResearchState:
    events = dict(state.transient_events)
    changed = False
    for defn in get_default_transient_events():
        if defn.id not in events:
            events[defn.id] = TransientEventState(event_id=defn.id)
            changed = True
    if changed:
        return state.model_copy(update={"transient_events": events})
    return state


def update_transient_event_states(state: ResearchState, *, turn: int | None = None) -> ResearchState:
    """Refresh active/expired flags for all catalog events at *turn* (default state.turn)."""
    state = ensure_transient_states(state)
    t = state.turn if turn is None else turn
    new_events: dict[str, TransientEventState] = {}
    for defn in get_default_transient_events():
        prev = state.transient_events[defn.id]
        end = defn.start_turn + defn.duration_turns
        active = defn.start_turn <= t < end
        expired = t >= end
        new_events[defn.id] = prev.model_copy(
            update={"active": active, "expired": expired}
        )
    return state.model_copy(update={"transient_events": new_events})


def active_transient_events(
    state: ResearchState,
    scene_id: str,
    *,
    turn: int | None = None,
) -> list[TransientEventDefinition]:
    state = update_transient_event_states(state, turn=turn)
    out: list[TransientEventDefinition] = []
    for defn in get_default_transient_events():
        if defn.scene_id != scene_id:
            continue
        ts = state.transient_events[defn.id]
        if ts.active and not ts.expired:
            out.append(defn)
    return out


def upcoming_transient_events(
    state: ResearchState,
    scene_id: str,
    *,
    turn: int | None = None,
) -> list[TransientEventDefinition]:
    t = state.turn if turn is None else turn
    return [
        d
        for d in get_default_transient_events()
        if d.scene_id == scene_id and d.start_turn > t
    ]


def expired_transient_events(
    state: ResearchState,
    scene_id: str,
    *,
    turn: int | None = None,
) -> list[tuple[TransientEventDefinition, TransientEventState]]:
    state = update_transient_event_states(state, turn=turn)
    out: list[tuple[TransientEventDefinition, TransientEventState]] = []
    for defn in get_default_transient_events():
        if defn.scene_id != scene_id:
            continue
        ts = state.transient_events[defn.id]
        if ts.expired:
            out.append((defn, ts))
    return out


def is_transient_observable(
    scene: SceneRegion,
    state: ResearchState,
    event_id: str,
    *,
    turn: int | None = None,
) -> tuple[bool, str]:
    defn = get_transient_event(event_id)
    if defn is None:
        return False, f"Unknown transient event: {event_id}"
    if scene.id != defn.scene_id:
        return False, f"Event belongs to scene '{defn.scene_id}', not '{scene.id}'."

    t = state.turn if turn is None else turn
    state = update_transient_event_states(state, turn=t)
    ts = state.transient_events[event_id]

    if ts.expired:
        return False, "Event has expired."
    if not ts.active:
        return False, f"Event not active (window turns {defn.start_turn}–{defn.start_turn + defn.duration_turns - 1})."
    if ts.reward_claimed and not defn.repeatable:
        return False, "Event already observed."
    if not _tier_requirement_met(state, defn.minimum_telescope_tier):
        return False, f"Requires telescope tier '{defn.minimum_telescope_tier}' or better."
    if not _signals_requirement_met(state, defn.required_signal_types):
        req = ", ".join(s.value for s in defn.required_signal_types)
        return False, f"Requires at least one signal: {req}."
    if not _scene_has_targets(scene, defn):
        return False, "No matching targets in this scene."
    return True, ""


def available_transient_events(
    state: ResearchState,
    scene_id: str,
    *,
    turn: int | None = None,
) -> list[TransientEventDefinition]:
    """Active events in *scene_id* matching tier/signal (no scene object check)."""
    state = update_transient_event_states(state, turn=turn)
    out: list[TransientEventDefinition] = []
    for defn in active_transient_events(state, scene_id, turn=turn):
        ts = state.transient_events[defn.id]
        if ts.reward_claimed and not defn.repeatable:
            continue
        if not _tier_requirement_met(state, defn.minimum_telescope_tier):
            continue
        if not _signals_requirement_met(state, defn.required_signal_types):
            continue
        out.append(defn)
    return out


def available_transient_events_for_scene(
    scene: SceneRegion,
    state: ResearchState,
    *,
    turn: int | None = None,
) -> list[TransientEventDefinition]:
    state = update_transient_event_states(state, turn=turn)
    return [
        d
        for d in active_transient_events(state, scene.id, turn=turn)
        if is_transient_observable(scene, state, d.id, turn=turn)[0]
    ]


def _pick_target_object(scene: SceneRegion, defn: TransientEventDefinition) -> CosmicObject | None:
    if defn.related_object_id:
        for obj in scene.objects:
            if obj.id == defn.related_object_id:
                return obj
    for obj in scene.objects:
        if obj.type.value in defn.target_object_types:
            return obj
    return scene.objects[0] if scene.objects and not defn.target_object_types else None


def observe_transient_event(
    scene: SceneRegion,
    state: ResearchState,
    event_id: str,
) -> tuple[ResearchState, TransientObserveResult | None, str]:
    """Observe a transient event. Returns (new_state, result, error_message)."""
    from universe.game.milestones import evaluate_milestones
    from universe.game.surveys import update_survey_progress_for_discovery

    state = ensure_transient_states(state)
    ok, reason = is_transient_observable(scene, state, event_id)
    if not ok:
        return state, None, reason

    defn = get_transient_event(event_id)
    assert defn is not None
    state = update_transient_event_states(state)
    ts = state.transient_events[defn.id]
    rp = _effective_reward(defn, state)
    detected = [s.value for s in defn.required_signal_types if s.value in state.known_signal_types]
    if not detected and defn.required_signal_types:
        detected = [defn.required_signal_types[0].value]

    target = _pick_target_object(scene, defn)
    object_id = target.id if target else f"transient:{defn.id}"
    object_type = target.type.value if target else (defn.target_object_types[0] if defn.target_object_types else "transient_event")

    observed_turns = list(ts.observed_turns)
    observed_turns.append(state.turn)
    first_turn = ts.first_observed_turn if ts.first_observed_turn is not None else state.turn

    new_ts = ts.model_copy(
        update={
            "discovered": True,
            "observed_turns": observed_turns,
            "first_observed_turn": first_turn,
            "reward_claimed": True,
        }
    )
    new_events = dict(state.transient_events)
    new_events[defn.id] = new_ts

    spec = " [SPECULATIVE]" if defn.speculative else ""
    message = (
        f"Transient event: {defn.name}{spec} — +{rp} RP "
        f"(turn {state.turn}, window {defn.start_turn}–{defn.start_turn + defn.duration_turns - 1})"
    )

    new_state = state.model_copy(
        update={
            "research_points": state.research_points + rp,
            "transient_events": new_events,
        }
    )

    new_state, _ = evaluate_milestones(new_state)

    from universe.game.objectives import evaluate_objectives

    new_state, _ = evaluate_objectives(new_state, scene)

    if state.active_survey_id and target:
        new_state, _ = update_survey_progress_for_discovery(
            new_state,
            object_id=object_id,
            object_type=object_type,
            detected_signals=detected,
            confidence=0.75,
            scene_id=scene.id,
        )

    result = TransientObserveResult(
        event=defn,
        research_points=rp,
        message=message,
        detected_signals=detected,
    )
    return new_state, result, ""


def transient_to_discovery_result(result: TransientObserveResult) -> DiscoveryResult:
    return DiscoveryResult(
        object_id=f"__transient__:{result.event.id}",
        object_type="transient_event",
        detected_signals=result.detected_signals,
        identification_confidence=0.85,
        newly_discovered=True,
        research_points_awarded=result.research_points,
        message=result.message,
    )


def transients_for_export() -> list[dict]:
    return [e.model_dump(mode="json") for e in get_default_transient_events()]


def format_transient_status_lines(
    scene: SceneRegion | None,
    state: ResearchState,
    *,
    scene_id: str | None = None,
    all_scenes: bool = False,
) -> list[str]:
    """CLI/report helper lines."""
    sid = scene_id or (scene.id if scene else None)
    state = update_transient_event_states(state)
    lines: list[str] = []
    catalog = get_default_transient_events()
    if not all_scenes and sid:
        catalog = [d for d in catalog if d.scene_id == sid]

    for defn in catalog:
        if all_scenes and sid and defn.scene_id != sid:
            continue
        ts = state.transient_events.get(defn.id)
        if ts is None:
            continue
        if defn.start_turn > state.turn:
            status = "upcoming"
        elif ts.expired:
            status = "expired" if not ts.discovered else "expired (observed)"
        elif ts.active:
            status = "active"
        else:
            status = "inactive"
        if ts.discovered and ts.active:
            status = "active (observed)"
        spec = " [SPECULATIVE]" if defn.speculative else ""
        req_sig = ", ".join(s.value for s in defn.required_signal_types) or "—"
        lines.append(
            f"- **{defn.name}** (`{defn.id}`){spec} — {status}; "
            f"turns {defn.start_turn}–{defn.start_turn + defn.duration_turns - 1}; "
            f"tier ≥ `{defn.minimum_telescope_tier}`; signals: {req_sig}; +{defn.reward_research_points} RP"
        )
        if scene and status == "active" and not ts.reward_claimed:
            ok, why = is_transient_observable(scene, state, defn.id)
            if not ok:
                lines.append(f"  - _(not observable: {why})_")
    return lines
