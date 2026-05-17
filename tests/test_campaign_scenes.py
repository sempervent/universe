"""Tests for expanded campaign observation scene generators."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from universe.cli import main
from universe.game.discovery import calculate_identification_confidence
from universe.game.models import ResearchState
from universe.game.playtest import get_scenario_by_id, run_playtest
from universe.game.scenes import (
    ensure_campaign_state,
    get_default_scene_catalog,
    set_active_scene,
    update_scene_unlocks,
)
from universe.game.playtest import bootstrap_unlocked_tiers
from universe.procedural.cosmic_web_map import generate_cosmic_web_map
from universe.procedural.now_scope_field import generate_now_scope_anomaly_field
from universe.procedural.radio_cmb import generate_radio_cmb_survey
from universe.procedural.registry import CAMPAIGN_SCENE_IDS
from universe.procedural.stellar_remnants import generate_stellar_remnant_field


NEW_SCENE_IDS = (
    "radio-cmb-survey",
    "stellar-remnant-field",
    "cosmic-web-map",
    "now-scope-anomaly-field",
)


class TestProceduralGenerators:
    @pytest.mark.parametrize(
        ("factory", "scene_id", "seed"),
        [
            (generate_radio_cmb_survey, "radio-cmb-survey", "radio-first-light"),
            (generate_stellar_remnant_field, "stellar-remnant-field", "high-energy-remnants"),
            (generate_cosmic_web_map, "cosmic-web-map", "invisible-architecture"),
            (generate_now_scope_anomaly_field, "now-scope-anomaly-field", "impossible-now"),
        ],
    )
    def test_generates_valid_scene(self, factory, scene_id, seed):
        a = factory(seed=seed)
        b = factory(seed=seed)
        assert a.model_dump() == b.model_dump()
        assert a.id == scene_id
        assert len(a.objects) >= 4
        meta = a.metadata
        assert meta.recommended_camera_target_object_id
        assert meta.recommended_initial_signal_mode
        assert meta.featured_object_ids
        assert meta.teaching_summary

    def test_radio_scene_has_cmb_and_radio_targets(self):
        scene = generate_radio_cmb_survey("radio-first-light")
        types = {o.type.value for o in scene.objects}
        assert "cmb_background" in types
        assert "galaxy" in types
        assert "quasar" in types

    def test_stellar_scene_has_magnetars(self):
        scene = generate_stellar_remnant_field("high-energy-remnants")
        assert sum(1 for o in scene.objects if o.type.value == "magnetar") >= 2

    def test_cosmic_web_has_web_graph(self):
        scene = generate_cosmic_web_map("invisible-architecture")
        assert len(scene.nodes) >= 4
        assert len(scene.filaments) >= 2

    def test_now_scope_speculative(self):
        scene = generate_now_scope_anomaly_field("impossible-now")
        assert scene.metadata.scene_class == "speculative"
        assert any(o.type.value == "speculative_anomaly" for o in scene.objects)


class TestCampaignCatalogExpansion:
    def test_catalog_includes_new_scenes(self):
        ids = {s.id for s in get_default_scene_catalog()}
        for sid in NEW_SCENE_IDS:
            assert sid in ids
        assert len(get_default_scene_catalog()) == 6

    def test_registry_matches_catalog(self):
        catalog_ids = {s.id for s in get_default_scene_catalog()}
        assert catalog_ids <= CAMPAIGN_SCENE_IDS

    def test_unlock_tiers_valid(self):
        from universe.game.tech_tree import get_tier_by_id

        for defn in get_default_scene_catalog():
            if defn.unlock_tier_id:
                assert get_tier_by_id(defn.unlock_tier_id) is not None


class TestSceneDiscovery:
    def _state_with_tiers(self, tier_ids: list[str]) -> ResearchState:
        state = ResearchState()
        return bootstrap_unlocked_tiers(state, tier_ids)

    def test_radio_scene_needs_radio_for_cmb(self):
        scene = generate_radio_cmb_survey("radio-first-light")
        cmb = next(o for o in scene.objects if o.type.value == "cmb_background")
        optical_only = self._state_with_tiers(
            ["naked_eye", "ground_optical", "improved_ground", "space_optical"]
        )
        radio = self._state_with_tiers(
            ["naked_eye", "ground_optical", "improved_ground", "space_optical", "radio"]
        )
        assert calculate_identification_confidence(cmb, optical_only)[0] == 0.0
        assert calculate_identification_confidence(cmb, radio)[0] > 0.25

    def test_stellar_scene_magnetar_needs_xray(self):
        scene = generate_stellar_remnant_field("high-energy-remnants")
        mag = next(o for o in scene.objects if o.type.value == "magnetar")
        radio_only = self._state_with_tiers(
            ["naked_eye", "ground_optical", "improved_ground", "space_optical", "radio"]
        )
        xray = self._state_with_tiers(
            [
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
                "radio",
                "xray_gamma",
            ]
        )
        xray = xray.model_copy(update={"active_telescope_tier": "xray_gamma"})
        assert calculate_identification_confidence(mag, radio_only)[0] == 0.0
        assert calculate_identification_confidence(mag, xray)[0] > 0.25

    def test_cosmic_web_lensing_tracer(self):
        scene = generate_cosmic_web_map("invisible-architecture")
        tracer = next(
            o for o in scene.objects if o.properties.get("mass_tracer")
        )
        optical = self._state_with_tiers(
            ["naked_eye", "ground_optical", "improved_ground", "space_optical"]
        )
        lensing = self._state_with_tiers(
            [
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
                "radio",
                "xray_gamma",
                "interferometer",
                "gravitational_wave",
                "neutrino_cosmic_ray",
                "multi_messenger",
                "dark_matter_mapper",
            ]
        )
        lensing = lensing.model_copy(update={"active_telescope_tier": "dark_matter_mapper"})
        assert calculate_identification_confidence(tracer, optical)[0] == 0.0
        assert calculate_identification_confidence(tracer, lensing)[0] > 0.25

    def test_now_scope_anomaly_requires_now_scope(self):
        scene = generate_now_scope_anomaly_field("impossible-now")
        anomaly = next(o for o in scene.objects if o.type.value == "speculative_anomaly")
        dm = self._state_with_tiers(
            [
                "naked_eye",
                "ground_optical",
                "improved_ground",
                "space_optical",
                "radio",
                "xray_gamma",
                "interferometer",
                "gravitational_wave",
                "neutrino_cosmic_ray",
                "multi_messenger",
                "dark_matter_mapper",
            ]
        )
        now = self._state_with_tiers(
            list(dm.unlocked_tiers) + ["now_scope"],
        )
        assert calculate_identification_confidence(anomaly, dm)[0] == 0.0
        assert calculate_identification_confidence(anomaly, now)[0] > 0.25


class TestCampaignSceneCLI:
    @pytest.mark.parametrize("scene_id", NEW_SCENE_IDS)
    def test_generate_cli(self, scene_id):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / scene_id
            result = runner.invoke(
                main,
                ["generate", scene_id, "--seed", "test-seed", "--out", str(out)],
            )
            assert result.exit_code == 0, result.output
            assert (out / "scene.json").exists()

    def test_game_generate_scene(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "radio"
            result = runner.invoke(
                main,
                ["game", "generate-scene", "--scene", "radio-cmb-survey", "--out", str(out)],
            )
            assert result.exit_code == 0, result.output
            data = json.loads((out / "scene.json").read_text())
            assert data["id"] == "radio-cmb-survey"


class TestCampaignUnlocks:
    def test_radio_scene_unlocks_with_radio_tier(self):
        state = ResearchState(unlocked_tiers=["space_optical", "radio"])
        state = ensure_campaign_state(state)
        state, _ = update_scene_unlocks(state)
        assert state.campaign.scenes["radio-cmb-survey"].unlocked

    def test_set_scene_rejects_locked_radio(self):
        state = ensure_campaign_state(ResearchState())
        new_state, msg = set_active_scene(state, "radio-cmb-survey")
        assert "locked" in msg.lower()
        assert new_state.campaign.active_scene_id == "solar-system"


class TestInstrumentLadderPlaytest:
    def test_visits_multiple_scenes(self):
        scenario = get_scenario_by_id("campaign_instrument_ladder")
        assert scenario is not None
        run = run_playtest(
            scenario,
            entity_type="private_institute",
            seed="ladder-test",
            max_turns=120,
        )
        visited = {
            sid
            for sid, cs in run.final_state.campaign.scenes.items()
            if cs.visited
        }
        assert "solar-system" in visited
        assert "scene-001" in visited
        assert len(visited) >= 3
        assert run.summary.get("campaign_transition_turn") is not None
        assert run.summary.get("scene_metrics") is not None
        assert "solar-system" in (run.summary.get("scene_metrics") or {})
