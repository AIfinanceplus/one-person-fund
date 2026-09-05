from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


class StateStore:
    """Small SQLite state store with idempotent events and lease-based tasks."""

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                role_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                worker_id TEXT,
                lease_until TEXT,
                attempt INTEGER NOT NULL DEFAULT 0,
                artifact_id TEXT,
                error_code TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS tasks_claim_idx ON tasks(status, lease_until);
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(run_id, sequence)
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                artifact_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create_run(self, run_id: str, mode: str) -> bool:
        now = _iso(_now())
        cur = self.conn.execute("INSERT OR IGNORE INTO runs(run_id, mode, status, created_at, updated_at) VALUES (?, ?, 'RUNNING', ?, ?)", (run_id, mode, now, now))
        self.conn.commit()
        return cur.rowcount == 1

    def set_run_status(self, run_id: str, status: str) -> None:
        self.conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?", (status, _iso(_now()), run_id))
        self.conn.commit()

    def enqueue_task(self, task_id: str, run_id: str, role_id: str, payload: dict[str, Any]) -> bool:
        cur = self.conn.execute("INSERT OR IGNORE INTO tasks(task_id, run_id, role_id, status, payload_json, updated_at) VALUES (?, ?, ?, 'PENDING', ?, ?)", (task_id, run_id, role_id, json.dumps(payload, sort_keys=True, default=str), _iso(_now())))
        self.conn.commit()
        return cur.rowcount == 1

    def claim_task(self, task_id: str, worker_id: str, lease_seconds: int = 60) -> bool:
        now = _now()
        lease_until = _iso(now + timedelta(seconds=lease_seconds))
        with self.conn:
            cur = self.conn.execute(
                """UPDATE tasks SET status='RUNNING', worker_id=?, lease_until=?, attempt=attempt+1, updated_at=?
                   WHERE task_id=? AND (status='PENDING' OR (status='RUNNING' AND lease_until <= ?))""",
                (worker_id, lease_until, _iso(now), task_id, _iso(now)),
            )
        return cur.rowcount == 1

    def complete_task(self, task_id: str, status: str, artifact_id: str | None = None, error_code: str | None = None) -> None:
        self.conn.execute("UPDATE tasks SET status=?, artifact_id=?, error_code=?, lease_until=NULL, updated_at=? WHERE task_id=?", (status, artifact_id, error_code, _iso(_now()), task_id))
        self.conn.commit()

    def append_event(self, event_id: str, run_id: str, sequence: int, event_type: str, payload: dict[str, Any]) -> bool:
        cur = self.conn.execute("INSERT OR IGNORE INTO events(event_id, run_id, sequence, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)", (event_id, run_id, sequence, event_type, json.dumps(payload, sort_keys=True, default=str), _iso(_now())))
        self.conn.commit()
        return cur.rowcount == 1

    def put_artifact(self, artifact_id: str, run_id: str, artifact_type: str, payload: Any) -> bool:
        cur = self.conn.execute("INSERT OR IGNORE INTO artifacts(artifact_id, run_id, artifact_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)", (artifact_id, run_id, artifact_type, json.dumps(payload, sort_keys=True, default=str), _iso(_now())))
        self.conn.commit()
        return cur.rowcount == 1

    def events(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT event_id, sequence, event_type, payload_json, created_at FROM events WHERE run_id=? ORDER BY sequence", (run_id,)).fetchall()
        return [{"event_id": r["event_id"], "sequence": r["sequence"], "event_type": r["event_type"], "payload": json.loads(r["payload_json"]), "created_at": r["created_at"]} for r in rows]

    def task(self, task_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def run(self, run_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None
