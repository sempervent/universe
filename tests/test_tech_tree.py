"""Tests for telescope tech tree."""

from universe.game.models import ResearchState
from universe.game.tech_tree import (
    all_signal_types_for_state,
    available_signal_modes,
    available_upgrades,
    can_unlock_tier,
    get_default_tech_tree,
    get_tier_by_id,
    unlock_tier,
)


class TestTechTreeIntegrity:
    def test_unique_tier_ids(self):
        tree = get_default_tech_tree()
        ids = [t.id for t in tree]
        assert len(ids) == len(set(ids))

    def test_tier_count(self):
        tree = get_default_tech_tree()
        assert len(tree) == 12

    def test_costs_non_negative(self):
        for tier in get_default_tech_tree():
            assert tier.research_cost >= 0, f"Tier {tier.id} has negative cost"

    def test_prerequisites_reference_valid_tiers(self):
        tree = get_default_tech_tree()
        ids = {t.id for t in tree}
        for tier in tree:
            for prereq in tier.prerequisites:
                assert prereq in ids, f"Tier {tier.id} has invalid prereq: {prereq}"

    def test_now_scope_is_speculative(self):
        ns = get_tier_by_id("now_scope")
        assert ns is not None
        assert ns.speculative is True

    def test_non_speculative_tiers_not_marked(self):
        for tier in get_default_tech_tree():
            if tier.id != "now_scope":
                assert tier.speculative is False, f"Tier {tier.id} unexpectedly speculative"

    def test_later_tiers_have_more_signals_cumulatively(self):
        tree = get_default_tech_tree()
        prev_count = 0
        cumulative = set()
        for tier in sorted(tree, key=lambda t: t.tier_index):
            cumulative.update(s.value for s in tier.signal_types)
            # Cumulative signal set should grow (weakly) with tier index
            assert len(cumulative) >= prev_count
            prev_count = len(cumulative)

    def test_tier_indices_sequential(self):
        tree = get_default_tech_tree()
        indices = sorted(t.tier_index for t in tree)
        assert indices == list(range(12))

    def test_naked_eye_is_free(self):
        ne = get_tier_by_id("naked_eye")
        assert ne is not None
        assert ne.research_cost == 0
        assert ne.prerequisites == []


class TestResearchState:
    def test_default_starts_with_naked_eye(self):
        state = ResearchState()
        assert "naked_eye" in state.unlocked_tiers
        assert state.active_telescope_tier == "naked_eye"
        assert "visible_light" in state.known_signal_types

    def test_initial_signals_only_visible_light(self):
        state = ResearchState()
        modes = available_signal_modes(state)
        assert modes == ["visible_light"]
        assert "radio" not in all_signal_types_for_state(state)
        assert "infrared" not in all_signal_types_for_state(state)

    def test_unlock_adds_signal_types(self):
        state = ResearchState(research_points=50)
        state, _ = unlock_tier(state, "ground_optical")
        sigs = all_signal_types_for_state(state)
        assert "visible_light" in sigs
        state, _ = unlock_tier(state, "improved_ground")
        assert "infrared" in all_signal_types_for_state(state)

    def test_unlock_spends_points(self):
        state = ResearchState(research_points=50)
        new_state, msg = unlock_tier(state, "ground_optical")
        assert new_state.research_points == 40  # cost 10
        assert "ground_optical" in new_state.unlocked_tiers
        assert "OK" not in msg or "Unlocked" in msg

    def test_cannot_unlock_without_points(self):
        state = ResearchState(research_points=5)
        ok, reason = can_unlock_tier(state, "ground_optical")
        assert ok is False
        assert "RP" in reason or "enough" in reason.lower()

    def test_cannot_unlock_without_prerequisites(self):
        state = ResearchState(research_points=1000)
        ok, reason = can_unlock_tier(state, "space_optical")
        assert ok is False
        assert "prerequisite" in reason.lower() or "prereq" in reason.lower()

    def test_cannot_unlock_already_unlocked(self):
        state = ResearchState()
        ok, reason = can_unlock_tier(state, "naked_eye")
        assert ok is False
        assert "already" in reason.lower()

    def test_unlock_chain(self):
        state = ResearchState(research_points=100)
        state, _ = unlock_tier(state, "ground_optical")
        state, _ = unlock_tier(state, "improved_ground")
        assert "ground_optical" in state.unlocked_tiers
        assert "improved_ground" in state.unlocked_tiers
        assert state.research_points == 100 - 10 - 25

    def test_available_upgrades_initially(self):
        state = ResearchState()
        ups = available_upgrades(state)
        assert len(ups) == 1
        assert ups[0].id == "ground_optical"

    def test_available_upgrades_after_unlock(self):
        state = ResearchState(research_points=100)
        state, _ = unlock_tier(state, "ground_optical")
        ups = available_upgrades(state)
        assert any(u.id == "improved_ground" for u in ups)

    def test_state_is_immutable_on_unlock(self):
        state = ResearchState(research_points=50)
        new_state, _ = unlock_tier(state, "ground_optical")
        assert state.research_points == 50  # original unchanged
        assert "ground_optical" not in state.unlocked_tiers
