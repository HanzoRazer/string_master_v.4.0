# tests/test_style_override.py
"""
Tests for style override bridge layer.

Verifies that:
1. Engine accepts style_overrides parameter
2. STYLE_REGISTRY is not mutated
3. Style dict in .ztprog is correctly parsed and passed through
"""
from __future__ import annotations

import copy
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


def test_apply_style_overrides_does_not_mutate_registry():
    """_apply_style_overrides should return a copy, not mutate registry."""
    from zt_band.engine import _apply_style_overrides
    from zt_band.patterns import STYLE_REGISTRY
    
    # Get original registry values
    original_samba = copy.deepcopy(asdict(STYLE_REGISTRY["samba_basic"]))
    
    # Apply overrides with different values
    overrides = {
        "ghost_vel": 42,
        "ghost_steps": [0, 4, 8, 12],
        "pickup_beat": 4.0,
        "pickup_vel": 55,
    }
    
    result = _apply_style_overrides(STYLE_REGISTRY["samba_basic"], overrides)
    
    # Result should have overridden values (ghost_steps stored as tuple)
    assert result.ghost_vel == 42
    assert result.ghost_steps == (0, 4, 8, 12)
    assert result.pickup_beat == 4.0
    assert result.pickup_vel == 55
    
    # Registry should be unchanged
    current_samba = asdict(STYLE_REGISTRY["samba_basic"])
    assert current_samba == original_samba, "STYLE_REGISTRY was mutated!"


def test_apply_style_overrides_expands_ghost_hits_sugar():
    """Nested ghost_hits dict should expand to flat fields."""
    from zt_band.engine import _apply_style_overrides
    from zt_band.patterns import STYLE_REGISTRY
    
    overrides = {
        "ghost_hits": {
            "enabled": True,
            "vel": 30,
            "steps": [1, 5, 9],
        }
    }
    
    result = _apply_style_overrides(STYLE_REGISTRY["samba_basic"], overrides)
    
    assert result.ghost_vel == 30
    assert result.ghost_steps == (1, 5, 9)  # stored as tuple


def test_apply_style_overrides_expands_vel_contour_preset():
    """vel_contour with preset should expand to multiplier values."""
    from zt_band.engine import _apply_style_overrides
    from zt_band.patterns import STYLE_REGISTRY
    
    overrides = {
        "vel_contour": {
            "enabled": True,
            "preset": "brazil_samba",
        }
    }
    
    result = _apply_style_overrides(STYLE_REGISTRY["swing_basic"], overrides)
    
    # brazil_samba preset values
    assert result.vel_contour_enabled is True
    assert result.vel_contour_soft == pytest.approx(0.82)
    assert result.vel_contour_strong == pytest.approx(1.08)
    assert result.vel_contour_pickup == pytest.approx(0.65)
    assert result.vel_contour_ghost == pytest.approx(0.55)


def test_apply_style_overrides_flat_fields_override_nested():
    """Flat fields should override nested sugar if both present."""
    from zt_band.engine import _apply_style_overrides
    from zt_band.patterns import STYLE_REGISTRY
    
    overrides = {
        # Nested sugar
        "ghost_hits": {
            "enabled": True,
            "vel": 30,
            "steps": [1, 5, 9],
        },
        # Flat fields (should win)
        "ghost_vel": 99,
    }
    
    result = _apply_style_overrides(STYLE_REGISTRY["samba_basic"], overrides)
    
    # Flat field wins
    assert result.ghost_vel == 99
    # Nested steps still applied (as tuple)
    assert result.ghost_steps == (1, 5, 9)


def test_apply_style_overrides_no_overrides_returns_copy():
    """Empty overrides should return a copy of base."""
    from zt_band.engine import _apply_style_overrides
    from zt_band.patterns import STYLE_REGISTRY
    
    base = STYLE_REGISTRY["swing_basic"]
    result = _apply_style_overrides(base, {})
    
    # Should be equal but not same object
    assert asdict(result) == asdict(base)
    assert result is not base


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "zt_band.cli", *args],
        capture_output=True,
        text=True,
    )


def test_cli_create_accepts_style_dict(tmp_path: Path):
    """CLI create should accept .ztprog with style as dict."""
    p = tmp_path / "style_dict.ztprog"
    outfile = tmp_path / "output.mid"
    
    p.write_text(
        textwrap.dedent(
            f"""\
            name: "Style Dict Test"
            time_signature: "4/4"
            tempo: 120
            bars_per_chord: 1
            chords: ["Dm7", "G7", "Cmaj7"]
            style:
              comp: samba_basic
              ghost_vel: 45
              pickup_vel: 60
            outfile: "{outfile.as_posix()}"
            """
        ),
        encoding="utf-8",
    )
    
    r = _run("create", "--config", str(p))
    assert r.returncode == 0, f"stderr: {r.stderr}"
    assert outfile.exists(), "MIDI file should be created"


def test_cli_create_rejects_style_dict_without_comp(tmp_path: Path):
    """CLI create should reject style dict missing 'comp' key."""
    p = tmp_path / "no_comp.ztprog"
    outfile = tmp_path / "output.mid"
    
    p.write_text(
        textwrap.dedent(
            f"""\
            name: "No Comp Key"
            time_signature: "4/4"
            tempo: 120
            bars_per_chord: 1
            chords: ["Dm7", "G7"]
            style:
              ghost_vel: 45
            outfile: "{outfile.as_posix()}"
            """
        ),
        encoding="utf-8",
    )
    
    r = _run("create", "--config", str(p))
    assert r.returncode != 0
    assert "comp" in r.stderr.lower() or "style" in r.stderr.lower()
