# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NLI (Natural Language Inference) backends for claim verification."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Literal

logger = logging.getLogger(__name__)

# Model configurations for different NLI modes
NLI_MODELS = {
    "fast": "cross-encoder/nli-distilroberta-base",  # ~50ms
    "balanced": "cross-encoder/nli-deberta-v3-base",  # ~150ms
    "accurate": "cross-encoder/nli-deberta-v3-large",  # ~300ms
}


class NLIBackend(ABC):
    """Abstract base class for NLI backends."""

    @abstractmethod
    def predict(self, premise: str, hypothesis: str) -> dict[str, float]:
        """
        Predict entailment relationship.

        Args:
            premise: The source text (context)
            hypothesis: The claim to verify

        Returns:
            Dict with scores for "entailment", "contradiction", "neutral"
        """
        pass

    @abstractmethod
    def predict_batch(
        self, pairs: list[tuple[str, str]]
    ) -> list[dict[str, float]]:
        """
        Predict entailment for multiple pairs.

        Args:
            pairs: List of (premise, hypothesis) tuples

        Returns:
            List of score dicts
        """
        pass


class CrossEncoderNLI(NLIBackend):
    """NLI backend using cross-encoder models from sentence-transformers."""

    def __init__(self, mode: Literal["fast", "balanced", "accurate"] = "fast"):
        """
        Initialize cross-encoder NLI backend.

        Args:
            mode: Speed/accuracy tradeoff
        """
        self.mode = mode
        self.model_name = NLI_MODELS[mode]
        self._model = None

    def _load_model(self) -> None:
        """Lazy load the model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
            logger.info(f"Loaded NLI model: {self.model_name}")
        except ImportError:
            raise ImportError(
                "NLI support requires sentence-transformers. "
                "Install with: pip install gridseal[nli]"
            )

    def predict(self, premise: str, hypothesis: str) -> dict[str, float]:
        """Predict entailment for a single pair."""
        self._load_model()

        scores = self._model.predict([(premise, hypothesis)])[0]

        # Cross-encoder returns [contradiction, entailment, neutral]
        return {
            "contradiction": float(scores[0]),
            "entailment": float(scores[1]),
            "neutral": float(scores[2]),
        }

    def predict_batch(
        self, pairs: list[tuple[str, str]]
    ) -> list[dict[str, float]]:
        """Predict entailment for multiple pairs."""
        if not pairs:
            return []

        self._load_model()

        all_scores = self._model.predict(pairs)

        results = []
        for scores in all_scores:
            results.append({
                "contradiction": float(scores[0]),
                "entailment": float(scores[1]),
                "neutral": float(scores[2]),
            })

        return results


class MockNLI(NLIBackend):
    """Mock NLI backend for testing."""

    def __init__(self, default_score: float = 0.8):
        self.default_score = default_score

    def predict(self, premise: str, hypothesis: str) -> dict[str, float]:
        """Return mock predictions."""
        # Simple heuristic: higher overlap = higher entailment
        premise_words = set(premise.lower().split())
        hypothesis_words = set(hypothesis.lower().split())

        if not hypothesis_words:
            return {"entailment": 0.5, "contradiction": 0.2, "neutral": 0.3}

        overlap = len(premise_words & hypothesis_words) / len(hypothesis_words)

        return {
            "entailment": min(overlap + 0.3, 1.0),
            "contradiction": max(0.1, 0.3 - overlap),
            "neutral": 0.2,
        }

    def predict_batch(
        self, pairs: list[tuple[str, str]]
    ) -> list[dict[str, float]]:
        """Return mock predictions for batch."""
        return [self.predict(p, h) for p, h in pairs]


def get_nli_backend(
    mode: Literal["fast", "balanced", "accurate"] = "fast",
    use_mock: bool = False,
) -> NLIBackend:
    """
    Get an NLI backend instance.

    Args:
        mode: Speed/accuracy tradeoff
        use_mock: Use mock backend for testing

    Returns:
        NLIBackend instance
    """
    if use_mock:
        return MockNLI()
    return CrossEncoderNLI(mode=mode)
