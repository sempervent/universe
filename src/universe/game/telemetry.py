"""Playtest telemetry models — machine-readable balance instrumentation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from universe.game.models import ResearchState


class PlaytestEvent(BaseModel):
    """Single instrumented action during an autoplay run."""

    turn: int
    event_type: str
    entity_type: str
    active_telescope_tier: str
    active_survey_id: str | None = None
    research_points_before: int
    research_points_after: int
    delta_research_points: int
    object_id: str | None = None
    object_type: str | None = None
    object_name: str | None = None
    confidence: float | None = None
    survey_id: str | None = None
    milestone_id: str | None = None
    tier_id: str | None = None
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_state_delta(
        cls,
        *,
        turn: int,
        event_type: str,
        entity_type: str,
        state_before: ResearchState,
        state_after: ResearchState,
        message: str = "",
        **fields: Any,
    ) -> PlaytestEvent:
        rp_before = state_before.research_points
        rp_after = state_after.research_points
        return cls(
            turn=turn,
            event_type=event_type,
            entity_type=entity_type,
            active_telescope_tier=state_after.active_telescope_tier,
            active_survey_id=state_after.active_survey_id,
            research_points_before=rp_before,
            research_points_after=rp_after,
            delta_research_points=rp_after - rp_before,
            message=message,
            **fields,
        )


class PlaytestRun(BaseModel):
    """Complete deterministic autoplay session."""

    id: str
    seed: str
    entity_name: str
    entity_type: str
    scenario_id: str
    started_at: str | None = None
    events: list[PlaytestEvent] = Field(default_factory=list)
    final_state: ResearchState | dict[str, Any]
    summary: dict[str, Any] = Field(default_factory=dict)

    def model_dump_json(self, *, indent: int | None = 2, **kwargs: Any) -> str:
        return super().model_dump_json(indent=indent, **kwargs)

    @staticmethod
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
