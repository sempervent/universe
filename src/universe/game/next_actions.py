"""Canonical next-action suggestions for manual play and CLI status."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from universe.game.models import ResearchState
from universe.game.scenes import (
    ensure_campaign_state,
    generate_scene_command,
    get_default_scene_catalog,
    recommended_next_scene,
    scene_json_path,
    set_active_scene_command,
)
from universe.models import SceneRegion

DEFAULT_STATE_PATH = "data/generated/game-state.json"

# Lower priority value = shown first.
_PRI_OBJECTIVE = 10
_PRI_SCENE_MISMATCH = 15
_PRI_MISSING_SCENE = 20
_PRI_ACTIVE_TRANSIENT = 25
_PRI_BLOCKED_TRANSIENT = 28
_PRI_SET_SCENE = 35
_PRI_UPGRADE = 40
_PRI_SURVEY = 45
_PRI_GUIDANCE_WARNING = 48
_PRI_GUIDANCE_NUDGE = 50
_PRI_UPCOMING_TRANSIENT = 55
_PRI_GUIDANCE_INFO = 60
_PRI_NO_RP = 70


class NextAction(BaseModel):
    id: str
    priority: int
    title: str
    message: str
    command: str = ""
    scene_id: str | None = None
    survey_id: str | None = None
    tier_id: str | None = None
    objective_id: str | None = None


def get_next_actions(
    state: ResearchState,
    scene: SceneRegion | None = None,
    *,
    max_items: int = 5,
    state_path: str = DEFAULT_STATE_PATH,
) -> list[NextAction]:
    """Merge objectives, guidance, upgrades, transients, campaign, and surveys."""
    from universe.game.guidance import GuidanceSeverity, get_guidance_hints
    from universe.game.objectives import (
        active_objectives,
        ensure_objective_progress,
        evaluate_objectives,
    )
    from universe.game.surveys import available_surveys, get_survey_by_id
    from universe.game.tech_tree import available_upgrades, effective_tier_research_cost
    from universe.game.transients import (
        active_transient_events,
        get_default_transient_events,
        is_transient_observable,
        update_transient_event_states,
    )
    from universe.game.campaign_balance import preferred_survey_id

    state = ensure_campaign_state(ensure_objective_progress(evaluate_objectives(state)[0]))
    actions: list[NextAction] = []
    seen_ids: set[str] = set()

    def add(action: NextAction) -> None:
        if action.id in seen_ids:
            return
        seen_ids.add(action.id)
        actions.append(action)

    # Active tutorial objective
    for obj in active_objectives(state):
        cmd = obj.suggested_command or ""
        add(
            NextAction(
                id=f"objective:{obj.id}",
                priority=_PRI_OBJECTIVE,
                title=obj.title,
                message=obj.hint or obj.description,
                command=cmd,
                objective_id=obj.id,
                scene_id=obj.required_scene_id,
                survey_id=obj.required_survey_id,
                tier_id=obj.required_tier_id,
            )
        )
        break

    active_campaign_id = state.campaign.active_scene_id
    loaded_id = scene.id if scene else None

    if scene and loaded_id and active_campaign_id and loaded_id != active_campaign_id:
        add(
            NextAction(
                id="scene_mismatch",
                priority=_PRI_SCENE_MISMATCH,
                title="Scene mismatch",
                message=(
                    f"Campaign active scene is '{active_campaign_id}' but you are viewing "
                    f"'{loaded_id}'. Set the active scene or export UI for the correct scene.json."
                ),
                command=set_active_scene_command(active_campaign_id, state_path),
                scene_id=active_campaign_id,
            )
        )

    # Unlocked scenes missing scene.json
    for defn in get_default_scene_catalog():
        cs = state.campaign.scenes.get(defn.id)
        if cs is None or not cs.unlocked:
            continue
        path = Path(scene_json_path(defn))
        if path.exists():
            continue
        add(
            NextAction(
                id=f"missing_scene:{defn.id}",
                priority=_PRI_MISSING_SCENE,
                title=f"Generate {defn.name}",
                message=f"Scene file missing at {path}.",
                command=generate_scene_command(defn),
                scene_id=defn.id,
            )
        )

    state = update_transient_event_states(state)
    if scene:
        for defn in active_transient_events(state, scene.id):
            ts = state.transient_events[defn.id]
            if ts.reward_claimed and not defn.repeatable:
                continue
            ok, reason = is_transient_observable(scene, state, defn.id)
            if ok:
                add(
                    NextAction(
                        id=f"transient_observe:{defn.id}",
                        priority=_PRI_ACTIVE_TRANSIENT,
                        title=f"Observe transient: {defn.name}",
                        message=(
                            f"Active now (turns {defn.start_turn}–"
                            f"{defn.start_turn + defn.duration_turns - 1}), "
                            f"+{defn.reward_research_points} RP."
                        ),
                        command=(
                            f"uv run universe game observe-transient "
                            f"--event {defn.id} "
                            f"--scene data/generated/{defn.scene_id}/scene.json "
                            f"--state {state_path} --out {state_path}"
                        ),
                        scene_id=defn.scene_id,
                    )
                )
            elif ts.active and not ts.reward_claimed:
                add(
                    NextAction(
                        id=f"transient_blocked:{defn.id}",
                        priority=_PRI_BLOCKED_TRANSIENT,
                        title=f"Transient blocked: {defn.name}",
                        message=reason or "Requirements not met.",
                        scene_id=defn.scene_id,
                    )
                )

    for defn in get_default_transient_events():
        if defn.start_turn > state.turn:
            if scene and defn.scene_id != scene.id:
                continue
            add(
                NextAction(
                    id=f"transient_upcoming:{defn.id}",
                    priority=_PRI_UPCOMING_TRANSIENT,
                    title=f"Upcoming: {defn.name}",
                    message=(
                        f"Starts turn {defn.start_turn} in scene '{defn.scene_id}' "
                        f"(+{defn.reward_research_points} RP)."
                    ),
                    scene_id=defn.scene_id,
                )
            )

    # Switch campaign scene when unlocked file exists
    nxt = recommended_next_scene(state)
    if nxt and nxt.id != active_campaign_id:
        path = Path(scene_json_path(nxt))
        if path.exists():
            add(
                NextAction(
                    id=f"set_scene:{nxt.id}",
                    priority=_PRI_SET_SCENE,
                    title=f"Switch to {nxt.name}",
                    message=f"Recommended campaign scene ({nxt.id}).",
                    command=set_active_scene_command(nxt.id, state_path),
                    scene_id=nxt.id,
                )
            )

    for tier in available_upgrades(state):
        cost = effective_tier_research_cost(tier, state)
        if state.research_points >= cost:
            add(
                NextAction(
                    id=f"upgrade:{tier.id}",
                    priority=_PRI_UPGRADE,
                    title=f"Unlock {tier.name}",
                    message=f"Costs {cost} RP (you have {state.research_points}).",
                    command=(
                        f"uv run universe game upgrade --tier {tier.id} "
                        f"--state {state_path} --out {state_path}"
                    ),
                    tier_id=tier.id,
                )
            )
            break

    pref_sid = preferred_survey_id(state, active_campaign_id)
    if pref_sid and state.active_survey_id != pref_sid:
        survey = get_survey_by_id(pref_sid)
        if survey and any(s.id == pref_sid for s in available_surveys(state)):
            add(
                NextAction(
                    id=f"survey:{pref_sid}",
                    priority=_PRI_SURVEY,
                    title=f"Start {survey.name}",
                    message="Recommended survey for this campaign scene.",
                    command=(
                        f"uv run universe game start-survey --survey {pref_sid} "
                        f"--state {state_path} --out {state_path}"
                    ),
                    survey_id=pref_sid,
                    scene_id=active_campaign_id,
                )
            )
    elif not state.active_survey_id:
        avail = available_surveys(state)
        if avail:
            s = avail[0]
            add(
                NextAction(
                    id=f"survey:{s.id}",
                    priority=_PRI_SURVEY,
                    title=f"Start {s.name}",
                    message="No active survey — start one to focus discoveries.",
                    command=(
                        f"uv run universe game start-survey --survey {s.id} "
                        f"--state {state_path} --out {state_path}"
                    ),
                    survey_id=s.id,
                )
            )

    if scene:
        for hint in get_guidance_hints(scene, state):
            pri = _PRI_GUIDANCE_INFO
            if hint.severity == GuidanceSeverity.WARNING:
                pri = _PRI_GUIDANCE_WARNING
            elif hint.severity == GuidanceSeverity.NUDGE:
                pri = _PRI_GUIDANCE_NUDGE
            add(
                NextAction(
                    id=f"guidance:{hint.id}",
                    priority=pri,
                    title=hint.title,
                    message=hint.message,
                    command=hint.suggested_action,
                    scene_id=hint.related_scene_id,
                    survey_id=hint.related_survey_id,
                    tier_id=hint.related_tier_id,
                )
            )

    if state.consecutive_no_rp_turns >= 3:
        add(
            NextAction(
                id="no_rp_streak",
                priority=_PRI_NO_RP,
                title="Stuck for RP?",
                message=(
                    f"No meaningful RP for {state.consecutive_no_rp_turns} turns. "
                    "Try a campaign scene switch, upgrade, survey, or transient."
                ),
            )
        )

    actions.sort(key=lambda a: (a.priority, a.id))
    return actions[:max_items]


def format_next_actions_cli(actions: list[NextAction]) -> list[str]:
    lines: list[str] = []
    for i, act in enumerate(actions, start=1):
        lines.append(f"  {i}. {act.title} — {act.message}")
        if act.command:
            lines.append(f"     → {act.command}")
    return lines
