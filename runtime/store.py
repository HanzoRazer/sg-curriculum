from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CatalogItem:
    content_id: str
    kind: str
    title: str
    summary: str
    tags: List[str]
    updated_at_utc: str


def upsert_catalog(con: sqlite3.Connection, updated_at_utc: str, items: List[CatalogItem]) -> None:
    for it in items:
        con.execute(
            """
            INSERT INTO catalog(content_id, kind, title, summary, tags_json, updated_at_utc)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(content_id) DO UPDATE SET
              kind=excluded.kind,
              title=excluded.title,
              summary=excluded.summary,
              tags_json=excluded.tags_json,
              updated_at_utc=excluded.updated_at_utc
            """,
            (it.content_id, it.kind, it.title, it.summary, json.dumps(it.tags), updated_at_utc),
        )
    con.commit()


def list_catalog(con: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = con.execute("SELECT * FROM catalog ORDER BY kind, title").fetchall()
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "content_id": r["content_id"],
                "kind": r["kind"],
                "title": r["title"],
                "summary": r["summary"] or "",
                "tags": json.loads(r["tags_json"] or "[]"),
                "updated_at_utc": r["updated_at_utc"],
            }
        )
    return out


def save_session(con: sqlite3.Connection, session_id: str, device_learner_id: str, started_at_utc: str,
                 ended_at_utc: str, instrument_id: Optional[str], session_json: Dict[str, Any]) -> None:
    con.execute(
        """
        INSERT INTO sessions(session_id, device_learner_id, started_at_utc, ended_at_utc, instrument_id, session_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, device_learner_id, started_at_utc, ended_at_utc, instrument_id, json.dumps(session_json)),
    )
    con.commit()


def list_sessions(con: sqlite3.Connection, device_learner_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    rows = con.execute(
        "SELECT session_json FROM sessions WHERE device_learner_id=? ORDER BY started_at_utc DESC LIMIT ?",
        (device_learner_id, limit),
    ).fetchall()
    return [json.loads(r["session_json"]) for r in rows]


def save_assignment(con: sqlite3.Connection, assignment_id: str, device_learner_id: str,
                    created_at_utc: str, assignment_json: Dict[str, Any]) -> None:
    con.execute(
        """
        INSERT INTO assignments(assignment_id, device_learner_id, created_at_utc, assignment_json)
        VALUES (?, ?, ?, ?)
        """,
        (assignment_id, device_learner_id, created_at_utc, json.dumps(assignment_json)),
    )
    con.commit()


def latest_assignment(con: sqlite3.Connection, device_learner_id: str) -> Optional[Dict[str, Any]]:
    row = con.execute(
        "SELECT assignment_json FROM assignments WHERE device_learner_id=? ORDER BY created_at_utc DESC LIMIT 1",
        (device_learner_id,),
    ).fetchone()
    return json.loads(row["assignment_json"]) if row else None


def save_feedback(con: sqlite3.Connection, feedback_id: str, device_learner_id: str, session_id: str,
                  created_at_utc: str, feedback_json: Dict[str, Any]) -> None:
    con.execute(
        """
        INSERT INTO coach_feedback(feedback_id, device_learner_id, session_id, created_at_utc, feedback_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (feedback_id, device_learner_id, session_id, created_at_utc, json.dumps(feedback_json)),
    )
    con.commit()


def save_attachments_manifest(con: sqlite3.Connection, attachment_id: str, device_learner_id: str,
                              created_at_utc: str, manifest_json: Dict[str, Any]) -> None:
    con.execute(
        """
        INSERT INTO attachments(attachment_id, device_learner_id, created_at_utc, manifest_json)
        VALUES (?, ?, ?, ?)
        """,
        (attachment_id, device_learner_id, created_at_utc, json.dumps(manifest_json)),
    )
    con.commit()
