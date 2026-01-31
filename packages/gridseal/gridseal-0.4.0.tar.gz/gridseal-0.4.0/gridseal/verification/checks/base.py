# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Base class for verification checks."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from gridseal.core.types import CheckResult

logger = logging.getLogger(__name__)


class BaseCheck(ABC):
    """
    Abstract base class for all verification checks.

    Subclasses must implement:
        - name: Unique identifier for the check
        - check(): The actual verification logic
    """

    name: str = "base"

    @abstractmethod
    def check(
        self,
        query: str,
        context: list[str],
        response: str,
        threshold: float,
    ) -> CheckResult:
        """
        Run the verification check.

        Args:
            query: The input query/prompt
            context: List of context documents (for RAG systems)
            response: The LLM response to verify
            threshold: Score threshold for passing

        Returns:
            CheckResult with score and pass/fail status

        Note:
            Implementations should catch exceptions and return
            a failed CheckResult with error message rather than
            raising, to allow other checks to continue.
        """
        pass

    def safe_check(
        self,
        query: str,
        context: list[str],
        response: str,
        threshold: float,
    ) -> CheckResult:
        """
        Wrapper that catches exceptions and returns error result.

        Use this in the verification engine to ensure one failing
        check doesn't prevent others from running.
        """
        start_time = time.perf_counter()
        try:
            result = self.check(query, context, response, threshold)
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                name=result.name,
                passed=result.passed,
                score=result.score,
                threshold=result.threshold,
                details=result.details,
                error=result.error,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.exception(f"Check '{self.name}' raised exception: {e}")
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                name=self.name,
                passed=False,
                score=0.0,
                threshold=threshold,
                error=str(e),
                duration_ms=duration_ms,
            )
