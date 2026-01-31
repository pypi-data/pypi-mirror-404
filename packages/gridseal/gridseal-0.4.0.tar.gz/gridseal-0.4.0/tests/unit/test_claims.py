# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for claim extraction module."""

from __future__ import annotations

import pytest

from gridseal.verification.claims import (
    ExtractedClaim,
    extract_claims,
    match_claim_to_context,
)


class TestExtractClaims:
    """Tests for claim extraction."""

    def test_extracts_single_sentence(self) -> None:
        """Test extraction of a single sentence."""
        text = "The policy allows 15 days of PTO per year."
        claims = extract_claims(text)

        assert len(claims) == 1
        assert "15 days" in claims[0].text

    def test_extracts_multiple_sentences(self) -> None:
        """Test extraction of multiple sentences."""
        text = "Employees get 15 days PTO. Requests require manager approval. Unused days expire."
        claims = extract_claims(text)

        assert len(claims) >= 2

    def test_skips_questions(self) -> None:
        """Test that questions are not extracted as claims."""
        text = "How many PTO days are available? Employees get 15 days."
        claims = extract_claims(text)

        # Should only get the statement, not the question
        claim_texts = [c.text for c in claims]
        assert not any("?" in t for t in claim_texts)

    def test_skips_greetings(self) -> None:
        """Test that greetings are not extracted."""
        text = "Hello there. The policy provides 15 days PTO."
        claims = extract_claims(text)

        claim_texts = [c.text.lower() for c in claims]
        assert not any("hello" in t for t in claim_texts)

    def test_skips_short_sentences(self) -> None:
        """Test that very short sentences are skipped."""
        text = "Yes. No. The policy provides 15 days of PTO per year."
        claims = extract_claims(text)

        # Only the longer sentence should be extracted
        assert len(claims) == 1
        assert "15 days" in claims[0].text

    def test_span_positions_are_correct(self) -> None:
        """Test that span positions correctly identify claim in text."""
        text = "The policy provides 15 days of PTO per year."
        claims = extract_claims(text)

        for claim in claims:
            # Extract using span positions should match claim text
            extracted = text[claim.span_start:claim.span_end]
            assert extracted == claim.text

    def test_handles_empty_text(self) -> None:
        """Test handling of empty text."""
        claims = extract_claims("")
        assert claims == []

    def test_handles_whitespace_only(self) -> None:
        """Test handling of whitespace-only text."""
        claims = extract_claims("   \n\t  ")
        assert claims == []

    def test_skips_meta_statements(self) -> None:
        """Test that meta-statements about inability are skipped."""
        text = "I don't have access to that information. The policy states 15 days PTO."
        claims = extract_claims(text)

        claim_texts = [c.text.lower() for c in claims]
        assert not any("don't have" in t for t in claim_texts)


class TestMatchClaimToContext:
    """Tests for claim-context matching."""

    def test_finds_matching_context(self) -> None:
        """Test finding matching context for a claim."""
        claim = ExtractedClaim(
            text="Employees receive 15 days of PTO.",
            span_start=0,
            span_end=33,
        )
        context = [
            "The company provides 15 days of PTO per year.",
            "Health insurance is available to all employees.",
        ]

        source, score = match_claim_to_context(claim, context)

        assert source is not None
        assert "15 days" in source
        assert score > 0

    def test_returns_best_match(self) -> None:
        """Test that the best matching context is returned."""
        claim = ExtractedClaim(
            text="PTO requests require 2 weeks advance notice.",
            span_start=0,
            span_end=44,
        )
        context = [
            "Employees get 15 days PTO.",
            "PTO requests must be submitted 2 weeks in advance.",
            "The office is closed on holidays.",
        ]

        source, score = match_claim_to_context(claim, context)

        assert source is not None
        assert "2 weeks" in source

    def test_handles_empty_context(self) -> None:
        """Test handling of empty context list."""
        claim = ExtractedClaim(
            text="Some claim text.",
            span_start=0,
            span_end=16,
        )

        source, score = match_claim_to_context(claim, [])

        assert source is None
        assert score == 0.0

    def test_low_score_for_unrelated_context(self) -> None:
        """Test low score when context is unrelated."""
        claim = ExtractedClaim(
            text="The salary for engineers is competitive.",
            span_start=0,
            span_end=40,
        )
        context = [
            "PTO policy provides 15 days per year.",
            "Health benefits are available.",
        ]

        source, score = match_claim_to_context(claim, context)

        # Score should be relatively low
        assert score < 0.5

    def test_custom_similarity_function(self) -> None:
        """Test using a custom similarity function."""
        claim = ExtractedClaim(
            text="Test claim.",
            span_start=0,
            span_end=11,
        )
        context = ["Context A", "Context B"]

        def custom_sim(a: str, b: str) -> float:
            return 0.99 if "A" in b else 0.1

        source, score = match_claim_to_context(
            claim, context, similarity_fn=custom_sim
        )

        assert source == "Context A"
        assert score == 0.99
