"""
Data models for Groove Layer v0.

These match the minimal event shape from the spec:
- t_onset_ms, event_type, strength, confidence
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    note_onset = "note_onset"
    strum_onset = "strum_onset"
    percussive_onset = "percussive_onset"


class TempoPolicy(str, Enum):
    follow_player = "follow_player"
    steady_clock = "steady_clock"
    gentle_nudge = "gentle_nudge"


class DensityTarget(str, Enum):
    sparse = "sparse"
    medium = "medium"
    full = "full"


class LoopPolicy(str, Enum):
    none = "none"
    micro_loop = "micro_loop"
    loop_section = "loop_section"


class AssistPolicy(str, Enum):
    minimal = "minimal"
    standard = "standard"
    supportive = "supportive"


@dataclass(frozen=True)
class PerformanceEvent:
    """A single onset event from the extractor."""
    t_onset_ms: int
    event_type: EventType
    strength: float  # 0.0–1.0
    confidence: float  # 0.0–1.0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PerformanceEvent:
        return cls(
            t_onset_ms=int(d["t_onset_ms"]),
            event_type=EventType(d["event_type"]),
            strength=float(d["strength"]),
            confidence=float(d["confidence"]),
        )


@dataclass(frozen=True)
class EngineContext:
    """Context from the engine host (tempo, grid, feel)."""
    tempo_bpm_target: float
    time_signature: str
    grid: str  # "quarter", "eighth", "sixteenth", "triplet"
    feel: str  # "straight", "swing", "hybrid"
    bar_position: Optional[float] = None
    section_id: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional[EngineContext]:
        if d is None:
            return None
        return cls(
            tempo_bpm_target=float(d["tempo_bpm_target"]),
            time_signature=str(d["time_signature"]),
            grid=str(d["grid"]),
            feel=str(d["feel"]),
            bar_position=d.get("bar_position"),
            section_id=d.get("section_id"),
        )


@dataclass(frozen=True)
class WindowStats:
    """Computed statistics for a single window."""
    event_count: int
    mean_confidence: float
    window_confidence: float  # gated by event count
    onset_interval_variance_ms: float  # stability proxy
    is_stable: bool


@dataclass
class GrooveState:
    """Internal state for the Groove Layer (fast + slow)."""
    # Fast state (session-only)
    last_window_stats: Optional[WindowStats] = None
    consecutive_unstable_windows: int = 0
    consecutive_stable_windows: int = 0
    
    # Control hysteresis
    last_density: DensityTarget = DensityTarget.medium
    last_loop_policy: LoopPolicy = LoopPolicy.none
    last_tempo_policy: TempoPolicy = TempoPolicy.follow_player
    
    # Probing state
    probe_active: bool = False
    probe_start_window: int = 0
    windows_since_last_probe: int = 0
    
    # Slow traits (cross-session, not implemented yet)
    latents_v0: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class GrooveLayerConfig:
    """Configuration knobs for the Groove Layer."""
    # Window parameters
    window_duration_ms: int = 15000
    min_events_per_window: int = 12
    
    # Stability thresholds
    stability_variance_threshold_ms: float = 50.0  # below = stable
    low_confidence_threshold: float = 0.6
    
    # Hysteresis
    windows_to_confirm_stability: int = 2
    windows_to_confirm_instability: int = 1
    
    # Probing
    min_windows_between_probes: int = 6
    probe_duration_windows: int = 2
