# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for confidence check."""

from __future__ import annotations

import pytest

from gridseal.verification.checks.confidence import ConfidenceCheck


class TestConfidenceCheck:
    """Tests for ConfidenceCheck."""

    @pytest.fixture
    def check(self) -> ConfidenceCheck:
        """Create confidence check instance."""
        return ConfidenceCheck()

    def test_name(self, check: ConfidenceCheck) -> None:
        """Test check name."""
        assert check.name == "confidence"

    def test_default_params(self, check: ConfidenceCheck) -> None:
        """Test default parameters."""
        assert check.model_name == "all-MiniLM-L6-v2"
        assert check.min_sentences == 2

    def test_empty_response(self, check: ConfidenceCheck) -> None:
        """Test with empty response."""
        result = check.check(
            query="Test query",
            context=[],
            response="",
            threshold=0.7,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details

    def test_short_response(self, check: ConfidenceCheck) -> None:
        """Test with response shorter than min_sentences."""
        result = check.check(
            query="Test query",
            context=[],
            response="Just one sentence here.",
            threshold=0.7,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details
        assert result.details.get("sentence_count") == 1

    def test_coherent_response(
        self,
        check: ConfidenceCheck,
        multi_sentence_response: str,
    ) -> None:
        """Test with coherent multi-sentence response."""
        result = check.check(
            query="What is the claim status?",
            context=[],
            response=multi_sentence_response,
            threshold=0.5,
        )

        assert result.score > 0
        assert "coherence_score" in result.details
        assert "consistency_score" in result.details

    def test_result_structure(self, check: ConfidenceCheck) -> None:
        """Test result contains expected fields."""
        response = (
            "First sentence about claims. "
            "Second sentence about approval. "
            "Third sentence about policies."
        )

        result = check.check(
            query="Test",
            context=[],
            response=response,
            threshold=0.5,
        )

        assert result.name == "confidence"
        assert isinstance(result.passed, bool)
        assert 0 <= result.score <= 1
        assert "coherence_score" in result.details
        assert "consistency_score" in result.details
        assert "sentence_count" in result.details

    def test_incoherent_response(self, check: ConfidenceCheck) -> None:
        """Test with semantically incoherent response."""
        incoherent = (
            "The policy requires manager approval. "
            "Purple elephants dance on Mars. "
            "Quantum mechanics governs atomic behavior. "
            "Pizza is the best breakfast food."
        )

        result = check.check(
            query="What are the requirements?",
            context=[],
            response=incoherent,
            threshold=0.5,
        )

        assert result.details.get("sentence_count", 0) >= 2

    def test_embedder_lazy_load(self, check: ConfidenceCheck) -> None:
        """Test that embedder is lazily loaded."""
        assert check._embedder is None

        _ = check.embedder

        assert check._embedder is not None

    def test_custom_min_sentences(self) -> None:
        """Test custom min_sentences parameter."""
        check = ConfidenceCheck(min_sentences=3)

        result = check.check(
            query="Test",
            context=[],
            response="Sentence one. Sentence two.",
            threshold=0.7,
        )

        assert result.passed is True
        assert "warning" in result.details

    def test_threshold_boundary(self, check: ConfidenceCheck) -> None:
        """Test threshold boundary behavior."""
        response = (
            "This is a consistent statement about policy. "
            "The policy is clear about requirements. "
            "Requirements must be followed strictly."
        )

        result_high = check.check(
            query="Test",
            context=[],
            response=response,
            threshold=0.99,
        )

        result_low = check.check(
            query="Test",
            context=[],
            response=response,
            threshold=0.01,
        )

        assert result_low.passed is True
        assert result_high.threshold == 0.99
        assert result_low.threshold == 0.01
