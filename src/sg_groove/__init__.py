"""
Groove Layer v0 — Accompaniment Adaptation Engine.

Converts player performance events into real-time accompaniment control.
Separate from coaching (no pedagogy objects here).
"""
from .models import (
    PerformanceEvent,
    EngineContext,
    WindowStats,
    GrooveState,
)
from .groove_layer import GrooveLayer
from .window_eval import compute_window_stats

__all__ = [
    "PerformanceEvent",
    "EngineContext",
    "WindowStats",
    "GrooveState",
    "GrooveLayer",
    "compute_window_stats",
]
