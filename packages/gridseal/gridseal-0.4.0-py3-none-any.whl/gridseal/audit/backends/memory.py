# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""In-memory audit storage backend for testing."""

from __future__ import annotations

from gridseal.audit.backends.base import BaseBackend
from gridseal.core.types import AuditRecord


class MemoryBackend(BaseBackend):
    """
    In-memory storage backend.

    Useful for testing and development. Data is lost when the
    process exits.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._records: list[AuditRecord] = []
        self._index: dict[str, int] = {}

    def insert(self, record: AuditRecord) -> None:
        """Insert a new audit record."""
        idx = len(self._records)
        self._records.append(record)
        self._index[record.id] = idx

    def get(self, record_id: str) -> AuditRecord | None:
        """Retrieve a record by ID."""
        idx = self._index.get(record_id)
        if idx is not None:
            return self._records[idx]
        return None

    def get_last_record(self) -> AuditRecord | None:
        """Get the most recent record."""
        if self._records:
            return self._records[-1]
        return None

    def get_all_ordered(self) -> list[AuditRecord]:
        """Get all records in insertion order."""
        return list(self._records)

    def query(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        verification_passed: bool | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """Query records with filters."""
        start_dt = self._parse_date(start_date)
        end_dt = self._parse_date(end_date)

        results: list[AuditRecord] = []
        for record in self._records:
            if start_dt and record.timestamp < start_dt:
                continue
            if end_dt and record.timestamp > end_dt:
                continue
            if verification_passed is not None:
                if record.verification_passed != verification_passed:
                    continue
            results.append(record)
            if len(results) >= limit:
                break

        return results

    def count(self) -> int:
        """Get total number of records."""
        return len(self._records)

    def close(self) -> None:
        """Close the backend (no-op for memory)."""
        pass

    def clear(self) -> None:
        """Clear all records (testing helper)."""
        self._records.clear()
        self._index.clear()
