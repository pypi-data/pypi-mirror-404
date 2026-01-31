# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for core types."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gridseal.core.types import AuditRecord, CheckResult, VerificationResult


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_creation_basic(self) -> None:
        """Test basic creation with required fields."""
        result = CheckResult(
            name="grounding",
            passed=True,
            score=0.85,
            threshold=0.7,
        )

        assert result.name == "grounding"
        assert result.passed is True
        assert result.score == 0.85
        assert result.threshold == 0.7
        assert result.details == {}
        assert result.error is None
        assert result.duration_ms == 0.0

    def test_creation_with_details(self) -> None:
        """Test creation with details dict."""
        details = {"unsupported_claims": ["claim1", "claim2"]}
        result = CheckResult(
            name="grounding",
            passed=False,
            score=0.5,
            threshold=0.7,
            details=details,
        )

        assert result.details == details
        assert result.details["unsupported_claims"] == ["claim1", "claim2"]

    def test_creation_with_error(self) -> None:
        """Test creation with error message."""
        result = CheckResult(
            name="grounding",
            passed=False,
            score=0.0,
            threshold=0.7,
            error="Model not loaded",
        )

        assert result.error == "Model not loaded"
        assert result.passed is False

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        result = CheckResult(
            name="grounding",
            passed=True,
            score=0.85,
            threshold=0.7,
            details={"key": "value"},
            duration_ms=10.5,
        )

        data = result.to_dict()

        assert data["name"] == "grounding"
        assert data["passed"] is True
        assert data["score"] == 0.85
        assert data["threshold"] == 0.7
        assert data["details"] == {"key": "value"}
        assert data["error"] is None
        assert data["duration_ms"] == 10.5

    def test_frozen(self) -> None:
        """Test that CheckResult is immutable."""
        result = CheckResult(
            name="grounding",
            passed=True,
            score=0.85,
            threshold=0.7,
        )

        with pytest.raises(AttributeError):
            result.score = 0.9  # type: ignore[misc]


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_creation_basic(self) -> None:
        """Test basic creation."""
        result = VerificationResult(
            response="Test response",
            passed=True,
        )

        assert result.response == "Test response"
        assert result.passed is True
        assert result.checks == {}
        assert result.flags == []
        assert result.audit_id is None
        assert result.duration_ms == 0.0

    def test_creation_with_checks(self) -> None:
        """Test creation with check results."""
        check = CheckResult(
            name="grounding",
            passed=True,
            score=0.85,
            threshold=0.7,
        )
        result = VerificationResult(
            response="Test",
            passed=True,
            checks={"grounding": check},
        )

        assert "grounding" in result.checks
        assert result.checks["grounding"].score == 0.85

    def test_grounding_score_property(self) -> None:
        """Test grounding_score convenience property."""
        check = CheckResult(
            name="grounding",
            passed=True,
            score=0.85,
            threshold=0.7,
        )
        result = VerificationResult(
            response="Test",
            passed=True,
            checks={"grounding": check},
        )

        assert result.grounding_score == 0.85

    def test_grounding_score_missing(self) -> None:
        """Test grounding_score when no grounding check."""
        result = VerificationResult(
            response="Test",
            passed=True,
        )

        assert result.grounding_score is None

    def test_confidence_score_property(self) -> None:
        """Test confidence_score convenience property."""
        check = CheckResult(
            name="confidence",
            passed=True,
            score=0.9,
            threshold=0.7,
        )
        result = VerificationResult(
            response="Test",
            passed=True,
            checks={"confidence": check},
        )

        assert result.confidence_score == 0.9

    def test_relevance_score_property(self) -> None:
        """Test relevance_score convenience property."""
        check = CheckResult(
            name="relevance",
            passed=True,
            score=0.75,
            threshold=0.5,
        )
        result = VerificationResult(
            response="Test",
            passed=True,
            checks={"relevance": check},
        )

        assert result.relevance_score == 0.75

    def test_citation_score_property(self) -> None:
        """Test citation_score convenience property."""
        check = CheckResult(
            name="citation",
            passed=True,
            score=0.8,
            threshold=0.5,
        )
        result = VerificationResult(
            response="Test",
            passed=True,
            checks={"citation": check},
        )

        assert result.citation_score == 0.8

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        check = CheckResult(
            name="grounding",
            passed=True,
            score=0.85,
            threshold=0.7,
        )
        result = VerificationResult(
            response="Test response",
            passed=True,
            checks={"grounding": check},
            flags=["flag1"],
            audit_id="abc-123",
            duration_ms=50.0,
        )

        data = result.to_dict()

        assert data["response"] == "Test response"
        assert data["passed"] is True
        assert "grounding" in data["checks"]
        assert data["flags"] == ["flag1"]
        assert data["audit_id"] == "abc-123"
        assert data["duration_ms"] == 50.0

    def test_generic_type(self) -> None:
        """Test that VerificationResult works with different response types."""
        result_str: VerificationResult[str] = VerificationResult(
            response="string",
            passed=True,
        )
        assert result_str.response == "string"

        result_dict: VerificationResult[dict[str, str]] = VerificationResult(
            response={"key": "value"},
            passed=True,
        )
        assert result_dict.response == {"key": "value"}


class TestAuditRecord:
    """Tests for AuditRecord dataclass."""

    def test_creation_basic(self) -> None:
        """Test basic creation."""
        record = AuditRecord(
            query="Test query",
            response="Test response",
        )

        assert record.query == "Test query"
        assert record.response == "Test response"
        assert record.previous_hash == "genesis"
        assert record.record_hash != ""
        assert record.id != ""
        assert record.context == []
        assert record.verification_passed is True

    def test_creation_with_all_fields(self) -> None:
        """Test creation with all fields."""
        timestamp = datetime.now(timezone.utc)
        record = AuditRecord(
            id="test-id",
            timestamp=timestamp,
            query="Test query",
            context=["doc1", "doc2"],
            response="Test response",
            verification_passed=False,
            verification_results={"grounding": {"score": 0.5}},
            metadata={"user": "test"},
            previous_hash="abc123",
        )

        assert record.id == "test-id"
        assert record.timestamp == timestamp
        assert record.context == ["doc1", "doc2"]
        assert record.verification_passed is False
        assert record.verification_results == {"grounding": {"score": 0.5}}
        assert record.metadata == {"user": "test"}
        assert record.previous_hash == "abc123"

    def test_hash_computation(self) -> None:
        """Test that hash is computed correctly."""
        record = AuditRecord(
            query="Test query",
            response="Test response",
        )

        expected = record.compute_hash()
        assert record.record_hash == expected

    def test_hash_deterministic(self) -> None:
        """Test that hash computation is deterministic."""
        record = AuditRecord(
            id="fixed-id",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            query="Test query",
            response="Test response",
        )

        hash1 = record.compute_hash()
        hash2 = record.compute_hash()

        assert hash1 == hash2

    def test_hash_changes_with_content(self) -> None:
        """Test that different content produces different hashes."""
        record1 = AuditRecord(query="Query 1", response="Response 1")
        record2 = AuditRecord(query="Query 2", response="Response 2")

        assert record1.record_hash != record2.record_hash

    def test_hash_changes_with_previous_hash(self) -> None:
        """Test that different previous_hash produces different hash."""
        record1 = AuditRecord(
            id="same-id",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            query="Same query",
            response="Same response",
            previous_hash="hash1",
        )
        record2 = AuditRecord(
            id="same-id",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            query="Same query",
            response="Same response",
            previous_hash="hash2",
        )

        assert record1.record_hash != record2.record_hash

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        record = AuditRecord(
            id="test-id",
            timestamp=timestamp,
            query="Test query",
            context=["doc1", "doc2"],
            response="Test response",
            verification_passed=True,
            verification_results={"score": 0.9},
            metadata={"key": "value"},
            previous_hash="prev-hash",
        )

        data = record.to_dict()

        assert data["id"] == "test-id"
        assert data["timestamp"] == "2024-01-01T12:00:00+00:00"
        assert data["query"] == "Test query"
        assert data["context"] == ["doc1", "doc2"]
        assert data["response"] == "Test response"
        assert data["verification_passed"] is True
        assert data["verification_results"] == {"score": 0.9}
        assert data["metadata"] == {"key": "value"}
        assert data["previous_hash"] == "prev-hash"
        assert "record_hash" in data

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data = {
            "id": "test-id",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "query": "Test query",
            "context": ["doc1"],
            "response": "Test response",
            "verification_passed": True,
            "verification_results": {},
            "metadata": {},
            "previous_hash": "genesis",
            "record_hash": "abc123",
        }

        record = AuditRecord.from_dict(data)

        assert record.id == "test-id"
        assert record.query == "Test query"
        assert record.context == ["doc1"]
        assert record.response == "Test response"
        assert record.previous_hash == "genesis"

    def test_from_dict_defaults(self) -> None:
        """Test from_dict with minimal data."""
        data: dict[str, object] = {}

        record = AuditRecord.from_dict(data)

        assert record.query == ""
        assert record.response == ""
        assert record.context == []
        assert record.previous_hash == "genesis"

    def test_uuid_generation(self) -> None:
        """Test that UUIDs are unique."""
        record1 = AuditRecord(query="q", response="r")
        record2 = AuditRecord(query="q", response="r")

        assert record1.id != record2.id
