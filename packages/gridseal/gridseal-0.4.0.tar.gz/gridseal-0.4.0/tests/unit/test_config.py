# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for configuration models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gridseal.core.config import (
    AuditConfig,
    GridSealConfig,
    VerificationConfig,
    parse_config,
)


class TestVerificationConfig:
    """Tests for VerificationConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = VerificationConfig()

        assert config.checks == ["grounding"]
        assert config.threshold == 0.7
        assert config.on_fail == "flag"
        assert config.thresholds == {}

    def test_custom_values(self) -> None:
        """Test custom configuration."""
        config = VerificationConfig(
            checks=["grounding", "confidence"],
            threshold=0.8,
            on_fail="block",
            thresholds={"confidence": 0.9},
        )

        assert config.checks == ["grounding", "confidence"]
        assert config.threshold == 0.8
        assert config.on_fail == "block"
        assert config.thresholds == {"confidence": 0.9}

    def test_get_threshold_default(self) -> None:
        """Test get_threshold returns default when not overridden."""
        config = VerificationConfig(threshold=0.7)

        assert config.get_threshold("grounding") == 0.7

    def test_get_threshold_override(self) -> None:
        """Test get_threshold returns override when set."""
        config = VerificationConfig(
            threshold=0.7,
            thresholds={"confidence": 0.9},
        )

        assert config.get_threshold("grounding") == 0.7
        assert config.get_threshold("confidence") == 0.9

    def test_threshold_validation_min(self) -> None:
        """Test threshold minimum validation."""
        with pytest.raises(ValidationError):
            VerificationConfig(threshold=-0.1)

    def test_threshold_validation_max(self) -> None:
        """Test threshold maximum validation."""
        with pytest.raises(ValidationError):
            VerificationConfig(threshold=1.5)

    def test_on_fail_validation(self) -> None:
        """Test on_fail literal validation."""
        with pytest.raises(ValidationError):
            VerificationConfig(on_fail="invalid")  # type: ignore[arg-type]

    def test_on_fail_valid_values(self) -> None:
        """Test all valid on_fail values."""
        for value in ["log", "flag", "block"]:
            config = VerificationConfig(on_fail=value)  # type: ignore[arg-type]
            assert config.on_fail == value


class TestAuditConfig:
    """Tests for AuditConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = AuditConfig()

        assert config.backend == "sqlite"
        assert config.path == "./gridseal_audit.db"
        assert config.connection is None
        assert config.retention_days == 2555

    def test_custom_values(self) -> None:
        """Test custom configuration."""
        config = AuditConfig(
            backend="postgresql",
            connection="postgresql://localhost/db",
            retention_days=365,
        )

        assert config.backend == "postgresql"
        assert config.connection == "postgresql://localhost/db"
        assert config.retention_days == 365

    def test_memory_backend(self) -> None:
        """Test memory backend configuration."""
        config = AuditConfig(backend="memory")

        assert config.backend == "memory"

    def test_backend_validation(self) -> None:
        """Test backend literal validation."""
        with pytest.raises(ValidationError):
            AuditConfig(backend="invalid")  # type: ignore[arg-type]

    def test_retention_days_min(self) -> None:
        """Test retention_days minimum validation."""
        with pytest.raises(ValidationError):
            AuditConfig(retention_days=0)


class TestGridSealConfig:
    """Tests for GridSealConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = GridSealConfig()

        assert config.mode == "standalone"
        assert isinstance(config.verification, VerificationConfig)
        assert isinstance(config.audit, AuditConfig)

    def test_custom_values(self) -> None:
        """Test custom configuration."""
        config = GridSealConfig(
            mode="adapter",
            verification=VerificationConfig(threshold=0.8),
            audit=AuditConfig(backend="memory"),
        )

        assert config.mode == "adapter"
        assert config.verification.threshold == 0.8
        assert config.audit.backend == "memory"

    def test_mode_validation(self) -> None:
        """Test mode literal validation."""
        with pytest.raises(ValidationError):
            GridSealConfig(mode="invalid")  # type: ignore[arg-type]

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError):
            GridSealConfig(unknown_field="value")  # type: ignore[call-arg]


class TestParseConfig:
    """Tests for parse_config function."""

    def test_defaults(self) -> None:
        """Test with no arguments."""
        config = parse_config()

        assert config.mode == "standalone"
        assert isinstance(config.verification, VerificationConfig)
        assert isinstance(config.audit, AuditConfig)

    def test_with_dicts(self) -> None:
        """Test with dictionary arguments."""
        config = parse_config(
            mode="adapter",
            verification={"threshold": 0.8},
            audit={"backend": "memory"},
        )

        assert config.mode == "adapter"
        assert config.verification.threshold == 0.8
        assert config.audit.backend == "memory"

    def test_with_config_objects(self) -> None:
        """Test with config object arguments."""
        verification = VerificationConfig(threshold=0.9)
        audit = AuditConfig(backend="memory")

        config = parse_config(
            verification=verification,
            audit=audit,
        )

        assert config.verification.threshold == 0.9
        assert config.audit.backend == "memory"

    def test_mixed_args(self) -> None:
        """Test with mixed dict and config object arguments."""
        audit = AuditConfig(backend="memory")

        config = parse_config(
            verification={"threshold": 0.6},
            audit=audit,
        )

        assert config.verification.threshold == 0.6
        assert config.audit.backend == "memory"
