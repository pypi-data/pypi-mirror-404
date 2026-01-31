# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Base class for audit storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from gridseal.core.types import AuditRecord


class BaseBackend(ABC):
    """
    Abstract base class for audit storage backends.

    Subclasses must implement all abstract methods to provide
    storage functionality.
    """

    @abstractmethod
    def insert(self, record: AuditRecord) -> None:
        """
        Insert a new audit record.

        Args:
            record: The audit record to insert
        """
        pass

    @abstractmethod
    def get(self, record_id: str) -> AuditRecord | None:
        """
        Retrieve a record by ID.

        Args:
            record_id: The unique record identifier

        Returns:
            The audit record if found, None otherwise
        """
        pass

    @abstractmethod
    def get_last_record(self) -> AuditRecord | None:
        """
        Get the most recent record.

        Returns:
            The last inserted record, or None if empty
        """
        pass

    @abstractmethod
    def get_all_ordered(self) -> list[AuditRecord]:
        """
        Get all records in insertion order.

        Returns:
            List of all records ordered by timestamp
        """
        pass

    @abstractmethod
    def query(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        verification_passed: bool | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """
        Query records with filters.

        Args:
            start_date: Filter records after this date (ISO format)
            end_date: Filter records before this date (ISO format)
            verification_passed: Filter by verification status
            limit: Maximum records to return

        Returns:
            List of matching records
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get total number of records.

        Returns:
            Total record count
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the backend connection."""
        pass

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse ISO date string to datetime."""
        if date_str is None:
            return None
        return datetime.fromisoformat(date_str)
