"""Discovery rules — evaluate scene objects against player capabilities.

The discovery engine does not modify scene data.  It reads a SceneRegion
and a ResearchState and returns DiscoveryResults describing what the
player can detect, at what confidence, and what research points to award.
"""

from __future__ import annotations

from universe.game.entity import get_entity_modifier
from universe.game.models import (
    DiscoveryRecord,
    DiscoveryRequirement,
    DiscoveryResult,
    ResearchState,
    SignalType,
)
from universe.game.tech_tree import (
    all_signal_types_for_state,
    best_resolution_for_state,
    best_sensitivity_for_state,
    max_distance_for_state,
)
from universe.models import CosmicObject, SceneRegion


# ---------------------------------------------------------------------------
# Discovery requirements per object type
# ---------------------------------------------------------------------------


def get_discovery_requirements() -> list[DiscoveryRequirement]:
    S = SignalType
    return [
        # Solar system
        DiscoveryRequirement(
            object_type="star",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED, S.ULTRAVIOLET, S.RADIO],
            minimum_telescope_tier=0,
            minimum_sensitivity=0.01,
            base_research_points=2,
            notes="The Sun and bright stars are visible to the naked eye.",
        ),
        DiscoveryRequirement(
            object_type="planet",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED],
            minimum_telescope_tier=0,
            minimum_sensitivity=0.03,
            minimum_resolution_arcsec=60.0,
            base_research_points=3,
            notes="Bright planets visible naked-eye; disk detail needs telescope.",
        ),
        DiscoveryRequirement(
            object_type="moon",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED],
            minimum_telescope_tier=0,
            minimum_sensitivity=0.02,
            base_research_points=2,
            notes="Earth's Moon is obvious; other moons need optical telescope.",
        ),
        DiscoveryRequirement(
            object_type="asteroid",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED],
            minimum_telescope_tier=2,
            minimum_sensitivity=0.2,
            minimum_resolution_arcsec=2.0,
            base_research_points=5,
            notes="Requires improved optics to distinguish from stars.",
        ),
        DiscoveryRequirement(
            object_type="comet",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED, S.ULTRAVIOLET],
            minimum_telescope_tier=1,
            minimum_sensitivity=0.1,
            base_research_points=5,
            notes="Bright comets visible naked-eye; faint ones need telescope.",
        ),
        DiscoveryRequirement(
            object_type="observatory",
            required_signal_types=[S.VISIBLE_LIGHT],
            minimum_telescope_tier=0,
            minimum_sensitivity=0.0,
            base_research_points=0,
            notes="The observer's own location. Always known.",
        ),
        # Deep sky
        DiscoveryRequirement(
            object_type="galaxy",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED, S.ULTRAVIOLET, S.RADIO],
            minimum_telescope_tier=2,
            minimum_sensitivity=0.2,
            minimum_resolution_arcsec=2.0,
            base_research_points=10,
            notes="Faint galaxies need improved ground or space optics.",
        ),
        DiscoveryRequirement(
            object_type="lyman_alpha_blob",
            required_signal_types=[S.ULTRAVIOLET, S.VISIBLE_LIGHT],
            optional_signal_types=[S.INFRARED, S.RADIO, S.XRAY],
            minimum_telescope_tier=3,
            minimum_sensitivity=0.4,
            minimum_resolution_arcsec=1.0,
            base_research_points=30,
            notes="Requires UV/deep optical; high-z LABs need space telescope.",
        ),
        DiscoveryRequirement(
            object_type="quasar",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.RADIO, S.XRAY, S.INFRARED, S.ULTRAVIOLET],
            minimum_telescope_tier=3,
            minimum_sensitivity=0.35,
            minimum_resolution_arcsec=1.0,
            base_research_points=20,
            notes="Point-like at optical; radio/xray improve classification.",
        ),
        DiscoveryRequirement(
            object_type="black_hole",
            required_signal_types=[S.XRAY],
            optional_signal_types=[
                S.GRAVITATIONAL_WAVE, S.RADIO, S.VISIBLE_LIGHT,
                S.WEAK_LENSING, S.GAMMA_RAY,
            ],
            minimum_telescope_tier=5,
            minimum_sensitivity=0.4,
            minimum_resolution_arcsec=1.0,
            base_research_points=25,
            notes="Indirect detection via accretion X-rays; multi-messenger confirms.",
        ),
        DiscoveryRequirement(
            object_type="magnetar",
            required_signal_types=[S.XRAY],
            optional_signal_types=[S.GAMMA_RAY, S.RADIO],
            minimum_telescope_tier=5,
            minimum_sensitivity=0.45,
            base_research_points=25,
            notes="Detected via X-ray/gamma bursts; radio pulsations add confidence.",
        ),
        DiscoveryRequirement(
            object_type="cosmic_web_node",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.WEAK_LENSING, S.DARK_MATTER_INFERENCE, S.RADIO],
            minimum_telescope_tier=3,
            minimum_sensitivity=0.4,
            base_research_points=15,
            notes="Galaxy overdensity mapping; weak lensing confirms mass.",
        ),
        DiscoveryRequirement(
            object_type="cosmic_web_filament",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.WEAK_LENSING, S.DARK_MATTER_INFERENCE, S.RADIO],
            minimum_telescope_tier=3,
            minimum_sensitivity=0.45,
            base_research_points=35,
            notes="Requires galaxy survey + statistical methods or weak lensing.",
        ),
        DiscoveryRequirement(
            object_type="void",
            required_signal_types=[S.VISIBLE_LIGHT],
            optional_signal_types=[S.WEAK_LENSING, S.RADIO],
            minimum_telescope_tier=3,
            minimum_sensitivity=0.4,
            base_research_points=15,
            notes="Detected as absence of galaxies in survey data.",
        ),
        DiscoveryRequirement(
            object_type="cmb_background",
            required_signal_types=[S.MICROWAVE],
            optional_signal_types=[S.RADIO],
            minimum_telescope_tier=4,
            minimum_sensitivity=0.4,
            base_research_points=20,
            notes="Requires microwave/radio receiver capability.",
        ),
        DiscoveryRequirement(
            object_type="speculative_anomaly",
            required_signal_types=[S.SPECULATIVE_NOW_SIGNAL],
            minimum_telescope_tier=11,
            minimum_sensitivity=0.9,
            minimum_resolution_arcsec=0.01,
            base_research_points=50,
            notes=(
                "Fictional now-scope target — causality-independent placeholder. "
                "Not a real astrophysical object."
            ),
            speculative=True,
        ),
    ]


_REQ_MAP: dict[str, DiscoveryRequirement] | None = None


def _requirements_map() -> dict[str, DiscoveryRequirement]:
    global _REQ_MAP
    if _REQ_MAP is None:
        _REQ_MAP = {r.object_type: r for r in get_discovery_requirements()}
    return _REQ_MAP


# ---------------------------------------------------------------------------
# Confidence calculation
# ---------------------------------------------------------------------------


def _confidence_label(c: float) -> str:
    if c < 0.25:
        return "not detected"
    if c < 0.50:
        return "signal anomaly"
    if c < 0.75:
        return "candidate"
    if c < 0.95:
        return "confirmed"
    return "characterized"


def calculate_identification_confidence(
    obj: CosmicObject,
    state: ResearchState,
) -> tuple[float, list[str]]:
    """Return (confidence, detected_signal_names) for an object given player state."""
    req = _requirements_map().get(obj.type.value)
    if req is None:
        return 0.0, []

    available_signals = all_signal_types_for_state(state)
    sensitivity = best_sensitivity_for_state(state)
    resolution = best_resolution_for_state(state)
    max_dist = max_distance_for_state(state)

    # Check minimum sensitivity
    if sensitivity < req.minimum_sensitivity:
        return 0.0, []

    # Check resolution
    if resolution > req.minimum_resolution_arcsec:
        return 0.0, []

    # Check distance (use object's position as rough distance from origin)
    obj_dist = (
        obj.position_mpc.x**2 + obj.position_mpc.y**2 + obj.position_mpc.z**2
    ) ** 0.5
    if obj_dist > max_dist and obj_dist > 0.0001:
        return 0.0, []

    # Signal coverage
    required = {s.value for s in req.required_signal_types}
    optional = {s.value for s in req.optional_signal_types}
    detected_required = required & available_signals
    detected_optional = optional & available_signals
    all_detected = sorted(detected_required | detected_optional)

    if not required:
        signal_coverage = 1.0
    else:
        signal_coverage = len(detected_required) / len(required)

    # Base confidence from signal coverage, sensitivity, resolution factors
    sens_factor = min(1.0, sensitivity / max(req.minimum_sensitivity, 0.01))
    res_factor = min(1.0, req.minimum_resolution_arcsec / max(resolution, 0.00001))
    base = signal_coverage * min(sens_factor, 1.0) * min(res_factor, 1.0)

    # Multi-messenger bonus: each optional signal type detected adds confidence
    mm_bonus = 0.08 * len(detected_optional)

    confidence = min(1.0, base + mm_bonus)

    # Distance penalty for objects far away relative to instrument range
    if max_dist > 0 and obj_dist > 0.0001:
        dist_ratio = obj_dist / max_dist
        if dist_ratio > 0.5:
            confidence *= max(0.3, 1.0 - (dist_ratio - 0.5))

    confidence = round(confidence, 4)
    # Entity modifier: confidence bonus only if already detectable (no "magic" detections).
    if confidence > 0:
        mod = get_entity_modifier(state.research_entity.entity_type)
        confidence = min(1.0, round(confidence + mod.confidence_bonus, 4))

    return confidence, all_detected


# ---------------------------------------------------------------------------
# Research points
# ---------------------------------------------------------------------------

_FIRST_TYPE_BONUS: set[str] = set()


def _award_points(
    obj: CosmicObject,
    confidence: float,
    newly_discovered: bool,
    confidence_upgraded: bool,
    state: ResearchState,
) -> int:
    req = _requirements_map().get(obj.type.value)
    base = req.base_research_points if req else 5

    if confidence < 0.25:
        return 0

    points = int(base * confidence)

    if newly_discovered:
        previously_seen_types = {
            d.object_type for d in state.discoveries.values()
        }
        if obj.type.value not in previously_seen_types:
            points = int(points * 1.5)

    if confidence_upgraded and not newly_discovered:
        points = max(1, points // 2)

    if points > 0:
        mod = get_entity_modifier(state.research_entity.entity_type)
        points = max(1, int(round(points * mod.discovery_rp_multiplier)))

    return max(1, points) if confidence >= 0.25 else 0


# ---------------------------------------------------------------------------
# Follow-up observations (diminishing returns)
# ---------------------------------------------------------------------------

MAX_FOLLOWUPS_PER_OBJECT = 2
_FOLLOWUP_CHARACTERIZED = 0.95
_FOLLOWUP_MIN_CONFIDENCE = 0.5

_SOLAR_TYPES = frozenset({"star", "planet", "moon", "asteroid", "comet"})
_DEEP_FOLLOWUP_RP: dict[str, int] = {
    "galaxy": 3,
    "quasar": 4,
    "lyman_alpha_blob": 5,
    "black_hole": 4,
    "magnetar": 4,
    "cosmic_web_node": 3,
    "cosmic_web_filament": 4,
    "void": 2,
    "cmb_background": 2,
    "speculative_anomaly": 5,
}


def _followup_base_rp(object_type: str) -> int:
    if object_type in _SOLAR_TYPES:
        return 1
    return _DEEP_FOLLOWUP_RP.get(object_type, 3)


def apply_followup_observations(
    scene: SceneRegion,
    state: ResearchState,
    primary_results: list[DiscoveryResult],
) -> tuple[list[DiscoveryResult], int, dict[str, int], dict[str, str]]:
    """Award small RP for re-observing known objects when primary pass is quiet.

    Returns follow-up results, total RP, and updated count/tier maps.
    """
    primary_ids = {
        r.object_id
        for r in primary_results
        if r.object_id and not r.object_id.startswith("__")
    }
    followup_counts = dict(state.followup_observation_counts)
    last_tiers = dict(state.last_observation_tier_by_object)
    active_tier = state.active_telescope_tier
    mod = get_entity_modifier(state.research_entity.entity_type)

    out: list[DiscoveryResult] = []
    total_rp = 0

    for obj in scene.objects:
        if obj.id in primary_ids:
            last_tiers[obj.id] = active_tier
            continue

        prev = state.discoveries.get(obj.id)
        if prev is None or prev.confidence < _FOLLOWUP_MIN_CONFIDENCE:
            continue

        count = followup_counts.get(obj.id, 0)
        tier_changed = last_tiers.get(obj.id) != active_tier
        if prev.confidence >= _FOLLOWUP_CHARACTERIZED and not tier_changed:
            continue
        if count >= MAX_FOLLOWUPS_PER_OBJECT and not tier_changed:
            continue

        base = _followup_base_rp(obj.type.value)
        rp = max(1, min(5, int(round(base * mod.discovery_rp_multiplier))))
        followup_counts[obj.id] = count + 1
        last_tiers[obj.id] = active_tier
        total_rp += rp
        out.append(
            DiscoveryResult(
                object_id=obj.id,
                object_type=obj.type.value,
                identification_confidence=prev.confidence,
                newly_discovered=False,
                confidence_upgraded=False,
                research_points_awarded=rp,
                message=(
                    f"Follow-up: {obj.name} ({obj.type.value}) — +{rp} RP "
                    f"(diminishing returns, {followup_counts[obj.id]}/{MAX_FOLLOWUPS_PER_OBJECT})"
                ),
            )
        )

    return out, total_rp, followup_counts, last_tiers


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def observable_objects(scene: SceneRegion, state: ResearchState) -> list[DiscoveryResult]:
    """Evaluate all objects in a scene and return discovery results."""
    results: list[DiscoveryResult] = []

    for obj in scene.objects:
        confidence, detected = calculate_identification_confidence(obj, state)
        if confidence < 0.01:
            continue

        prev = state.discoveries.get(obj.id)
        newly_discovered = prev is None
        confidence_upgraded = (
            prev is not None and confidence > prev.confidence + 0.05
        )

        if not newly_discovered and not confidence_upgraded:
            continue

        points = _award_points(obj, confidence, newly_discovered, confidence_upgraded, state)
        label = _confidence_label(confidence)

        msg = f"{label}: {obj.name} ({obj.type.value})"
        if newly_discovered:
            msg += " [NEW]"
        elif confidence_upgraded:
            msg += " [UPGRADED]"
        msg += f" — confidence {confidence:.0%}, +{points} RP"

        results.append(
            DiscoveryResult(
                object_id=obj.id,
                object_type=obj.type.value,
                detected_signals=detected,
                identification_confidence=confidence,
                newly_discovered=newly_discovered,
                confidence_upgraded=confidence_upgraded,
                research_points_awarded=points,
                message=msg,
            )
        )

    results.sort(key=lambda r: (-r.identification_confidence, r.object_id))
    return results


def observe_scene(
    scene: SceneRegion,
    state: ResearchState,
) -> tuple[ResearchState, list[DiscoveryResult]]:
    """Run a full observation pass.  Returns (new_state, results).

    The input state is not mutated.  This function also advances the turn
    counter, updates the active survey's progress, and evaluates milestones,
    auto-claiming any newly-achieved rewards.
    """
    # Local import to avoid an import cycle (surveys/milestones reference state).
    from universe.game.milestones import evaluate_milestones
    from universe.game.scenes import ensure_campaign_state, mark_scene_visited, update_scene_unlocks
    from universe.game.surveys import update_survey_progress_for_discovery

    state = ensure_campaign_state(state)
    primary_results = observable_objects(scene, state)
    followup_results, _, followup_counts, last_tiers = apply_followup_observations(
        scene, state, primary_results
    )
    results = primary_results + followup_results

    new_discoveries = dict(state.discoveries)
    total_rp = 0

    for r in primary_results:
        if not r.object_id or r.object_id.startswith("__"):
            continue
        total_rp += r.research_points_awarded
        prev = new_discoveries.get(r.object_id)
        if prev is None or r.identification_confidence > prev.confidence:
            new_discoveries[r.object_id] = DiscoveryRecord(
                object_id=r.object_id,
                object_type=r.object_type,
                confidence=r.identification_confidence,
                detected_signals=r.detected_signals,
                research_points_earned=(
                    (prev.research_points_earned if prev else 0)
                    + r.research_points_awarded
                ),
                first_detected_tier=state.active_telescope_tier,
            )

    for r in followup_results:
        total_rp += r.research_points_awarded
        prev = new_discoveries.get(r.object_id)
        if prev is not None:
            new_discoveries[r.object_id] = prev.model_copy(
                update={
                    "research_points_earned": prev.research_points_earned
                    + r.research_points_awarded,
                }
            )

    consecutive = 0 if total_rp > 0 else state.consecutive_no_rp_turns + 1

    new_state = state.model_copy(
        update={
            "research_points": state.research_points + total_rp,
            "discoveries": new_discoveries,
            "turn": state.turn + 1,
            "followup_observation_counts": followup_counts,
            "last_observation_tier_by_object": last_tiers,
            "consecutive_no_rp_turns": consecutive,
        }
    )

    # Apply survey progress for each fresh / upgraded discovery.
    survey_messages: list[str] = []
    for r in results:
        new_state, msgs = update_survey_progress_for_discovery(
            new_state,
            object_id=r.object_id,
            object_type=r.object_type,
            detected_signals=r.detected_signals,
            confidence=r.identification_confidence,
            scene_id=scene.id,
        )
        survey_messages.extend(msgs)

    # Evaluate milestones (auto-claim rewards).
    new_state, achieved = evaluate_milestones(new_state)

    new_state, newly_unlocked_scenes = update_scene_unlocks(new_state)
    if scene.id == new_state.campaign.active_scene_id:
        new_state = mark_scene_visited(new_state, scene.id)

    # Append milestone / survey progression messages as info-level results.
    for msg in survey_messages:
        results.append(
            DiscoveryResult(
                object_id="__survey__",
                object_type="survey_event",
                identification_confidence=0.0,
                research_points_awarded=0,
                message=msg,
            )
        )
    for award in achieved:
        m = award.milestone
        spec = " [SPECULATIVE]" if m.speculative else ""
        results.append(
            DiscoveryResult(
                object_id="__milestone__",
                object_type="milestone_event",
                identification_confidence=0.0,
                research_points_awarded=award.research_points,
                message=(
                    f"Milestone: {m.name}{spec} — +{award.research_points} RP"
                ),
            )
        )

    from universe.game.scenes import get_scene_definition

    for sid in newly_unlocked_scenes:
        defn = get_scene_definition(sid)
        label = defn.name if defn else sid
        results.append(
            DiscoveryResult(
                object_id="__campaign__",
                object_type="campaign_event",
                identification_confidence=0.0,
                research_points_awarded=0,
                message=f"Campaign: unlocked observation scene '{label}' ({sid}).",
            )
        )

    return new_state, results
