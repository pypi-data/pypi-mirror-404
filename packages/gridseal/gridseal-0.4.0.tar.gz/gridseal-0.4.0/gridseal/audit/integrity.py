# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Hash chain integrity verification."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gridseal.core.types import AuditRecord

logger = logging.getLogger(__name__)


def verify_chain(records: list[AuditRecord]) -> tuple[bool, list[str]]:
    """
    Verify the integrity of a chain of audit records.

    Checks:
    1. First record has previous_hash = "genesis"
    2. Each record's hash matches its computed hash
    3. Each record's previous_hash matches the prior record's hash

    Args:
        records: List of audit records in insertion order

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: list[str] = []

    if not records:
        return True, []

    if records[0].previous_hash != "genesis":
        errors.append(
            f"First record {records[0].id} has invalid previous_hash: "
            f"expected 'genesis', got '{records[0].previous_hash}'"
        )

    for i, record in enumerate(records):
        expected_hash = record.compute_hash()
        if record.record_hash != expected_hash:
            errors.append(
                f"Record {record.id} has invalid hash: "
                f"expected '{expected_hash[:16]}...', "
                f"got '{record.record_hash[:16]}...'"
            )

        if i > 0:
            expected_previous = records[i - 1].record_hash
            if record.previous_hash != expected_previous:
                errors.append(
                    f"Record {record.id} breaks chain: "
                    f"expected previous_hash '{expected_previous[:16]}...', "
                    f"got '{record.previous_hash[:16]}...'"
                )

    is_valid = len(errors) == 0

    if is_valid:
        logger.info(f"Integrity check passed for {len(records)} records")
    else:
        logger.error(f"Integrity check failed with {len(errors)} errors")

    return is_valid, errors


def verify_record(record: AuditRecord) -> bool:
    """
    Verify a single record's self-hash.

    Args:
        record: The audit record to verify

    Returns:
        True if hash is valid
    """
    expected = record.compute_hash()
    return record.record_hash == expected
