"""Tests for the release script."""

import pytest

from release import (
    bump_patch,
    validate_version,
    VERSION_PATTERN,
)

class TestValidateVersion:
    """Tests for version validation."""

    def test_valid_versions(self):
        """Valid vX.Y.Z versions should pass."""
        valid = ["0.0.0", "1.0.0", "1.2.3", "10.20.30", "999.999.999"]
        for v in valid:
            assert validate_version(v), f"{v} should be valid"

    def test_invalid_wrong_format(self):
        """Malformed versions should fail."""
        invalid = [
            "1",
            "1.0",
            "1.0.0.0",
            "1.0.0-beta",
            "1.0.0rc1",
            "X.Y.Z",
            "1.0.a",
            "a.b.c",
            "v1.0.0",
            "version1.0.0",
        ]
        for v in invalid:
            assert not validate_version(v), f"{v} should be invalid"

    def test_invalid_with_spaces(self):
        """Versions with spaces should fail."""
        assert not validate_version(" 1.0.0")
        assert not validate_version("1.0.0 ")
        assert not validate_version(" 1.0.0 ")


class TestBumpPatch:
    """Tests for patch version bumping."""

    def test_bump_simple(self):
        """Should increment patch version."""
        assert bump_patch("1.0.0") == "1.0.1"
        assert bump_patch("1.0.9") == "1.0.10"
        assert bump_patch("1.2.3") == "1.2.4"

    def test_bump_preserves_major_minor(self):
        """Major and minor should remain unchanged."""
        assert bump_patch("5.10.0") == "5.10.1"
        assert bump_patch("0.0.0") == "0.0.1"

    def test_bump_large_numbers(self):
        """Should handle large version numbers."""
        assert bump_patch("100.200.999") == "100.200.1000"

    def test_bump_invalid_format(self):
        """Should raise error for invalid format."""
        with pytest.raises(ValueError):
            bump_patch("1.0")
        with pytest.raises(ValueError):
            bump_patch("1.0.0.0")
        with pytest.raises(ValueError):
            bump_patch("invalid")


class TestVersionPattern:
    """Tests for the VERSION_PATTERN regex."""

    def test_pattern_matches_valid(self):
        """Pattern should match valid versions."""
        assert VERSION_PATTERN.match("1.0.0")
        assert VERSION_PATTERN.match("0.0.1")
        assert VERSION_PATTERN.match("123.456.789")

    def test_pattern_rejects_invalid(self):
        """Pattern should reject invalid versions."""
        assert not VERSION_PATTERN.match("v1.0.0")
        assert not VERSION_PATTERN.match("1.0")
        assert not VERSION_PATTERN.match("1.0.0-rc1")
        assert not VERSION_PATTERN.match("1.0.0beta")
