# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
GridSeal: Verification and compliance-grade audit logging for LLM applications.

GridSeal sits between your AI systems and their outputs, providing:
- Hallucination detection via verification checks
- Immutable audit trails with hash chain integrity
- Compliance-grade logging for FedRAMP, NIST AI RMF, EU AI Act
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Any, Callable, ParamSpec, TypeVar

from gridseal._version import __version__
from gridseal.audit import AuditStore
from gridseal.core import (
    AdapterError,
    AuditConfig,
    AuditError,
    AuditRecord,
    CheckResult,
    ClaimVerification,
    ConfigurationError,
    GridSealConfig,
    GridSealError,
    IntegrityError,
    RequestContext,
    VerificationConfig,
    VerificationError,
    VerificationProfile,
    VerificationResult,
    clear_context,
    get_context,
    parse_config,
    set_context,
)
from gridseal.verification import VerificationEngine

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

__all__ = [
    "__version__",
    "GridSeal",
    "CheckResult",
    "ClaimVerification",
    "VerificationResult",
    "AuditRecord",
    "GridSealConfig",
    "VerificationConfig",
    "VerificationProfile",
    "AuditConfig",
    "GridSealError",
    "ConfigurationError",
    "VerificationError",
    "AuditError",
    "AdapterError",
    "IntegrityError",
    "VerificationEngine",
    "AuditStore",
]


class GridSeal:
    """
    Main entry point for GridSeal verification and audit logging.

    GridSeal can operate in two modes:

    1. Standalone Mode (default):
       Full verification and audit logging.

    2. Adapter Mode:
       Adds compliance layer on top of existing observability tools.
    """

    def __init__(
        self,
        mode: str | None = None,
        verification: dict[str, Any] | VerificationConfig | None = None,
        audit: dict[str, Any] | AuditConfig | None = None,
        adapter: Any = None,
        langfuse_client: Any = None,
        verification_profiles: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize GridSeal.

        Args:
            mode: Operating mode ("standalone" or "adapter")
            verification: Verification configuration
            audit: Audit configuration
            adapter: Adapter instance for adapter mode
            langfuse_client: Optional Langfuse client for auto-scoring
            verification_profiles: Named verification profiles
        """
        self.config = parse_config(
            mode=mode,
            verification=verification,
            audit=audit,
            verification_profiles=verification_profiles,
        )
        self.engine = VerificationEngine(self.config.verification)
        self.store = AuditStore(self.config.audit)
        self._adapter = adapter
        self._langfuse_client = langfuse_client
        self._langfuse_scorer = None

        if adapter is not None:
            adapter.attach_store(self.store)

        if langfuse_client is not None:
            from gridseal.integrations.langfuse import LangfuseScorer
            self._langfuse_scorer = LangfuseScorer(client=langfuse_client)

    def verify(
        self,
        func: Callable[P, T] | None = None,
        *,
        checks: list[str] | None = None,
        threshold: float | None = None,
    ) -> Callable[[Callable[P, T]], Callable[P, VerificationResult[T]]] | Callable[
        P, VerificationResult[T]
    ]:
        """
        Decorator to verify LLM function outputs.

        Can be used with or without arguments:
            @gs.verify
            def my_func(...): ...

            @gs.verify(threshold=0.8)
            def my_func(...): ...

        Args:
            func: The function to decorate
            checks: Override which checks to run
            threshold: Override default threshold
        """
        def decorator(
            fn: Callable[P, T],
        ) -> Callable[P, VerificationResult[T]]:
            @functools.wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> VerificationResult[T]:
                existing_ctx = get_context()
                owns_context = existing_ctx is None
                if owns_context:
                    ctx = RequestContext()
                    set_context(ctx)
                else:
                    ctx = existing_ctx

                try:
                    response = fn(*args, **kwargs)

                    query = ""
                    context: list[str] = []

                    if args:
                        query = str(args[0]) if args else ""
                        if len(args) > 1 and isinstance(args[1], list):
                            context = [str(c) for c in args[1]]

                    if "query" in kwargs:
                        query = str(kwargs["query"])
                    if "context" in kwargs:
                        kwctx = kwargs["context"]
                        if isinstance(kwctx, list):
                            context = [str(c) for c in kwctx]

                    response_str = str(response) if response is not None else ""

                    result = self.engine.verify(
                        query=query,
                        context=context,
                        response=response_str,
                    )

                    ctx.query = query
                    ctx.context = context
                    ctx.response = response_str
                    ctx.verification_passed = result.passed
                    ctx.verification_results = {
                        k: v.to_dict() for k, v in result.checks.items()
                    }

                    if not result.passed:
                        if self.config.verification.on_fail == "block":
                            raise VerificationError(
                                "Verification failed",
                                results=result.checks,
                            )

                    return VerificationResult(
                        response=response,  # type: ignore[arg-type]
                        passed=result.passed,
                        checks=result.checks,
                        flags=result.flags,
                        audit_id=ctx.audit_id,
                        duration_ms=result.duration_ms,
                    )
                finally:
                    if owns_context:
                        clear_context()

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def audit(
        self,
        func: Callable[P, T] | None = None,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Callable[[Callable[P, T]], Callable[P, T]] | Callable[P, T]:
        """
        Decorator to audit LLM function calls.

        Can be used with or without arguments:
            @gs.audit
            def my_func(...): ...

            @gs.audit(metadata={"user": "test"})
            def my_func(...): ...

        Args:
            func: The function to decorate
            metadata: Additional metadata to include in audit record
        """
        def decorator(fn: Callable[P, T]) -> Callable[P, T]:
            @functools.wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                existing_ctx = get_context()
                owns_context = existing_ctx is None
                if owns_context:
                    ctx = RequestContext()
                    set_context(ctx)
                else:
                    ctx = existing_ctx

                try:
                    result = fn(*args, **kwargs)

                    if isinstance(result, VerificationResult):
                        response_str = str(result.response)
                        passed = result.passed
                        verification_results = {
                            k: v.to_dict() for k, v in result.checks.items()
                        }
                    else:
                        response_str = str(result) if result is not None else ""
                        passed = ctx.verification_passed
                        verification_results = ctx.verification_results

                    query = ctx.query
                    context = ctx.context

                    if not query and args:
                        query = str(args[0])
                    if not context and len(args) > 1 and isinstance(args[1], list):
                        context = [str(c) for c in args[1]]

                    combined_metadata = metadata.copy() if metadata else {}
                    combined_metadata.update(ctx.metadata)

                    record = self.store.log(
                        query=query,
                        context=context,
                        response=response_str,
                        verification_passed=passed,
                        verification_results=verification_results,
                        metadata=combined_metadata,
                    )

                    ctx.audit_id = record.id

                    if isinstance(result, VerificationResult):
                        result.audit_id = record.id

                    return result

                finally:
                    if owns_context:
                        clear_context()

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def start_sync(self) -> None:
        """Start adapter sync (adapter mode only)."""
        if self._adapter is None:
            raise ConfigurationError("No adapter configured")
        self._adapter.start_sync()

    def stop_sync(self) -> None:
        """Stop adapter sync (adapter mode only)."""
        if self._adapter is not None:
            self._adapter.stop_sync()

    async def verify_async(
        self,
        response: str,
        context: list[str],
        query: str = "",
        profile: str = "default",
        callback: Callable[[VerificationResult[str]], None] | None = None,
    ) -> VerificationResult[str]:
        """
        Verify a response asynchronously (non-blocking).

        Designed for fire-and-forget usage after streaming responses.
        Runs verification in a thread pool to avoid blocking the event loop.

        Args:
            response: The LLM response to verify
            context: List of context documents
            query: Optional query string
            profile: Verification profile to use
            callback: Optional callback when verification completes

        Returns:
            VerificationResult with scores and claims
        """
        loop = asyncio.get_event_loop()

        # Get profile settings
        profile_config = self.config.get_profile(profile)

        # Run verification in thread pool
        result = await loop.run_in_executor(
            None,
            self._run_verification,
            response,
            context,
            query,
            profile_config,
            profile,
        )

        if callback is not None:
            try:
                callback(result)
            except Exception as e:
                logger.warning(f"Verification callback error: {e}")

        return result

    async def verify_and_score(
        self,
        response: str,
        context: list[str],
        query: str = "",
        trace_id: str | None = None,
        observation_id: str | None = None,
        profile: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> VerificationResult[str]:
        """
        Verify response and automatically log scores to Langfuse.

        Combines verification with Langfuse scoring in a single async call.
        Designed for streaming applications that need post-hoc verification.

        Args:
            response: The LLM response to verify
            context: List of context documents
            query: Optional query string
            trace_id: Langfuse trace ID for scoring
            observation_id: Langfuse observation ID for granular scoring
            profile: Verification profile to use
            metadata: Additional metadata to include in audit

        Returns:
            VerificationResult with scores, claims, and audit_id
        """
        # Run verification
        result = await self.verify_async(
            response=response,
            context=context,
            query=query,
            profile=profile,
        )

        # Log to audit store
        record = self.store.log(
            query=query,
            context=context,
            response=response,
            verification_passed=result.passed,
            verification_results={k: v.to_dict() for k, v in result.checks.items()},
            metadata=metadata or {},
        )
        result.audit_id = record.id

        # Score to Langfuse if configured and trace_id provided
        if trace_id and self._langfuse_scorer:
            try:
                self._langfuse_scorer.score_trace(
                    trace_id=trace_id,
                    result=result,
                    observation_id=observation_id,
                )
            except Exception as e:
                logger.warning(f"Langfuse scoring error: {e}")

        return result

    def _run_verification(
        self,
        response: str,
        context: list[str],
        query: str,
        profile_config: VerificationProfile,
        profile_name: str,
    ) -> VerificationResult[str]:
        """
        Run verification synchronously (called from thread pool).

        Internal method for async verification.
        """
        start_time = time.perf_counter()

        # Use profile threshold
        threshold = profile_config.threshold

        # Run engine verification
        engine_result = self.engine.verify(
            query=query,
            context=context,
            response=response,
        )

        # Extract claims if enabled
        claims: list[ClaimVerification] = []
        if self.config.verification.extract_claims:
            claims = self._extract_and_verify_claims(response, context)

        # Determine pass/fail based on profile settings
        passed = engine_result.passed
        if profile_config.strict and claims:
            # In strict mode, all claims must be supported
            unsupported = [c for c in claims if c.status != "supported"]
            if unsupported:
                passed = False

        if profile_config.require_citations:
            citation_check = engine_result.checks.get("citation")
            if citation_check is None or not citation_check.passed:
                passed = False

        duration_ms = (time.perf_counter() - start_time) * 1000

        return VerificationResult(
            response=response,
            passed=passed,
            checks=engine_result.checks,
            flags=engine_result.flags,
            claims=claims,
            audit_id=None,
            duration_ms=duration_ms,
            profile=profile_name,
        )

    def _extract_and_verify_claims(
        self,
        response: str,
        context: list[str],
    ) -> list[ClaimVerification]:
        """Extract and verify individual claims from response."""
        from gridseal.verification.claims import extract_claims, match_claim_to_context

        extracted = extract_claims(response)
        verified_claims: list[ClaimVerification] = []

        for claim in extracted:
            source_text, score = match_claim_to_context(claim, context)

            # Determine status based on score
            if score >= 0.7:
                status = "supported"
            elif score >= 0.3:
                status = "unverifiable"
            else:
                status = "contradicted"

            verified_claims.append(ClaimVerification(
                claim_text=claim.text,
                source_text=source_text,
                entailment_score=score,
                status=status,
                span_start=claim.span_start,
                span_end=claim.span_end,
            ))

        return verified_claims

    def close(self) -> None:
        """Close GridSeal and release resources."""
        self.stop_sync()
        if self._langfuse_scorer:
            self._langfuse_scorer.flush()
        self.store.close()
