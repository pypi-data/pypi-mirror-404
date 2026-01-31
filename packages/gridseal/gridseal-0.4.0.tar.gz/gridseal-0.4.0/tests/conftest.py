# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures for GridSeal tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from gridseal import GridSeal
from gridseal.audit.backends.memory import MemoryBackend
from gridseal.core.config import AuditConfig, VerificationConfig


@pytest.fixture
def gs() -> GridSeal:
    """GridSeal instance with memory backend for testing."""
    return GridSeal(
        verification={"checks": ["grounding"], "threshold": 0.5},
        audit={"backend": "memory"},
    )


@pytest.fixture
def gs_no_verify() -> GridSeal:
    """GridSeal instance without verification (audit only)."""
    return GridSeal(
        verification={"checks": []},
        audit={"backend": "memory"},
    )


@pytest.fixture
def gs_all_checks() -> GridSeal:
    """GridSeal instance with all checks enabled."""
    return GridSeal(
        verification={
            "checks": ["grounding", "confidence", "relevance"],
            "threshold": 0.5,
        },
        audit={"backend": "memory"},
    )


@pytest.fixture
def sample_context() -> list[str]:
    """Sample context documents for testing."""
    return [
        "The policy states that claims over $1000 require manager approval.",
        "Patients over 65 are eligible for Medicare coverage.",
        "All claims must be submitted within 90 days of service.",
    ]


@pytest.fixture
def sample_query() -> str:
    """Sample query for testing."""
    return "Is a $1500 claim eligible for automatic approval?"


@pytest.fixture
def grounded_response() -> str:
    """Response that is grounded in context."""
    return "No, claims over $1000 require manager approval according to the policy."


@pytest.fixture
def ungrounded_response() -> str:
    """Response that is NOT grounded in context."""
    return "Yes, all claims are automatically approved regardless of amount."


@pytest.fixture
def memory_backend() -> MemoryBackend:
    """Fresh memory backend for testing."""
    return MemoryBackend()


@pytest.fixture
def verification_config() -> VerificationConfig:
    """Default verification config."""
    return VerificationConfig(
        checks=["grounding"],
        threshold=0.7,
        on_fail="flag",
    )


@pytest.fixture
def audit_config() -> AuditConfig:
    """Default audit config with memory backend."""
    return AuditConfig(backend="memory")


@pytest.fixture
def temp_db_path() -> str:
    """Temporary SQLite database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return f.name


@pytest.fixture
def multi_sentence_response() -> str:
    """Response with multiple sentences for confidence testing."""
    return (
        "The claim requires manager approval because it exceeds $1000. "
        "This is consistent with the policy guidelines. "
        "Additionally, the patient is eligible for Medicare coverage. "
        "The claim was submitted within the required 90-day window."
    )
