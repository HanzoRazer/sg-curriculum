from __future__ import annotations
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .config import RuntimeConfig
from .identity import ensure_device_identity, device_learner_id
from .db import connect, migrate
from .store import list_catalog, list_sessions, save_assignment, save_feedback, save_session
from .policy import PolicyConfig, pick_next_assignment, coach_feedback_from_session


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def init_runtime(cfg: RuntimeConfig) -> Dict[str, Any]:
    dev = ensure_device_identity(cfg.device_secret_path)
    con = connect(cfg.db_path)
    migrate(con)
    return {"device_id": dev.device_id, "db_path": str(cfg.db_path)}


def compute_assignment(cfg: RuntimeConfig, learner_slot: int = 1) -> Dict[str, Any]:
    dev = ensure_device_identity(cfg.device_secret_path)
    lrn = device_learner_id(dev, learner_slot)
    con = connect(cfg.db_path)
    migrate(con)

    catalog = list_catalog(con)
    recent = list_sessions(con, lrn, limit=20)

    items = pick_next_assignment(catalog, recent, PolicyConfig())
    payload = {
        "schema_id": "assignment",
        "schema_version": "v1",
        "created_at_utc": utc_now(),
        "device_learner_id": lrn,
        "plan_label": "practice_first_v0",
        "items": items,
    }

    assignment_id = "asg_" + uuid.uuid4().hex
    save_assignment(con, assignment_id, lrn, payload["created_at_utc"], payload)
    return payload


def ingest_session(cfg: RuntimeConfig, session_payload: Dict[str, Any], learner_slot: int = 1) -> Dict[str, Any]:
    dev = ensure_device_identity(cfg.device_secret_path)
    lrn = device_learner_id(dev, learner_slot)
    con = connect(cfg.db_path)
    migrate(con)

    # enforce device-local learner id if missing/mismatched
    session_payload = dict(session_payload)
    session_payload["device_learner_id"] = lrn

    session_id = session_payload.get("session_id") or ("ses_" + uuid.uuid4().hex)
    session_payload["session_id"] = session_id

    started = session_payload.get("started_at_utc") or utc_now()
    ended = session_payload.get("ended_at_utc") or utc_now()
    session_payload["started_at_utc"] = started
    session_payload["ended_at_utc"] = ended

    save_session(
        con,
        session_id=session_id,
        device_learner_id=lrn,
        started_at_utc=started,
        ended_at_utc=ended,
        instrument_id=session_payload.get("instrument_id"),
        session_json=session_payload,
    )

    fb = coach_feedback_from_session(session_payload)
    fb_payload = {
        "schema_id": "coach_feedback",
        "schema_version": "v1",
        "created_at_utc": utc_now(),
        "device_learner_id": lrn,
        "session_id": session_id,
        "feedback": fb,
    }
    feedback_id = "fb_" + uuid.uuid4().hex
    save_feedback(con, feedback_id, lrn, session_id, fb_payload["created_at_utc"], fb_payload)

    return {"stored_session_id": session_id, "coach_feedback": fb_payload}
