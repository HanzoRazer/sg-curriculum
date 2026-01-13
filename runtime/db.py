from __future__ import annotations
import sqlite3
from pathlib import Path


SCHEMA_V1 = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog (
  content_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT,
  tags_json TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  device_learner_id TEXT NOT NULL,
  started_at_utc TEXT NOT NULL,
  ended_at_utc TEXT NOT NULL,
  instrument_id TEXT,
  session_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
  assignment_id TEXT PRIMARY KEY,
  device_learner_id TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  assignment_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coach_feedback (
  feedback_id TEXT PRIMARY KEY,
  device_learner_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  feedback_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attachments (
  attachment_id TEXT PRIMARY KEY,
  device_learner_id TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  manifest_json TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    return con


def migrate(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA_V1)
    # schema version marker
    cur = con.execute("SELECT v FROM meta WHERE k='schema_version'")
    row = cur.fetchone()
    if not row:
        con.execute("INSERT INTO meta(k, v) VALUES ('schema_version', 'v1')")
    con.commit()
