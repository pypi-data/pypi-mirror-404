# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for verification profiles."""

from __future__ import annotations

import pytest

from gridseal.core.config import (
    GridSealConfig,
    VerificationConfig,
    VerificationProfile,
    parse_config,
)


class TestVerificationProfile:
    """Tests for VerificationProfile model."""

    def test_default_values(self) -> None:
        """Test default profile values."""
        profile = VerificationProfile()

        assert profile.threshold == 0.7
        assert profile.checks is None
        assert profile.require_citations is False
        assert profile.strict is False
        assert profile.on_fail is None

    def test_custom_threshold(self) -> None:
        """Test custom threshold."""
        profile = VerificationProfile(threshold=0.9)
        assert profile.threshold == 0.9

    def test_strict_mode(self) -> None:
        """Test strict mode setting."""
        profile = VerificationProfile(strict=True)
        assert profile.strict is True

    def test_require_citations(self) -> None:
        """Test require_citations setting."""
        profile = VerificationProfile(require_citations=True)
        assert profile.require_citations is True

    def test_custom_checks(self) -> None:
        """Test custom checks override."""
        profile = VerificationProfile(checks=["grounding", "citation"])
        assert profile.checks == ["grounding", "citation"]

    def test_on_fail_override(self) -> None:
        """Test on_fail override."""
        profile = VerificationProfile(on_fail="block")
        assert profile.on_fail == "block"


class TestGridSealConfigWithProfiles:
    """Tests for GridSealConfig with profiles."""

    def test_default_profile_exists(self) -> None:
        """Test that default profile is always present."""
        config = GridSealConfig()
        assert "default" in config.verification_profiles

    def test_get_profile_returns_existing(self) -> None:
        """Test get_profile returns existing profile."""
        config = GridSealConfig(
            verification_profiles={
                "default": VerificationProfile(),
                "strict": VerificationProfile(threshold=0.9),
            }
        )

        profile = config.get_profile("strict")
        assert profile.threshold == 0.9

    def test_get_profile_returns_default_for_unknown(self) -> None:
        """Test get_profile returns default for unknown names."""
        config = GridSealConfig(
            verification_profiles={
                "default": VerificationProfile(threshold=0.5),
            }
        )

        profile = config.get_profile("nonexistent")
        assert profile.threshold == 0.5

    def test_multiple_profiles(self) -> None:
        """Test configuration with multiple profiles."""
        config = GridSealConfig(
            verification_profiles={
                "default": VerificationProfile(threshold=0.5),
                "legal": VerificationProfile(
                    threshold=0.85,
                    require_citations=True,
                    strict=True,
                ),
                "general": VerificationProfile(
                    threshold=0.6,
                    strict=False,
                ),
            }
        )

        assert len(config.verification_profiles) == 3

        legal = config.get_profile("legal")
        assert legal.threshold == 0.85
        assert legal.require_citations is True
        assert legal.strict is True

        general = config.get_profile("general")
        assert general.threshold == 0.6
        assert general.strict is False


class TestParseConfigWithProfiles:
    """Tests for parse_config with profiles."""

    def test_parse_profiles_from_dict(self) -> None:
        """Test parsing profiles from dictionaries."""
        config = parse_config(
            verification_profiles={
                "default": {"threshold": 0.5},
                "strict": {"threshold": 0.9, "strict": True},
            }
        )

        assert config.get_profile("default").threshold == 0.5
        assert config.get_profile("strict").threshold == 0.9
        assert config.get_profile("strict").strict is True

    def test_parse_profiles_from_objects(self) -> None:
        """Test parsing profiles from VerificationProfile objects."""
        config = parse_config(
            verification_profiles={
                "default": VerificationProfile(threshold=0.6),
                "legal": VerificationProfile(threshold=0.85),
            }
        )

        assert config.get_profile("default").threshold == 0.6
        assert config.get_profile("legal").threshold == 0.85

    def test_parse_without_profiles(self) -> None:
        """Test parsing without profiles creates default."""
        config = parse_config()

        assert "default" in config.verification_profiles
        profile = config.get_profile("default")
        assert profile.threshold == 0.7  # Default threshold


class TestVerificationConfigExtensions:
    """Tests for extended VerificationConfig."""

    def test_nli_mode_default(self) -> None:
        """Test default NLI mode."""
        config = VerificationConfig()
        assert config.nli_mode == "fast"

    def test_nli_mode_options(self) -> None:
        """Test valid NLI mode options."""
        for mode in ["fast", "balanced", "accurate"]:
            config = VerificationConfig(nli_mode=mode)
            assert config.nli_mode == mode

    def test_extract_claims_default(self) -> None:
        """Test extract_claims default is False."""
        config = VerificationConfig()
        assert config.extract_claims is False

    def test_extract_claims_enabled(self) -> None:
        """Test enabling claim extraction."""
        config = VerificationConfig(extract_claims=True)
        assert config.extract_claims is True

    def test_on_fail_extended_options(self) -> None:
        """Test extended on_fail options."""
        for action in ["log", "flag", "warn", "annotate", "block"]:
            config = VerificationConfig(on_fail=action)
            assert config.on_fail == action
