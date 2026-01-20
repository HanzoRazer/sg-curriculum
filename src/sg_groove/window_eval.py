"""
Window evaluator for Groove Layer v0.

Computes per-window statistics from performance events.
No learning here—just evidence extraction.
"""
from __future__ import annotations

import statistics
from typing import List, Optional

from .models import (
    GrooveLayerConfig,
    PerformanceEvent,
    WindowStats,
)


def compute_window_stats(
    events: List[PerformanceEvent],
    config: GrooveLayerConfig = GrooveLayerConfig(),
) -> WindowStats:
    """
    Compute window statistics from a list of events.
    
    Returns a WindowStats with:
    - event_count
    - mean_confidence
    - window_confidence (gated by event count)
    - onset_interval_variance_ms (stability proxy)
    - is_stable (based on variance threshold)
    """
    event_count = len(events)
    
    # No events = maximally uncertain
    if event_count == 0:
        return WindowStats(
            event_count=0,
            mean_confidence=0.0,
            window_confidence=0.0,
            onset_interval_variance_ms=float("inf"),
            is_stable=False,
        )
    
    # Mean confidence of events
    mean_confidence = sum(e.confidence for e in events) / event_count
    
    # Gate confidence by event count
    # Below min_events, scale down confidence proportionally
    count_factor = min(1.0, event_count / config.min_events_per_window)
    window_confidence = mean_confidence * count_factor
    
    # Compute onset interval variance (stability proxy)
    if event_count < 2:
        onset_interval_variance_ms = float("inf")
    else:
        sorted_events = sorted(events, key=lambda e: e.t_onset_ms)
        intervals = [
            sorted_events[i + 1].t_onset_ms - sorted_events[i].t_onset_ms
            for i in range(len(sorted_events) - 1)
        ]
        if len(intervals) >= 2:
            onset_interval_variance_ms = statistics.variance(intervals)
        else:
            onset_interval_variance_ms = 0.0
    
    # Determine stability
    is_stable = (
        event_count >= config.min_events_per_window
        and window_confidence >= config.low_confidence_threshold
        and onset_interval_variance_ms <= config.stability_variance_threshold_ms
    )
    
    return WindowStats(
        event_count=event_count,
        mean_confidence=mean_confidence,
        window_confidence=window_confidence,
        onset_interval_variance_ms=onset_interval_variance_ms,
        is_stable=is_stable,
    )
