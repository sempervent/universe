"""Campaign scene catalog — multi-scene observation progression."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from universe.game.models import (
    CampaignSceneState,
    CampaignState,
    ResearchState,
    SignalType,
)

DEFAULT_ACTIVE_SCENE_ID = "solar-system"


class ObservationSceneClass(str, Enum):
    SOLAR_SYSTEM = "solar_system"
    DEEP_FIELD = "deep_field"
    SPECULATIVE = "speculative"
    CUSTOM = "custom"


class ObservationSceneDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    scene_class: str = ObservationSceneClass.SOLAR_SYSTEM.value
    generator_name: str = ""
    default_seed: str = ""
    default_output_path: str = ""
    unlock_tier_id: str | None = None
    unlock_milestone_id: str | None = None
    recommended_survey_ids: list[str] = Field(default_factory=list)
    recommended_signal_modes: list[SignalType] = Field(default_factory=list)
    teaching_summary: str = ""
    scale_description: str = ""
    order_index: int = 0
    speculative: bool = False


_CATALOG_CACHE: list[ObservationSceneDefinition] | None = None


def get_default_scene_catalog() -> list[ObservationSceneDefinition]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    _CATALOG_CACHE = [
        ObservationSceneDefinition(
            id="solar-system",
            name="Local Solar System",
            description=(
                "Starter tutorial sky: Sun, Moon, planets, and local surveys. "
                "Teaches naked-eye and ground optical observation."
            ),
            scene_class=ObservationSceneClass.SOLAR_SYSTEM.value,
            generator_name="solar-system",
            default_seed="local-sky",
            default_output_path="data/generated/solar-system",
            unlock_tier_id=None,
            recommended_survey_ids=[
                "local_sky_survey",
                "planetary_census",
                "small_bodies_watch",
            ],
            recommended_signal_modes=[SignalType.VISIBLE_LIGHT],
            teaching_summary=(
                "Local solar system tutorial sky: survey bright planets and moons "
                "before deep-field campaigns."
            ),
            scale_description=(
                "Distances stored as Mpc (AU × conversion); Godot uses a log-radial layout."
            ),
            order_index=0,
        ),
        ObservationSceneDefinition(
            id="scene-001",
            name="The Lyman-alpha Furnace",
            description=(
                "High-redshift protocluster deep field (z ≈ 3.1): galaxies, LAB, "
                "quasars, compact objects, cosmic web, and speculative endgame targets."
            ),
            scene_class=ObservationSceneClass.DEEP_FIELD.value,
            generator_name="scene-001",
            default_seed="lyman-alpha-furnace",
            default_output_path="data/generated/scene-001",
            unlock_tier_id="space_optical",
            unlock_milestone_id="first_deep_field_ready",
            recommended_survey_ids=[
                "deep_field_survey",
                "radio_sky_survey",
                "compact_object_search",
                "cosmic_web_mapping",
                "dark_matter_inference_program",
                "now_scope_first_light",
            ],
            recommended_signal_modes=[
                SignalType.VISIBLE_LIGHT,
                SignalType.RADIO,
                SignalType.XRAY,
                SignalType.WEAK_LENSING,
                SignalType.DARK_MATTER_INFERENCE,
                SignalType.SPECULATIVE_NOW_SIGNAL,
            ],
            teaching_summary=(
                "Deep-field protocluster: use signal modes to stress different physics "
                "(radio jets, X-ray accretion, weak lensing structure)."
            ),
            scale_description=(
                "Comoving positions in Mpc; normalize by scene size_mpc for navigation."
            ),
            order_index=1,
            speculative=False,
        ),
    ]
    return _CATALOG_CACHE


def get_scene_definition(scene_id: str) -> ObservationSceneDefinition | None:
    return next((s for s in get_default_scene_catalog() if s.id == scene_id), None)


def _scene_unlocked(defn: ObservationSceneDefinition, state: ResearchState) -> bool:
    if defn.unlock_tier_id is None and defn.unlock_milestone_id is None:
        return True
    if defn.unlock_tier_id and defn.unlock_tier_id in state.unlocked_tiers:
        return True
    if defn.unlock_milestone_id:
        rec = state.milestones.get(defn.unlock_milestone_id)
        if rec and rec.achieved:
            return True
    return False


def default_campaign_state(state: ResearchState | None = None) -> CampaignState:
    """Build campaign scene entries from the catalog and optional existing progress."""
    scenes: dict[str, CampaignSceneState] = {}
    for defn in get_default_scene_catalog():
        prev = None
        if state and state.campaign.scenes:
            prev = state.campaign.scenes.get(defn.id)
        unlocked = _scene_unlocked(defn, state) if state else (defn.id == DEFAULT_ACTIVE_SCENE_ID)
        if prev:
            unlocked = prev.unlocked or unlocked
        scenes[defn.id] = CampaignSceneState(
            scene_id=defn.id,
            unlocked=unlocked,
            visited=prev.visited if prev else False,
            first_unlocked_turn=prev.first_unlocked_turn if prev else None,
            first_visited_turn=prev.first_visited_turn if prev else None,
            completed=prev.completed if prev else False,
            metadata=dict(prev.metadata) if prev else {},
        )
    active = DEFAULT_ACTIVE_SCENE_ID
    if state and state.campaign.active_scene_id:
        active = state.campaign.active_scene_id
    if active not in scenes or not scenes[active].unlocked:
        active = DEFAULT_ACTIVE_SCENE_ID
    return CampaignState(
        active_scene_id=active,
        scenes=scenes,
        completed_scene_ids=list(state.campaign.completed_scene_ids) if state else [],
    )


def ensure_campaign_state(state: ResearchState) -> ResearchState:
    """Ensure campaign scenes exist and reflect current tier/milestone unlocks."""
    if not state.campaign.scenes:
        base = state.model_copy(update={"campaign": default_campaign_state(state)})
    else:
        base = state
    return update_scene_unlocks(base)[0]


def update_scene_unlocks(state: ResearchState) -> tuple[ResearchState, list[str]]:
    """Refresh unlock flags; return (new_state, newly_unlocked_scene_ids)."""
    campaign = default_campaign_state(state)
    newly: list[str] = []
    new_scenes: dict[str, CampaignSceneState] = {}

    for defn in get_default_scene_catalog():
        prev = campaign.scenes.get(defn.id) or CampaignSceneState(scene_id=defn.id)
        should_unlock = _scene_unlocked(defn, state)
        unlocked = prev.unlocked or should_unlock
        first_unlock_turn = prev.first_unlocked_turn
        if unlocked and not prev.unlocked:
            newly.append(defn.id)
            if first_unlock_turn is None:
                first_unlock_turn = state.turn

        new_scenes[defn.id] = CampaignSceneState(
            scene_id=defn.id,
            unlocked=unlocked,
            visited=prev.visited,
            first_unlocked_turn=first_unlock_turn,
            first_visited_turn=prev.first_visited_turn,
            completed=prev.completed,
            metadata=dict(prev.metadata),
        )

    active = campaign.active_scene_id
    if active not in new_scenes or not new_scenes[active].unlocked:
        active = DEFAULT_ACTIVE_SCENE_ID

    new_campaign = CampaignState(
        active_scene_id=active,
        scenes=new_scenes,
        completed_scene_ids=list(campaign.completed_scene_ids),
    )
    return state.model_copy(update={"campaign": new_campaign}), newly


def available_scenes(state: ResearchState) -> list[ObservationSceneDefinition]:
    state = ensure_campaign_state(state)
    out: list[ObservationSceneDefinition] = []
    for defn in sorted(get_default_scene_catalog(), key=lambda d: d.order_index):
        cs = state.campaign.scenes.get(defn.id)
        if cs and cs.unlocked:
            out.append(defn)
    return out


def recommended_next_scene(state: ResearchState) -> ObservationSceneDefinition | None:
    """Suggest the next campaign scene after the active one, if unlocked and unvisited."""
    state = ensure_campaign_state(state)
    catalog = sorted(get_default_scene_catalog(), key=lambda d: d.order_index)
    active_id = state.campaign.active_scene_id
    active_idx = next((d.order_index for d in catalog if d.id == active_id), -1)

    for defn in catalog:
        if defn.order_index <= active_idx:
            continue
        cs = state.campaign.scenes.get(defn.id)
        if cs and cs.unlocked and not cs.visited:
            return defn
    # If active is solar and deep field unlocked, recommend scene-001 even if "visited" logic differs
    if active_id == "solar-system":
        cs = state.campaign.scenes.get("scene-001")
        if cs and cs.unlocked:
            return get_scene_definition("scene-001")
    return None


def generate_scene_command(defn: ObservationSceneDefinition) -> str:
    return f"uv run universe game generate-scene --scene {defn.id}"


def catalog_generate_command(defn: ObservationSceneDefinition) -> str:
    gen = defn.generator_name or defn.id
    return (
        f"uv run universe generate {gen} --seed {defn.default_seed} "
        f"--out {defn.default_output_path}"
    )


def set_active_scene_command(scene_id: str, state_path: str = "data/generated/game-state.json") -> str:
    return (
        f"uv run universe game set-scene --scene {scene_id} "
        f"--state {state_path} --out {state_path}"
    )


def mark_scene_visited(state: ResearchState, scene_id: str) -> ResearchState:
    state = ensure_campaign_state(state)
    cs = state.campaign.scenes.get(scene_id)
    if cs is None or not cs.unlocked:
        return state
    if cs.visited:
        return state
    new_cs = cs.model_copy(
        update={
            "visited": True,
            "first_visited_turn": state.turn,
        }
    )
    new_scenes = dict(state.campaign.scenes)
    new_scenes[scene_id] = new_cs
    return state.model_copy(
        update={"campaign": state.campaign.model_copy(update={"scenes": new_scenes})}
    )


def set_active_scene(
    state: ResearchState,
    scene_id: str,
    *,
    mark_visited: bool = True,
) -> tuple[ResearchState, str]:
    """Set campaign active scene. Returns (new_state, message). Fails if locked."""
    state, _ = update_scene_unlocks(state)
    defn = get_scene_definition(scene_id)
    if defn is None:
        return state, f"Unknown campaign scene: {scene_id}"

    cs = state.campaign.scenes.get(scene_id)
    if cs is None or not cs.unlocked:
        req = defn.unlock_tier_id or defn.unlock_milestone_id or "none"
        return state, f"Scene '{defn.name}' is locked (requires {req})."

    prev_active = state.campaign.active_scene_id
    new_campaign = state.campaign.model_copy(update={"active_scene_id": scene_id})
    new_state = state.model_copy(update={"campaign": new_campaign})
    if mark_visited:
        new_state = mark_scene_visited(new_state, scene_id)

    if prev_active == scene_id:
        return new_state, f"Active scene already set to '{defn.name}'."
    return new_state, f"Active campaign scene: {defn.name} ({scene_id})."


def scene_json_path(defn: ObservationSceneDefinition) -> str:
    return f"{defn.default_output_path}/scene.json"


def _unlock_requirement_text(defn: ObservationSceneDefinition) -> str:
    parts: list[str] = []
    if defn.unlock_tier_id:
        parts.append(f"tier {defn.unlock_tier_id}")
    if defn.unlock_milestone_id:
        parts.append(f"milestone {defn.unlock_milestone_id}")
    return " or ".join(parts) if parts else "none (starter scene)"


def catalog_for_export() -> list[dict[str, Any]]:
    """JSON-serializable scene definitions for HTML/Godot exports."""
    out: list[dict[str, Any]] = []
    for defn in get_default_scene_catalog():
        d = defn.model_dump(mode="json")
        d["recommended_signal_modes"] = [s.value for s in defn.recommended_signal_modes]
        d["generate_command"] = generate_scene_command(defn)
        d["legacy_generate_command"] = catalog_generate_command(defn)
        d["scene_json_path"] = scene_json_path(defn)
        d["unlock_requirement"] = _unlock_requirement_text(defn)
        out.append(d)
    return out


def campaign_catalog_bundle(
    state: ResearchState | None = None,
    *,
    state_path: str = "data/generated/game-state.json",
) -> dict[str, Any]:
    """Campaign catalog + recommendations for static UI exports."""
    scenes = catalog_for_export()
    rec_id: str | None = None
    rec_gen: str | None = None
    rec_set: str | None = None
    if state is not None:
        state = ensure_campaign_state(state)
        rec = recommended_next_scene(state)
        if rec:
            rec_id = rec.id
            rec_gen = generate_scene_command(rec)
            rec_set = set_active_scene_command(rec.id, state_path)
    return {
        "scenes": scenes,
        "recommended_next_scene_id": rec_id,
        "recommended_generate_command": rec_gen,
        "recommended_set_scene_command": rec_set,
    }
