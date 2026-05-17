"""Campaign ladder balance checks and scene-progression helpers."""

from __future__ import annotations

import re
from typing import Any

from universe.game.discovery import (
    calculate_identification_confidence,
    get_discovery_requirements,
)
from universe.game.models import ResearchState
from universe.game.scenes import get_default_scene_catalog, get_scene_definition
from universe.game.surveys import get_default_survey_programs, get_survey_by_id
from universe.game.tech_tree import get_tier_by_id
from universe.models import CosmicObject, SceneRegion
from universe.procedural.registry import generate_scene_by_id


# Max turns autoplay spends in a scene before advancing (campaign_ordered).
SCENE_MAX_TURNS: dict[str, int] = {
    "solar-system": 8,
    "scene-001": 12,
    "radio-cmb-survey": 12,
    "stellar-remnant-field": 12,
    "cosmic-web-map": 35,
    "now-scope-anomaly-field": 10,
}

SCENE_MIN_TURNS: dict[str, int] = {
    "solar-system": 2,
    "scene-001": 4,
    "radio-cmb-survey": 3,
    "stellar-remnant-field": 3,
    "cosmic-web-map": 5,
    "now-scope-anomaly-field": 2,
}


def scene_max_turns(scene_id: str) -> int:
    return SCENE_MAX_TURNS.get(scene_id, 15)


def scene_min_turns(scene_id: str) -> int:
    return SCENE_MIN_TURNS.get(scene_id, 2)


def empty_scene_metric() -> dict[str, Any]:
    return {
        "unlock_turn": None,
        "first_visit_turn": None,
        "first_discovery_turn": None,
        "first_confirmed_discovery_turn": None,
        "total_discoveries": 0,
        "total_rp_earned": 0,
        "surveys_completed": [],
        "milestones_achieved": [],
        "turns_spent_active": 0,
        "no_rp_turns_while_active": 0,
        "signal_mode_detections": 0,
        "surveys_started": [],
    }


class SceneMetricsTracker:
    """Accumulates per-scene playtest metrics during autoplay."""

    def __init__(self, scene_ids: list[str] | None = None) -> None:
        ids = scene_ids or [d.id for d in get_default_scene_catalog()]
        self.metrics: dict[str, dict[str, Any]] = {
            sid: empty_scene_metric() for sid in ids
        }
        self.visit_sequence: list[str] = []
        self.tier_unlock_context: dict[str, dict[str, Any]] = {}

    def sync_campaign_state(
        self,
        state: ResearchState,
        scene_unlock_turns: dict[str, int],
    ) -> None:
        for sid, turn in scene_unlock_turns.items():
            if sid in self.metrics:
                self.metrics[sid]["unlock_turn"] = turn
        for sid, cs in state.campaign.scenes.items():
            if sid not in self.metrics:
                continue
            if cs.first_unlocked_turn is not None:
                self.metrics[sid]["unlock_turn"] = cs.first_unlocked_turn
            if cs.first_visited_turn is not None:
                self.metrics[sid]["first_visit_turn"] = cs.first_visited_turn

    def record_visit(self, scene_id: str, turn: int) -> None:
        if scene_id not in self.metrics:
            return
        if self.metrics[scene_id]["first_visit_turn"] is None:
            self.metrics[scene_id]["first_visit_turn"] = turn
        if scene_id not in self.visit_sequence:
            self.visit_sequence.append(scene_id)

    def record_turn(
        self,
        state: ResearchState,
        *,
        rp_before: int,
        rp_after: int,
        active_scene_id: str,
    ) -> None:
        if active_scene_id not in self.metrics:
            return
        m = self.metrics[active_scene_id]
        m["turns_spent_active"] = int(m["turns_spent_active"]) + 1
        if rp_after == rp_before:
            m["no_rp_turns_while_active"] = int(m["no_rp_turns_while_active"]) + 1

    def record_tier_unlock(
        self,
        tier_id: str,
        turn: int,
        active_scene_id: str,
        cost: int,
    ) -> None:
        if tier_id not in self.tier_unlock_context:
            self.tier_unlock_context[tier_id] = {
                "turn": turn,
                "active_scene_id": active_scene_id,
                "rp_cost": cost,
            }

    def record_discovery_event(
        self,
        *,
        active_scene_id: str,
        turn: int,
        confidence: float,
        delta_rp: int,
        detected_signals: list[str] | None = None,
    ) -> None:
        if active_scene_id not in self.metrics:
            return
        m = self.metrics[active_scene_id]
        if m["first_discovery_turn"] is None and confidence >= 0.25:
            m["first_discovery_turn"] = turn
        if m["first_confirmed_discovery_turn"] is None and confidence >= 0.5:
            m["first_confirmed_discovery_turn"] = turn
        if confidence >= 0.25:
            m["total_discoveries"] = int(m["total_discoveries"]) + 1
        if delta_rp > 0:
            m["total_rp_earned"] = int(m["total_rp_earned"]) + delta_rp
        if detected_signals:
            m["signal_mode_detections"] = int(m["signal_mode_detections"]) + 1

    def record_survey_started(self, active_scene_id: str, survey_id: str) -> None:
        if active_scene_id not in self.metrics:
            return
        started: list[str] = self.metrics[active_scene_id]["surveys_started"]
        if survey_id not in started:
            started.append(survey_id)

    def record_survey_complete(self, active_scene_id: str, survey_id: str) -> None:
        if active_scene_id not in self.metrics:
            return
        completed: list[str] = self.metrics[active_scene_id]["surveys_completed"]
        if survey_id not in completed:
            completed.append(survey_id)

    def record_milestone(self, active_scene_id: str, milestone_id: str) -> None:
        if active_scene_id not in self.metrics:
            return
        achieved: list[str] = self.metrics[active_scene_id]["milestones_achieved"]
        if milestone_id not in achieved:
            achieved.append(milestone_id)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "scene_metrics": {k: dict(v) for k, v in self.metrics.items()},
            "scene_visit_sequence": list(self.visit_sequence),
            "tier_unlock_context": dict(self.tier_unlock_context),
        }


def scene_for_playtest(scene_id: str, seed: str) -> SceneRegion:
    return generate_scene_by_id(scene_id, seed=seed)


def _objects_by_type(scene: SceneRegion) -> dict[str, list[CosmicObject]]:
    out: dict[str, list[CosmicObject]] = {}
    for obj in scene.objects:
        out.setdefault(obj.type.value, []).append(obj)
    return out


def max_confidence_at_tier(
    state: ResearchState,
    obj: CosmicObject,
    tier_id: str,
) -> float:
    """Confidence for *obj* if only *tier_id* (and prerequisites) are unlocked."""
    from universe.game.tech_tree import get_default_tech_tree

    tier = get_tier_by_id(tier_id)
    if tier is None:
        return 0.0
    allowed: list[str] = []
    for t in get_default_tech_tree():
        if t.tier_index <= tier.tier_index:
            allowed.append(t.id)
    signals: set[str] = set()
    for tid in allowed:
        t = get_tier_by_id(tid)
        if t:
            signals.update(s.value for s in t.signal_types)
    stub = state.model_copy(
        update={
            "unlocked_tiers": allowed,
            "active_telescope_tier": tier_id,
            "known_signal_types": sorted(signals),
        }
    )
    conf, _ = calculate_identification_confidence(obj, stub)
    return conf


def scene_has_detectable_at_unlock_tier(
    scene: SceneRegion,
    unlock_tier_id: str | None,
    state: ResearchState | None = None,
) -> bool:
    if unlock_tier_id is None:
        return len(scene.objects) > 0
    base = state or ResearchState()
    for obj in scene.objects:
        if max_confidence_at_tier(base, obj, unlock_tier_id) >= 0.25:
            return True
    return False


def scene_benefits_from_recommended_signals(
    scene: SceneRegion,
    recommended_modes: list[str],
    state: ResearchState | None = None,
) -> bool:
    if not recommended_modes:
        return True
    rec = set(recommended_modes)
    req_by_type = {r.object_type: r for r in get_discovery_requirements()}
    types_in_scene = {obj.type.value for obj in scene.objects}

    for obj in scene.objects:
        props = obj.properties or {}
        req_sigs = props.get("required_signal_types") or []
        if rec & {str(s) for s in req_sigs}:
            return True

    for otype in types_in_scene:
        req = req_by_type.get(otype)
        if req is None:
            continue
        required = {s.value for s in req.required_signal_types}
        optional = {s.value for s in req.optional_signal_types}
        if rec & required or rec & optional:
            return True

    base = state or ResearchState(unlocked_tiers=["now_scope"])
    for obj in scene.objects:
        conf, detected = calculate_identification_confidence(obj, base)
        if conf >= 0.25 and rec & set(detected):
            return True

    defn = get_scene_definition(scene.id)
    if defn and defn.recommended_signal_modes:
        catalog_modes = {s.value for s in defn.recommended_signal_modes}
        if rec <= catalog_modes and types_in_scene:
            return True

    return False


def is_visible_light_trivial_scene(scene: SceneRegion, unlock_tier_id: str | None) -> bool:
    """True if every object is easy at naked-eye/ground without specialty signals."""
    if unlock_tier_id not in (None, "naked_eye", "ground_optical", "improved_ground"):
        return False
    base = ResearchState()
    for obj in scene.objects:
        conf, _ = calculate_identification_confidence(obj, base)
        props = obj.properties or {}
        if props.get("required_signal_types"):
            return False
        if conf < 0.5:
            return False
    return bool(scene.objects)


def run_campaign_alignment_checks(
    *,
    seed: str = "alignment-check",
) -> list[dict[str, Any]]:
    """Validate catalog scenes vs surveys, tiers, and generators. Returns check rows."""
    survey_ids = {s.id for s in get_default_survey_programs()}
    checks: list[dict[str, Any]] = []

    for defn in get_default_scene_catalog():
        scene = scene_for_playtest(defn.id, defn.default_seed or seed)
        row_base = {"scene_id": defn.id, "scene_name": defn.name}

        if not defn.recommended_survey_ids:
            checks.append({**row_base, "check": "recommended_surveys", "status": "warn", "detail": "none"})
        else:
            for sid in defn.recommended_survey_ids:
                if sid not in survey_ids:
                    checks.append({
                        **row_base,
                        "check": f"survey_exists:{sid}",
                        "status": "fail",
                        "detail": "unknown survey id",
                    })
                else:
                    checks.append({
                        **row_base,
                        "check": f"survey_exists:{sid}",
                        "status": "pass",
                        "detail": "",
                    })

        by_type = _objects_by_type(scene)
        for sid in defn.recommended_survey_ids:
            survey = get_survey_by_id(sid)
            if survey is None:
                continue
            if survey.target_object_types:
                matched = any(t in by_type for t in survey.target_object_types)
                checks.append({
                    **row_base,
                    "check": f"survey_targets:{sid}",
                    "status": "pass" if matched else "warn",
                    "detail": "no matching object types in scene" if not matched else "",
                })

        tier = defn.unlock_tier_id
        if tier and get_tier_by_id(tier) is None:
            checks.append({
                **row_base,
                "check": "unlock_tier_valid",
                "status": "fail",
                "detail": f"unknown tier {tier}",
            })
        else:
            detectable = scene_has_detectable_at_unlock_tier(scene, tier)
            checks.append({
                **row_base,
                "check": "detectable_at_unlock",
                "status": "pass" if detectable else "fail",
                "detail": "" if detectable else f"nothing detectable at {tier}",
            })

        modes = [s.value for s in defn.recommended_signal_modes]
        if modes:
            benefits = scene_benefits_from_recommended_signals(scene, modes)
            checks.append({
                **row_base,
                "check": "recommended_signals_useful",
                "status": "pass" if benefits else "warn",
                "detail": "" if benefits else "recommended signals may not match objects",
            })

        if is_visible_light_trivial_scene(scene, tier) and defn.id != "solar-system":
            checks.append({
                **row_base,
                "check": "not_all_visible_light_trivial",
                "status": "warn",
                "detail": "scene may be entirely visible-light trivial",
            })
        else:
            checks.append({
                **row_base,
                "check": "not_all_visible_light_trivial",
                "status": "pass",
                "detail": "",
            })

    return checks


def alignment_summary_markdown(checks: list[dict[str, Any]]) -> str:
    if not checks:
        return "- _(no alignment checks)_\n"
    lines: list[str] = []
    by_scene: dict[str, list[dict[str, Any]]] = {}
    for c in checks:
        by_scene.setdefault(c["scene_id"], []).append(c)
    for sid in sorted(by_scene):
        fails = [c for c in by_scene[sid] if c["status"] == "fail"]
        warns = [c for c in by_scene[sid] if c["status"] == "warn"]
        if fails:
            lines.append(f"- `{sid}`: **FAIL** — " + "; ".join(f"{c['check']}" for c in fails))
        elif warns:
            lines.append(f"- `{sid}`: warn — " + "; ".join(f"{c['check']}" for c in warns))
        else:
            lines.append(f"- `{sid}`: pass")
    return "\n".join(lines) + "\n"


def _survey_completed(state: ResearchState, survey_id: str) -> bool:
    prog = state.survey_progress.get(survey_id)
    return prog is not None and prog.completed


def _recommended_survey_ids(scene_id: str) -> list[str]:
    defn = get_scene_definition(scene_id)
    return list(defn.recommended_survey_ids) if defn else []


def recommended_survey_started(state: ResearchState, scene_id: str) -> bool:
    for sid in _recommended_survey_ids(scene_id):
        if state.active_survey_id == sid:
            return True
        prog = state.survey_progress.get(sid)
        if prog and (prog.completed or prog.discoveries_completed > 0):
            return True
    return False


def any_recommended_survey_completed(state: ResearchState, scene_id: str) -> bool:
    return any(_survey_completed(state, sid) for sid in _recommended_survey_ids(scene_id))


def any_recommended_survey_available(state: ResearchState, scene_id: str) -> bool:
    avail = {s.id for s in available_surveys_from_state(state, scene_id)}
    return any(sid in avail for sid in _recommended_survey_ids(scene_id))


def scene_ready_to_advance(
    state: ResearchState,
    scene: SceneRegion,
    *,
    min_meaningful_discoveries: int = 2,
    turns_in_scene: int = 0,
    max_turns: int | None = None,
) -> bool:
    """True when the active scene has enough progress to move to the next program."""
    if max_turns is not None and turns_in_scene >= max_turns:
        return True

    scene_id = scene.id
    if turns_in_scene < scene_min_turns(scene_id):
        return False

    meaningful = 0
    remaining_easy = 0
    for obj in scene.objects:
        disc = state.discoveries.get(obj.id)
        conf, _ = calculate_identification_confidence(obj, state)
        if disc and disc.confidence >= 0.25:
            meaningful += 1
        elif conf >= 0.35:
            remaining_easy += 1

    if meaningful < min_meaningful_discoveries:
        return False

    if any_recommended_survey_available(state, scene_id) and not recommended_survey_started(
        state, scene_id
    ):
        return False

    if state.active_survey_id in _recommended_survey_ids(scene_id):
        prog = state.survey_progress.get(state.active_survey_id)
        if prog and not prog.completed and remaining_easy > 0:
            return False

    if any_recommended_survey_completed(state, scene_id):
        return remaining_easy <= 1

    if not any_recommended_survey_available(state, scene_id):
        return remaining_easy <= 1

    return remaining_easy <= 0


def pick_next_scene_in_order(state: ResearchState) -> str | None:
    """Next catalog scene by order_index that is unlocked and ahead of active."""
    catalog = sorted(get_default_scene_catalog(), key=lambda d: d.order_index)
    active_id = state.campaign.active_scene_id
    active_idx = next((d.order_index for d in catalog if d.id == active_id), -1)
    for defn in catalog:
        if defn.order_index <= active_idx:
            continue
        cs = state.campaign.scenes.get(defn.id)
        if cs and cs.unlocked:
            return defn.id
    return None


def should_switch_to_recommended_survey(
    state: ResearchState,
    scene_id: str,
    preferred_id: str | None,
) -> bool:
    if not preferred_id:
        return False
    if state.active_survey_id == preferred_id:
        return False
    if state.active_survey_id is None:
        return True
    prog = state.survey_progress.get(state.active_survey_id)
    if prog is not None and prog.completed:
        return True
    rec = set(_recommended_survey_ids(scene_id))
    if state.active_survey_id not in rec:
        return True
    return False


def preferred_survey_id(state: ResearchState, scene_id: str) -> str | None:
    defn = get_scene_definition(scene_id)
    if defn is None:
        return None
    candidates = available_surveys_from_state(state, scene_id)
    if not candidates:
        return None
    cand_ids = {c.id for c in candidates}
    for sid in defn.recommended_survey_ids:
        if sid in cand_ids:
            return sid
    return candidates[0].id


def available_surveys_from_state(state: ResearchState, scene_id: str):
    from universe.game.surveys import available_surveys

    return available_surveys(state, scene_id=scene_id)


def collect_ladder_warnings(
    run_summary: dict[str, Any],
    final_state: ResearchState,
) -> list[str]:
    """Heuristic warnings for campaign_instrument_ladder runs."""
    warnings: list[str] = []
    scene_metrics: dict[str, dict] = run_summary.get("scene_metrics") or {}
    catalog_ids = [d.id for d in get_default_scene_catalog()]

    for sid in catalog_ids:
        m = scene_metrics.get(sid, {})
        unlock = m.get("unlock_turn")
        visit = m.get("first_visit_turn")
        first_disc = m.get("first_discovery_turn")
        if unlock is not None and visit is None:
            warnings.append(f"Scene '{sid}' unlocked but never visited.")
        if visit is not None and m.get("total_discoveries", 0) == 0:
            warnings.append(f"Scene '{sid}' visited but no discoveries recorded.")
        if unlock is not None and first_disc is not None and first_disc - unlock > 8:
            warnings.append(
                f"Scene '{sid}' first discovery late (unlock t{unlock}, discovery t{first_disc})."
            )
        if unlock is not None and visit is not None and visit - unlock > 12:
            warnings.append(f"Scene '{sid}' first visit late (unlock t{unlock}, visit t{visit}).")

    seq = run_summary.get("scene_visit_sequence") or []
    if seq and catalog_ids:
        order = {d.id: d.order_index for d in get_default_scene_catalog()}
        prev_idx = -1
        for sid in seq:
            idx = order.get(sid, 99)
            if idx < prev_idx:
                warnings.append(
                    f"Scene visit sequence out of order: {seq} (skipped back to {sid})."
                )
            prev_idx = max(prev_idx, idx)

    if "now_scope" in final_state.unlocked_tiers:
        now_m = scene_metrics.get("now-scope-anomaly-field", {})
        if now_m.get("unlock_turn") is not None and now_m.get("first_visit_turn") is None:
            warnings.append("Now-scope field unlocked but never visited.")
        if not run_summary.get("now_scope_exclusive_discovery"):
            if now_m.get("first_visit_turn") is not None:
                warnings.append(
                    "Now-scope field visited but no speculative_anomaly detection."
                )
    else:
        turns = run_summary.get("turns_played", 0)
        if turns >= 200 and not run_summary.get("now_scope_reached"):
            warnings.append(
                f"Now-scope not reached by turn {turns} — check late-game RP and cosmic-web pacing."
            )

    for sid in ("radio-cmb-survey", "stellar-remnant-field"):
        m = scene_metrics.get(sid, {})
        if m.get("first_visit_turn") is not None and m.get("turns_spent_active", 0) < 2:
            started = m.get("surveys_started") or []
            if not started and m.get("surveys_completed"):
                started = m.get("surveys_completed")
            if not started:
                warnings.append(
                    f"Scene '{sid}' active <2 turns and no recommended survey started."
                )

    cw = scene_metrics.get("cosmic-web-map", {})
    if cw.get("turns_spent_active", 0) > 50 and cw.get("total_rp_earned", 0) < 500:
        warnings.append(
            "Cosmic-web scene dominated play with little discovery RP — possible late-game desert."
        )

    for cap in run_summary.get("reward_cap_events") or []:
        msg = cap.get("message", "")
        if "uncapped" in msg:
            m = re.search(r"(\d+) awarded of (\d+) uncapped", msg)
            if m:
                capped, uncapped = int(m.group(1)), int(m.group(2))
                if uncapped > capped * 10:
                    warnings.append(
                        f"Scene '{cap.get('scene_id')}' uncapped RP would exceed cap by >10× "
                        f"({uncapped} vs {capped} awarded)."
                    )
                    break

    return warnings


def _median(values: list[int | float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    mid = len(s) // 2
    if len(s) % 2:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def generate_campaign_ladder_analysis(
    runs: list[Any],
    *,
    late_discovery_threshold: int = 8,
) -> str:
    """Markdown section for campaign_instrument_ladder balance runs."""
    from universe.game.telemetry import PlaytestRun

    ladder = [r for r in runs if isinstance(r, PlaytestRun) and r.scenario_id == "campaign_instrument_ladder"]
    if not ladder:
        return "- _(no campaign_instrument_ladder runs in input)_\n"

    catalog_ids = [d.id for d in get_default_scene_catalog()]
    lines: list[str] = []

    lines.append("### Scene unlock / visit / discovery (by entity type)")
    lines.append("")
    lines.append(
        "| Entity | Scene | Unlock | Visit | 1st disc | Confirmed | Disc | RP | Surveys | Active turns |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |")
    first_disc_by_scene: dict[str, list[int]] = {sid: [] for sid in catalog_ids}

    for run in ladder:
        sm = run.summary.get("scene_metrics") or {}
        for sid in catalog_ids:
            m = sm.get(sid, {})
            unlock = m.get("unlock_turn")
            visit = m.get("first_visit_turn")
            fd = m.get("first_discovery_turn")
            if fd is not None:
                first_disc_by_scene.setdefault(sid, []).append(int(fd))
            surveys = m.get("surveys_completed") or []
            lines.append(
                f"| `{run.entity_type}` | `{sid}` | "
                f"{unlock if unlock is not None else '—'} | "
                f"{visit if visit is not None else '—'} | "
                f"{fd if fd is not None else '—'} | "
                f"{m.get('first_confirmed_discovery_turn', '—')} | "
                f"{m.get('total_discoveries', 0)} | "
                f"{m.get('total_rp_earned', 0)} | "
                f"{len(surveys)} | "
                f"{m.get('turns_spent_active', 0)} |"
            )
    lines.append("")

    lines.append("### Median turn to first discovery per scene")
    lines.append("")
    for sid in catalog_ids:
        med = _median([float(v) for v in first_disc_by_scene.get(sid, [])])
        lines.append(
            f"- `{sid}`: {med:.0f}" if med is not None else f"- `{sid}`: _(no discoveries)_"
        )
    lines.append("")

    lines.append("### Scene visit sequences")
    lines.append("")
    for run in ladder:
        seq = run.summary.get("scene_visit_sequence") or []
        lines.append(f"- `{run.entity_type}`: {seq}")
    lines.append("")

    lines.append("### Tier unlocks (active scene at unlock)")
    lines.append("")
    for run in ladder:
        ctx = run.summary.get("tier_unlock_context") or {}
        if not ctx:
            lines.append(f"- `{run.entity_type}`: _(no tier unlocks recorded)_")
            continue
        parts = [
            f"{tid}@t{c['turn']}(scene `{c.get('active_scene_id', '?')}`, cost {c.get('rp_cost', 0)})"
            for tid, c in sorted(
                ctx.items(),
                key=lambda x: (get_tier_by_id(x[0]).tier_index if get_tier_by_id(x[0]) else 99, x[0]),
            )
        ]
        lines.append(f"- `{run.entity_type}`: " + ", ".join(parts))
    lines.append("")

    lines.append("### Observation RP caps")
    lines.append("")
    for run in ladder:
        caps = run.summary.get("reward_cap_count", 0)
        lines.append(
            f"- `{run.entity_type}`: {caps} cap event(s) in run"
        )
    lines.append("")

    reached = sum(1 for r in ladder if r.summary.get("now_scope_reached"))
    lines.append(
        f"### Now-scope reach rate: {reached}/{len(ladder)} "
        f"({100.0 * reached / len(ladder):.0f}%) within scenario max turns"
    )
    lines.append("")

    lines.append("### Surveys started per scene (sample)")
    lines.append("")
    for run in ladder[:3]:
        sm = run.summary.get("scene_metrics") or {}
        parts = [
            f"{sid}: started={sm.get(sid, {}).get('surveys_started', [])}, "
            f"completed={sm.get(sid, {}).get('surveys_completed', [])}"
            for sid in catalog_ids
            if sm.get(sid, {}).get("surveys_started") or sm.get(sid, {}).get("surveys_completed")
        ]
        lines.append(f"- `{run.entity_type}`: " + ("; ".join(parts) if parts else "_(none)_"))
    lines.append("")

    lines.append("### Entity progression summary")
    lines.append("")
    lines.append(
        "| Entity | Final tier | RP | Turns | Max dead streak | Now-scope | Anomaly |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | --- | --- |")
    for run in ladder:
        s = run.summary
        lines.append(
            f"| `{run.entity_type}` | `{s.get('final_tier', '')}` | "
            f"{s.get('final_rp', 0)} | {s.get('turns_played', 0)} | "
            f"{s.get('dead_turn_count', 0)} | "
            f"{s.get('now_scope_reached', False)} | "
            f"{s.get('now_scope_exclusive_discovery', False)} |"
        )
    lines.append("")

    lines.append("### Ladder warnings")
    lines.append("")
    all_ladder_warnings: list[str] = []
    for run in ladder:
        for w in run.summary.get("warnings") or []:
            if any(
                kw in w
                for kw in (
                    "unlocked but never visited",
                    "visited but no discoveries",
                    "first discovery late",
                    "first visit late",
                    "visit sequence out of order",
                    "Now-scope",
                    "speculative_anomaly",
                )
            ):
                all_ladder_warnings.append(f"`{run.entity_type}`: {w}")
    if all_ladder_warnings:
        for w in sorted(set(all_ladder_warnings)):
            lines.append(f"- {w}")
    else:
        lines.append("- _(no ladder-specific warnings)_")
    lines.append("")

    lines.append("### Scene / survey alignment (catalog)")
    lines.append("")
    checks = run_campaign_alignment_checks()
    lines.append(alignment_summary_markdown(checks))
    fail_count = sum(1 for c in checks if c["status"] == "fail")
    warn_count = sum(1 for c in checks if c["status"] == "warn")
    lines.append(f"- Alignment summary: {fail_count} fail, {warn_count} warn checks.")
    lines.append("")

    skipped: list[str] = []
    for run in ladder:
        sm = run.summary.get("scene_metrics") or {}
        for sid in catalog_ids:
            m = sm.get(sid, {})
            if m.get("unlock_turn") is not None and m.get("first_visit_turn") is None:
                skipped.append(f"`{run.entity_type}` / `{sid}` unlocked, never visited")
            elif m.get("first_visit_turn") is not None and m.get("total_discoveries", 0) == 0:
                skipped.append(f"`{run.entity_type}` / `{sid}` visited, no discoveries")
            unlock = m.get("unlock_turn")
            fd = m.get("first_discovery_turn")
            if unlock is not None and fd is not None and fd - unlock > late_discovery_threshold:
                skipped.append(
                    f"`{run.entity_type}` / `{sid}` late first discovery (t{unlock}→t{fd})"
                )
    if skipped:
        lines.append("### Skipped / thin scenes")
        lines.append("")
        for s in sorted(set(skipped)):
            lines.append(f"- {s}")
        lines.append("")

    now_runs = [r for r in ladder if not r.summary.get("now_scope_exclusive_discovery")]
    if now_runs:
        lines.append("### Now-scope detection status")
        lines.append("")
        for run in now_runs:
            now_m = (run.summary.get("scene_metrics") or {}).get(
                "now-scope-anomaly-field", {}
            )
            lines.append(
                f"- `{run.entity_type}`: visited={now_m.get('first_visit_turn')}, "
                f"unlock={now_m.get('unlock_turn')}, "
                f"discoveries={now_m.get('total_discoveries', 0)}"
            )
        lines.append("")

    return "\n".join(lines)
