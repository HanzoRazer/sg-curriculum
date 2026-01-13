from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from sg_coach.models import (
    CoachEvaluation,
    CoachFinding,
    FindingEvidence,
    FocusRecommendation,
    Severity,
    SessionRecord,
)


@dataclass(frozen=True)
class CoachPolicyConfig:
    """
    Deterministic rules-first coach configuration.
    Keep this small and explicit; it is part of Mode-1 behavior.
    """

    # When per-step error exceeds this, treat as a targeted weakness.
    step_error_primary_ms: float = 25.0
    step_error_secondary_ms: float = 15.0

    # Global mean error thresholds
    mean_error_primary_ms: float = 18.0
    mean_error_secondary_ms: float = 12.0

    # If strict is enabled, recommend a window sized to current mean error (bounded)
    recommend_strict_window_min_ms: int = 15
    recommend_strict_window_max_ms: int = 60


DEFAULT_POLICY = CoachPolicyConfig()


def _top_k_steps(error_by_step: Dict[str, float], k: int = 3) -> List[Tuple[int, float]]:
    items: List[Tuple[int, float]] = []
    for ks, v in error_by_step.items():
        if not ks.isdigit():
            continue
        items.append((int(ks), float(v)))
    items.sort(key=lambda t: t[1], reverse=True)
    return items[:k]


def _step_label(step_i: int, grid: int) -> str:
    """
    Human label for a grid step. We keep it minimal and deterministic.
    - grid=16: 0..15  (16th steps)
    - grid=8:  0..7   (8th steps)
    """
    return f"step {step_i}/{grid}"


def evaluate_session(
    session: SessionRecord,
    *,
    coach_version: str = "coach-rules@0.1.0",
    policy: CoachPolicyConfig = DEFAULT_POLICY,
) -> CoachEvaluation:
    """
    Deterministic Mode-1 coach:
    - reads SessionRecord facts
    - emits structured CoachEvaluation

    No randomness. No LLM. No freeform analysis beyond the short interpretation strings.
    """
    perf = session.performance
    timing = session.timing

    findings: List[CoachFinding] = []
    strengths: List[str] = []
    weaknesses: List[str] = []

    # ---- 1) Global timing evaluation ----
    mean_err = float(perf.timing_error_ms.mean)
    std_err = float(perf.timing_error_ms.std)

    if mean_err <= policy.mean_error_secondary_ms:
        strengths.append("Timing mean error is low.")
    else:
        sev = Severity.primary if mean_err >= policy.mean_error_primary_ms else Severity.secondary
        weaknesses.append("Timing mean error is elevated.")
        findings.append(
            CoachFinding(
                type="timing",
                severity=sev,
                evidence=FindingEvidence(metric="timing_mean_ms", value=mean_err),
                interpretation=f"Mean timing error {mean_err:.1f} ms (std {std_err:.1f} ms).",
            )
        )

    # ---- 2) Step-local timing hotspots ----
    top_steps = _top_k_steps(perf.error_by_step, k=3)
    primary_step: Tuple[int, float] | None = None

    for step_i, step_err in top_steps:
        if step_err >= policy.step_error_primary_ms and primary_step is None:
            primary_step = (step_i, step_err)

        if step_err >= policy.step_error_secondary_ms:
            sev = Severity.primary if step_err >= policy.step_error_primary_ms else Severity.secondary
            weaknesses.append(f"Hotspot at {_step_label(step_i, timing.grid)}.")
            findings.append(
                CoachFinding(
                    type="timing",
                    severity=sev,
                    evidence=FindingEvidence(step=step_i, mean_error_ms=step_err),
                    interpretation=f"Timing hotspot: {_step_label(step_i, timing.grid)} ~ {step_err:.1f} ms.",
                )
            )

    # ---- 3) Reliability signals (late drops) ----
    if session.events.late_drops == 0:
        strengths.append("No late-drop events.")
    else:
        weaknesses.append("Late-drop events detected (ornament protection active).")
        findings.append(
            CoachFinding(
                type="consistency",
                severity=Severity.info,
                evidence=FindingEvidence(metric="late_drops", value=float(session.events.late_drops)),
                interpretation=f"Late-drops: {session.events.late_drops} (threshold {timing.late_drop_ms} ms).",
            )
        )

    # ---- Focus recommendation (single primary concept) ----
    # Default focus selection is deterministic:
    # 1) timing hotspot if available
    # 2) global timing if elevated
    # 3) otherwise consistency (tempo stability)
    if primary_step is not None:
        step_i, step_err = primary_step
        focus = FocusRecommendation(
            concept="grid_alignment",
            reason=f"Highest hotspot at {_step_label(step_i, timing.grid)} (~{step_err:.1f} ms).",
        )
        confidence = 0.90
    elif mean_err >= policy.mean_error_secondary_ms:
        focus = FocusRecommendation(
            concept="timing_foundation",
            reason=f"Mean timing error {mean_err:.1f} ms is above target.",
        )
        confidence = 0.80
    else:
        focus = FocusRecommendation(
            concept="consistency",
            reason="Timing is solid; build consistency and endurance with tempo ramps.",
        )
        confidence = 0.65

    # Keep bullets reasonably sized and deduplicate deterministically
    def _uniq(xs: List[str]) -> List[str]:
        out: List[str] = []
        seen = set()
        for x in xs:
            x2 = x.strip()
            if not x2 or x2 in seen:
                continue
            seen.add(x2)
            out.append(x2)
        return out

    strengths = _uniq(strengths)
    weaknesses = _uniq(weaknesses)

    # Ensure we always return at least one strength/weakness for UI stability
    if not strengths:
        strengths = ["Session completed."]
    if not weaknesses:
        weaknesses = ["No major issues detected."]

    return CoachEvaluation(
        session_id=session.session_id,
        coach_version=coach_version,
        findings=findings,
        strengths=strengths,
        weaknesses=weaknesses,
        focus_recommendation=focus,
        confidence=confidence,
    )
