# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Langfuse integration for GridSeal verification scoring."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from gridseal.core.types import VerificationResult

logger = logging.getLogger(__name__)


class LangfuseScorer:
    """
    Integration for logging GridSeal verification scores to Langfuse.

    Automatically logs grounding, confidence, relevance, and citation scores
    to an existing Langfuse trace/observation.
    """

    def __init__(self, client: Any = None):
        """
        Initialize Langfuse scorer.

        Args:
            client: Existing Langfuse client instance.
                    If None, attempts to create from environment variables.
        """
        self._client = client
        self._initialized = False

    def _ensure_client(self) -> None:
        """Ensure Langfuse client is available."""
        if self._client is not None:
            self._initialized = True
            return

        try:
            from langfuse import Langfuse
            self._client = Langfuse()
            self._initialized = True
            logger.info("Initialized Langfuse client from environment")
        except ImportError:
            raise ImportError(
                "Langfuse integration requires langfuse package. "
                "Install with: pip install langfuse"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse client: {e}")
            self._initialized = False

    @property
    def client(self) -> Any:
        """Get the Langfuse client."""
        self._ensure_client()
        return self._client

    def score_trace(
        self,
        trace_id: str,
        result: VerificationResult[Any],
        observation_id: str | None = None,
    ) -> None:
        """
        Log verification scores to a Langfuse trace.

        Args:
            trace_id: The Langfuse trace ID
            result: GridSeal verification result
            observation_id: Optional observation ID for more granular scoring
        """
        if not self._initialized:
            self._ensure_client()

        if self._client is None:
            logger.warning("Langfuse client not available, skipping scoring")
            return

        # Log overall pass/fail
        self._client.score(
            trace_id=trace_id,
            observation_id=observation_id,
            name="gridseal_passed",
            value=1.0 if result.passed else 0.0,
            comment=f"GridSeal verification {'passed' if result.passed else 'failed'}",
        )

        # Log individual check scores
        for check_name, check_result in result.checks.items():
            self._client.score(
                trace_id=trace_id,
                observation_id=observation_id,
                name=f"gridseal_{check_name}",
                value=check_result.score,
                comment=f"{check_name} check: {'passed' if check_result.passed else 'failed'} "
                        f"(threshold: {check_result.threshold})",
            )

        # Log flags if any
        if result.flags:
            self._client.score(
                trace_id=trace_id,
                observation_id=observation_id,
                name="gridseal_flags",
                value=len(result.flags),
                comment="; ".join(result.flags),
            )

        # Log claim-level results if available
        if result.claims:
            supported = sum(1 for c in result.claims if c.status == "supported")
            total = len(result.claims)
            self._client.score(
                trace_id=trace_id,
                observation_id=observation_id,
                name="gridseal_claims_supported",
                value=supported / total if total > 0 else 0.0,
                comment=f"{supported}/{total} claims supported",
            )

    def score_generation(
        self,
        trace_id: str,
        generation_id: str,
        result: VerificationResult[Any],
    ) -> None:
        """
        Log verification scores to a specific generation.

        Args:
            trace_id: The Langfuse trace ID
            generation_id: The generation ID to score
            result: GridSeal verification result
        """
        self.score_trace(
            trace_id=trace_id,
            result=result,
            observation_id=generation_id,
        )

    def flush(self) -> None:
        """Flush pending Langfuse events."""
        if self._client is not None:
            try:
                self._client.flush()
            except Exception as e:
                logger.warning(f"Failed to flush Langfuse: {e}")
