# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configuration models for GridSeal."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class VerificationProfile(BaseModel):
    """
    A verification profile with specific settings.

    Profiles allow different verification strictness for different use cases
    (e.g., "legal" vs "general" queries).
    """

    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Score threshold for passing checks",
    )
    checks: list[str] | None = Field(
        default=None,
        description="Override checks for this profile (None = use default)",
    )
    require_citations: bool = Field(
        default=False,
        description="Require citation check to pass",
    )
    strict: bool = Field(
        default=False,
        description="Strict mode: all claims must be supported",
    )
    on_fail: Literal["log", "flag", "warn", "annotate", "block"] | None = Field(
        default=None,
        description="Override on_fail action for this profile",
    )


class VerificationConfig(BaseModel):
    """
    Configuration for the verification engine.

    Attributes:
        checks: List of check names to run (e.g., ["grounding", "confidence"])
        threshold: Default score threshold for all checks (0.0 to 1.0)
        on_fail: Action when checks fail
            - "log": Silent logging only
            - "flag": Log warning and add to flags
            - "warn": Return warning metadata
            - "annotate": Suggest adding disclaimer
            - "block": Raise VerificationError
        nli_mode: NLI model speed/accuracy tradeoff
            - "fast": DistilBERT (~50ms)
            - "balanced": DeBERTa-base (~150ms)
            - "accurate": DeBERTa-large (~300ms)
    """

    checks: list[str] = Field(
        default=["grounding"],
        description="List of verification checks to run",
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Default score threshold for passing checks",
    )
    on_fail: Literal["log", "flag", "warn", "annotate", "block"] = Field(
        default="flag",
        description="Action when verification fails",
    )
    thresholds: dict[str, float] = Field(
        default_factory=dict,
        description="Per-check threshold overrides",
    )
    nli_mode: Literal["fast", "balanced", "accurate"] = Field(
        default="fast",
        description="NLI model speed/accuracy tradeoff",
    )
    extract_claims: bool = Field(
        default=False,
        description="Extract and verify individual claims",
    )

    def get_threshold(self, check_name: str) -> float:
        """Get threshold for a specific check."""
        return self.thresholds.get(check_name, self.threshold)


class AuditConfig(BaseModel):
    """
    Configuration for the audit store.

    Attributes:
        backend: Storage backend ("sqlite", "postgresql", "memory")
        path: Path for SQLite database file
        connection: Connection string for PostgreSQL
        retention_days: How long to keep records (default: 7 years)
    """

    backend: Literal["sqlite", "postgresql", "memory"] = Field(
        default="sqlite",
        description="Storage backend type",
    )
    path: str = Field(
        default="./gridseal_audit.db",
        description="Path for SQLite database",
    )
    connection: str | None = Field(
        default=None,
        description="PostgreSQL connection string",
    )
    retention_days: int = Field(
        default=2555,
        ge=1,
        description="Audit record retention period in days",
    )


class GridSealConfig(BaseModel):
    """
    Top-level GridSeal configuration.

    Attributes:
        mode: Operating mode
            - "standalone": Full verification + tracing
            - "adapter": Adds compliance to existing observability
        verification: Verification engine configuration
        audit: Audit store configuration
        verification_profiles: Named profiles with different settings
    """

    mode: Literal["standalone", "adapter"] = Field(
        default="standalone",
        description="Operating mode",
    )
    verification: VerificationConfig = Field(default_factory=VerificationConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    verification_profiles: dict[str, VerificationProfile] = Field(
        default_factory=lambda: {"default": VerificationProfile()},
        description="Named verification profiles",
    )

    model_config = {"extra": "forbid"}

    def get_profile(self, name: str) -> VerificationProfile:
        """Get a verification profile by name."""
        if name not in self.verification_profiles:
            return self.verification_profiles.get("default", VerificationProfile())
        return self.verification_profiles[name]


def parse_config(
    mode: str | None = None,
    verification: dict[str, Any] | VerificationConfig | None = None,
    audit: dict[str, Any] | AuditConfig | None = None,
    verification_profiles: dict[str, dict[str, Any] | VerificationProfile] | None = None,
) -> GridSealConfig:
    """
    Parse configuration from various input formats.

    Accepts dicts or config objects, returns validated GridSealConfig.
    """
    if isinstance(verification, dict):
        verification = VerificationConfig(**verification)
    if isinstance(audit, dict):
        audit = AuditConfig(**audit)

    parsed_profiles: dict[str, VerificationProfile] = {"default": VerificationProfile()}
    if verification_profiles:
        for name, profile in verification_profiles.items():
            if isinstance(profile, dict):
                parsed_profiles[name] = VerificationProfile(**profile)
            else:
                parsed_profiles[name] = profile

    return GridSealConfig(
        mode=mode or "standalone",  # type: ignore[arg-type]
        verification=verification or VerificationConfig(),
        audit=audit or AuditConfig(),
        verification_profiles=parsed_profiles,
    )
