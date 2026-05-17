"""Per-scene observation RP caps — discoveries still register; funding is bounded."""

from __future__ import annotations

from pydantic import BaseModel

from universe.game.models import DiscoveryResult


class ObservationRewardBudget(BaseModel):
    """RP cap for primary discovery awards in one observe pass."""

    per_turn_discovery_rp_cap: int
    scene_id: str | None = None


# Per-scene caps (one `observe_scene` primary-discovery pass).
DISCOVERY_RP_CAP_BY_SCENE: dict[str, int] = {
    "solar-system": 70,
    "scene-001": 250,
    "radio-cmb-survey": 150,
    "stellar-remnant-field": 150,
    "cosmic-web-map": 250,
    "now-scope-anomaly-field": 400,
}

DEFAULT_DISCOVERY_RP_CAP = 200


def discovery_rp_cap_for_scene(scene_id: str) -> int:
    return DISCOVERY_RP_CAP_BY_SCENE.get(scene_id, DEFAULT_DISCOVERY_RP_CAP)


def _priority_key(result: DiscoveryResult) -> tuple:
    exotic = result.object_type in (
        "lyman_alpha_blob",
        "quasar",
        "speculative_anomaly",
        "black_hole",
        "magnetar",
        "cmb_background",
    )
    return (
        0 if result.newly_discovered else 1,
        0 if exotic else 1,
        -result.identification_confidence,
        -result.research_points_awarded,
        result.object_id or "",
    )


def apply_discovery_rp_cap(
    primary_results: list[DiscoveryResult],
    scene_id: str,
) -> tuple[list[DiscoveryResult], dict[str, int | bool]]:
    """Cap primary discovery RP; update messages. Returns (results, cap_telemetry)."""
    cap = discovery_rp_cap_for_scene(scene_id)
    uncapped = sum(r.research_points_awarded for r in primary_results)
    telemetry: dict[str, int | bool] = {
        "reward_cap_applied": False,
        "uncapped_rp": uncapped,
        "capped_rp": uncapped,
        "cap_value": cap,
    }
    if uncapped <= cap or not primary_results:
        return primary_results, telemetry

    telemetry["reward_cap_applied"] = True
    order = sorted(range(len(primary_results)), key=lambda i: _priority_key(primary_results[i]))
    remaining = cap
    new_results: list[DiscoveryResult] = []
    for i, r in enumerate(primary_results):
        new_results.append(r.model_copy())

    for idx in order:
        r = new_results[idx]
        award = min(r.research_points_awarded, max(0, remaining))
        remaining -= award
        if award != r.research_points_awarded:
            msg = r.message
            if "— +" in msg:
                prefix = msg.rsplit("— +", 1)[0]
                msg = f"{prefix}— +{award} RP (capped)"
            else:
                msg = f"{msg} (+{award} RP, capped)"
            new_results[idx] = r.model_copy(
                update={
                    "research_points_awarded": award,
                    "message": msg,
                }
            )

    telemetry["capped_rp"] = sum(r.research_points_awarded for r in new_results)
    return new_results, telemetry
