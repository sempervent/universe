"""Telescope tech tree — 12 tiers from naked eye to now-scope.

Each tier unlocks new instruments and signal types.  Signal access is
cumulative: unlocking Tier 4 (radio) does not remove optical capability.
"""

from __future__ import annotations

from universe.game.entity import get_entity_modifier
from universe.game.models import (
    InstrumentType,
    ResearchState,
    SignalType,
    TelescopeTier,
)

# Early ground optical tiers (backyard_observatory discount applies here only).
EARLY_OPTICAL_TIER_IDS: frozenset[str] = frozenset({"ground_optical", "improved_ground"})


def get_default_tech_tree() -> list[TelescopeTier]:
    return [
        TelescopeTier(
            id="naked_eye",
            name="Naked Eye / Ancient Sky",
            tier_index=0,
            instrument_types=[InstrumentType.NAKED_EYE],
            signal_types=[SignalType.VISIBLE_LIGHT],
            description="Unaided human vision. Detects bright planets, stars, and the Milky Way band.",
            research_cost=0,
            prerequisites=[],
            unlocks=["ground_optical"],
            resolution_arcsec=60.0,
            sensitivity=0.05,
            max_effective_distance_mpc=0.001,
            atmosphere_penalty=0.4,
        ),
        TelescopeTier(
            id="ground_optical",
            name="Ground Optical Telescope",
            tier_index=1,
            instrument_types=[InstrumentType.OPTICAL_TELESCOPE],
            signal_types=[SignalType.VISIBLE_LIGHT],
            description="Basic refracting/reflecting telescope. Reveals lunar detail, planet disks, bright nebulae.",
            research_cost=10,
            prerequisites=["naked_eye"],
            unlocks=["improved_ground"],
            resolution_arcsec=2.0,
            sensitivity=0.15,
            max_effective_distance_mpc=10.0,
            atmosphere_penalty=0.5,
        ),
        TelescopeTier(
            id="improved_ground",
            name="Improved Ground Observatory",
            tier_index=2,
            instrument_types=[InstrumentType.OPTICAL_TELESCOPE],
            signal_types=[SignalType.VISIBLE_LIGHT, SignalType.INFRARED],
            description="Adaptive optics, larger aperture. Detects faint galaxies, asteroids, outer planets.",
            research_cost=25,
            prerequisites=["ground_optical"],
            unlocks=["space_optical"],
            resolution_arcsec=1.0,
            sensitivity=0.3,
            max_effective_distance_mpc=100.0,
            atmosphere_penalty=0.6,
        ),
        TelescopeTier(
            id="space_optical",
            name="Space Optical Telescope",
            tier_index=3,
            instrument_types=[InstrumentType.SPACE_TELESCOPE],
            signal_types=[SignalType.VISIBLE_LIGHT, SignalType.INFRARED, SignalType.ULTRAVIOLET],
            description="No atmosphere. Deep-field imaging, quasar detection, galaxy morphology.",
            research_cost=60,
            prerequisites=["improved_ground"],
            unlocks=["radio"],
            resolution_arcsec=0.05,
            sensitivity=0.5,
            max_effective_distance_mpc=5000.0,
            atmosphere_penalty=1.0,
        ),
        TelescopeTier(
            id="radio",
            name="Radio Telescope",
            tier_index=4,
            instrument_types=[InstrumentType.RADIO_TELESCOPE],
            signal_types=[SignalType.RADIO, SignalType.MICROWAVE],
            description="Detects pulsars, neutral hydrogen, radio galaxies, quasar jets, CMB anisotropy.",
            research_cost=80,
            prerequisites=["space_optical"],
            unlocks=["xray_gamma"],
            resolution_arcsec=1.0,
            sensitivity=0.45,
            max_effective_distance_mpc=3000.0,
            atmosphere_penalty=0.9,
        ),
        TelescopeTier(
            id="xray_gamma",
            name="X-ray / Gamma Observatory",
            tier_index=5,
            instrument_types=[InstrumentType.XRAY_OBSERVATORY, InstrumentType.GAMMA_OBSERVATORY],
            signal_types=[SignalType.XRAY, SignalType.GAMMA_RAY],
            description="High-energy photons. Reveals magnetars, accretion disks, BH candidates, GRBs.",
            research_cost=120,
            prerequisites=["radio"],
            unlocks=["interferometer"],
            resolution_arcsec=0.5,
            sensitivity=0.55,
            max_effective_distance_mpc=2000.0,
            atmosphere_penalty=1.0,
        ),
        TelescopeTier(
            id="interferometer",
            name="Interferometer Array",
            tier_index=6,
            instrument_types=[InstrumentType.INTERFEROMETER],
            signal_types=[SignalType.VISIBLE_LIGHT, SignalType.INFRARED, SignalType.RADIO],
            description="Combined baselines for extreme resolution. Black hole shadows, stellar surfaces.",
            research_cost=180,
            prerequisites=["xray_gamma"],
            unlocks=["gravitational_wave"],
            resolution_arcsec=0.00001,
            sensitivity=0.6,
            max_effective_distance_mpc=5000.0,
            atmosphere_penalty=0.8,
        ),
        TelescopeTier(
            id="gravitational_wave",
            name="Gravitational-Wave Observatory",
            tier_index=7,
            instrument_types=[InstrumentType.GRAVITATIONAL_WAVE_DETECTOR],
            signal_types=[SignalType.GRAVITATIONAL_WAVE],
            description="Spacetime strain detection. BH mergers, NS mergers, compact binary inspiral.",
            research_cost=250,
            prerequisites=["interferometer"],
            unlocks=["neutrino_cosmic_ray"],
            resolution_arcsec=3600.0,
            sensitivity=0.5,
            max_effective_distance_mpc=10000.0,
            atmosphere_penalty=1.0,
        ),
        TelescopeTier(
            id="neutrino_cosmic_ray",
            name="Neutrino / Cosmic-Ray Observatory",
            tier_index=8,
            instrument_types=[InstrumentType.NEUTRINO_DETECTOR, InstrumentType.COSMIC_RAY_DETECTOR],
            signal_types=[SignalType.NEUTRINO, SignalType.COSMIC_RAY],
            description="Particle astronomy. Core-collapse SN neutrinos, cosmic accelerators.",
            research_cost=325,
            prerequisites=["gravitational_wave"],
            unlocks=["multi_messenger"],
            resolution_arcsec=3600.0,
            sensitivity=0.4,
            max_effective_distance_mpc=1000.0,
            atmosphere_penalty=1.0,
        ),
        TelescopeTier(
            id="multi_messenger",
            name="Multi-Messenger Observatory",
            tier_index=9,
            instrument_types=[
                InstrumentType.OPTICAL_TELESCOPE, InstrumentType.SPACE_TELESCOPE,
                InstrumentType.RADIO_TELESCOPE, InstrumentType.XRAY_OBSERVATORY,
                InstrumentType.GAMMA_OBSERVATORY, InstrumentType.INTERFEROMETER,
                InstrumentType.GRAVITATIONAL_WAVE_DETECTOR,
                InstrumentType.NEUTRINO_DETECTOR, InstrumentType.COSMIC_RAY_DETECTOR,
            ],
            signal_types=[
                SignalType.VISIBLE_LIGHT, SignalType.INFRARED, SignalType.ULTRAVIOLET,
                SignalType.RADIO, SignalType.MICROWAVE, SignalType.XRAY, SignalType.GAMMA_RAY,
                SignalType.GRAVITATIONAL_WAVE, SignalType.NEUTRINO, SignalType.COSMIC_RAY,
            ],
            description="All real instruments combined. Cross-correlation confirms multi-signal events.",
            research_cost=420,
            prerequisites=["neutrino_cosmic_ray"],
            unlocks=["dark_matter_mapper"],
            resolution_arcsec=0.00001,
            sensitivity=0.8,
            max_effective_distance_mpc=10000.0,
            atmosphere_penalty=1.0,
        ),
        TelescopeTier(
            id="dark_matter_mapper",
            name="Dark Matter / Weak-Lensing Observatory",
            tier_index=10,
            instrument_types=[InstrumentType.WEAK_LENSING_MAPPER, InstrumentType.DARK_MATTER_OBSERVATORY],
            signal_types=[SignalType.WEAK_LENSING, SignalType.DARK_MATTER_INFERENCE],
            description="Statistical mass mapping. Dark matter halos, cosmic web mass distribution.",
            research_cost=580,
            prerequisites=["multi_messenger"],
            unlocks=["now_scope"],
            resolution_arcsec=10.0,
            sensitivity=0.7,
            max_effective_distance_mpc=10000.0,
            atmosphere_penalty=1.0,
        ),
        TelescopeTier(
            id="now_scope",
            name="Now-Scope (Speculative)",
            tier_index=11,
            instrument_types=[InstrumentType.NOW_SCOPE],
            signal_types=[SignalType.SPECULATIVE_NOW_SIGNAL],
            description=(
                "Fictional causality-independent observatory. Observes the current state "
                "of distant objects rather than light from the past. Speculative endgame."
            ),
            research_cost=780,
            prerequisites=["dark_matter_mapper"],
            unlocks=[],
            resolution_arcsec=0.0,
            sensitivity=1.0,
            max_effective_distance_mpc=100000.0,
            atmosphere_penalty=1.0,
            speculative=True,
        ),
    ]


_TREE_CACHE: list[TelescopeTier] | None = None


def _tree() -> list[TelescopeTier]:
    global _TREE_CACHE
    if _TREE_CACHE is None:
        _TREE_CACHE = get_default_tech_tree()
    return _TREE_CACHE


def get_tier_by_id(tier_id: str) -> TelescopeTier | None:
    return next((t for t in _tree() if t.id == tier_id), None)


def is_space_track_tier(tier: TelescopeTier) -> bool:
    """Tiers from space_optical onward in the default tree (tier_index ≥ 3)."""
    return tier.tier_index >= 3


def effective_tier_research_cost(tier: TelescopeTier, state: ResearchState) -> int:
    """RP cost after entity background modifiers (matches charged amount on unlock)."""
    mod = get_entity_modifier(state.research_entity.entity_type)
    cost = float(tier.research_cost)
    cost *= mod.upgrade_cost_multiplier
    if tier.id in EARLY_OPTICAL_TIER_IDS:
        cost *= mod.early_optical_upgrade_cost_multiplier
    if is_space_track_tier(tier):
        cost *= mod.space_upgrade_cost_multiplier
    return max(0, int(round(cost)))


def all_signal_types_for_state(state: ResearchState) -> set[str]:
    """Return cumulative set of signal types across all unlocked tiers."""
    signals: set[str] = set()
    for tier_id in state.unlocked_tiers:
        tier = get_tier_by_id(tier_id)
        if tier:
            signals.update(s.value for s in tier.signal_types)
    return signals


def best_sensitivity_for_state(state: ResearchState) -> float:
    """Return the highest sensitivity among all unlocked tiers."""
    best = 0.0
    for tier_id in state.unlocked_tiers:
        tier = get_tier_by_id(tier_id)
        if tier:
            best = max(best, tier.sensitivity)
    return best


def best_resolution_for_state(state: ResearchState) -> float:
    """Return the best (lowest) resolution among all unlocked tiers."""
    best = 99999.0
    for tier_id in state.unlocked_tiers:
        tier = get_tier_by_id(tier_id)
        if tier:
            best = min(best, tier.resolution_arcsec)
    return best


def max_distance_for_state(state: ResearchState) -> float:
    """Return the greatest effective distance among all unlocked tiers."""
    best = 0.0
    for tier_id in state.unlocked_tiers:
        tier = get_tier_by_id(tier_id)
        if tier:
            best = max(best, tier.max_effective_distance_mpc)
    return best


def available_upgrades(state: ResearchState) -> list[TelescopeTier]:
    """Return tiers the player could unlock next (prerequisites met, not yet unlocked)."""
    unlocked = set(state.unlocked_tiers)
    upgrades = []
    for tier in _tree():
        if tier.id in unlocked:
            continue
        if all(p in unlocked for p in tier.prerequisites):
            upgrades.append(tier)
    return upgrades


def can_unlock_tier(state: ResearchState, tier_id: str) -> tuple[bool, str]:
    """Check if a tier can be unlocked.  Returns (ok, reason)."""
    tier = get_tier_by_id(tier_id)
    if tier is None:
        return False, f"Unknown tier: {tier_id}"
    if tier_id in state.unlocked_tiers:
        return False, f"Tier '{tier.name}' is already unlocked"
    for prereq in tier.prerequisites:
        if prereq not in state.unlocked_tiers:
            return False, f"Missing prerequisite: {prereq}"
    eff = effective_tier_research_cost(tier, state)
    if state.research_points < eff:
        return False, f"Not enough RP: need {eff}, have {state.research_points}"
    return True, "OK"


def unlock_tier(state: ResearchState, tier_id: str) -> tuple[ResearchState, str]:
    """Attempt to unlock a tier.  Returns (new_state, message).

    The returned state is a new object; the input is not mutated.
    """
    ok, reason = can_unlock_tier(state, tier_id)
    if not ok:
        return state, reason

    tier = get_tier_by_id(tier_id)
    assert tier is not None

    eff_cost = effective_tier_research_cost(tier, state)
    new_unlocked = list(state.unlocked_tiers) + [tier_id]
    new_signals = set(state.known_signal_types)
    new_signals.update(s.value for s in tier.signal_types)

    new_state = state.model_copy(
        update={
            "research_points": state.research_points - eff_cost,
            "unlocked_tiers": new_unlocked,
            "active_telescope_tier": tier_id,
            "known_signal_types": sorted(new_signals),
        }
    )
    return new_state, f"Unlocked '{tier.name}'. Active telescope set to {tier_id}."
