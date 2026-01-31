# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Relevance check: verify response is relevant to the query."""

from __future__ import annotations

import logging
from typing import Any

from gridseal.core.types import CheckResult
from gridseal.verification.checks.base import BaseCheck

logger = logging.getLogger(__name__)


class RelevanceCheck(BaseCheck):
    """
    Verify that LLM response is relevant to the input query.

    Uses embedding similarity between query and response to determine
    if the response actually addresses what was asked.

    This catches cases where the response may be factually grounded
    but doesn't actually answer the question.

    Attributes:
        name: "relevance"
        model_name: Sentence transformer model for embeddings
    """

    name = "relevance"

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        """
        Initialize relevance check.

        Args:
            model_name: Sentence transformer model for embeddings
        """
        self.model_name = model_name
        self._embedder: Any = None

    @property
    def embedder(self) -> Any:
        """Lazy load sentence transformer model."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedder = SentenceTransformer(self.model_name)
                logger.debug(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for relevance check. "
                    "Install with: pip install sentence-transformers"
                )
        return self._embedder

    def check(
        self,
        query: str,
        context: list[str],
        response: str,
        threshold: float = 0.5,
    ) -> CheckResult:
        """
        Check if response is relevant to the query.

        Args:
            query: The input query
            context: Context documents (not used directly)
            response: The LLM response to check
            threshold: Minimum similarity score to pass
        """
        if not query or not query.strip():
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "Empty query, skipping check"},
            )

        if not response or not response.strip():
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "Empty response, skipping check"},
            )

        query_embedding = self.embedder.encode([query], show_progress_bar=False)
        response_embedding = self.embedder.encode([response], show_progress_bar=False)

        from sklearn.metrics.pairwise import cosine_similarity

        similarity = float(cosine_similarity(query_embedding, response_embedding)[0][0])

        sentences = self._split_sentences(response)
        if len(sentences) > 1:
            sentence_embeddings = self.embedder.encode(
                sentences, show_progress_bar=False
            )
            sentence_similarities = cosine_similarity(
                query_embedding, sentence_embeddings
            )[0]
            best_sentence_idx = int(sentence_similarities.argmax())
            best_sentence_score = float(sentence_similarities.max())
        else:
            best_sentence_idx = 0
            best_sentence_score = similarity

        final_score = max(similarity, best_sentence_score)

        return CheckResult(
            name=self.name,
            passed=final_score >= threshold,
            score=round(final_score, 4),
            threshold=threshold,
            details={
                "overall_similarity": round(similarity, 4),
                "best_sentence_score": round(best_sentence_score, 4),
                "best_sentence_idx": best_sentence_idx,
                "sentence_count": len(sentences),
            },
        )

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        import re

        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
