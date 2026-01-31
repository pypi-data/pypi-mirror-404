# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Request context management using contextvars."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequestContext:
    """
    Context for a single request/verification cycle.

    Used to track state across decorator calls and enable
    correlation between verify and audit operations.
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    context: list[str] = field(default_factory=list)
    response: str = ""
    verification_passed: bool = True
    verification_results: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    audit_id: str | None = None


_current_context: ContextVar[RequestContext | None] = ContextVar(
    "gridseal_context",
    default=None,
)


def get_context() -> RequestContext | None:
    """Get the current request context."""
    return _current_context.get()


def set_context(ctx: RequestContext) -> None:
    """Set the current request context."""
    _current_context.set(ctx)


def clear_context() -> None:
    """Clear the current request context."""
    _current_context.set(None)
