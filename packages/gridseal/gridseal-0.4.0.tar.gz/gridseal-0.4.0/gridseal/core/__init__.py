# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Core GridSeal types and configuration."""

from gridseal.core.config import (
    AuditConfig,
    GridSealConfig,
    VerificationConfig,
    VerificationProfile,
    parse_config,
)
from gridseal.core.context import (
    RequestContext,
    clear_context,
    get_context,
    set_context,
)
from gridseal.core.exceptions import (
    AdapterError,
    AuditError,
    ConfigurationError,
    GridSealError,
    IntegrityError,
    VerificationError,
)
from gridseal.core.types import (
    AuditRecord,
    CheckResult,
    ClaimVerification,
    VerificationResult,
)

__all__ = [
    "CheckResult",
    "ClaimVerification",
    "VerificationResult",
    "AuditRecord",
    "GridSealConfig",
    "VerificationConfig",
    "VerificationProfile",
    "AuditConfig",
    "parse_config",
    "GridSealError",
    "ConfigurationError",
    "VerificationError",
    "AuditError",
    "AdapterError",
    "IntegrityError",
    "RequestContext",
    "get_context",
    "set_context",
    "clear_context",
]
