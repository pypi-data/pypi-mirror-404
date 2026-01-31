# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for async verification methods."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gridseal import GridSeal, VerificationResult


class TestAsyncVerification:
    """Tests for verify_async method."""

    @pytest.fixture
    def gs(self) -> GridSeal:
        """Create GridSeal instance with memory backend."""
        return GridSeal(
            verification={"checks": ["grounding"], "threshold": 0.5},
            audit={"backend": "memory"},
        )

    @pytest.fixture
    def context(self) -> list[str]:
        """Sample context documents."""
        return [
            "The company provides 15 days of PTO per year.",
            "Employees must submit PTO requests 2 weeks in advance.",
            "Unused PTO expires at year end.",
        ]

    @pytest.mark.asyncio
    async def test_verify_async_returns_result(
        self, gs: GridSeal, context: list[str]
    ) -> None:
        """Test that verify_async returns a VerificationResult."""
        result = await gs.verify_async(
            response="Employees get 15 days of PTO.",
            context=context,
        )

        assert isinstance(result, VerificationResult)
        assert isinstance(result.passed, bool)
        assert "grounding" in result.checks

    @pytest.mark.asyncio
    async def test_verify_async_non_blocking(
        self, gs: GridSeal, context: list[str]
    ) -> None:
        """Test that verify_async doesn't block the event loop."""
        # Create a flag to track concurrent execution
        concurrent_executed = False

        async def concurrent_task() -> None:
            nonlocal concurrent_executed
            await asyncio.sleep(0.01)
            concurrent_executed = True

        # Run verification and concurrent task
        await asyncio.gather(
            gs.verify_async(
                response="Employees get 15 days of PTO.",
                context=context,
            ),
            concurrent_task(),
        )

        assert concurrent_executed

    @pytest.mark.asyncio
    async def test_verify_async_with_callback(
        self, gs: GridSeal, context: list[str]
    ) -> None:
        """Test that callback is invoked with result."""
        callback_result: list[VerificationResult[str]] = []

        def callback(result: VerificationResult[str]) -> None:
            callback_result.append(result)

        await gs.verify_async(
            response="Employees get 15 days of PTO.",
            context=context,
            callback=callback,
        )

        assert len(callback_result) == 1
        assert isinstance(callback_result[0], VerificationResult)

    @pytest.mark.asyncio
    async def test_verify_async_grounded_response(
        self, gs: GridSeal, context: list[str]
    ) -> None:
        """Test grounded response passes verification."""
        result = await gs.verify_async(
            response="The company gives employees 15 days of PTO per year.",
            context=context,
        )

        assert result.passed
        assert result.checks["grounding"].score > 0.5

    @pytest.mark.asyncio
    async def test_verify_async_ungrounded_response(
        self, gs: GridSeal, context: list[str]
    ) -> None:
        """Test ungrounded response fails verification."""
        result = await gs.verify_async(
            response="The salary for senior engineers is $200,000.",
            context=context,
        )

        # Response about salary is not grounded in PTO context
        assert result.checks["grounding"].score < 0.5


class TestVerifyAndScore:
    """Tests for verify_and_score method."""

    @pytest.fixture
    def gs(self) -> GridSeal:
        """Create GridSeal instance."""
        return GridSeal(
            verification={"checks": ["grounding"], "threshold": 0.5},
            audit={"backend": "memory"},
        )

    @pytest.fixture
    def context(self) -> list[str]:
        """Sample context."""
        return ["Employees receive 15 days PTO."]

    @pytest.mark.asyncio
    async def test_verify_and_score_creates_audit_record(
        self, gs: GridSeal, context: list[str]
    ) -> None:
        """Test that verify_and_score creates an audit record."""
        result = await gs.verify_and_score(
            response="Employees get 15 days PTO.",
            context=context,
            query="How much PTO do employees get?",
        )

        assert result.audit_id is not None
        # Verify record exists in store
        record = gs.store.get(result.audit_id)
        assert record is not None
        assert record.query == "How much PTO do employees get?"

    @pytest.mark.asyncio
    async def test_verify_and_score_with_metadata(
        self, gs: GridSeal, context: list[str]
    ) -> None:
        """Test metadata is included in audit record."""
        result = await gs.verify_and_score(
            response="Employees get 15 days PTO.",
            context=context,
            metadata={"user_id": "test-user", "session": "abc123"},
        )

        record = gs.store.get(result.audit_id)
        assert record.metadata["user_id"] == "test-user"
        assert record.metadata["session"] == "abc123"

    @pytest.mark.asyncio
    async def test_verify_and_score_with_langfuse(
        self, context: list[str]
    ) -> None:
        """Test Langfuse scoring is called when client provided."""
        mock_langfuse = MagicMock()

        gs = GridSeal(
            verification={"checks": ["grounding"], "threshold": 0.5},
            audit={"backend": "memory"},
            langfuse_client=mock_langfuse,
        )

        await gs.verify_and_score(
            response="Employees get 15 days PTO.",
            context=context,
            trace_id="trace-123",
        )

        # Langfuse score should have been called
        assert mock_langfuse.score.called


class TestVerificationProfiles:
    """Tests for verification profiles."""

    @pytest.fixture
    def gs_with_profiles(self) -> GridSeal:
        """Create GridSeal with multiple profiles."""
        return GridSeal(
            verification={"checks": ["grounding"], "threshold": 0.5},
            audit={"backend": "memory"},
            verification_profiles={
                "default": {"threshold": 0.5},
                "strict": {"threshold": 0.9, "strict": True},
                "legal": {"threshold": 0.85, "require_citations": True},
            },
        )

    @pytest.fixture
    def context(self) -> list[str]:
        """Sample context."""
        return ["Employees receive 15 days PTO per year."]

    @pytest.mark.asyncio
    async def test_default_profile(
        self, gs_with_profiles: GridSeal, context: list[str]
    ) -> None:
        """Test default profile uses default threshold."""
        result = await gs_with_profiles.verify_async(
            response="Employees get 15 days of PTO.",
            context=context,
            profile="default",
        )

        assert result.profile == "default"

    @pytest.mark.asyncio
    async def test_strict_profile_higher_threshold(
        self, gs_with_profiles: GridSeal, context: list[str]
    ) -> None:
        """Test strict profile uses higher threshold."""
        result = await gs_with_profiles.verify_async(
            response="Employees get around 15 days of PTO.",
            context=context,
            profile="strict",
        )

        assert result.profile == "strict"

    @pytest.mark.asyncio
    async def test_unknown_profile_uses_default(
        self, gs_with_profiles: GridSeal, context: list[str]
    ) -> None:
        """Test unknown profile falls back to default."""
        result = await gs_with_profiles.verify_async(
            response="Employees get 15 days of PTO.",
            context=context,
            profile="nonexistent",
        )

        # Should not raise, uses default
        assert isinstance(result, VerificationResult)


class TestClaimExtraction:
    """Tests for claim extraction."""

    @pytest.fixture
    def gs_with_claims(self) -> GridSeal:
        """Create GridSeal with claim extraction enabled."""
        return GridSeal(
            verification={
                "checks": ["grounding"],
                "threshold": 0.5,
                "extract_claims": True,
            },
            audit={"backend": "memory"},
        )

    @pytest.fixture
    def context(self) -> list[str]:
        """Sample context."""
        return [
            "Employees receive 15 days PTO per year.",
            "PTO must be requested 2 weeks in advance.",
        ]

    @pytest.mark.asyncio
    async def test_claims_extracted(
        self, gs_with_claims: GridSeal, context: list[str]
    ) -> None:
        """Test that claims are extracted from response."""
        result = await gs_with_claims.verify_async(
            response="Employees get 15 days of PTO. Requests must be submitted 2 weeks early.",
            context=context,
        )

        assert len(result.claims) > 0

    @pytest.mark.asyncio
    async def test_claim_has_span_info(
        self, gs_with_claims: GridSeal, context: list[str]
    ) -> None:
        """Test that claims include span information."""
        result = await gs_with_claims.verify_async(
            response="Employees receive 15 days of PTO per year.",
            context=context,
        )

        if result.claims:
            claim = result.claims[0]
            assert claim.span_start >= 0
            assert claim.span_end > claim.span_start
            assert claim.status in ["supported", "contradicted", "unverifiable"]

    @pytest.mark.asyncio
    async def test_claims_have_source_text(
        self, gs_with_claims: GridSeal, context: list[str]
    ) -> None:
        """Test that supported claims have source text."""
        result = await gs_with_claims.verify_async(
            response="Employees receive 15 days PTO per year.",
            context=context,
        )

        supported = [c for c in result.claims if c.status == "supported"]
        for claim in supported:
            assert claim.source_text is not None
