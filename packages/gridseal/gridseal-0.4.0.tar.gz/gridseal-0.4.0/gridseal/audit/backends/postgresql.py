# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""PostgreSQL audit storage backend."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from gridseal.audit.backends.base import BaseBackend
from gridseal.core.types import AuditRecord

logger = logging.getLogger(__name__)


class PostgreSQLBackend(BaseBackend):
    """
    PostgreSQL storage backend.

    Enterprise-grade persistent storage with full ACID compliance.
    Requires psycopg2 to be installed.
    """

    def __init__(self, connection_string: str) -> None:
        """
        Initialize PostgreSQL backend.

        Args:
            connection_string: PostgreSQL connection string
        """
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL backend. "
                "Install with: pip install psycopg2-binary"
            )

        self._psycopg2 = psycopg2
        self._conn = psycopg2.connect(connection_string)
        self._conn.autocommit = False
        self._create_schema()

    def _create_schema(self) -> None:
        """Create database schema if not exists."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_records (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                query TEXT NOT NULL,
                context JSONB NOT NULL,
                response TEXT NOT NULL,
                verification_passed BOOLEAN NOT NULL,
                verification_results JSONB NOT NULL,
                metadata JSONB NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_records(timestamp)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_verification_passed
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
                previous_hash, record_hash
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                record.id,
                record.timestamp,
                record.query,
                json.dumps(record.context),
                record.response,
                record.verification_passed,
                json.dumps(record.verification_results),
                json.dumps(record.metadata),
                record.previous_hash,
                record.record_hash,
            ),
        )
        self._conn.commit()

    def get(self, record_id: str) -> AuditRecord | None:
        """Retrieve a record by ID."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_records WHERE id = %s",
            (record_id,),
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_record(row, cursor.description)
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
            return self._row_to_record(row, cursor.description)
        return None

    def get_all_ordered(self) -> list[AuditRecord]:
        """Get all records in insertion order."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_records ORDER BY created_at ASC"
        )
        description = cursor.description
        return [self._row_to_record(row, description) for row in cursor.fetchall()]

    def query(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        verification_passed: bool | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """Query records with filters."""
        conditions: list[str] = []
        params: list[Any] = []

        if start_date:
            conditions.append("timestamp >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp <= %s")
            params.append(end_date)
        if verification_passed is not None:
            conditions.append("verification_passed = %s")
            params.append(verification_passed)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        cursor = self._conn.cursor()
        cursor.execute(
            f"""
            SELECT * FROM audit_records
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT %s
            """,
            params + [limit],
        )
        description = cursor.description
        return [self._row_to_record(row, description) for row in cursor.fetchall()]

    def count(self) -> int:
        """Get total number of records."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_records")
        result = cursor.fetchone()
        return int(result[0]) if result else 0

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def _row_to_record(
        self,
        row: tuple[Any, ...],
        description: Any,
    ) -> AuditRecord:
        """Convert database row to AuditRecord."""
        columns = [col[0] for col in description]
        data = dict(zip(columns, row))

        context = data["context"]
        if isinstance(context, str):
            context = json.loads(context)

        verification_results = data["verification_results"]
        if isinstance(verification_results, str):
            verification_results = json.loads(verification_results)

        metadata = data["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return AuditRecord(
            id=data["id"],
            timestamp=data["timestamp"],
            query=data["query"],
            context=context,
            response=data["response"],
            verification_passed=data["verification_passed"],
            verification_results=verification_results,
            metadata=metadata,
            previous_hash=data["previous_hash"],
            record_hash=data["record_hash"],
        )
