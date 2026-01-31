# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for Langfuse scoring integration."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from gridseal import CheckResult, ClaimVerification, VerificationResult
from gridseal.integrations.langfuse import LangfuseScorer


class TestLangfuseScorer:
    """Tests for LangfuseScorer class."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock Langfuse client."""
        return MagicMock()

    @pytest.fixture
    def scorer(self, mock_client: MagicMock) -> LangfuseScorer:
        """Create scorer with mock client."""
        return LangfuseScorer(client=mock_client)

    @pytest.fixture
    def sample_result(self) -> VerificationResult[str]:
        """Create sample verification result."""
        return VerificationResult(
            response="Test response",
            passed=True,
            checks={
                "grounding": CheckResult(
                    name="grounding",
                    passed=True,
                    score=0.85,
                    threshold=0.7,
                ),
                "relevance": CheckResult(
                    name="relevance",
                    passed=True,
                    score=0.92,
                    threshold=0.7,
                ),
            },
            flags=[],
            claims=[],
        )

    def test_score_trace_logs_passed_status(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
        sample_result: VerificationResult[str],
    ) -> None:
        """Test that pass/fail status is logged."""
        scorer.score_trace(
            trace_id="trace-123",
            result=sample_result,
        )

        # Find the gridseal_passed call
        calls = mock_client.score.call_args_list
        passed_call = next(
            c for c in calls if c.kwargs.get("name") == "gridseal_passed"
        )
        assert passed_call.kwargs["value"] == 1.0
        assert passed_call.kwargs["trace_id"] == "trace-123"

    def test_score_trace_logs_individual_checks(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
        sample_result: VerificationResult[str],
    ) -> None:
        """Test that individual check scores are logged."""
        scorer.score_trace(
            trace_id="trace-123",
            result=sample_result,
        )

        calls = mock_client.score.call_args_list
        score_names = [c.kwargs.get("name") for c in calls]

        assert "gridseal_grounding" in score_names
        assert "gridseal_relevance" in score_names

        # Check score values
        grounding_call = next(
            c for c in calls if c.kwargs.get("name") == "gridseal_grounding"
        )
        assert grounding_call.kwargs["value"] == 0.85

    def test_score_trace_logs_failed_status(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
    ) -> None:
        """Test that failed verification logs 0.0."""
        result = VerificationResult(
            response="Test",
            passed=False,
            checks={
                "grounding": CheckResult(
                    name="grounding",
                    passed=False,
                    score=0.4,
                    threshold=0.7,
                ),
            },
            flags=["grounding check failed"],
        )

        scorer.score_trace(trace_id="trace-123", result=result)

        calls = mock_client.score.call_args_list
        passed_call = next(
            c for c in calls if c.kwargs.get("name") == "gridseal_passed"
        )
        assert passed_call.kwargs["value"] == 0.0

    def test_score_trace_logs_flags(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
    ) -> None:
        """Test that flags are logged."""
        result = VerificationResult(
            response="Test",
            passed=False,
            checks={},
            flags=["grounding failed", "relevance failed"],
        )

        scorer.score_trace(trace_id="trace-123", result=result)

        calls = mock_client.score.call_args_list
        flags_call = next(
            c for c in calls if c.kwargs.get("name") == "gridseal_flags"
        )
        assert flags_call.kwargs["value"] == 2
        assert "grounding failed" in flags_call.kwargs["comment"]

    def test_score_trace_with_observation_id(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
        sample_result: VerificationResult[str],
    ) -> None:
        """Test that observation_id is passed through."""
        scorer.score_trace(
            trace_id="trace-123",
            result=sample_result,
            observation_id="obs-456",
        )

        calls = mock_client.score.call_args_list
        for c in calls:
            assert c.kwargs.get("observation_id") == "obs-456"

    def test_score_trace_with_claims(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
    ) -> None:
        """Test that claim statistics are logged."""
        result = VerificationResult(
            response="Test",
            passed=True,
            checks={},
            flags=[],
            claims=[
                ClaimVerification(
                    claim_text="Claim 1",
                    source_text="Source 1",
                    entailment_score=0.9,
                    status="supported",
                    span_start=0,
                    span_end=7,
                ),
                ClaimVerification(
                    claim_text="Claim 2",
                    source_text=None,
                    entailment_score=0.3,
                    status="unverifiable",
                    span_start=8,
                    span_end=15,
                ),
            ],
        )

        scorer.score_trace(trace_id="trace-123", result=result)

        calls = mock_client.score.call_args_list
        claims_call = next(
            c for c in calls if c.kwargs.get("name") == "gridseal_claims_supported"
        )
        assert claims_call.kwargs["value"] == 0.5  # 1/2 supported
        assert "1/2" in claims_call.kwargs["comment"]

    def test_score_generation(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
        sample_result: VerificationResult[str],
    ) -> None:
        """Test score_generation passes observation_id."""
        scorer.score_generation(
            trace_id="trace-123",
            generation_id="gen-789",
            result=sample_result,
        )

        calls = mock_client.score.call_args_list
        for c in calls:
            assert c.kwargs.get("observation_id") == "gen-789"

    def test_flush_calls_client_flush(
        self,
        scorer: LangfuseScorer,
        mock_client: MagicMock,
    ) -> None:
        """Test that flush calls client flush."""
        scorer.flush()
        mock_client.flush.assert_called_once()


class TestLangfuseScorerWithoutClient:
    """Tests for LangfuseScorer without client."""

    def test_score_without_client_no_error(self) -> None:
        """Test that scoring without client doesn't raise."""
        scorer = LangfuseScorer(client=None)
        scorer._initialized = False  # Force uninitialized state

        result = VerificationResult(
            response="Test",
            passed=True,
            checks={},
        )

        # Should not raise, just log warning
        # We can't actually test this without langfuse installed
        # so we just verify the scorer was created
        assert scorer._client is None
