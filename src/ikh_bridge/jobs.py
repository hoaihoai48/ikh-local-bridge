"""Small SQLite store for completed and failed local tool runs."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_db_path() -> Path:
    override = os.environ.get("IKH_BRIDGE_DB")
    if override:
        return Path(override).expanduser().resolve()
    data_dir = Path.home() / ".ikh-local-bridge"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "jobs.sqlite3"


class JobStore:
    def __init__(self, path: Path | None = None):
        self.path = path or default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_slug TEXT NOT NULL,
                    tool_id TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    exit_code INTEGER,
                    stdout TEXT NOT NULL DEFAULT '',
                    stderr TEXT NOT NULL DEFAULT '',
                    error TEXT
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def create(self, skill_slug: str, tool_id: str, workspace: str) -> int:
        started = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO jobs (skill_slug, tool_id, workspace, status, started_at) VALUES (?, ?, ?, 'RUNNING', ?)",
                (skill_slug, tool_id, workspace, started),
            )
            return int(cursor.lastrowid)

    def finish(self, job_id: int, status: str, exit_code: int | None,
               stdout: str = "", stderr: str = "", error: str | None = None) -> None:
        finished = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute(
                "UPDATE jobs SET status=?, finished_at=?, exit_code=?, stdout=?, stderr=?, error=? WHERE id=?",
                (status, finished, exit_code, stdout[-50000:], stderr[-50000:], error, job_id),
            )

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id, skill_slug, tool_id, workspace, status, started_at, finished_at, exit_code, stdout, stderr, error FROM jobs ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 100)),),
            ).fetchall()
        return [dict(row) for row in rows]
