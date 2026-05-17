"""Tests for per-scene observation RP caps."""

from __future__ import annotations

from universe.game.discovery import observe_scene
from universe.game.models import ResearchState
from universe.game.observation_rewards import (
    apply_discovery_rp_cap,
    discovery_rp_cap_for_scene,
)
from universe.game.playtest import get_scenario_by_id, run_playtest
from universe.procedural.registry import generate_scene_by_id


class TestDiscoveryRpCap:
    def test_scene_001_cap_value(self):
        assert discovery_rp_cap_for_scene("scene-001") == 250

    def test_apply_cap_reduces_total(self):
        from universe.game.models import DiscoveryResult

        results = [
            DiscoveryResult(
                object_id=f"g{i}",
                object_type="galaxy",
                identification_confidence=0.9,
                newly_discovered=True,
                research_points_awarded=5000,
                message=f"galaxy {i}",
            )
            for i in range(30)
        ]
        capped, telem = apply_discovery_rp_cap(results, "scene-001")
        assert telem["reward_cap_applied"] is True
        assert telem["uncapped_rp"] == 150000
        assert telem["capped_rp"] == 250
        assert sum(r.research_points_awarded for r in capped) == 250

    def test_scene_001_observe_not_120k_rp(self):
        scene = generate_scene_by_id("scene-001", seed="lyman-alpha-furnace")
        state = ResearchState(
            unlocked_tiers=[
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
            ],
            active_telescope_tier="space_optical",
        )
        state, results = observe_scene(scene, state)
        primary_rp = sum(
            r.research_points_awarded
            for r in results
            if r.object_id
            and not r.object_id.startswith("__")
            and not r.message.startswith("Follow-up:")
            and r.object_type != "reward_cap_event"
        )
        assert primary_rp <= 250
        cap_msgs = [r for r in results if r.object_id == "__reward_cap__"]
        assert cap_msgs, "expected cap telemetry result"

    def test_cap_does_not_block_discoveries(self):
        scene = generate_scene_by_id("scene-001", seed="cap-disc")
        state = ResearchState(
            unlocked_tiers=["naked_eye", "ground_optical", "improved_ground", "space_optical"],
            active_telescope_tier="space_optical",
        )
        state, _ = observe_scene(scene, state)
        assert len(state.discoveries) > 5

    def test_solar_tutorial_still_progresses(self):
        scene = generate_scene_by_id("solar-system", seed="local-sky")
        state = ResearchState()
        state, _ = observe_scene(scene, state)
        assert state.research_points > 0
        assert state.research_points <= 70


class TestCapInPlaytest:
    def test_ladder_records_cap_events(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="cap-ladder",
            max_turns=40,
        )
        assert run.summary.get("reward_cap_count", 0) >= 1
