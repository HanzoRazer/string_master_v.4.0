"""
Tests for vel_contour preset: 'none' (explicit no-op).

The 'none' preset allows YAML standardization across programs
without changing any velocities.
"""
import pytest
from zt_band.velocity_contour import resolve_vel_contour, VelContour


def test_vel_contour_none_preset_is_noop():
    """The 'none' preset applies no scaling (all multipliers = 1.0)."""
    c = resolve_vel_contour({"enabled": True, "preset": "none"})
    assert c.enabled is True
    assert c.soft_mul == 1.0
    assert c.strong_mul == 1.0
    assert c.pickup_mul == 1.0
    assert c.ghost_mul == 1.0


def test_vel_contour_brazil_samba_preset():
    """The 'brazil_samba' preset applies Brazilian breathing feel."""
    c = resolve_vel_contour({"enabled": True, "preset": "brazil_samba"})
    assert c.enabled is True
    assert c.soft_mul == 0.82
    assert c.strong_mul == 1.08
    assert c.pickup_mul == 0.65
    assert c.ghost_mul == 0.55


def test_vel_contour_preset_with_override():
    """Preset values can be overridden by explicit config keys."""
    c = resolve_vel_contour({
        "enabled": True,
        "preset": "none",
        "soft_mul": 0.9,
    })
    assert c.enabled is True
    assert c.soft_mul == 0.9  # overridden
    assert c.strong_mul == 1.0  # from preset


def test_vel_contour_disabled_returns_disabled():
    """enabled: false returns a disabled VelContour."""
    c = resolve_vel_contour({"enabled": False, "preset": "brazil_samba"})
    assert c.enabled is False


def test_vel_contour_none_config_returns_disabled():
    """None config returns a disabled VelContour."""
    c = resolve_vel_contour(None)
    assert c.enabled is False


def test_vel_contour_missing_enabled_returns_disabled():
    """Missing 'enabled' key returns a disabled VelContour."""
    c = resolve_vel_contour({"preset": "brazil_samba"})
    assert c.enabled is False


def test_vel_contour_unknown_preset_uses_defaults():
    """Unknown preset name falls back to VelContour defaults."""
    c = resolve_vel_contour({"enabled": True, "preset": "unknown_preset"})
    assert c.enabled is True
    # Should use VelContour defaults
    assert c.soft_mul == 0.80
    assert c.strong_mul == 1.08
