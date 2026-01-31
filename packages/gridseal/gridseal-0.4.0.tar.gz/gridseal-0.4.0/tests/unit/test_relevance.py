# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for relevance check."""

from __future__ import annotations

import pytest

from gridseal.verification.checks.relevance import RelevanceCheck


class TestRelevanceCheck:
    """Tests for RelevanceCheck."""

    @pytest.fixture
    def check(self) -> RelevanceCheck:
        """Create relevance check instance."""
        return RelevanceCheck()

    def test_name(self, check: RelevanceCheck) -> None:
        """Test check name."""
        assert check.name == "relevance"

    def test_default_params(self, check: RelevanceCheck) -> None:
        """Test default parameters."""
        assert check.model_name == "all-MiniLM-L6-v2"

    def test_empty_query(self, check: RelevanceCheck) -> None:
        """Test with empty query."""
        result = check.check(
            query="",
            context=[],
            response="Some response.",
            threshold=0.5,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details

    def test_empty_response(self, check: RelevanceCheck) -> None:
        """Test with empty response."""
        result = check.check(
            query="What is the policy?",
            context=[],
            response="",
            threshold=0.5,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details

    def test_relevant_response(self, check: RelevanceCheck) -> None:
        """Test with relevant response."""
        result = check.check(
            query="What is the claim approval policy?",
            context=[],
            response="The claim approval policy requires manager sign-off for amounts over $1000.",
            threshold=0.3,
        )

        assert result.passed is True
        assert result.score > 0.3
        assert "overall_similarity" in result.details

    def test_irrelevant_response(self, check: RelevanceCheck) -> None:
        """Test with irrelevant response."""
        result = check.check(
            query="What is the weather forecast?",
            context=[],
            response="The mitochondria is the powerhouse of the cell.",
            threshold=0.8,
        )

        assert result.score < 0.8

    def test_result_structure(self, check: RelevanceCheck) -> None:
        """Test result contains expected fields."""
        result = check.check(
            query="Test query about policies",
            context=[],
            response="Response about policies and procedures.",
            threshold=0.5,
        )

        assert result.name == "relevance"
        assert isinstance(result.passed, bool)
        assert 0 <= result.score <= 1
        assert "overall_similarity" in result.details
        assert "best_sentence_score" in result.details
        assert "sentence_count" in result.details

    def test_multi_sentence_best_match(self, check: RelevanceCheck) -> None:
        """Test that best matching sentence is found."""
        result = check.check(
            query="What is the claim limit?",
            context=[],
            response=(
                "There are many policies in effect. "
                "The claim limit is $1000 for automatic approval. "
                "Please contact support for more information."
            ),
            threshold=0.3,
        )

        assert "best_sentence_idx" in result.details
        assert result.details["sentence_count"] == 3

    def test_embedder_lazy_load(self, check: RelevanceCheck) -> None:
        """Test that embedder is lazily loaded."""
        assert check._embedder is None

        _ = check.embedder

        assert check._embedder is not None

    def test_single_sentence_response(self, check: RelevanceCheck) -> None:
        """Test with single sentence response."""
        result = check.check(
            query="What is the policy?",
            context=[],
            response="The policy is documented here.",
            threshold=0.3,
        )

        assert result.details["sentence_count"] == 1
        assert result.details["best_sentence_idx"] == 0

    def test_high_threshold(self, check: RelevanceCheck) -> None:
        """Test with high threshold."""
        result = check.check(
            query="Exact match query",
            context=[],
            response="Completely different topic.",
            threshold=0.95,
        )

        assert result.threshold == 0.95

    def test_context_not_used(self, check: RelevanceCheck) -> None:
        """Test that context doesn't affect relevance score."""
        result_with_context = check.check(
            query="Policy question",
            context=["Unrelated context document."],
            response="Policy answer here.",
            threshold=0.3,
        )

        result_without_context = check.check(
            query="Policy question",
            context=[],
            response="Policy answer here.",
            threshold=0.3,
        )

        assert abs(result_with_context.score - result_without_context.score) < 0.01
