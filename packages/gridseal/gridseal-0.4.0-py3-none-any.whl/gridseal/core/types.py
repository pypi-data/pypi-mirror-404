# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Core data types for GridSeal."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ClaimVerification:
    """
    Verification result for a single claim extracted from an LLM response.

    Provides span-level granularity for UI highlighting and detailed analysis.

    Attributes:
        claim_text: The extracted claim from the response
        source_text: Matching context snippet (if found)
        entailment_score: NLI entailment score (0.0-1.0)
        status: Verification status ("supported", "contradicted", "unverifiable")
        span_start: Character position where claim starts in response
        span_end: Character position where claim ends in response
    """

    claim_text: str
    source_text: str | None
    entailment_score: float
    status: str  # "supported", "contradicted", "unverifiable"
    span_start: int
    span_end: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "claim_text": self.claim_text,
            "source_text": self.source_text,
            "entailment_score": self.entailment_score,
            "status": self.status,
            "span_start": self.span_start,
            "span_end": self.span_end,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClaimVerification:
        """Create ClaimVerification from dictionary."""
        return cls(
            claim_text=data["claim_text"],
            source_text=data.get("source_text"),
            entailment_score=data["entailment_score"],
            status=data["status"],
            span_start=data["span_start"],
            span_end=data["span_end"],
        )


@dataclass(frozen=True)
class CheckResult:
    """
    Result from a single verification check.

    Attributes:
        name: Identifier for this check (e.g., "grounding", "confidence")
        passed: Whether the check passed its threshold
        score: Numeric score from 0.0 to 1.0
        threshold: The threshold used for pass/fail determination
        details: Additional check-specific information
        error: Error message if check failed to execute
        duration_ms: Time taken to run the check
    """

    name: str
    passed: bool
    score: float
    threshold: float
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "threshold": self.threshold,
            "details": self.details,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class VerificationResult(Generic[T]):
    """
    Wrapper around LLM response with verification metadata.

    This is returned by @gs.verify decorated functions instead of
    the raw response, allowing access to both the response and
    verification details.

    Attributes:
        response: The original LLM output
        passed: True if all checks passed their thresholds
        checks: Dict mapping check name to CheckResult
        flags: Human-readable warnings/errors
        audit_id: ID of the audit record (if auditing enabled)
        duration_ms: Total verification time
    """

    response: T
    passed: bool
    checks: dict[str, CheckResult] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    claims: list[ClaimVerification] = field(default_factory=list)
    audit_id: str | None = None
    duration_ms: float = 0.0
    profile: str = "default"

    @property
    def grounding_score(self) -> float | None:
        """Convenience accessor for grounding check score."""
        check = self.checks.get("grounding")
        return check.score if check else None

    @property
    def confidence_score(self) -> float | None:
        """Convenience accessor for confidence check score."""
        check = self.checks.get("confidence")
        return check.score if check else None

    @property
    def relevance_score(self) -> float | None:
        """Convenience accessor for relevance check score."""
        check = self.checks.get("relevance")
        return check.score if check else None

    @property
    def citation_score(self) -> float | None:
        """Convenience accessor for citation check score."""
        check = self.checks.get("citation")
        return check.score if check else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "response": self.response,
            "passed": self.passed,
            "checks": {k: v.to_dict() for k, v in self.checks.items()},
            "flags": self.flags,
            "claims": [c.to_dict() for c in self.claims],
            "audit_id": self.audit_id,
            "duration_ms": self.duration_ms,
            "profile": self.profile,
        }


@dataclass
class AuditRecord:
    """
    Immutable audit record with hash chain integrity.

    Once created, records cannot be modified. Each record contains
    a hash of the previous record, forming a tamper-evident chain.

    Attributes:
        id: Unique identifier (UUID)
        timestamp: When the decision was made (UTC)
        query: The input query/prompt
        context: List of context documents (for RAG)
        response: The LLM response
        verification_passed: Whether verification passed
        verification_results: Detailed check results
        metadata: Additional user-provided metadata
        previous_hash: Hash of the previous record (chain link)
        record_hash: Hash of this record's contents
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    query: str = ""
    context: list[str] = field(default_factory=list)
    response: str = ""

    verification_passed: bool = True
    verification_results: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    previous_hash: str = "genesis"
    record_hash: str = ""

    def __post_init__(self) -> None:
        """Compute hash after initialization if not set."""
        if not self.record_hash:
            self.record_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of record contents.

        The hash includes all fields that should be immutable,
        ensuring any tampering is detectable.
        """
        content = json.dumps(
            {
                "id": self.id,
                "timestamp": self.timestamp.isoformat(),
                "query": self.query,
                "context": self.context,
                "response": self.response,
                "verification_passed": self.verification_passed,
                "verification_results": self.verification_results,
                "metadata": self.metadata,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "context": self.context,
            "response": self.response,
            "verification_passed": self.verification_passed,
            "verification_results": self.verification_results,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
            "record_hash": self.record_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditRecord:
        """Create AuditRecord from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        record = cls(
            id=data.get("id", str(uuid.uuid4())),
            timestamp=timestamp or datetime.now(timezone.utc),
            query=data.get("query", ""),
            context=data.get("context", []),
            response=data.get("response", ""),
            verification_passed=data.get("verification_passed", True),
            verification_results=data.get("verification_results", {}),
            metadata=data.get("metadata", {}),
            previous_hash=data.get("previous_hash", "genesis"),
            record_hash=data.get("record_hash", ""),
        )
        return record
