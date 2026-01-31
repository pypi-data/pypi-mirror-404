# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Verification engine orchestrator."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from gridseal.core.config import VerificationConfig
from gridseal.core.types import CheckResult, VerificationResult
from gridseal.verification.checks import (
    BaseCheck,
    CitationCheck,
    ConfidenceCheck,
    GroundingCheck,
    RelevanceCheck,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

CHECK_REGISTRY: dict[str, type[BaseCheck]] = {
    "grounding": GroundingCheck,
    "confidence": ConfidenceCheck,
    "relevance": RelevanceCheck,
    "citation": CitationCheck,
}


class VerificationEngine:
    """
    Main verification orchestrator.

    Manages multiple verification checks and aggregates their results.
    Supports configurable thresholds and failure handling.
    """

    def __init__(self, config: VerificationConfig | None = None) -> None:
        """
        Initialize verification engine.

        Args:
            config: Verification configuration. Defaults to grounding check only.
        """
        self.config = config or VerificationConfig()
        self._checks: dict[str, BaseCheck] = {}
        self._init_checks()

    def _init_checks(self) -> None:
        """Initialize configured checks."""
        for check_name in self.config.checks:
            if check_name in CHECK_REGISTRY:
                self._checks[check_name] = CHECK_REGISTRY[check_name]()
                logger.debug(f"Initialized check: {check_name}")
            else:
                logger.warning(f"Unknown check: {check_name}, skipping")

    def register_check(self, check: BaseCheck) -> None:
        """
        Register a custom check.

        Args:
            check: Check instance to register
        """
        self._checks[check.name] = check
        if check.name not in self.config.checks:
            self.config.checks.append(check.name)
        logger.debug(f"Registered custom check: {check.name}")

    def verify(
        self,
        query: str,
        context: list[str],
        response: str,
    ) -> VerificationResult[str]:
        """
        Run all configured verification checks.

        Args:
            query: The input query/prompt
            context: List of context documents
            response: The LLM response to verify

        Returns:
            VerificationResult with aggregated check results
        """
        start_time = time.perf_counter()
        results: dict[str, CheckResult] = {}
        flags: list[str] = []
        all_passed = True

        for check_name, check in self._checks.items():
            threshold = self.config.get_threshold(check_name)
            result = check.safe_check(query, context, response, threshold)
            results[check_name] = result

            if not result.passed:
                all_passed = False
                flag_msg = (
                    f"{check_name} check failed: "
                    f"score={result.score:.2f}, threshold={threshold:.2f}"
                )
                flags.append(flag_msg)
                logger.debug(flag_msg)

            if result.error:
                flags.append(f"{check_name} error: {result.error}")

        duration_ms = (time.perf_counter() - start_time) * 1000

        return VerificationResult(
            response=response,
            passed=all_passed,
            checks=results,
            flags=flags,
            duration_ms=duration_ms,
        )

    @property
    def available_checks(self) -> list[str]:
        """List available check names."""
        return list(CHECK_REGISTRY.keys())

    @property
    def enabled_checks(self) -> list[str]:
        """List enabled check names."""
        return list(self._checks.keys())
