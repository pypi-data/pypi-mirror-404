# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for verification engine."""

from __future__ import annotations

import pytest

from gridseal.core.config import VerificationConfig
from gridseal.core.types import CheckResult
from gridseal.verification.checks.base import BaseCheck
from gridseal.verification.engine import CHECK_REGISTRY, VerificationEngine


class TestVerificationEngine:
    """Tests for VerificationEngine."""

    def test_default_config(self) -> None:
        """Test engine with default configuration."""
        engine = VerificationEngine()

        assert engine.config.checks == ["grounding"]
        assert "grounding" in engine.enabled_checks

    def test_custom_config(self) -> None:
        """Test engine with custom configuration."""
        config = VerificationConfig(
            checks=["grounding", "confidence"],
            threshold=0.8,
        )
        engine = VerificationEngine(config)

        assert engine.config.threshold == 0.8
        assert "grounding" in engine.enabled_checks
        assert "confidence" in engine.enabled_checks

    def test_available_checks(self) -> None:
        """Test available_checks property."""
        engine = VerificationEngine()

        available = engine.available_checks

        assert "grounding" in available
        assert "confidence" in available
        assert "relevance" in available
        assert "citation" in available

    def test_enabled_checks(self) -> None:
        """Test enabled_checks property."""
        config = VerificationConfig(checks=["grounding"])
        engine = VerificationEngine(config)

        assert engine.enabled_checks == ["grounding"]

    def test_unknown_check_skipped(self) -> None:
        """Test that unknown check names are skipped."""
        config = VerificationConfig(checks=["grounding", "unknown_check"])
        engine = VerificationEngine(config)

        assert "grounding" in engine.enabled_checks
        assert "unknown_check" not in engine.enabled_checks

    def test_verify_returns_result(
        self,
        sample_context: list[str],
        grounded_response: str,
    ) -> None:
        """Test that verify returns VerificationResult."""
        config = VerificationConfig(checks=["grounding"], threshold=0.3)
        engine = VerificationEngine(config)

        result = engine.verify(
            query="Test query",
            context=sample_context,
            response=grounded_response,
        )

        assert result.response == grounded_response
        assert isinstance(result.passed, bool)
        assert "grounding" in result.checks
        assert result.duration_ms > 0

    def test_verify_multiple_checks(self, sample_context: list[str]) -> None:
        """Test verification with multiple checks."""
        config = VerificationConfig(
            checks=["grounding", "confidence", "relevance"],
            threshold=0.3,
        )
        engine = VerificationEngine(config)

        result = engine.verify(
            query="What is the claim policy?",
            context=sample_context,
            response=(
                "Claims over $1000 require manager approval. "
                "This is consistent with company policy. "
                "Please submit claims promptly."
            ),
        )

        assert "grounding" in result.checks
        assert "confidence" in result.checks
        assert "relevance" in result.checks

    def test_verify_with_threshold_override(
        self,
        sample_context: list[str],
    ) -> None:
        """Test per-check threshold override."""
        config = VerificationConfig(
            checks=["grounding"],
            threshold=0.5,
            thresholds={"grounding": 0.9},
        )
        engine = VerificationEngine(config)

        result = engine.verify(
            query="Test",
            context=sample_context,
            response="Claims need approval.",
        )

        assert result.checks["grounding"].threshold == 0.9

    def test_verify_flags_failures(self, sample_context: list[str]) -> None:
        """Test that failed checks are flagged."""
        config = VerificationConfig(checks=["grounding"], threshold=0.99)
        engine = VerificationEngine(config)

        result = engine.verify(
            query="Test",
            context=sample_context,
            response="Somewhat related to claims.",
        )

        if not result.passed:
            assert len(result.flags) > 0
            assert "grounding" in result.flags[0]

    def test_verify_empty_checks(self) -> None:
        """Test verification with no checks enabled."""
        config = VerificationConfig(checks=[])
        engine = VerificationEngine(config)

        result = engine.verify(
            query="Test",
            context=["Context"],
            response="Response",
        )

        assert result.passed is True
        assert len(result.checks) == 0

    def test_register_custom_check(self) -> None:
        """Test registering a custom check."""

        class CustomCheck(BaseCheck):
            name = "custom"

            def check(
                self,
                query: str,
                context: list[str],
                response: str,
                threshold: float,
            ) -> CheckResult:
                return CheckResult(
                    name=self.name,
                    passed=True,
                    score=1.0,
                    threshold=threshold,
                )

        engine = VerificationEngine()
        custom = CustomCheck()
        engine.register_check(custom)

        assert "custom" in engine.enabled_checks
        assert engine._checks["custom"] is custom

    def test_check_registry_contents(self) -> None:
        """Test that CHECK_REGISTRY contains expected checks."""
        assert "grounding" in CHECK_REGISTRY
        assert "confidence" in CHECK_REGISTRY
        assert "relevance" in CHECK_REGISTRY
        assert "citation" in CHECK_REGISTRY

    def test_verify_result_duration(self, sample_context: list[str]) -> None:
        """Test that verification duration is measured."""
        config = VerificationConfig(checks=["grounding"], threshold=0.3)
        engine = VerificationEngine(config)

        result = engine.verify(
            query="Test",
            context=sample_context,
            response="Claims over $1000 need approval.",
        )

        assert result.duration_ms >= 0

    def test_verify_all_passed(self, sample_context: list[str]) -> None:
        """Test result.passed reflects all checks."""
        config = VerificationConfig(
            checks=["grounding", "relevance"],
            threshold=0.2,
        )
        engine = VerificationEngine(config)

        result = engine.verify(
            query="What is the claim policy?",
            context=sample_context,
            response="The claim policy requires manager approval for amounts over $1000.",
        )

        all_individual_passed = all(c.passed for c in result.checks.values())
        assert result.passed == all_individual_passed
