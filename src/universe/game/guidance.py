"""Progression hints — steer players from solar tutorial into deep-field play."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from universe.game.models import ResearchState
from universe.game.scenes import (
    ensure_campaign_state,
    generate_scene_command,
    get_scene_definition,
    recommended_next_scene,
    set_active_scene_command,
)
from universe.game.surveys import get_survey_by_id
from universe.models import SceneRegion

SOLAR_OBJECT_TYPES = frozenset(
    {"star", "planet", "moon", "asteroid", "comet", "observatory"}
)
SOLAR_SURVEYABLE_TYPES = frozenset({"star", "planet", "moon", "asteroid", "comet"})


class GuidanceSeverity(str, Enum):
    INFO = "info"
    NUDGE = "nudge"
    WARNING = "warning"


class GuidanceHint(BaseModel):
    id: str
    severity: GuidanceSeverity
    title: str
    message: str
    suggested_action: str = ""
    related_tier_id: str | None = None
    related_survey_id: str | None = None
    related_scene_id: str | None = None


def _is_solar_scene(scene: SceneRegion) -> bool:
    if scene.id == "solar-system":
        return True
    meta = scene.metadata
    return meta is not None and meta.scene_class == "solar_system"


def _solar_surveyable_objects(scene: SceneRegion) -> list:
    return [
        o
        for o in scene.objects
        if o.type.value in SOLAR_SURVEYABLE_TYPES
    ]


def solar_system_mostly_exhausted(
    scene: SceneRegion,
    state: ResearchState,
    *,
    min_confidence: float = 0.5,
    fraction: float = 0.8,
) -> bool:
    """True when most solar survey targets are discovered at ``min_confidence``."""
    if not _is_solar_scene(scene):
        return False
    targets = _solar_surveyable_objects(scene)
    if not targets:
        return False
    done = sum(
        1
        for o in targets
        if (d := state.discoveries.get(o.id)) and d.confidence >= min_confidence
    )
    return done / len(targets) >= fraction


def first_light_survey_complete(state: ResearchState) -> bool:
    prog = state.survey_progress.get("local_sky_survey")
    return prog is not None and prog.completed


def has_speculative_discovery(state: ResearchState) -> bool:
    return any(
        d.object_type == "speculative_anomaly" for d in state.discoveries.values()
    )


def get_guidance_hints(scene: SceneRegion, state: ResearchState) -> list[GuidanceHint]:
    """Return contextual hints for the current scene and research state."""
    state = ensure_campaign_state(state)
    hints: list[GuidanceHint] = []
    solar = _is_solar_scene(scene)
    exhausted = solar and solar_system_mostly_exhausted(scene, state)
    has_space = "space_optical" in state.unlocked_tiers
    has_now = "now_scope" in state.unlocked_tiers
    next_scene = recommended_next_scene(state)
    deep_defn = get_scene_definition("scene-001")
    deep_unlocked = (
        state.campaign.scenes.get("scene-001")
        and state.campaign.scenes["scene-001"].unlocked
    )

    if exhausted and has_space and deep_unlocked and deep_defn:
        deep_survey = get_survey_by_id("deep_field_survey")
        survey_note = (
            f" Start the “{deep_survey.name}” program in the deep-field scene."
            if deep_survey
            else ""
        )
        gen_cmd = generate_scene_command(deep_defn)
        set_cmd = set_active_scene_command("scene-001")
        hints.append(
            GuidanceHint(
                id="solar_exhausted_deep_field_ready",
                severity=GuidanceSeverity.NUDGE,
                title="Ready for deep field",
                message=(
                    f"Local easy targets are mostly catalogued. Your instruments can "
                    f"work in “{deep_defn.name}”. Generate the scene, set it as the "
                    f"active campaign scene, then observe there.{survey_note}"
                ),
                suggested_action=f"{gen_cmd}\n{set_cmd}",
                related_tier_id="space_optical",
                related_survey_id="deep_field_survey",
                related_scene_id="scene-001",
            )
        )

    if next_scene and next_scene.id != state.campaign.active_scene_id:
        hints.append(
            GuidanceHint(
                id="campaign_next_scene",
                severity=GuidanceSeverity.NUDGE,
                title="Next campaign scene",
                message=(
                    f"Recommended: switch to “{next_scene.name}” "
                    f"({next_scene.default_output_path})."
                ),
                suggested_action=set_active_scene_command(next_scene.id),
                related_scene_id=next_scene.id,
            )
        )

    if exhausted and not has_space:
        hints.append(
            GuidanceHint(
                id="solar_exhausted_need_upgrade",
                severity=GuidanceSeverity.NUDGE,
                title="Local sky mostly exhausted",
                message=(
                    "The solar-system tutorial scene has few new discoveries left. "
                    "Unlock improved optics (aim for space_optical) or finish remaining "
                    "surveys and milestones to earn research points."
                ),
                suggested_action="uv run universe game upgrade --tier ground_optical --state <state.json>",
                related_scene_id="solar-system",
            )
        )

    if state.consecutive_no_rp_turns >= 3:
        action = (
            generate_scene_command(deep_defn) + "\n" + set_active_scene_command("scene-001")
            if has_space and solar and deep_defn and deep_unlocked
            else "uv run universe game surveys --state <state.json>"
        )
        hints.append(
            GuidanceHint(
                id="no_observable_targets",
                severity=GuidanceSeverity.WARNING,
                title="No new research this turn",
                message=(
                    f"Recent observations ({state.consecutive_no_rp_turns} turns) yielded "
                    "little or no RP. Switch campaign scene, upgrade your telescope, "
                    "change the active survey, or use limited follow-up observations."
                ),
                suggested_action=action,
            )
        )

    if has_now and not has_speculative_discovery(state):
        hints.append(
            GuidanceHint(
                id="now_scope_needs_speculative_targets",
                severity=GuidanceSeverity.INFO,
                title="Now-Scope (speculative)",
                message=(
                    "The now-scope can resolve the Causality Shadow anomaly in Scene 001. "
                    "This is fictional endgame placeholder content — not a real instrument."
                ),
                suggested_action=set_active_scene_command("scene-001"),
                related_tier_id="now_scope",
                related_scene_id="scene-001",
            )
        )

    return hints
