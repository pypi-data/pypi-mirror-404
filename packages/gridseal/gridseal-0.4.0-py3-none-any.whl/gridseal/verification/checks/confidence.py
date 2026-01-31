# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Confidence check: estimate LLM output confidence via embedding variance."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from gridseal.core.types import CheckResult
from gridseal.verification.checks.base import BaseCheck

logger = logging.getLogger(__name__)


class ConfidenceCheck(BaseCheck):
    """
    Estimate confidence in LLM response using embedding-based analysis.

    This check measures semantic coherence and consistency of the response.
    Responses that are semantically fragmented or contain contradictory
    statements will have lower confidence scores.

    The approach computes:
    1. Sentence-level embeddings of the response
    2. Variance in embedding space (high variance = uncertain/inconsistent)
    3. Coherence score based on sequential sentence similarity

    Attributes:
        name: "confidence"
        model_name: Sentence transformer model for embeddings
    """

    name = "confidence"

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        min_sentences: int = 2,
    ) -> None:
        """
        Initialize confidence check.

        Args:
            model_name: Sentence transformer model for embeddings
            min_sentences: Minimum sentences required for meaningful analysis
        """
        self.model_name = model_name
        self.min_sentences = min_sentences
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
                    "sentence-transformers is required for confidence check. "
                    "Install with: pip install sentence-transformers"
                )
        return self._embedder

    def check(
        self,
        query: str,
        context: list[str],
        response: str,
        threshold: float = 0.7,
    ) -> CheckResult:
        """
        Compute confidence score for the response.

        Args:
            query: The input query (used for relevance component)
            context: Context documents (not used in this check)
            response: The LLM response to analyze
            threshold: Minimum confidence score to pass
        """
        if not response or not response.strip():
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "Empty response, skipping check"},
            )

        sentences = self._split_sentences(response)

        if len(sentences) < self.min_sentences:
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={
                    "warning": f"Response has fewer than {self.min_sentences} sentences",
                    "sentence_count": len(sentences),
                },
            )

        embeddings = self.embedder.encode(sentences, show_progress_bar=False)
        embeddings_array = np.array(embeddings)

        coherence_score = self._compute_coherence(embeddings_array)
        consistency_score = self._compute_consistency(embeddings_array)

        overall_score = (coherence_score + consistency_score) / 2

        return CheckResult(
            name=self.name,
            passed=overall_score >= threshold,
            score=round(overall_score, 4),
            threshold=threshold,
            details={
                "coherence_score": round(coherence_score, 4),
                "consistency_score": round(consistency_score, 4),
                "sentence_count": len(sentences),
            },
        )

    def _compute_coherence(self, embeddings: np.ndarray) -> float:
        """
        Compute coherence as average sequential similarity.

        High coherence means sentences flow logically from one to the next.
        """
        if len(embeddings) < 2:
            return 1.0

        from sklearn.metrics.pairwise import cosine_similarity

        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(
                embeddings[i : i + 1], embeddings[i + 1 : i + 2]
            )[0][0]
            similarities.append(float(sim))

        return sum(similarities) / len(similarities)

    def _compute_consistency(self, embeddings: np.ndarray) -> float:
        """
        Compute consistency as inverse of embedding variance.

        Low variance means all sentences are semantically aligned.
        High variance suggests contradictory or scattered content.
        """
        if len(embeddings) < 2:
            return 1.0

        centroid = embeddings.mean(axis=0)
        distances = np.linalg.norm(embeddings - centroid, axis=1)
        mean_distance = float(distances.mean())
        consistency = 1.0 / (1.0 + mean_distance)

        return min(1.0, consistency * 2)

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        import re

        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
