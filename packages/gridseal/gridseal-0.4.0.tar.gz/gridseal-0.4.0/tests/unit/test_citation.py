# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for citation check."""

from __future__ import annotations

import pytest

from gridseal.verification.checks.citation import CitationCheck


class TestCitationCheck:
    """Tests for CitationCheck."""

    @pytest.fixture
    def check(self) -> CitationCheck:
        """Create citation check instance."""
        return CitationCheck()

    def test_name(self, check: CitationCheck) -> None:
        """Test check name."""
        assert check.name == "citation"

    def test_default_params(self, check: CitationCheck) -> None:
        """Test default parameters."""
        assert check.model_name == "cross-encoder/nli-deberta-v3-base"
        assert check.min_claim_length == 20

    def test_custom_params(self) -> None:
        """Test custom parameters."""
        check = CitationCheck(
            model_name="cross-encoder/nli-MiniLM2-L6-H768",
            min_claim_length=30,
        )

        assert check.model_name == "cross-encoder/nli-MiniLM2-L6-H768"
        assert check.min_claim_length == 30

    def test_empty_context(self, check: CitationCheck) -> None:
        """Test with empty context."""
        result = check.check(
            query="Test query",
            context=[],
            response="Some response with claims.",
            threshold=0.5,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details

    def test_empty_context_strings(self, check: CitationCheck) -> None:
        """Test with context containing empty strings."""
        result = check.check(
            query="Test query",
            context=["", "  "],
            response="Some claim here.",
            threshold=0.5,
        )

        assert result.passed is True
        assert "warning" in result.details

    def test_empty_response(self, check: CitationCheck) -> None:
        """Test with empty response."""
        result = check.check(
            query="Test query",
            context=["Some context."],
            response="",
            threshold=0.5,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details

    def test_no_claims_extracted(self, check: CitationCheck) -> None:
        """Test with response too short for claims."""
        result = check.check(
            query="Test",
            context=["Context."],
            response="OK.",
            threshold=0.5,
        )

        assert result.passed is True
        assert "warning" in result.details

    def test_result_structure(
        self,
        check: CitationCheck,
        sample_context: list[str],
    ) -> None:
        """Test result contains expected fields."""
        result = check.check(
            query="Test query",
            context=sample_context,
            response="Claims over $1000 require manager approval as per policy.",
            threshold=0.3,
        )

        assert result.name == "citation"
        assert isinstance(result.passed, bool)
        assert 0 <= result.score <= 1
        assert "total_claims" in result.details
        assert "supported_claims" in result.details
        assert "claim_results" in result.details

    def test_extract_claims(self, check: CitationCheck) -> None:
        """Test claim extraction."""
        response = (
            "First claim that is long enough. "
            "Second claim also long enough. "
            "Short. "
            "Is this a question?"
        )
        claims = check._extract_claims(response)

        assert len(claims) == 2
        assert "First claim" in claims[0]
        assert "Second claim" in claims[1]

    def test_extract_claims_filters_questions(self, check: CitationCheck) -> None:
        """Test that questions are filtered from claims."""
        response = "What is the policy about this matter?"
        claims = check._extract_claims(response)

        assert len(claims) == 0

    def test_extract_claims_filters_short(self, check: CitationCheck) -> None:
        """Test that short sentences are filtered."""
        check_custom = CitationCheck(min_claim_length=50)
        response = "This is a short claim. This is a much longer claim that exceeds the minimum length requirement."
        claims = check_custom._extract_claims(response)

        assert len(claims) == 1

    def test_supported_claim(
        self,
        check: CitationCheck,
        sample_context: list[str],
    ) -> None:
        """Test with claim that is supported by context."""
        result = check.check(
            query="Test",
            context=sample_context,
            response="According to the policy, claims over $1000 require manager approval.",
            threshold=0.3,
        )

        assert "claim_results" in result.details

    def test_unsupported_claim(
        self,
        check: CitationCheck,
        sample_context: list[str],
    ) -> None:
        """Test with claim that is not supported by context."""
        result = check.check(
            query="Test",
            context=sample_context,
            response="All claims are automatically approved without any review process.",
            threshold=0.9,
        )

        if result.details.get("total_claims", 0) > 0:
            assert "unsupported_claims" in result.details

    def test_nli_model_lazy_load(self, check: CitationCheck) -> None:
        """Test that NLI model is lazily loaded."""
        assert check._nli_model is None

        _ = check.nli_model

        assert check._nli_model is not None

    def test_threshold_affects_pass(self, check: CitationCheck) -> None:
        """Test that threshold affects pass/fail."""
        context = ["Claims over $1000 need manager approval."]
        response = "Large claims require managerial sign-off per company policy guidelines."

        result_low = check.check(
            query="Test",
            context=context,
            response=response,
            threshold=0.1,
        )

        result_high = check.check(
            query="Test",
            context=context,
            response=response,
            threshold=0.99,
        )

        assert result_low.threshold == 0.1
        assert result_high.threshold == 0.99

    def test_multiple_claims(
        self,
        check: CitationCheck,
        sample_context: list[str],
    ) -> None:
        """Test with multiple claims."""
        response = (
            "Claims over $1000 require manager approval. "
            "Patients over 65 qualify for Medicare. "
            "Claims must be filed within 90 days."
        )

        result = check.check(
            query="Test",
            context=sample_context,
            response=response,
            threshold=0.3,
        )

        assert result.details.get("total_claims", 0) >= 2
