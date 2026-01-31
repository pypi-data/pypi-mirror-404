# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for hash chain integrity verification."""

from __future__ import annotations

from datetime import datetime, timezone

from gridseal.audit.integrity import verify_chain, verify_record
from gridseal.core.types import AuditRecord


class TestVerifyRecord:
    """Tests for verify_record function."""

    def test_valid_record(self) -> None:
        """Test verification of valid record."""
        record = AuditRecord(
            query="Test query",
            response="Test response",
        )

        assert verify_record(record) is True

    def test_tampered_query(self) -> None:
        """Test detection of tampered query."""
        record = AuditRecord(
            query="Original query",
            response="Response",
        )

        original_hash = record.record_hash
        record.query = "Tampered query"

        assert record.record_hash == original_hash
        assert verify_record(record) is False

    def test_tampered_response(self) -> None:
        """Test detection of tampered response."""
        record = AuditRecord(
            query="Query",
            response="Original response",
        )

        original_hash = record.record_hash
        record.response = "Tampered response"

        assert verify_record(record) is False

    def test_tampered_metadata(self) -> None:
        """Test detection of tampered metadata."""
        record = AuditRecord(
            query="Query",
            response="Response",
            metadata={"key": "original"},
        )

        original_hash = record.record_hash
        record.metadata["key"] = "tampered"

        assert verify_record(record) is False


class TestVerifyChain:
    """Tests for verify_chain function."""

    def test_empty_chain(self) -> None:
        """Test verification of empty chain."""
        is_valid, errors = verify_chain([])

        assert is_valid is True
        assert errors == []

    def test_single_record_genesis(self) -> None:
        """Test single record with genesis hash."""
        record = AuditRecord(
            query="Query",
            response="Response",
            previous_hash="genesis",
        )

        is_valid, errors = verify_chain([record])

        assert is_valid is True
        assert errors == []

    def test_single_record_invalid_genesis(self) -> None:
        """Test single record without genesis hash."""
        record = AuditRecord(
            query="Query",
            response="Response",
            previous_hash="not-genesis",
        )

        is_valid, errors = verify_chain([record])

        assert is_valid is False
        assert len(errors) == 1
        assert "genesis" in errors[0]

    def test_valid_chain(self) -> None:
        """Test verification of valid chain."""
        r1 = AuditRecord(
            id="r1",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            query="Query 1",
            response="Response 1",
            previous_hash="genesis",
        )

        r2 = AuditRecord(
            id="r2",
            timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
            query="Query 2",
            response="Response 2",
            previous_hash=r1.record_hash,
        )

        r3 = AuditRecord(
            id="r3",
            timestamp=datetime(2024, 1, 3, tzinfo=timezone.utc),
            query="Query 3",
            response="Response 3",
            previous_hash=r2.record_hash,
        )

        is_valid, errors = verify_chain([r1, r2, r3])

        assert is_valid is True
        assert errors == []

    def test_broken_chain(self) -> None:
        """Test detection of broken chain."""
        r1 = AuditRecord(
            id="r1",
            query="Query 1",
            response="Response 1",
            previous_hash="genesis",
        )

        r2 = AuditRecord(
            id="r2",
            query="Query 2",
            response="Response 2",
            previous_hash="wrong-hash",
        )

        is_valid, errors = verify_chain([r1, r2])

        assert is_valid is False
        assert len(errors) == 1
        assert "breaks chain" in errors[0]

    def test_tampered_record_in_chain(self) -> None:
        """Test detection of tampered record in chain."""
        r1 = AuditRecord(
            id="r1",
            query="Query 1",
            response="Response 1",
            previous_hash="genesis",
        )

        r2 = AuditRecord(
            id="r2",
            query="Query 2",
            response="Response 2",
            previous_hash=r1.record_hash,
        )

        r2.query = "Tampered query"

        is_valid, errors = verify_chain([r1, r2])

        assert is_valid is False
        assert any("invalid hash" in e for e in errors)

    def test_multiple_errors(self) -> None:
        """Test detection of multiple integrity errors."""
        r1 = AuditRecord(
            id="r1",
            query="Query 1",
            response="Response 1",
            previous_hash="not-genesis",
        )

        r2 = AuditRecord(
            id="r2",
            query="Query 2",
            response="Response 2",
            previous_hash="wrong-hash",
        )

        r2.query = "Tampered"

        is_valid, errors = verify_chain([r1, r2])

        assert is_valid is False
        assert len(errors) >= 2

    def test_chain_with_context(self) -> None:
        """Test chain with context data."""
        r1 = AuditRecord(
            query="Query 1",
            context=["doc1", "doc2"],
            response="Response 1",
            previous_hash="genesis",
        )

        r2 = AuditRecord(
            query="Query 2",
            context=["doc3"],
            response="Response 2",
            previous_hash=r1.record_hash,
        )

        is_valid, errors = verify_chain([r1, r2])

        assert is_valid is True

    def test_chain_with_verification_results(self) -> None:
        """Test chain with verification results."""
        r1 = AuditRecord(
            query="Query 1",
            response="Response 1",
            verification_passed=True,
            verification_results={"grounding": {"score": 0.9}},
            previous_hash="genesis",
        )

        r2 = AuditRecord(
            query="Query 2",
            response="Response 2",
            verification_passed=False,
            verification_results={"grounding": {"score": 0.3}},
            previous_hash=r1.record_hash,
        )

        is_valid, errors = verify_chain([r1, r2])

        assert is_valid is True

    def test_chain_preserves_order(self) -> None:
        """Test that chain verification respects order."""
        r1 = AuditRecord(
            id="r1",
            query="First",
            response="R1",
            previous_hash="genesis",
        )

        r2 = AuditRecord(
            id="r2",
            query="Second",
            response="R2",
            previous_hash=r1.record_hash,
        )

        is_valid_correct, _ = verify_chain([r1, r2])
        is_valid_reversed, errors = verify_chain([r2, r1])

        assert is_valid_correct is True
        assert is_valid_reversed is False
