"""
Tests for Groove Layer v0 using deterministic fixtures.

Validates:
- Vector 02: Unstable → reduce density, micro-loop, disable probes
- Vector 04: Missing tempo → freeze, no grid claims, no probes
- Vector 01: Stable → follow player (baseline)
- Vector 03: Recovery → de-escalate assist
- Vector 05: Probe A/B (multi-window)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sg_groove import GrooveLayer, PerformanceEvent, EngineContext
from sg_groove.groove_layer import process_fixture, process_multi_window_fixture


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "groove_v0"


def load_vector(name: str) -> dict:
    return json.loads((FIXTURES_DIR / "vectors" / f"{name}.json").read_text())


def load_expected(name: str) -> dict:
    return json.loads((FIXTURES_DIR / "expected" / f"{name}.json").read_text())


def load_assertions() -> dict:
    return json.loads((FIXTURES_DIR / "acceptance" / "assertions.json").read_text())


class TestVector02UnstableMicroLoop:
    """Vector 02: Unstable burst → reduce density, micro-loop, disable probes."""
    
    def test_reduces_density_on_instability(self):
        vector = load_vector("02_unstable_reduce_density_micro_loop")
        result = process_fixture(vector)
        
        assert result["controls"]["arrangement"]["density_target"] == "sparse"
    
    def test_engages_micro_loop_on_instability(self):
        vector = load_vector("02_unstable_reduce_density_micro_loop")
        result = process_fixture(vector)
        
        assert result["controls"]["loop"]["policy"] == "micro_loop"
    
    def test_disables_probes_during_instability(self):
        vector = load_vector("02_unstable_reduce_density_micro_loop")
        result = process_fixture(vector)
        
        assert result["controls"]["change_policy"]["allow_density_probes"] is False
    
    def test_uses_steady_clock_on_instability(self):
        vector = load_vector("02_unstable_reduce_density_micro_loop")
        result = process_fixture(vector)
        
        assert result["controls"]["tempo"]["policy"] == "steady_clock"


class TestVector04MissingContext:
    """Vector 04: Missing tempo/context → freeze, no grid claims, no probes."""
    
    def test_freezes_tempo_on_missing_context(self):
        vector = load_vector("04_missing_tempo_freeze_conservative")
        result = process_fixture(vector)
        
        assert result["controls"]["tempo"]["policy"] == "steady_clock"
        assert result["controls"]["tempo"]["nudge_strength"] == 0.0
        assert result["controls"]["tempo"]["max_delta_pct_per_min"] == 0
    
    def test_disables_probes_on_missing_context(self):
        vector = load_vector("04_missing_tempo_freeze_conservative")
        result = process_fixture(vector)
        
        assert result["controls"]["change_policy"]["allow_density_probes"] is False
    
    def test_no_tempo_changes_on_missing_context(self):
        vector = load_vector("04_missing_tempo_freeze_conservative")
        result = process_fixture(vector)
        
        assert result["controls"]["change_policy"]["allow_tempo_change_events"] is False


class TestVector01StableBaseline:
    """Vector 01: Stable timing → follow player, no loop."""
    
    def test_follows_player_when_stable(self):
        vector = load_vector("01_stable_follow_player")
        result = process_fixture(vector)
        
        assert result["controls"]["tempo"]["policy"] == "follow_player"
    
    def test_no_loop_when_stable(self):
        vector = load_vector("01_stable_follow_player")
        result = process_fixture(vector)
        
        assert result["controls"]["loop"]["policy"] == "none"
    
    def test_medium_density_when_stable(self):
        vector = load_vector("01_stable_follow_player")
        result = process_fixture(vector)
        
        assert result["controls"]["arrangement"]["density_target"] == "medium"
    
    def test_allows_probes_when_stable(self):
        vector = load_vector("01_stable_follow_player")
        result = process_fixture(vector)
        
        assert result["controls"]["change_policy"]["allow_density_probes"] is True


class TestVector03Recovery:
    """Vector 03: Recovery from instability → de-escalate assist."""
    
    def test_restores_density_on_recovery(self):
        vector = load_vector("03_recovery_exit_loop")
        result = process_fixture(vector)
        
        assert result["controls"]["arrangement"]["density_target"] == "medium"
    
    def test_uses_standard_assist_on_recovery(self):
        vector = load_vector("03_recovery_exit_loop")
        result = process_fixture(vector)
        
        assert result["controls"]["assist"]["assist_policy"] == "standard"
    
    def test_allows_probes_on_recovery(self):
        vector = load_vector("03_recovery_exit_loop")
        result = process_fixture(vector)
        
        assert result["controls"]["change_policy"]["allow_density_probes"] is True


class TestVector05ProbeAB:
    """Vector 05: Probe A/B — probe only when stable, revert if hurts."""
    
    def test_allows_probes_in_stable_window(self):
        vector = load_vector("05_probe_density_ab")
        results = process_multi_window_fixture(vector)
        
        window_a = results[0]
        assert window_a["controls"]["change_policy"]["allow_density_probes"] is True
    
    def test_reverts_and_disables_probes_when_hurts(self):
        vector = load_vector("05_probe_density_ab")
        results = process_multi_window_fixture(vector)
        
        window_b = results[1]
        # When probe hurts, should revert to sparse and disable probes
        assert window_b["controls"]["arrangement"]["density_target"] == "sparse"
        assert window_b["controls"]["change_policy"]["allow_density_probes"] is False


class TestAcceptanceAssertions:
    """Run all machine-checkable assertions from assertions.json."""
    
    def test_all_assertions(self):
        assertions = load_assertions()
        
        for assertion in assertions["v0_assertions"]:
            name = assertion["name"]
            when = assertion["when"]
            vector_name = when["vector"]
            
            # Load and process vector
            vector = load_vector(vector_name)
            
            if "windows" in vector:
                results = process_multi_window_fixture(vector)
                if "window" in when:
                    # Find specific window by label
                    label = when["window"]
                    result = next(r for r in results if r.get("_label") == label)
                else:
                    result = results[0]
            else:
                result = process_fixture(vector)
            
            # Check expectations
            if "expect" in assertion:
                for path, expected in assertion["expect"].items():
                    actual = self._get_nested(result, path)
                    assert actual == expected, f"{name}: {path} expected {expected}, got {actual}"
            
            if "expect_any" in assertion:
                matched = False
                for option in assertion["expect_any"]:
                    all_match = True
                    for path, expected in option.items():
                        actual = self._get_nested(result, path)
                        if actual != expected:
                            all_match = False
                            break
                    if all_match:
                        matched = True
                        break
                assert matched, f"{name}: none of expect_any options matched"
    
    def _get_nested(self, obj: dict, path: str):
        """Get nested value from dict using dot notation."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
