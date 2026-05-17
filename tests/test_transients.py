"""Tests for transient observation events."""

from __future__ import annotations

import json

from click.testing import CliRunner

from universe.cli import main
from universe.game.models import ResearchState
from universe.game.transients import (
    get_default_transient_events,
    get_transient_event,
    observe_transient_event,
    update_transient_event_states,
)
from universe.procedural.registry import generate_scene_by_id


class TestTransientCatalog:
    def test_event_ids_unique(self):
        ids = [e.id for e in get_default_transient_events()]
        assert len(ids) == len(set(ids))

    def test_tier_and_scene_ids_valid(self):
        from universe.game.scenes import get_default_scene_catalog
        from universe.game.tech_tree import get_default_tech_tree

        scene_ids = {d.id for d in get_default_scene_catalog()}
        tier_ids = {t.id for t in get_default_tech_tree()}
        for ev in get_default_transient_events():
            assert ev.scene_id in scene_ids
            assert ev.minimum_telescope_tier in tier_ids

    def test_speculative_event_marked(self):
        ev = get_transient_event("causality_echo_001")
        assert ev is not None
        assert ev.speculative is True


class TestTransientObservation:
    def test_inactive_before_start_turn(self):
        scene = generate_scene_by_id("solar-system", seed="local-sky")
        state = ResearchState(turn=1)
        ok, _ = __import__(
            "universe.game.transients", fromlist=["is_transient_observable"]
        ).is_transient_observable(scene, state, "solar_flare_001")
        assert ok is False

    def test_active_during_window(self):
        scene = generate_scene_by_id("solar-system", seed="local-sky")
        state = ResearchState(
            turn=3,
            unlocked_tiers=["naked_eye", "ground_optical"],
            active_telescope_tier="ground_optical",
        )
        state = update_transient_event_states(state)
        from universe.game.transients import is_transient_observable

        ok, _ = is_transient_observable(scene, state, "solar_flare_001")
        assert ok is True

    def test_expired_after_duration(self):
        scene = generate_scene_by_id("solar-system", seed="local-sky")
        state = ResearchState(
            turn=10,
            unlocked_tiers=["naked_eye", "ground_optical"],
            active_telescope_tier="ground_optical",
        )
        state = update_transient_event_states(state)
        from universe.game.transients import is_transient_observable

        ok, msg = is_transient_observable(scene, state, "solar_flare_001")
        assert ok is False
        assert "expired" in msg.lower()

    def test_reward_once(self):
        scene = generate_scene_by_id("solar-system", seed="local-sky")
        state = ResearchState(
            turn=3,
            unlocked_tiers=["naked_eye", "ground_optical", "improved_ground"],
            active_telescope_tier="ground_optical",
        )
        state, res, err = observe_transient_event(scene, state, "solar_flare_001")
        assert res is not None and err == ""
        rp1 = state.research_points
        state, res2, err2 = observe_transient_event(scene, state, "solar_flare_001")
        assert res2 is None
        assert state.research_points == rp1

    def test_speculative_requires_now_scope(self):
        scene = generate_scene_by_id("now-scope-anomaly-field", seed="impossible-now")
        state = ResearchState(
            turn=35,
            unlocked_tiers=["now_scope"],
            active_telescope_tier="now_scope",
            known_signal_types=["speculative_now_signal"],
        )
        state = update_transient_event_states(state)
        from universe.game.transients import is_transient_observable

        ok, _ = is_transient_observable(scene, state, "causality_echo_001")
        assert ok is True

    def test_backward_compatible_state(self):
        data = ResearchState().model_dump()
        data.pop("transient_events", None)
        loaded = ResearchState.model_validate(data)
        assert loaded.transient_events == {}


class TestTransientCLI:
    def test_transients_command(self, tmp_path):
        state_path = tmp_path / "state.json"
        state_path.write_text(ResearchState().model_dump_json())
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["game", "transients", "--state", str(state_path), "--scene", "solar-system"],
        )
        assert result.exit_code == 0, result.output
        assert "solar_flare_001" in result.output or "Solar Flare" in result.output

    def test_observe_transient_command(self, tmp_path):
        scene = generate_scene_by_id("solar-system", seed="local-sky")
        scene_path = tmp_path / "scene.json"
        scene_path.write_text(scene.model_dump_json())
        state_path = tmp_path / "state.json"
        state = ResearchState(
            turn=3,
            unlocked_tiers=["naked_eye", "ground_optical"],
            active_telescope_tier="ground_optical",
        )
        state_path.write_text(state.model_dump_json())
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "game",
                "observe-transient",
                "--scene",
                str(scene_path),
                "--state",
                str(state_path),
                "--event",
                "solar_flare_001",
                "--out",
                str(state_path),
            ],
        )
        assert result.exit_code == 0, result.output
        saved = json.loads(state_path.read_text())
        assert saved["transient_events"]["solar_flare_001"]["reward_claimed"] is True


class TestTransientPlaytest:
    def test_ladder_observes_transient(self):
        from universe.game.playtest import get_scenario_by_id, run_playtest

        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="transient-ladder",
            max_turns=80,
        )
        assert run.summary.get("transient_events_observed")
