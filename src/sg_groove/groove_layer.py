"""
Groove Layer v0 — Main engine.

Converts performance events + engine context into accompaniment controls.
This is a deterministic, rules-first implementation (Mode-1).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    AssistPolicy,
    DensityTarget,
    EngineContext,
    GrooveLayerConfig,
    GrooveState,
    LoopPolicy,
    PerformanceEvent,
    TempoPolicy,
    WindowStats,
)
from .window_eval import compute_window_stats


class GrooveLayer:
    """
    Groove Layer v0 engine.
    
    Consumes performance events and engine context,
    emits groove_layer_control_v0 messages.
    """
    
    def __init__(
        self,
        device_id: str,
        session_id: str,
        config: GrooveLayerConfig = GrooveLayerConfig(),
    ):
        self.device_id = device_id
        self.session_id = session_id
        self.config = config
        self.state = GrooveState()
    
    def update_window(
        self,
        events: List[PerformanceEvent],
        engine_context: Optional[EngineContext],
        prior_state_hint: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a window of events and emit control output.
        
        Args:
            events: Performance events for this window
            engine_context: Tempo/grid/feel context (or None if missing)
            prior_state_hint: Optional hint for testing recovery scenarios
            
        Returns:
            groove_layer_control_v0 message
        """
        # Apply prior state hint if provided (for testing)
        if prior_state_hint:
            self._apply_prior_state_hint(prior_state_hint)
        
        # Compute window statistics
        stats = compute_window_stats(events, self.config)
        
        # Determine controls based on state
        controls = self._compute_controls(stats, engine_context)
        
        # Update internal state
        self._update_state(stats)
        
        # Build output message
        return self._build_output(stats, controls, engine_context)
    
    def _apply_prior_state_hint(self, hint: Dict[str, Any]) -> None:
        """Apply prior state hint for testing scenarios."""
        if "last_loop_policy" in hint:
            self.state.last_loop_policy = LoopPolicy(hint["last_loop_policy"])
        if "last_density" in hint:
            self.state.last_density = DensityTarget(hint["last_density"])
        # Imply we were unstable if we were in micro_loop
        if self.state.last_loop_policy == LoopPolicy.micro_loop:
            self.state.consecutive_unstable_windows = 1
    
    def _compute_controls(
        self,
        stats: WindowStats,
        engine_context: Optional[EngineContext],
    ) -> Dict[str, Any]:
        """
        Compute control intents based on window stats and context.
        
        This is the core policy logic:
        1. Missing context → freeze, conservative
        2. Unstable → reduce density, micro-loop, disable probing
        3. Stable → follow player, allow probing
        """
        # Case 1: Missing engine context — freeze and stay conservative
        if engine_context is None:
            return self._frozen_controls()
        
        # Case 2: Unstable window — degradation behavior
        if not stats.is_stable:
            self.state.consecutive_unstable_windows += 1
            self.state.consecutive_stable_windows = 0
            return self._unstable_controls(stats)
        
        # Case 3: Stable window — check for recovery or baseline
        self.state.consecutive_stable_windows += 1
        self.state.consecutive_unstable_windows = 0
        
        # Recovery: was unstable, now stable
        if self.state.last_loop_policy == LoopPolicy.micro_loop:
            return self._recovery_controls(stats, engine_context)
        
        # Baseline stable: follow player
        return self._stable_controls(stats, engine_context)
    
    def _frozen_controls(self) -> Dict[str, Any]:
        """Controls when engine context is missing — fail boringly."""
        return {
            "tempo": {
                "policy": TempoPolicy.steady_clock.value,
                "nudge_strength": 0.0,
                "max_delta_pct_per_min": 0,
            },
            "arrangement": {
                "density_target": DensityTarget.medium.value,
                "instrumentation_policy": "keep_layers",
                "dynamics_follow": "fixed",
            },
            "loop": {
                "policy": LoopPolicy.none.value,
                "length_bars": 4,
                "exit_condition": "manual",
            },
            "feel": {
                "feel_policy": "straight",
                "grid": "quarter",  # conservative, no grid claims
                "click_policy": "off",
            },
            "assist": {
                "assist_policy": AssistPolicy.minimal.value,
                "ghost_drums": "off",
                "count_in_bars": 0,
            },
            "change_policy": {
                "allow_modulation": False,
                "allow_tempo_change_events": False,
                "allow_density_probes": False,
            },
            "_rationale": {
                "trigger": "missing_context",
                "notes": "No engine context; freezing corrective behavior to avoid wrong claims.",
            },
        }
    
    def _unstable_controls(self, stats: WindowStats) -> Dict[str, Any]:
        """Controls when player is unstable — support and simplify."""
        return {
            "tempo": {
                "policy": TempoPolicy.steady_clock.value,
                "nudge_strength": 0.4,
                "max_delta_pct_per_min": 3,
            },
            "arrangement": {
                "density_target": DensityTarget.sparse.value,
                "instrumentation_policy": "reduce_layers",
                "dynamics_follow": "fixed",
            },
            "loop": {
                "policy": LoopPolicy.micro_loop.value,
                "length_bars": 4,
                "exit_condition": "stability_recovered",
            },
            "feel": {
                "feel_policy": "straight",
                "grid": "eighth",
                "click_policy": "prominent",
            },
            "assist": {
                "assist_policy": AssistPolicy.supportive.value,
                "ghost_drums": "light",
                "count_in_bars": 2,
            },
            "change_policy": {
                "allow_modulation": False,
                "allow_tempo_change_events": False,
                "allow_density_probes": False,
            },
            "_rationale": {
                "trigger": "low_tempo_stability",
                "notes": "Detected instability; simplifying and gating changes until stable.",
            },
        }
    
    def _recovery_controls(
        self,
        stats: WindowStats,
        engine_context: EngineContext,
    ) -> Dict[str, Any]:
        """Controls when recovering from instability — de-escalate gradually."""
        # Use hysteresis: require multiple stable windows before full recovery
        if self.state.consecutive_stable_windows < self.config.windows_to_confirm_stability:
            # Still in recovery, but improving
            return {
                "tempo": {
                    "policy": TempoPolicy.follow_player.value,
                    "nudge_strength": 0.25,
                    "max_delta_pct_per_min": 5,
                },
                "arrangement": {
                    "density_target": DensityTarget.medium.value,
                    "instrumentation_policy": "keep_layers",
                    "dynamics_follow": "soft_follow",
                },
                "loop": {
                    "policy": LoopPolicy.loop_section.value,
                    "length_bars": 4,
                    "exit_condition": "stability_recovered",
                },
                "feel": {
                    "feel_policy": engine_context.feel,
                    "grid": engine_context.grid,
                    "click_policy": "subtle",
                },
                "assist": {
                    "assist_policy": AssistPolicy.standard.value,
                    "ghost_drums": "off",
                    "count_in_bars": 0,
                },
                "change_policy": {
                    "allow_modulation": False,
                    "allow_tempo_change_events": True,
                    "allow_density_probes": True,
                },
                "_rationale": {
                    "trigger": "stability_recovering",
                    "notes": "Stability recovered; relaxing assist and restoring density.",
                },
            }
        
        # Fully recovered
        return self._stable_controls(stats, engine_context)
    
    def _stable_controls(
        self,
        stats: WindowStats,
        engine_context: EngineContext,
    ) -> Dict[str, Any]:
        """Controls when player is stable — follow and allow exploration."""
        return {
            "tempo": {
                "policy": TempoPolicy.follow_player.value,
                "nudge_strength": 0.2,
                "max_delta_pct_per_min": 5,
            },
            "arrangement": {
                "density_target": DensityTarget.medium.value,
                "instrumentation_policy": "keep_layers",
                "dynamics_follow": "soft_follow",
            },
            "loop": {
                "policy": LoopPolicy.none.value,
                "length_bars": 4,
                "exit_condition": "manual",
            },
            "feel": {
                "feel_policy": engine_context.feel,
                "grid": engine_context.grid,
                "click_policy": "subtle",
            },
            "assist": {
                "assist_policy": AssistPolicy.standard.value,
                "ghost_drums": "off",
                "count_in_bars": 1,
            },
            "change_policy": {
                "allow_modulation": False,
                "allow_tempo_change_events": True,
                "allow_density_probes": True,
            },
            "_rationale": {
                "trigger": "stable_baseline",
                "notes": "Baseline stable play; no corrective action required.",
            },
        }
    
    def _update_state(self, stats: WindowStats) -> None:
        """Update internal state after processing a window."""
        self.state.last_window_stats = stats
        
        # Update hysteresis tracking
        if stats.is_stable:
            self.state.last_density = DensityTarget.medium
            if self.state.last_loop_policy == LoopPolicy.micro_loop:
                self.state.last_loop_policy = LoopPolicy.loop_section
            elif self.state.consecutive_stable_windows >= self.config.windows_to_confirm_stability:
                self.state.last_loop_policy = LoopPolicy.none
            self.state.last_tempo_policy = TempoPolicy.follow_player
        else:
            self.state.last_density = DensityTarget.sparse
            self.state.last_loop_policy = LoopPolicy.micro_loop
            self.state.last_tempo_policy = TempoPolicy.steady_clock
    
    def _build_output(
        self,
        stats: WindowStats,
        controls: Dict[str, Any],
        engine_context: Optional[EngineContext],
    ) -> Dict[str, Any]:
        """Build the groove_layer_control_v0 output message."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Extract rationale before building controls
        rationale = controls.pop("_rationale", {"trigger": "unknown", "notes": ""})
        
        return {
            "schema_id": "groove_layer_control",
            "schema_version": "v0",
            "emitted_at_utc": now,
            "device_id": self.device_id,
            "session_id": self.session_id,
            "window": {
                "window_start_utc": now,  # simplified for v0
                "window_end_utc": now,
                "duration_ms": self.config.window_duration_ms,
                "event_count": stats.event_count,
                "confidence": round(stats.window_confidence, 2),
            },
            "controls": controls,
            "rationale": {
                "trigger": rationale.get("trigger", "manual_override"),
                "notes": rationale.get("notes", ""),
            },
        }


def process_fixture(fixture: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to process a test fixture.
    
    Args:
        fixture: A test vector from fixtures/groove_v0/vectors/
        
    Returns:
        groove_layer_control_v0 message
    """
    device_id = fixture["device_id"]
    session_id = fixture["session_id"]
    
    engine_context = EngineContext.from_dict(fixture.get("engine_context"))
    events = [PerformanceEvent.from_dict(e) for e in fixture.get("events", [])]
    prior_state_hint = fixture.get("prior_state_hint")
    
    layer = GrooveLayer(device_id, session_id)
    return layer.update_window(events, engine_context, prior_state_hint)


def process_multi_window_fixture(fixture: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process a multi-window fixture (like vector 05).
    
    Args:
        fixture: A test vector with "windows" array
        
    Returns:
        List of groove_layer_control_v0 messages, one per window
    """
    device_id = fixture["device_id"]
    session_id = fixture["session_id"]
    engine_context = EngineContext.from_dict(fixture.get("engine_context"))
    
    layer = GrooveLayer(device_id, session_id)
    results = []
    
    for window in fixture.get("windows", []):
        events = [PerformanceEvent.from_dict(e) for e in window.get("events", [])]
        result = layer.update_window(events, engine_context)
        result["_label"] = window.get("label", "")
        results.append(result)
    
    return results
