# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SQLite audit storage backend."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from gridseal.audit.backends.base import BaseBackend
from gridseal.core.types import AuditRecord

logger = logging.getLogger(__name__)


class SQLiteBackend(BaseBackend):
    """
    SQLite storage backend.

    Production-ready persistent storage. Creates the database file
    and schema automatically if they don't exist.
    """

    def __init__(self, path: str) -> None:
        """
        Initialize SQLite backend.

        Args:
            path: Path to SQLite database file
        """
        self.path = path
        self._ensure_directory()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    def _ensure_directory(self) -> None:
        """Ensure parent directory exists."""
        parent = Path(self.path).parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

    def _create_schema(self) -> None:
        """Create database schema if not exists."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_records (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                context TEXT NOT NULL,
                response TEXT NOT NULL,
                verification_passed INTEGER NOT NULL,
                verification_results TEXT NOT NULL,
                metadata TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON audit_records(timestamp)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_verification_passed
            ON audit_records(verification_passed)
            """
        )
        self._conn.commit()

    def insert(self, record: AuditRecord) -> None:
        """Insert a new audit record."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_records (
                id, timestamp, query, context, response,
                verification_passed, verification_results, metadata,
                previous_hash, record_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.timestamp.isoformat(),
                record.query,
                json.dumps(record.context),
                record.response,
                1 if record.verification_passed else 0,
                json.dumps(record.verification_results),
                json.dumps(record.metadata),
                record.previous_hash,
                record.record_hash,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, record_id: str) -> AuditRecord | None:
        """Retrieve a record by ID."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_records WHERE id = ?",
            (record_id,),
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_record(row)
        return None

    def get_last_record(self) -> AuditRecord | None:
        """Get the most recent record."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT * FROM audit_records
            ORDER BY created_at DESC LIMIT 1
            """
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_record(row)
        return None

    def get_all_ordered(self) -> list[AuditRecord]:
        """Get all records in insertion order."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_records ORDER BY created_at ASC"
        )
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def query(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        verification_passed: bool | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """Query records with filters."""
        conditions: list[str] = []
        params: list[str | int] = []

        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
        if verification_passed is not None:
            conditions.append("verification_passed = ?")
            params.append(1 if verification_passed else 0)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        cursor = self._conn.cursor()
        cursor.execute(
            f"""
            SELECT * FROM audit_records
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            params + [limit],
        )
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """Get total number of records."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_records")
        result = cursor.fetchone()
        return int(result[0]) if result else 0

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def _row_to_record(self, row: sqlite3.Row) -> AuditRecord:
        """Convert database row to AuditRecord."""
        return AuditRecord(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            query=row["query"],
            context=json.loads(row["context"]),
            response=row["response"],
            verification_passed=bool(row["verification_passed"]),
            verification_results=json.loads(row["verification_results"]),
            metadata=json.loads(row["metadata"]),
            previous_hash=row["previous_hash"],
            record_hash=row["record_hash"],
        )
