"""First-run tutorial objectives — guided onboarding, not a quest engine."""

from __future__ import annotations

from typing import NamedTuple

from pydantic import BaseModel, Field

from universe.game.entity import DEFAULT_ENTITY_NAME
from universe.game.models import ObjectiveProgress, ObjectiveStatus, ResearchState
from universe.models import SceneRegion

SOLAR_DISCOVERY_TYPES = frozenset(
    {"star", "planet", "moon", "asteroid", "comet", "observatory"}
)
DEEP_FIELD_DISCOVERY_TYPES = frozenset({"galaxy", "quasar", "lyman_alpha_blob"})
DEEP_FIELD_CONFIDENCE = 0.5


class ObjectiveDefinition(BaseModel):
    id: str
    title: str
    description: str = ""
    tutorial_step: int = 0
    trigger_type: str = ""
    required_scene_id: str | None = None
    required_tier_id: str | None = None
    required_survey_id: str | None = None
    required_milestone_id: str | None = None
    required_transient_event_id: str | None = None
    reward_research_points: int = 0
    next_objective_ids: list[str] = Field(default_factory=list)
    hint: str = ""
    suggested_command: str = ""
    hidden: bool = False


class ObjectiveCompletion(NamedTuple):
    definition: ObjectiveDefinition
    research_points: int


def get_default_objectives() -> list[ObjectiveDefinition]:
    return [
        ObjectiveDefinition(
            id="name_research_entity",
            title="Name Your Research Entity",
            description="Give your institute a proper name and charter.",
            tutorial_step=1,
            trigger_type="entity_named",
            reward_research_points=5,
            next_objective_ids=["observe_local_sky"],
            hint="Use the naming panel in the UI or `universe game init --name \"...\"`.",
            suggested_command=(
                'uv run universe game init --name "Your Institute" '
                "--entity-type private_institute --out data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="observe_local_sky",
            title="Observe the Local Sky",
            description="Make your first discovery in the solar-system scene.",
            tutorial_step=2,
            trigger_type="solar_discovery",
            required_scene_id="solar-system",
            reward_research_points=5,
            next_objective_ids=["complete_first_light_survey"],
            hint="Load the solar-system scene and run Observe or Survey.",
            suggested_command=(
                "uv run universe game observe "
                "--scene data/generated/solar-system/scene.json "
                "--state data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="complete_first_light_survey",
            title="Complete First Light Survey",
            description="Finish the local sky survey program.",
            tutorial_step=3,
            trigger_type="survey_complete",
            required_survey_id="local_sky_survey",
            reward_research_points=10,
            next_objective_ids=["unlock_ground_optical"],
            hint="Start local_sky_survey, then observe solar targets until complete.",
            suggested_command=(
                "uv run universe game start-survey "
                "--survey local_sky_survey --state data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="unlock_ground_optical",
            title="Unlock Ground Optical",
            description="Upgrade to the ground optical telescope tier.",
            tutorial_step=4,
            trigger_type="tier_unlocked",
            required_tier_id="ground_optical",
            reward_research_points=5,
            next_objective_ids=["observe_first_transient"],
            hint="Earn RP from discoveries, then unlock ground_optical in the tech tree.",
            suggested_command=(
                "uv run universe game upgrade "
                "--tier ground_optical --state data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="observe_first_transient",
            title="Observe a Transient Event",
            description="Catch a time-domain event while it is active.",
            tutorial_step=5,
            trigger_type="transient_observed",
            required_scene_id="solar-system",
            reward_research_points=10,
            next_objective_ids=["unlock_space_optical"],
            hint="Check Transients during turns 2–5 for a solar flare in solar-system.",
            suggested_command=(
                "uv run universe game observe-transient "
                "--event solar_flare_001 "
                "--scene data/generated/solar-system/scene.json "
                "--state data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="unlock_space_optical",
            title="Reach Space Optical",
            description="Unlock the space optical telescope tier.",
            tutorial_step=6,
            trigger_type="tier_unlocked",
            required_tier_id="space_optical",
            reward_research_points=10,
            next_objective_ids=["unlock_scene_001"],
            hint="Progress through improved_ground, then unlock space_optical.",
            suggested_command=(
                "uv run universe game upgrade "
                "--tier space_optical --state data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="unlock_scene_001",
            title="Unlock Scene 001",
            description="Unlock the deep-field campaign scene.",
            tutorial_step=7,
            trigger_type="campaign_scene_unlocked",
            required_scene_id="scene-001",
            reward_research_points=10,
            next_objective_ids=["switch_to_scene_001"],
            hint="space_optical unlocks scene-001 in the campaign catalog.",
        ),
        ObjectiveDefinition(
            id="switch_to_scene_001",
            title="Switch to Scene 001",
            description="Set Scene 001 as the active campaign scene.",
            tutorial_step=8,
            trigger_type="campaign_scene_active",
            required_scene_id="scene-001",
            reward_research_points=10,
            next_objective_ids=["start_deep_field_survey"],
            hint="Generate scene-001 if needed, then set it active.",
            suggested_command=(
                "uv run universe game generate-scene --scene scene-001 && "
                "uv run universe game set-scene --scene scene-001 "
                "--state data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="start_deep_field_survey",
            title="Start Deep Field Survey",
            description="Begin or complete the deep field survey program.",
            tutorial_step=9,
            trigger_type="survey_active_or_complete",
            required_survey_id="deep_field_survey",
            reward_research_points=15,
            next_objective_ids=["first_deep_field_discovery"],
            hint="Start deep_field_survey while observing Scene 001.",
            suggested_command=(
                "uv run universe game start-survey "
                "--survey deep_field_survey --state data/generated/game-state.json"
            ),
        ),
        ObjectiveDefinition(
            id="first_deep_field_discovery",
            title="First Deep-Field Discovery",
            description="Detect a galaxy, quasar, or Lyman-alpha blob in the deep field.",
            tutorial_step=10,
            trigger_type="deep_field_discovery",
            required_scene_id="scene-001",
            reward_research_points=25,
            next_objective_ids=[],
            hint="Observe Scene 001 with space_optical (or better) until a deep target registers.",
            suggested_command=(
                "uv run universe game observe "
                "--scene data/generated/scene-001/scene.json "
                "--state data/generated/game-state.json"
            ),
        ),
    ]


def get_objective(objective_id: str) -> ObjectiveDefinition | None:
    for obj in get_default_objectives():
        if obj.id == objective_id:
            return obj
    return None


def _objectives_by_id() -> dict[str, ObjectiveDefinition]:
    return {o.id: o for o in get_default_objectives()}


def _first_objective_id() -> str:
    return get_default_objectives()[0].id


def ensure_objective_progress(state: ResearchState) -> ResearchState:
    """Ensure every catalog objective has progress; bootstrap active chain."""
    by_id = _objectives_by_id()
    progress = dict(state.objectives)
    for oid in by_id:
        if oid not in progress:
            progress[oid] = ObjectiveProgress(objective_id=oid)

    active_ids = list(state.active_objective_ids)
    if not active_ids:
        first = _first_objective_id()
        for oid, prog in progress.items():
            if prog.status == ObjectiveStatus.ACTIVE:
                active_ids.append(oid)
        if not active_ids:
            for oid, prog in progress.items():
                if prog.status == ObjectiveStatus.COMPLETED:
                    continue
                progress[oid] = prog.model_copy(
                    update={"status": ObjectiveStatus.LOCKED}
                )
            progress[first] = progress[first].model_copy(
                update={"status": ObjectiveStatus.ACTIVE}
            )
            active_ids = [first]

    return state.model_copy(
        update={"objectives": progress, "active_objective_ids": active_ids}
    )


def _entity_is_named(state: ResearchState) -> bool:
    name = (state.research_entity.name or "").strip()
    return bool(name) and name != DEFAULT_ENTITY_NAME


def _has_solar_discovery(state: ResearchState) -> bool:
    return any(d.object_type in SOLAR_DISCOVERY_TYPES for d in state.discoveries.values())


def _survey_completed(state: ResearchState, survey_id: str) -> bool:
    prog = state.survey_progress.get(survey_id)
    return prog is not None and prog.completed


def _survey_active_or_complete(state: ResearchState, survey_id: str) -> bool:
    if state.active_survey_id == survey_id:
        return True
    return _survey_completed(state, survey_id)


def _tier_unlocked(state: ResearchState, tier_id: str) -> bool:
    return tier_id in state.unlocked_tiers


def _any_transient_observed(state: ResearchState) -> bool:
    return any(ts.reward_claimed for ts in state.transient_events.values())


def _scene_unlocked(state: ResearchState, scene_id: str) -> bool:
    cs = state.campaign.scenes.get(scene_id)
    return cs is not None and cs.unlocked


def _scene_active(state: ResearchState, scene_id: str) -> bool:
    return state.campaign.active_scene_id == scene_id


def _deep_field_discovery(state: ResearchState) -> bool:
    return any(
        d.object_type in DEEP_FIELD_DISCOVERY_TYPES
        and d.confidence >= DEEP_FIELD_CONFIDENCE
        for d in state.discoveries.values()
    )


def _condition_met(
    defn: ObjectiveDefinition,
    state: ResearchState,
    scene: SceneRegion | None,
) -> bool:
    tt = defn.trigger_type
    if tt == "entity_named":
        return _entity_is_named(state)
    if tt == "solar_discovery":
        return _has_solar_discovery(state)
    if tt == "survey_complete":
        sid = defn.required_survey_id or ""
        return _survey_completed(state, sid)
    if tt == "tier_unlocked":
        tid = defn.required_tier_id or ""
        return _tier_unlocked(state, tid)
    if tt == "transient_observed":
        if defn.required_transient_event_id:
            ts = state.transient_events.get(defn.required_transient_event_id)
            return ts is not None and ts.reward_claimed
        return _any_transient_observed(state)
    if tt == "campaign_scene_unlocked":
        sid = defn.required_scene_id or ""
        return _scene_unlocked(state, sid)
    if tt == "campaign_scene_active":
        sid = defn.required_scene_id or ""
        if _scene_active(state, sid):
            return True
        return scene is not None and scene.id == sid
    if tt == "survey_active_or_complete":
        sid = defn.required_survey_id or ""
        return _survey_active_or_complete(state, sid)
    if tt == "deep_field_discovery":
        return _deep_field_discovery(state)
    if tt == "milestone_achieved":
        mid = defn.required_milestone_id or ""
        rec = state.milestones.get(mid)
        return rec is not None and rec.achieved
    return False


def _predecessors_complete(defn: ObjectiveDefinition, progress: dict[str, ObjectiveProgress]) -> bool:
    """Linear chain: the immediate prior objective must be completed."""
    ordered = sorted(get_default_objectives(), key=lambda o: o.tutorial_step)
    idx = next((i for i, o in enumerate(ordered) if o.id == defn.id), -1)
    if idx <= 0:
        return True
    prev = ordered[idx - 1]
    prog = progress.get(prev.id)
    return prog is not None and prog.status == ObjectiveStatus.COMPLETED


def _can_evaluate(defn: ObjectiveDefinition, progress: dict[str, ObjectiveProgress]) -> bool:
    prog = progress.get(defn.id)
    if prog is None or prog.status == ObjectiveStatus.COMPLETED:
        return False
    if prog.status == ObjectiveStatus.ACTIVE:
        return True
    if prog.status == ObjectiveStatus.LOCKED and _predecessors_complete(defn, progress):
        return True
    return False


def claim_objective_rewards(
    state: ResearchState,
    completed: list[ObjectiveDefinition],
) -> ResearchState:
    """Credit RP for newly completed objectives (once each)."""
    if not completed:
        return state
    progress = dict(state.objectives)
    total_rp = 0
    for defn in completed:
        prog = progress[defn.id]
        if prog.reward_claimed:
            continue
        total_rp += defn.reward_research_points
        progress[defn.id] = prog.model_copy(update={"reward_claimed": True})
    if total_rp == 0:
        return state
    return state.model_copy(
        update={
            "objectives": progress,
            "research_points": state.research_points + total_rp,
        }
    )


def evaluate_objectives(
    state: ResearchState,
    scene: SceneRegion | None = None,
    *,
    recent_results: object = None,
) -> tuple[ResearchState, list[ObjectiveCompletion]]:
    """Evaluate tutorial objectives; catch up out-of-order progress."""
    del recent_results  # reserved for future hooks
    state = ensure_objective_progress(state)
    progress = dict(state.objectives)
    active_ids = list(state.active_objective_ids)
    newly: list[ObjectiveDefinition] = []
    changed = True

    while changed:
        changed = False
        for defn in sorted(get_default_objectives(), key=lambda o: o.tutorial_step):
            if not _can_evaluate(defn, progress):
                continue
            if not _condition_met(defn, state, scene):
                continue
            prog = progress[defn.id]
            progress[defn.id] = prog.model_copy(
                update={
                    "status": ObjectiveStatus.COMPLETED,
                    "completed_turn": state.turn,
                }
            )
            if defn.id in active_ids:
                active_ids.remove(defn.id)
            for nxt in defn.next_objective_ids:
                if nxt in progress and progress[nxt].status == ObjectiveStatus.LOCKED:
                    progress[nxt] = progress[nxt].model_copy(
                        update={"status": ObjectiveStatus.ACTIVE}
                    )
                    if nxt not in active_ids:
                        active_ids.append(nxt)
            newly.append(defn)
            changed = True

    state = state.model_copy(
        update={"objectives": progress, "active_objective_ids": active_ids}
    )
    completions: list[ObjectiveCompletion] = []
    if newly:
        state = claim_objective_rewards(state, newly)
        for defn in newly:
            rp = defn.reward_research_points
            completions.append(ObjectiveCompletion(defn, rp))
    return state, completions


def active_objectives(state: ResearchState) -> list[ObjectiveDefinition]:
    state = ensure_objective_progress(state)
    by_id = _objectives_by_id()
    return [
        by_id[oid]
        for oid in state.active_objective_ids
        if oid in by_id
        and state.objectives[oid].status == ObjectiveStatus.ACTIVE
    ]


def next_objective_hint(state: ResearchState) -> str:
    active = active_objectives(state)
    if not active:
        if _tutorial_chain_complete(state):
            return "Tutorial complete — explore the campaign at your own pace."
        return ""
    obj = active[0]
    parts = [obj.hint] if obj.hint else [obj.description]
    if obj.suggested_command:
        parts.append(f"Try: {obj.suggested_command}")
    return " ".join(p for p in parts if p)


def _tutorial_chain_complete(state: ResearchState) -> bool:
    final = get_objective("first_deep_field_discovery")
    if final is None:
        return False
    prog = state.objectives.get(final.id)
    return prog is not None and prog.status == ObjectiveStatus.COMPLETED


def tutorial_completed_count(state: ResearchState) -> int:
    return sum(
        1
        for p in state.objectives.values()
        if p.status == ObjectiveStatus.COMPLETED
    )


def objectives_for_export() -> list[dict]:
    return [o.model_dump(mode="json") for o in get_default_objectives()]


def format_objective_status_lines(state: ResearchState) -> list[str]:
    state = ensure_objective_progress(state)
    by_id = _objectives_by_id()
    lines: list[str] = []
    active = active_objectives(state)
    if active:
        lines.append("**Active**")
        for obj in active:
            lines.append(f"- {obj.title} (`{obj.id}`) — {obj.hint or obj.description}")
    completed = [
        by_id[oid]
        for oid, prog in state.objectives.items()
        if prog.status == ObjectiveStatus.COMPLETED and oid in by_id
    ]
    if completed:
        lines.append("**Completed**")
        for obj in sorted(completed, key=lambda o: o.tutorial_step):
            lines.append(f"- ✓ {obj.title} (+{obj.reward_research_points} RP)")
    locked = sum(
        1 for p in state.objectives.values() if p.status == ObjectiveStatus.LOCKED
    )
    if locked:
        lines.append(f"_{locked} locked_")
    return lines

