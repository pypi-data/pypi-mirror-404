# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for grounding check."""

from __future__ import annotations

import pytest

from gridseal.verification.checks.grounding import GroundingCheck


class TestGroundingCheck:
    """Tests for GroundingCheck."""

    @pytest.fixture
    def check(self) -> GroundingCheck:
        """Create grounding check instance."""
        return GroundingCheck()

    def test_name(self, check: GroundingCheck) -> None:
        """Test check name."""
        assert check.name == "grounding"

    def test_default_params(self, check: GroundingCheck) -> None:
        """Test default parameters."""
        assert check.model_name == "all-MiniLM-L6-v2"
        assert check.chunk_size == 500
        assert check.min_sentence_length == 10

    def test_custom_params(self) -> None:
        """Test custom parameters."""
        check = GroundingCheck(
            model_name="all-mpnet-base-v2",
            chunk_size=300,
            min_sentence_length=15,
        )

        assert check.model_name == "all-mpnet-base-v2"
        assert check.chunk_size == 300
        assert check.min_sentence_length == 15

    def test_empty_context(self, check: GroundingCheck) -> None:
        """Test with empty context."""
        result = check.check(
            query="Test query",
            context=[],
            response="Some response.",
            threshold=0.7,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details

    def test_empty_context_strings(self, check: GroundingCheck) -> None:
        """Test with context containing empty strings."""
        result = check.check(
            query="Test query",
            context=["", "  ", ""],
            response="Some response.",
            threshold=0.7,
        )

        assert result.passed is True
        assert result.score == 1.0

    def test_empty_response(self, check: GroundingCheck) -> None:
        """Test with empty response."""
        result = check.check(
            query="Test query",
            context=["Some context document."],
            response="",
            threshold=0.7,
        )

        assert result.passed is True
        assert result.score == 1.0
        assert "warning" in result.details

    def test_whitespace_response(self, check: GroundingCheck) -> None:
        """Test with whitespace-only response."""
        result = check.check(
            query="Test query",
            context=["Some context."],
            response="   ",
            threshold=0.7,
        )

        assert result.passed is True

    def test_grounded_response(
        self,
        check: GroundingCheck,
        sample_context: list[str],
        grounded_response: str,
    ) -> None:
        """Test with response that is grounded in context."""
        result = check.check(
            query="Test query",
            context=sample_context,
            response=grounded_response,
            threshold=0.5,
        )

        assert result.passed is True
        assert result.score > 0.5
        assert "sentence_scores" in result.details

    def test_ungrounded_response(
        self,
        check: GroundingCheck,
        sample_context: list[str],
    ) -> None:
        """Test with response that is not grounded in context."""
        ungrounded = "The moon is made of cheese and aliens built the pyramids."

        result = check.check(
            query="Test query",
            context=sample_context,
            response=ungrounded,
            threshold=0.8,
        )

        assert result.score < 0.8

    def test_result_structure(
        self,
        check: GroundingCheck,
        sample_context: list[str],
    ) -> None:
        """Test result structure contains expected fields."""
        result = check.check(
            query="Test query",
            context=sample_context,
            response="Claims over $1000 need approval.",
            threshold=0.5,
        )

        assert result.name == "grounding"
        assert isinstance(result.passed, bool)
        assert 0 <= result.score <= 1
        assert result.threshold == 0.5
        assert "sentence_count" in result.details
        assert "chunk_count" in result.details

    def test_split_sentences(self, check: GroundingCheck) -> None:
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = check._split_sentences(text)

        assert len(sentences) == 3
        assert "First sentence." in sentences
        assert "Second sentence!" in sentences
        assert "Third sentence?" in sentences

    def test_split_sentences_short_filtered(self, check: GroundingCheck) -> None:
        """Test that short sentences are filtered."""
        text = "OK. This is a longer sentence that should be kept."
        sentences = check._split_sentences(text)

        assert len(sentences) == 1
        assert "longer sentence" in sentences[0]

    def test_chunk_context(self, check: GroundingCheck) -> None:
        """Test context chunking."""
        context = ["Short doc.", "A" * 600]
        chunks = check._chunk_context(context)

        assert len(chunks) >= 2
        assert "Short doc." in chunks

    def test_chunk_context_empty_docs(self, check: GroundingCheck) -> None:
        """Test chunking with empty documents."""
        context = ["", "Valid doc.", ""]
        chunks = check._chunk_context(context)

        assert len(chunks) == 1
        assert chunks[0] == "Valid doc."

    def test_embedder_lazy_load(self, check: GroundingCheck) -> None:
        """Test that embedder is lazily loaded."""
        assert check._embedder is None

        _ = check.embedder

        assert check._embedder is not None

    def test_high_threshold(
        self,
        check: GroundingCheck,
        sample_context: list[str],
    ) -> None:
        """Test with very high threshold."""
        result = check.check(
            query="Test",
            context=sample_context,
            response="Something about claims and approval.",
            threshold=0.99,
        )

        assert result.threshold == 0.99

    def test_no_sentences_extracted(self, check: GroundingCheck) -> None:
        """Test when no sentences can be extracted."""
        result = check.check(
            query="Test",
            context=["Some context."],
            response="Hi",
            threshold=0.7,
        )

        assert result.passed is True
        assert "warning" in result.details
