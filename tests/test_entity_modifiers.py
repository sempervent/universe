"""Tests for research entity background modifiers."""

from pathlib import Path

from click.testing import CliRunner

from universe.cli import main
from universe.game.discovery import calculate_identification_confidence, observe_scene
from universe.game.entity import (
    EntityModifier,
    get_all_entity_modifiers,
    get_entity_modifier,
    make_research_entity,
)
from universe.game.milestones import effective_milestone_reward
from universe.game.models import ResearchState
from universe.game.surveys import (
    effective_survey_reward,
    get_survey_by_id,
    start_survey,
)
from universe.game.tech_tree import (
    effective_tier_research_cost,
    get_tier_by_id,
    unlock_tier,
)
from universe.models import ObjectType
from universe.procedural.solar_system import generate_solar_system


class TestEntityModifierRegistry:
    def test_all_known_types_have_modifiers(self):
        types = {m.entity_type for m in get_all_entity_modifiers()}
        for t in [
            "backyard_observatory",
            "university_lab",
            "national_observatory",
            "private_institute",
            "orbital_consortium",
            "ai_research_bureau",
            "citizen_science_network",
            "occult_sky_society",
            "corporate_research_division",
            "custom",
        ]:
            assert t in types

    def test_custom_is_neutral(self):
        m = get_entity_modifier("custom")
        assert m.discovery_rp_multiplier == 1.0
        assert m.confidence_bonus == 0.0

    def test_unknown_type_falls_back_to_neutral(self):
        m = get_entity_modifier("not_a_real_type_ever")
        assert m.entity_type == "custom"

    def test_multipliers_in_sane_range(self):
        for m in get_all_entity_modifiers():
            assert 0.5 <= m.discovery_rp_multiplier <= 1.5
            assert 0.5 <= m.milestone_rp_multiplier <= 1.5
            assert 0.5 <= m.survey_rp_multiplier <= 1.5
            assert 0.7 <= m.upgrade_cost_multiplier <= 1.05
            assert 0.0 <= m.confidence_bonus <= 0.2

    def test_model_dump_roundtrip(self):
        m = get_entity_modifier("private_institute")
        data = m.model_dump()
        m2 = EntityModifier.model_validate(data)
        assert m2.discovery_rp_multiplier == 1.05


class TestDiscoveryModifiers:
    def test_private_institute_boosts_discovery_rp(self):
        scene = generate_solar_system(seed="em-rp")
        base = ResearchState()
        inst = ResearchState(research_entity=make_research_entity("Lab", entity_type="private_institute"))
        new_b, res_b = observe_scene(scene, base)
        new_i, res_i = observe_scene(scene, inst)
        rp_b = new_b.research_points
        rp_i = new_i.research_points
        assert rp_i > rp_b

    def test_ai_bureau_never_enables_impossible_detection(self):
        from universe.procedural.region import generate_scene_001

        scene = generate_scene_001(seed="em-ai", num_galaxies=5, num_nodes=3)
        state = ResearchState(
            research_entity=make_research_entity("AI", entity_type="ai_research_bureau"),
        )
        bh = next(o for o in scene.objects if o.type == ObjectType.BLACK_HOLE)
        conf, _ = calculate_identification_confidence(bh, state)
        assert conf == 0.0

    def test_ai_bureau_boosts_when_detectable(self):
        scene = generate_solar_system(seed="em-ai2")
        state = ResearchState(
            research_entity=make_research_entity("AI", entity_type="ai_research_bureau"),
        )
        sun = next(o for o in scene.objects if o.id == "sun")
        plain = ResearchState()
        c0, _ = calculate_identification_confidence(sun, plain)
        c1, _ = calculate_identification_confidence(sun, state)
        assert c1 >= c0
        if c0 > 0:
            assert c1 > c0 or abs(c1 - min(1.0, c0 + 0.05)) < 1e-6


class TestTechCostModifiers:
    def test_backyard_cheaper_early_optical(self):
        tier = get_tier_by_id("ground_optical")
        assert tier is not None
        st_custom = ResearchState(research_points=100)
        st_back = ResearchState(
            research_points=100,
            research_entity=make_research_entity("BY", entity_type="backyard_observatory"),
        )
        assert effective_tier_research_cost(tier, st_back) < effective_tier_research_cost(tier, st_custom)

    def test_orbital_consortium_cheaper_space_track(self):
        tier = get_tier_by_id("space_optical")
        assert tier is not None
        st_custom = ResearchState(research_points=500)
        st_orb = ResearchState(
            research_points=500,
            research_entity=make_research_entity("OC", entity_type="orbital_consortium"),
        )
        assert effective_tier_research_cost(tier, st_orb) < effective_tier_research_cost(tier, st_custom)

    def test_unlock_charges_effective_cost(self):
        tier = get_tier_by_id("ground_optical")
        assert tier is not None
        state = ResearchState(
            research_points=100,
            research_entity=make_research_entity("BY", entity_type="backyard_observatory"),
        )
        eff = effective_tier_research_cost(tier, state)
        new_state, _ = unlock_tier(state, "ground_optical")
        assert new_state.research_points == state.research_points - eff


class TestCorporateTradeoff:
    def test_corporate_milestone_multiplier(self):
        m = get_milestone_by_id_safe("first_black_hole_candidate")
        st = ResearchState(
            turn=1,
            research_entity=make_research_entity("Corp", entity_type="corporate_research_division"),
        )
        assert effective_milestone_reward(m, st) < m.reward_research_points


def get_milestone_by_id_safe(mid: str):
    from universe.game.milestones import get_milestone_by_id

    m = get_milestone_by_id(mid)
    assert m is not None
    return m


class TestSurveyModifiers:
    def test_national_observatory_survey_reward(self):
        survey = get_survey_by_id("local_sky_survey")
        assert survey is not None
        st = ResearchState(
            research_entity=make_research_entity("Nat", entity_type="national_observatory"),
        )
        assert effective_survey_reward(survey, st) > survey.reward_research_points

    def test_citizen_science_survey_progress_bonus(self):
        scene = generate_solar_system(seed="em-csn")
        survey = get_survey_by_id("local_sky_survey")
        assert survey is not None
        state = ResearchState(
            research_entity=make_research_entity("CSN", entity_type="citizen_science_network"),
        )
        state, _ = start_survey(state, "local_sky_survey")
        state2, _ = observe_scene(scene, state)
        prog = state2.survey_progress.get("local_sky_survey")
        assert prog is not None
        assert prog.discoveries_completed >= 2


class TestCliEntityVisibility:
    def test_status_shows_background(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            p = Path("st.json")
            st = ResearchState(
                research_entity=make_research_entity("X", entity_type="university_lab"),
            )
            p.write_text(st.model_dump_json(indent=2), encoding="utf-8")
            r = runner.invoke(main, ["game", "status", "--state", str(p)])
            assert r.exit_code == 0
            assert "Peer Review" in r.output or "Background" in r.output

    def test_tech_tree_state_shows_effective_cost(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            p = Path("st.json")
            st = ResearchState(
                research_points=100,
                research_entity=make_research_entity("BY", entity_type="backyard_observatory"),
            )
            p.write_text(st.model_dump_json(indent=2), encoding="utf-8")
            r = runner.invoke(main, ["game", "tech-tree", "--state", str(p)])
            assert r.exit_code == 0
            assert "ground_optical" in r.output
            assert "Cost:" in r.output


class TestReportBackground:
    def test_report_contains_background_section(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            scene = generate_solar_system(seed="rpt")
            from universe.export.scene_json import export_scene

            export_scene(scene, "sc")
            st = ResearchState(
                research_entity=make_research_entity("R", entity_type="private_institute"),
            )
            Path("st.json").write_text(st.model_dump_json(indent=2), encoding="utf-8")
            r = runner.invoke(
                main,
                [
                    "game",
                    "report",
                    "--scene",
                    "sc/scene.json",
                    "--state",
                    "st.json",
                    "--out",
                    "rep.md",
                ],
            )
            assert r.exit_code == 0
            text = Path("rep.md").read_text(encoding="utf-8")
            assert "Research Entity Background" in text
            assert "Flexible Funding" in text
