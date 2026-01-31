# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""GridSeal exception hierarchy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gridseal.core.types import CheckResult


class GridSealError(Exception):
    """Base exception for all GridSeal errors."""

    pass


class ConfigurationError(GridSealError):
    """Raised when GridSeal is misconfigured."""

    pass


class VerificationError(GridSealError):
    """Raised when verification fails and on_fail='block'."""

    def __init__(
        self,
        message: str,
        results: dict[str, "CheckResult"] | None = None,
    ) -> None:
        super().__init__(message)
        self.results = results or {}


class AuditError(GridSealError):
    """Raised when audit logging fails."""

    pass


class AdapterError(GridSealError):
    """Raised when adapter operations fail."""

    pass


class IntegrityError(GridSealError):
    """Raised when audit log integrity check fails."""

    pass
