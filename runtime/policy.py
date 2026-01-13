from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class PolicyConfig:
    # simple knobs; tune later
    default_target_minutes: int = 15
    max_items: int = 6


def pick_next_assignment(
    catalog: List[Dict[str, Any]],
    recent_sessions: List[Dict[str, Any]],
    cfg: PolicyConfig,
) -> List[Dict[str, Any]]:
    """
    v0 policy:
    - prioritize drills first (practice-first), then lessons
    - de-prioritize content seen in the last N sessions
    """
    seen: set[str] = set()
    for s in recent_sessions[:10]:
        for a in s.get("attempts", []):
            cid = a.get("content_id")
            if cid:
                seen.add(cid)

    drills = [c for c in catalog if c.get("kind") == "drill"]
    lessons = [c for c in catalog if c.get("kind") == "lesson"]

    def score(item: Dict[str, Any]) -> int:
        cid = item.get("content_id", "")
        # unseen gets higher score
        return 100 if cid not in seen else 10

    ranked = sorted(drills, key=score, reverse=True) + sorted(lessons, key=score, reverse=True)
    chosen = ranked[: cfg.max_items] if ranked else []

    items: List[Dict[str, Any]] = []
    for i, it in enumerate(chosen, start=1):
        items.append(
            {
                "content_id": it["content_id"],
                "kind": it["kind"],
                "target_minutes": cfg.default_target_minutes,
                "target_tempo_bpm": 90 if it["kind"] == "drill" else 70,
                "priority": 1 if it["kind"] == "drill" else 2,
                "why": "Unseen item (variety)" if it["content_id"] not in seen else "Reinforce recent work",
            }
        )
    return items


def coach_feedback_from_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    v0 coach:
    - reads session attempt summaries if present
    - produces structured observations + next steps
    """
    observations: List[str] = []
    next_steps: List[str] = []
    warnings: List[str] = []

    attempts = session.get("attempts", [])
    if not attempts:
        observations.append("No attempts recorded.")
        next_steps.append("Record at least one drill or lesson attempt next session.")
        return {
            "observations": observations,
            "next_steps": next_steps,
            "warnings": warnings,
            "rubric_tags": ["no_data"],
            "confidence": 0.4,
            "policy_version": "policy_v0"
        }

    # Aggregate simple signals
    accs = []
    p95s = []
    for a in attempts:
        summ = a.get("summary") or {}
        if "note_accuracy_percent" in summ:
            accs.append(float(summ["note_accuracy_percent"]))
        if "timing_error_ms_p95" in summ:
            p95s.append(float(summ["timing_error_ms_p95"]))

    if accs:
        avg_acc = sum(accs) / max(1, len(accs))
        observations.append(f"Average note accuracy ≈ {avg_acc:.1f}%.")
        if avg_acc < 75:
            next_steps.append("Slow down 10–15 BPM and aim for clean fretting and consistent picking.")
            warnings.append("Accuracy under 75% suggests tempo is too high or fingering is unstable.")
        else:
            next_steps.append("Increase tempo by 5 BPM on the best-performing drill.")

    if p95s:
        avg_p95 = sum(p95s) / max(1, len(p95s))
        observations.append(f"Timing stability (p95 error) ≈ {avg_p95:.0f} ms.")
        if avg_p95 > 80:
            next_steps.append("Use a click and focus on downbeat alignment for 2 minutes per drill.")
            warnings.append("Timing drift is high; prioritize metronome work.")
        else:
            next_steps.append("Add a 2-minute groove loop at current tempo to build endurance.")

    if not accs and not p95s:
        observations.append("Session captured attempts but no summary metrics.")
        next_steps.append("Enable summary metrics capture (timing/accuracy) when available.")
        return {
            "observations": observations,
            "next_steps": next_steps,
            "warnings": warnings,
            "rubric_tags": ["metrics_missing"],
            "confidence": 0.5,
            "policy_version": "policy_v0"
        }

    tags = []
    if accs and (sum(accs)/len(accs)) < 75:
        tags.append("accuracy_low")
    if p95s and (sum(p95s)/len(p95s)) > 80:
        tags.append("timing_unstable")
    if not tags:
        tags.append("steady_progress")

    return {
        "observations": observations,
        "next_steps": next_steps,
        "warnings": warnings,
        "rubric_tags": tags,
        "confidence": 0.7,
        "policy_version": "policy_v0"
    }
