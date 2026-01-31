# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Grounding check: verify response is supported by context."""

from __future__ import annotations

import logging
import re
from typing import Any

from gridseal.core.types import CheckResult
from gridseal.verification.checks.base import BaseCheck

logger = logging.getLogger(__name__)


class GroundingCheck(BaseCheck):
    """
    Verify that LLM response is grounded in provided context.

    Uses sentence embeddings to check if each claim in the response
    is semantically similar to at least one context chunk. High
    similarity indicates the response is supported by the context.

    This is the primary hallucination detection method for RAG systems.

    Attributes:
        name: "grounding"
        model_name: Sentence transformer model (default: all-MiniLM-L6-v2)
        chunk_size: Max characters per context chunk
        min_sentence_length: Ignore sentences shorter than this
    """

    name = "grounding"

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        min_sentence_length: int = 10,
    ) -> None:
        """
        Initialize grounding check.

        Args:
            model_name: Sentence transformer model to use for embeddings.
                Smaller models are faster, larger models more accurate.
            chunk_size: Maximum characters per context chunk.
            min_sentence_length: Ignore response sentences shorter than this.
        """
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.min_sentence_length = min_sentence_length
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
                    "sentence-transformers is required for grounding check. "
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
        Check if response is grounded in context.

        Algorithm:
        1. Split response into sentences
        2. Chunk context documents
        3. Embed all sentences and chunks
        4. For each sentence, find highest similarity to any chunk
        5. Average sentence scores for overall grounding score
        """
        if not context or all(not c.strip() for c in context):
            logger.debug("No context provided, skipping grounding check")
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "No context provided, skipping check"},
            )

        if not response or not response.strip():
            logger.debug("Empty response, skipping grounding check")
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "Empty response, skipping check"},
            )

        sentences = self._split_sentences(response)
        if not sentences:
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "No sentences extracted from response"},
            )

        chunks = self._chunk_context(context)
        if not chunks:
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "No chunks extracted from context"},
            )

        sentence_embeddings = self.embedder.encode(sentences, show_progress_bar=False)
        chunk_embeddings = self.embedder.encode(chunks, show_progress_bar=False)

        from sklearn.metrics.pairwise import cosine_similarity

        similarities = cosine_similarity(sentence_embeddings, chunk_embeddings)

        sentence_scores: list[dict[str, Any]] = []
        unsupported_claims: list[str] = []

        for i, sentence in enumerate(sentences):
            best_score = float(similarities[i].max())
            best_chunk_idx = int(similarities[i].argmax())
            best_chunk = chunks[best_chunk_idx]

            sentence_scores.append(
                {
                    "sentence": sentence,
                    "score": round(best_score, 4),
                    "best_match": (
                        best_chunk[:100] + ("..." if len(best_chunk) > 100 else "")
                    ),
                }
            )

            if best_score < threshold:
                unsupported_claims.append(sentence)

        overall_score = sum(s["score"] for s in sentence_scores) / len(sentence_scores)

        return CheckResult(
            name=self.name,
            passed=overall_score >= threshold,
            score=round(overall_score, 4),
            threshold=threshold,
            details={
                "sentence_count": len(sentences),
                "chunk_count": len(chunks),
                "sentence_scores": sentence_scores,
                "unsupported_claims": unsupported_claims,
            },
        )

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, text)
        return [
            s.strip()
            for s in sentences
            if s.strip() and len(s.strip()) >= self.min_sentence_length
        ]

    def _chunk_context(self, context: list[str]) -> list[str]:
        """Split context documents into chunks."""
        chunks: list[str] = []
        for doc in context:
            if not doc or not doc.strip():
                continue
            doc = doc.strip()
            if len(doc) <= self.chunk_size:
                chunks.append(doc)
            else:
                for i in range(0, len(doc), self.chunk_size):
                    chunk = doc[i : i + self.chunk_size].strip()
                    if chunk:
                        chunks.append(chunk)
        return chunks
