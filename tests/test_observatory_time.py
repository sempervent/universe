"""Observatory local time model."""

from universe.game.models import ResearchState
from universe.game.observatory_time import (
    advance_observatory_time,
    default_observatory_time,
    is_daytime,
    set_observatory_paused,
    sun_altitude_factor,
)


class TestObservatoryTime:
    def test_default_starts_daytime(self):
        ot = default_observatory_time()
        assert ot.local_day_fraction == 0.5
        state = ResearchState()
        assert is_daytime(state)

    def test_advance_changes_fraction(self):
        state = ResearchState()
        new_state = advance_observatory_time(state, 3.0)
        assert new_state.observatory_time.local_day_fraction != 0.5

    def test_night_after_advance_to_midnight(self):
        state = ResearchState()
        state = advance_observatory_time(state, 8.0)
        assert not is_daytime(state) or sun_altitude_factor(state) < 0.2

    def test_pause(self):
        state = ResearchState()
        paused = set_observatory_paused(state, True)
        assert paused.observatory_time.paused is True
