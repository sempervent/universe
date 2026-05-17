"""Tests for campaign ladder balance metrics and alignment checks."""

from __future__ import annotations

from universe.game.campaign_balance import (
    SceneMetricsTracker,
    alignment_summary_markdown,
    generate_campaign_ladder_analysis,
    pick_next_scene_in_order,
    run_campaign_alignment_checks,
    scene_ready_to_advance,
)
from universe.game.playtest import (
    generate_balance_report,
    get_scenario_by_id,
    run_playtest,
)
from universe.game.scenes import ensure_campaign_state, get_default_scene_catalog
from universe.game.models import ResearchState
from universe.procedural.registry import generate_scene_by_id


class TestAlignmentChecks:
    def test_every_scene_has_alignment_rows(self):
        checks = run_campaign_alignment_checks()
        scene_ids = {d.id for d in get_default_scene_catalog()}
        assert scene_ids.issubset({c["scene_id"] for c in checks})

    def test_no_fail_on_default_catalog(self):
        checks = run_campaign_alignment_checks()
        fails = [c for c in checks if c["status"] == "fail"]
        assert not fails, fails

    def test_recommended_signals_no_false_warn_solar(self):
        checks = run_campaign_alignment_checks()
        solar_warns = [
            c
            for c in checks
            if c["scene_id"] == "solar-system"
            and c["check"] == "recommended_signals_useful"
            and c["status"] == "warn"
        ]
        assert not solar_warns

    def test_recommended_surveys_exist(self):
        checks = run_campaign_alignment_checks()
        for c in checks:
            if c["check"].startswith("survey_exists:") and c["status"] == "fail":
                raise AssertionError(c)

    def test_alignment_markdown_lists_all_scenes(self):
        checks = run_campaign_alignment_checks()
        md = alignment_summary_markdown(checks)
        for defn in get_default_scene_catalog():
            assert f"`{defn.id}`" in md


class TestSceneMetricsTracker:
    def test_records_unlock_visit_discovery(self):
        tracker = SceneMetricsTracker(["solar-system", "scene-001"])
        tracker.sync_campaign_state(
            ensure_campaign_state(ResearchState()),
            {"solar-system": 0, "scene-001": 5},
        )
        tracker.record_visit("solar-system", 0)
        tracker.record_visit("scene-001", 6)
        tracker.record_discovery_event(
            active_scene_id="solar-system",
            turn=2,
            confidence=0.5,
            delta_rp=10,
        )
        summary = tracker.to_summary_dict()
        assert summary["scene_metrics"]["solar-system"]["first_discovery_turn"] == 2
        assert summary["scene_visit_sequence"] == ["solar-system", "scene-001"]


class TestCampaignOrderedAutoplay:
    def test_starts_radio_survey_in_radio_scene(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="radio-survey-start",
            max_turns=80,
        )
        radio = (run.summary.get("scene_metrics") or {}).get("radio-cmb-survey", {})
        started = radio.get("surveys_started") or []
        completed = radio.get("surveys_completed") or []
        assert "radio_sky_survey" in started or "radio_sky_survey" in completed

    def test_stellar_starts_compact_object_search(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="stellar-survey-start",
            max_turns=90,
        )
        stellar = (run.summary.get("scene_metrics") or {}).get(
            "stellar-remnant-field", {}
        )
        started = stellar.get("surveys_started") or []
        completed = stellar.get("surveys_completed") or []
        assert "compact_object_search" in started or "compact_object_search" in completed

    def test_radio_scene_more_than_one_turn(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="radio-turns",
            max_turns=100,
        )
        radio = (run.summary.get("scene_metrics") or {}).get("radio-cmb-survey", {})
        assert radio.get("turns_spent_active", 0) >= 2

    def test_private_institute_reaches_now_scope(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="now-scope-reach",
            max_turns=250,
        )
        assert run.summary.get("now_scope_reached") is True

    def test_campaign_ordered_visits_solar_and_scene_001(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        assert scenario.strategy == "campaign_ordered"
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="ordered-ladder",
            max_turns=100,
        )
        visited = {
            sid
            for sid, cs in run.final_state.campaign.scenes.items()
            if cs.visited
        }
        assert "solar-system" in visited
        assert "scene-001" in visited

    def test_campaign_ordered_deterministic(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        a = run_playtest(
            scenario,
            entity_type="university_lab",
            seed="ordered-deterministic",
            max_turns=60,
        )
        b = run_playtest(
            scenario,
            entity_type="university_lab",
            seed="ordered-deterministic",
            max_turns=60,
        )
        assert a.summary.get("scene_visit_sequence") == b.summary.get(
            "scene_visit_sequence"
        )
        assert a.summary.get("scene_metrics") == b.summary.get("scene_metrics")

    def test_ladder_records_scene_metrics(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="metrics-ladder",
            max_turns=80,
        )
        sm = run.summary.get("scene_metrics")
        assert sm is not None
        assert "solar-system" in sm
        assert sm["solar-system"].get("turns_spent_active", 0) > 0
        assert run.summary.get("tier_unlock_context") is not None

    def test_visit_sequence_respects_catalog_order(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="order-seq",
            max_turns=120,
        )
        order = {d.id: d.order_index for d in get_default_scene_catalog()}
        seq = run.summary.get("scene_visit_sequence") or []
        prev = -1
        for sid in seq:
            assert order.get(sid, 99) >= prev
            prev = order.get(sid, 99)


class TestBalanceReportLadder:
    def test_balance_report_includes_campaign_ladder_section(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="custom",
            seed="report-ladder",
            max_turns=40,
        )
        md = generate_balance_report([run])
        assert "Campaign Ladder Analysis" in md
        assert "Observation RP Cap" in md or "Observation RP caps" in md
        for sid in [
            "solar-system",
            "scene-001",
            "radio-cmb-survey",
            "stellar-remnant-field",
            "cosmic-web-map",
            "now-scope-anomaly-field",
        ]:
            assert sid in md

    def test_generate_ladder_analysis_all_six_scenes(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="custom",
            seed="ladder-md",
            max_turns=30,
        )
        section = generate_campaign_ladder_analysis([run])
        for sid in [
            "solar-system",
            "scene-001",
            "radio-cmb-survey",
            "stellar-remnant-field",
            "cosmic-web-map",
            "now-scope-anomaly-field",
        ]:
            assert f"`{sid}`" in section


class TestSceneProgressionHelpers:
    def test_pick_next_scene_in_order(self):
        state = ensure_campaign_state(ResearchState())
        state.campaign.scenes["scene-001"].unlocked = True
        nxt = pick_next_scene_in_order(state)
        assert nxt == "scene-001"

    def test_scene_ready_requires_discoveries(self):
        state = ensure_campaign_state(ResearchState())
        scene = generate_scene_by_id("solar-system", seed="local-sky")
        assert scene_ready_to_advance(state, scene) is False
