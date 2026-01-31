# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Citation check: verify claims using Natural Language Inference."""

from __future__ import annotations

import logging
import re
from typing import Any

from gridseal.core.types import CheckResult
from gridseal.verification.checks.base import BaseCheck

logger = logging.getLogger(__name__)


class CitationCheck(BaseCheck):
    """
    Verify claims in LLM response using Natural Language Inference.

    Uses an NLI model to check if claims in the response are entailed
    by (supported by) the provided context documents.

    This is more precise than embedding similarity because it captures
    logical entailment rather than just semantic similarity.

    Attributes:
        name: "citation"
        model_name: NLI model (default: cross-encoder/nli-deberta-v3-base)
    """

    name = "citation"

    def __init__(
        self,
        model_name: str = "cross-encoder/nli-deberta-v3-base",
        min_claim_length: int = 20,
    ) -> None:
        """
        Initialize citation check.

        Args:
            model_name: Cross-encoder NLI model name
            min_claim_length: Minimum characters for a claim to be checked
        """
        self.model_name = model_name
        self.min_claim_length = min_claim_length
        self._nli_model: Any = None

    @property
    def nli_model(self) -> Any:
        """Lazy load NLI model."""
        if self._nli_model is None:
            try:
                from sentence_transformers import CrossEncoder

                self._nli_model = CrossEncoder(self.model_name)
                logger.debug(f"Loaded NLI model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for citation check. "
                    "Install with: pip install sentence-transformers"
                )
        return self._nli_model

    def check(
        self,
        query: str,
        context: list[str],
        response: str,
        threshold: float = 0.5,
    ) -> CheckResult:
        """
        Verify claims in response against context using NLI.

        Args:
            query: The input query (logged but not used in scoring)
            context: List of context documents to check against
            response: The LLM response containing claims
            threshold: Minimum entailment score for a claim to be supported
        """
        if not context or all(not c.strip() for c in context):
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "No context provided, skipping check"},
            )

        if not response or not response.strip():
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "Empty response, skipping check"},
            )

        claims = self._extract_claims(response)

        if not claims:
            return CheckResult(
                name=self.name,
                passed=True,
                score=1.0,
                threshold=threshold,
                details={"warning": "No claims extracted from response"},
            )

        claim_results: list[dict[str, Any]] = []
        for claim in claims:
            is_supported, confidence, evidence = self._verify_claim(
                claim, context, threshold
            )
            claim_results.append(
                {
                    "claim": claim,
                    "supported": is_supported,
                    "confidence": round(confidence, 4),
                    "evidence": evidence[:200] if evidence else None,
                }
            )

        supported_count = sum(1 for c in claim_results if c["supported"])
        score = supported_count / len(claim_results) if claim_results else 1.0

        unsupported = [c for c in claim_results if not c["supported"]]

        return CheckResult(
            name=self.name,
            passed=score >= threshold,
            score=round(score, 4),
            threshold=threshold,
            details={
                "total_claims": len(claims),
                "supported_claims": supported_count,
                "claim_results": claim_results,
                "unsupported_claims": [c["claim"] for c in unsupported],
            },
        )

    def _extract_claims(self, response: str) -> list[str]:
        """Extract verifiable claims from response."""
        sentences = re.split(r"(?<=[.!?])\s+", response)
        claims = []
        for s in sentences:
            s = s.strip()
            if len(s) >= self.min_claim_length and not s.endswith("?"):
                claims.append(s)
        return claims

    def _verify_claim(
        self,
        claim: str,
        context: list[str],
        threshold: float,
    ) -> tuple[bool, float, str | None]:
        """
        Verify a single claim against context using NLI.

        Returns: (is_supported, confidence, evidence)
        """
        best_score = 0.0
        best_evidence: str | None = None

        for chunk in context:
            if not chunk or not chunk.strip():
                continue

            scores = self.nli_model.predict([(chunk, claim)])

            if hasattr(scores, "__len__") and len(scores) > 0:
                if hasattr(scores[0], "__len__") and len(scores[0]) >= 3:
                    entailment_score = float(scores[0][1])
                else:
                    entailment_score = float(scores[0])
            else:
                entailment_score = float(scores)

            if entailment_score > best_score:
                best_score = entailment_score
                best_evidence = chunk

        is_supported = best_score > threshold
        return is_supported, best_score, best_evidence
