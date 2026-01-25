#!/usr/bin/env python3
"""
Unit tests for check_style_registry_metadata.py gate script.

Validates:
- Passes on well-formed registry
- Fails on missing required attrs
- --warn mode downgrades quality checks to warnings
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

# Import gate module
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ci"))
from check_style_registry_metadata import main


# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------


class FakePattern:
    """Minimal pattern for testing."""

    def __init__(
        self,
        id: str,
        family: str = "straight",
        max_density: int = 2,
        min_energy: int = 0,
        max_energy: int = 2,
    ):
        self.id = id
        self.family = family
        self.max_density = max_density
        self.min_energy = min_energy
        self.max_energy = max_energy


def make_good_registry() -> dict[str, FakePattern]:
    """Registry with fully valid patterns."""
    return {
        "swing_a": FakePattern(id="swing_a", family="swing", max_density=2, min_energy=0, max_energy=2),
        "shuffle_b": FakePattern(id="shuffle_b", family="shuffle", max_density=1, min_energy=1, max_energy=2),
    }


def make_bad_registry_missing_attrs() -> dict[str, FakePattern]:
    """Registry with pattern missing required attrs."""
    pat = FakePattern(id="incomplete")
    del pat.family  # Remove required attr
    del pat.max_density
    return {"incomplete": pat}


def make_bad_registry_invalid_family() -> dict[str, FakePattern]:
    """Registry with invalid family value."""
    return {
        "weird": FakePattern(id="weird", family="polka"),  # Not in VALID_FAMILIES
    }


def make_bad_registry_key_mismatch() -> dict[str, FakePattern]:
    """Registry where key != pattern.id."""
    return {
        "alias_key": FakePattern(id="real_id", family="straight"),
    }


# -----------------------------------------------------------------------------
# UNIT TESTS
# -----------------------------------------------------------------------------


def test_main_with_good_registry_returns_zero():
    """main() should return 0 for valid registry."""
    good_registry = make_good_registry()

    def mock_import(module_path, registry_name):
        return good_registry

    with mock.patch(
        "check_style_registry_metadata._import_registry",
        side_effect=mock_import,
    ):
        result = main(["--module", "fake.module", "--registry-name", "FAKE"])
    assert result == 0


def test_main_with_missing_attrs_returns_one():
    """main() should return 1 for registry with missing attrs."""
    bad_registry = make_bad_registry_missing_attrs()

    def mock_import(module_path, registry_name):
        return bad_registry

    with mock.patch(
        "check_style_registry_metadata._import_registry",
        side_effect=mock_import,
    ):
        result = main(["--module", "fake.module", "--registry-name", "FAKE"])
    assert result == 1


def test_main_with_invalid_family_returns_one():
    """main() should return 1 for registry with invalid family."""
    bad_registry = make_bad_registry_invalid_family()

    def mock_import(module_path, registry_name):
        return bad_registry

    with mock.patch(
        "check_style_registry_metadata._import_registry",
        side_effect=mock_import,
    ):
        result = main(["--module", "fake.module", "--registry-name", "FAKE"])
    assert result == 1


def test_main_key_mismatch_strict_fails():
    """Key != id should fail in strict mode (default)."""
    bad_registry = make_bad_registry_key_mismatch()

    def mock_import(module_path, registry_name):
        return bad_registry

    with mock.patch(
        "check_style_registry_metadata._import_registry",
        side_effect=mock_import,
    ):
        result = main(["--module", "fake.module", "--registry-name", "FAKE", "--strict"])
    assert result == 1


def test_main_key_mismatch_warn_passes():
    """Key != id should pass in --warn mode (quality check downgraded)."""
    bad_registry = make_bad_registry_key_mismatch()

    def mock_import(module_path, registry_name):
        return bad_registry

    with mock.patch(
        "check_style_registry_metadata._import_registry",
        side_effect=mock_import,
    ):
        result = main(["--module", "fake.module", "--registry-name", "FAKE", "--warn"])
    assert result == 0  # Passes because quality check is now a warning


def test_main_returns_two_on_import_failure():
    """main() should return 2 when registry can't be loaded."""

    def mock_import(module_path, registry_name):
        raise ImportError("Module not found")

    with mock.patch(
        "check_style_registry_metadata._import_registry",
        side_effect=mock_import,
    ):
        result = main(["--module", "does.not.exist", "--registry-name", "NOPE"])
    assert result == 2


# -----------------------------------------------------------------------------
# RUN
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
