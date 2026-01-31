# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for standalone flow."""

from __future__ import annotations

import pytest

from gridseal import GridSeal, VerificationResult
from gridseal.core.exceptions import VerificationError


class TestStandaloneFlow:
    """Integration tests for standalone verification and audit flow."""

    def test_basic_verify_decorator(
        self,
        gs: GridSeal,
        sample_context: list[str],
    ) -> None:
        """Test basic @gs.verify decorator."""

        @gs.verify
        def get_answer(query: str, context: list[str]) -> str:
            return "Claims over $1000 require manager approval."

        result = get_answer("What is the policy?", sample_context)

        assert isinstance(result, VerificationResult)
        assert result.response == "Claims over $1000 require manager approval."
        assert isinstance(result.passed, bool)
        assert "grounding" in result.checks

    def test_basic_audit_decorator(self, gs_no_verify: GridSeal) -> None:
        """Test basic @gs.audit decorator."""

        @gs_no_verify.audit
        def get_answer(query: str, context: list[str]) -> str:
            return "Test response"

        result = get_answer("Test query", ["context"])

        assert result == "Test response"
        assert gs_no_verify.store.count() == 1

        record = gs_no_verify.store.query()[0]
        assert record.query == "Test query"
        assert record.response == "Test response"

    def test_combined_verify_audit(
        self,
        gs: GridSeal,
        sample_context: list[str],
    ) -> None:
        """Test combined @gs.verify and @gs.audit decorators."""

        @gs.verify
        @gs.audit
        def get_answer(query: str, context: list[str]) -> str:
            return "Claims over $1000 need approval per policy guidelines."

        result = get_answer("What is the claim policy?", sample_context)

        assert isinstance(result, VerificationResult)
        assert result.audit_id is not None
        assert gs.store.count() == 1

        record = gs.store.get(result.audit_id)
        assert record is not None
        assert record.verification_passed == result.passed

    def test_verify_blocking_mode(self, sample_context: list[str]) -> None:
        """Test verification with on_fail='block'."""
        gs = GridSeal(
            verification={
                "checks": ["grounding"],
                "threshold": 0.99,
                "on_fail": "block",
            },
            audit={"backend": "memory"},
        )

        @gs.verify
        def get_answer(query: str, context: list[str]) -> str:
            return "Completely unrelated response about weather."

        with pytest.raises(VerificationError):
            get_answer("What is the policy?", sample_context)

    def test_verify_flag_mode(
        self,
        gs: GridSeal,
        sample_context: list[str],
    ) -> None:
        """Test verification with on_fail='flag' (default)."""

        @gs.verify
        def get_answer(query: str, context: list[str]) -> str:
            return "Unrelated response."

        result = get_answer("What is the policy?", sample_context)

        assert isinstance(result, VerificationResult)

    def test_multiple_calls_audit_chain(self, gs_no_verify: GridSeal) -> None:
        """Test that multiple calls create linked audit records."""

        @gs_no_verify.audit
        def get_answer(query: str, context: list[str]) -> str:
            return f"Answer to: {query}"

        get_answer("Query 1", [])
        get_answer("Query 2", [])
        get_answer("Query 3", [])

        assert gs_no_verify.store.count() == 3
        assert gs_no_verify.store.verify_integrity() is True

    def test_verify_with_kwargs(
        self,
        gs: GridSeal,
        sample_context: list[str],
    ) -> None:
        """Test verify decorator with keyword arguments."""

        @gs.verify
        def get_answer(query: str, context: list[str]) -> str:
            return "Claims need manager approval."

        result = get_answer(query="What is needed?", context=sample_context)

        assert isinstance(result, VerificationResult)
        assert "grounding" in result.checks

    def test_audit_with_metadata(self, gs_no_verify: GridSeal) -> None:
        """Test audit decorator with metadata."""

        @gs_no_verify.audit(metadata={"user_id": "123"})
        def get_answer(query: str, context: list[str]) -> str:
            return "Response"

        get_answer("Query", [])

        record = gs_no_verify.store.query()[0]
        assert record.metadata.get("user_id") == "123"

    def test_all_checks_integration(self, sample_context: list[str]) -> None:
        """Test with all verification checks enabled."""
        gs = GridSeal(
            verification={
                "checks": ["grounding", "confidence", "relevance"],
                "threshold": 0.3,
            },
            audit={"backend": "memory"},
        )

        @gs.verify
        @gs.audit
        def get_answer(query: str, context: list[str]) -> str:
            return (
                "Claims over $1000 require manager approval. "
                "This policy ensures proper oversight. "
                "All claims must be documented properly."
            )

        result = get_answer("What is the claim approval process?", sample_context)

        assert isinstance(result, VerificationResult)
        assert "grounding" in result.checks
        assert "confidence" in result.checks
        assert "relevance" in result.checks

    def test_gridseal_close(self) -> None:
        """Test GridSeal close method."""
        gs = GridSeal(audit={"backend": "memory"})

        gs.store.log(query="test", context=[], response="response")
        gs.close()

    def test_verification_result_properties(
        self,
        gs: GridSeal,
        sample_context: list[str],
    ) -> None:
        """Test VerificationResult property accessors."""

        @gs.verify
        def get_answer(query: str, context: list[str]) -> str:
            return "Claims over $1000 need approval."

        result = get_answer("Policy question", sample_context)

        assert result.grounding_score is not None
        assert 0 <= result.grounding_score <= 1

    def test_empty_context_handling(self, gs: GridSeal) -> None:
        """Test handling of empty context."""

        @gs.verify
        @gs.audit
        def get_answer(query: str, context: list[str]) -> str:
            return "Default response."

        result = get_answer("Query", [])

        assert isinstance(result, VerificationResult)
        assert gs.store.count() == 1

    def test_result_serialization(
        self,
        gs: GridSeal,
        sample_context: list[str],
    ) -> None:
        """Test that results can be serialized."""

        @gs.verify
        def get_answer(query: str, context: list[str]) -> str:
            return "Claims need approval."

        result = get_answer("Query", sample_context)
        result_dict = result.to_dict()

        assert "response" in result_dict
        assert "passed" in result_dict
        assert "checks" in result_dict
        assert "grounding" in result_dict["checks"]


class TestAdapterMode:
    """Tests for adapter mode."""

    def test_adapter_mode_config(self) -> None:
        """Test adapter mode configuration."""
        gs = GridSeal(
            mode="adapter",
            audit={"backend": "memory"},
        )

        assert gs.config.mode == "adapter"

    def test_start_sync_without_adapter(self) -> None:
        """Test that start_sync fails without adapter."""
        from gridseal.core.exceptions import ConfigurationError

        gs = GridSeal(audit={"backend": "memory"})

        with pytest.raises(ConfigurationError):
            gs.start_sync()

    def test_stop_sync_without_adapter(self) -> None:
        """Test that stop_sync is safe without adapter."""
        gs = GridSeal(audit={"backend": "memory"})

        gs.stop_sync()
