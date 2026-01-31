# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Main audit store interface."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gridseal.audit.backends import MemoryBackend, SQLiteBackend
from gridseal.audit.integrity import verify_chain
from gridseal.core.config import AuditConfig
from gridseal.core.exceptions import AuditError
from gridseal.core.types import AuditRecord

if TYPE_CHECKING:
    from gridseal.audit.backends.base import BaseBackend

logger = logging.getLogger(__name__)


class AuditStore:
    """
    Immutable audit log with hash chain integrity.

    The audit store provides compliance-grade logging for AI decisions.
    Records cannot be modified or deleted once written, and each record
    is cryptographically linked to the previous one.

    Features:
        - Append-only storage
        - Hash chain integrity (tamper-evident)
        - Configurable backends (SQLite, PostgreSQL, memory)
        - Query and export capabilities
    """

    def __init__(self, config: AuditConfig | None = None) -> None:
        """
        Initialize audit store.

        Args:
            config: Audit configuration. Defaults to SQLite in current directory.
        """
        self.config = config or AuditConfig()
        self._backend = self._create_backend()
        self._last_hash = "genesis"
        self._init_chain()

    def _create_backend(self) -> BaseBackend:
        """Create storage backend from config."""
        if self.config.backend == "memory":
            return MemoryBackend()
        elif self.config.backend == "sqlite":
            return SQLiteBackend(self.config.path)
        elif self.config.backend == "postgresql":
            if not self.config.connection:
                raise AuditError("PostgreSQL connection string required")
            from gridseal.audit.backends import get_postgresql_backend

            PostgreSQLBackend = get_postgresql_backend()
            return PostgreSQLBackend(self.config.connection)
        else:
            raise AuditError(f"Unknown backend: {self.config.backend}")

    def _init_chain(self) -> None:
        """Initialize hash chain state from existing records."""
        last = self._backend.get_last_record()
        if last:
            self._last_hash = last.record_hash
            logger.debug(
                f"Initialized chain from existing records, "
                f"last hash: {self._last_hash[:16]}..."
            )

    def log(
        self,
        query: str,
        context: list[str],
        response: str,
        verification_passed: bool = True,
        verification_results: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """
        Log a decision to the audit store.

        Creates an immutable record linked to the previous record
        via hash chain.

        Args:
            query: The input query/prompt
            context: List of context documents
            response: The LLM response
            verification_passed: Whether verification passed
            verification_results: Detailed verification check results
            metadata: Additional user-provided metadata

        Returns:
            The created audit record

        Raises:
            AuditError: If logging fails
        """
        record = AuditRecord(
            query=query,
            context=context,
            response=response,
            verification_passed=verification_passed,
            verification_results=verification_results or {},
            metadata=metadata or {},
            previous_hash=self._last_hash,
        )

        record.record_hash = record.compute_hash()

        try:
            self._backend.insert(record)
        except Exception as e:
            raise AuditError(f"Failed to log record: {e}") from e

        self._last_hash = record.record_hash
        logger.debug(f"Logged audit record {record.id}")

        return record

    def get(self, record_id: str) -> AuditRecord | None:
        """Retrieve a record by ID."""
        return self._backend.get(record_id)

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
        return self._backend.query(
            start_date=start_date,
            end_date=end_date,
            verification_passed=verification_passed,
            limit=limit,
        )

    def verify_integrity(self) -> bool:
        """
        Verify the integrity of the entire audit log.

        Checks that:
        1. All record hashes are valid
        2. The hash chain is unbroken

        Returns:
            True if integrity is valid
        """
        records = self._backend.get_all_ordered()
        is_valid, errors = verify_chain(records)

        if not is_valid:
            for error in errors:
                logger.error(f"Integrity error: {error}")

        return is_valid

    def count(self) -> int:
        """Get total number of records."""
        return self._backend.count()

    def export(
        self,
        output: str,
        format: str = "json",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> int:
        """
        Export records to file.

        Args:
            output: Output file path
            format: Export format ("json" or "csv")
            start_date: Filter records after this date
            end_date: Filter records before this date

        Returns:
            Number of records exported
        """
        records = self._backend.query(
            start_date=start_date,
            end_date=end_date,
            limit=1000000,
        )

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(
                    [r.to_dict() for r in records],
                    f,
                    indent=2,
                    default=str,
                )
        elif format == "csv":
            if not records:
                with open(output_path, "w") as f:
                    f.write("")
                return 0

            fieldnames = [
                "id",
                "timestamp",
                "query",
                "response",
                "verification_passed",
                "record_hash",
            ]
            with open(output_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in records:
                    writer.writerow(
                        {
                            "id": record.id,
                            "timestamp": record.timestamp.isoformat(),
                            "query": record.query,
                            "response": record.response,
                            "verification_passed": record.verification_passed,
                            "record_hash": record.record_hash,
                        }
                    )
        else:
            raise AuditError(f"Unknown export format: {format}")

        logger.info(f"Exported {len(records)} records to {output}")
        return len(records)

    def close(self) -> None:
        """Close the audit store."""
        self._backend.close()
