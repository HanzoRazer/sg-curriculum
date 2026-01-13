from __future__ import annotations

from uuid import uuid4

from sg_coach.coach_policy import evaluate_session
from sg_coach.models import (
    PerformanceSummary,
    ProgramRef,
    ProgramType,
    SessionRecord,
    SessionTiming,
    TimingErrorStats,
)


def _base_session(**overrides):
    sid = overrides.pop("session_id", uuid4())
    defaults = dict(
        session_id=sid,
        instrument_id="sg-000142",
        engine_version="zt-band@0.2.0",
        program_ref=ProgramRef(type=ProgramType.ztprog, name="salsa_minor_Dm", hash="sha256:abc123"),
        timing=SessionTiming(bpm=110, grid=16, strict=True, late_drop_ms=35, ghost_vel_max=22, panic_enabled=True),
        duration_s=120,
        performance=PerformanceSummary(
            bars_played=8,
            notes_expected=100,
            notes_played=100,
            notes_dropped=0,
            timing_error_ms=TimingErrorStats(mean=10.0, std=4.0, max=22.0),
            error_by_step={},
        ),
    )
    defaults.update(overrides)
    return SessionRecord(**defaults)


def test_evaluate_session_prefers_step_hotspot_focus():
    s = _base_session(
        performance=PerformanceSummary(
            bars_played=8,
            notes_expected=100,
            notes_played=100,
            notes_dropped=0,
            timing_error_ms=TimingErrorStats(mean=14.0, std=6.0, max=40.0),
            error_by_step={"7": 32.0, "3": 18.0},
        )
    )
    ev = evaluate_session(s)
    assert ev.focus_recommendation.concept == "grid_alignment"
    assert any("step 7/16" in f.interpretation for f in ev.findings)


def test_evaluate_session_uses_timing_foundation_when_mean_high():
    s = _base_session(
        performance=PerformanceSummary(
            bars_played=8,
            notes_expected=100,
            notes_played=100,
            notes_dropped=0,
            timing_error_ms=TimingErrorStats(mean=19.5, std=7.0, max=45.0),
            error_by_step={},
        )
    )
    ev = evaluate_session(s)
    assert ev.focus_recommendation.concept == "timing_foundation"
    assert any("Mean timing error" in f.interpretation for f in ev.findings)


def test_evaluate_session_records_late_drops_as_info_finding():
    s = _base_session()
    s = s.model_copy(update={"events": {"late_drops": 5, "panic_triggered": False}})
    ev = evaluate_session(s)
    assert any(f.type == "consistency" for f in ev.findings)
    assert any("Late-drops" in f.interpretation for f in ev.findings)
