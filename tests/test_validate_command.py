# tests/test_validate_command.py
"""
Tests for zt-band validate subcommand.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import textwrap


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "zt_band.cli", *args],
        capture_output=True,
        text=True,
    )


def test_validate_ok_minimal(tmp_path: Path):
    """Valid .ztprog with all style knobs correct should pass."""
    p = tmp_path / "ok.ztprog"
    p.write_text(
        textwrap.dedent(
            """\
            name: ok
            time_signature: "4/4"
            tempo: 120
            bars_per_chord: 1
            chords: ["Dm7", "G7", "Cmaj7"]
            style:
              comp: samba_basic
              meter: "4/4"
              bar_steps: 16
              ghost_hits:
                enabled: true
                steps: [3, 7, 11, 15]
              vel_contour:
                enabled: true
                preset: brazil_samba
            """
        ),
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p))
    assert r.returncode == 0
    assert "OK:" in r.stdout


def test_validate_ok_preset_none(tmp_path: Path):
    """Valid .ztprog with preset: none should pass."""
    p = tmp_path / "ok_none.ztprog"
    p.write_text(
        textwrap.dedent(
            """\
            name: ok_none
            time_signature: "4/4"
            chords: ["C7"]
            style:
              comp: swing_basic
              vel_contour:
                enabled: true
                preset: none
            """
        ),
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p))
    assert r.returncode == 0
    assert "OK:" in r.stdout


def test_validate_catches_mismatch(tmp_path: Path):
    """Invalid .ztprog with multiple issues should fail with exit code 2."""
    p = tmp_path / "bad.ztprog"
    p.write_text(
        textwrap.dedent(
            """\
            name: bad
            time_sig: "4/4"
            chords: ["C7", "F7"]
            style:
              comp: samba_basic
              meter: "2/4"
              bar_steps: 8
              ghost_hits:
                enabled: false
                steps: [0, 99]
              vel_contour:
                enabled: false
                preset: nope
            """
        ),
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p))
    assert r.returncode == 2
    # should include multiple issues
    assert "KEY_RENAME" in r.stdout
    assert "METER_MISMATCH" in r.stdout
    assert "GHOST_STEPS_RANGE" in r.stdout
    assert "VEL_PRESET_UNKNOWN" in r.stdout


def test_validate_json_format(tmp_path: Path):
    """JSON output format should be machine-parseable."""
    p = tmp_path / "bad2.ztprog"
    p.write_text(
        '{"time_signature":"3/4","chords":["C7"],"style":{"vel_contour":{"enabled":true,"preset":"none"}}}',
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p), "--format", "json", "--warn-only")
    assert r.returncode == 0
    assert '"ok": false' in r.stdout
    assert '"METER_UNSUPPORTED"' in r.stdout


def test_validate_warn_only_exits_zero(tmp_path: Path):
    """--warn-only should always exit 0 even with issues."""
    p = tmp_path / "bad3.ztprog"
    p.write_text(
        textwrap.dedent(
            """\
            name: bad
            time_signature: "5/4"
            chords: ["C7"]
            style: swing
            """
        ),
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p), "--warn-only")
    assert r.returncode == 0
    assert "METER_UNSUPPORTED" in r.stdout


def test_validate_missing_file():
    """Validate non-existent file should fail with LOAD_ERROR."""
    r = _run("validate", "--file", "/nonexistent/path/foo.ztprog")
    assert r.returncode == 2
    assert "LOAD_ERROR" in r.stdout


def test_validate_missing_style(tmp_path: Path):
    """Missing style key should be flagged."""
    p = tmp_path / "nostyle.ztprog"
    p.write_text(
        textwrap.dedent(
            """\
            name: nostyle
            time_signature: "4/4"
            chords: ["C7"]
            """
        ),
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p))
    assert r.returncode == 2
    assert "STYLE_MISSING" in r.stdout


def test_validate_flat_knobs_valid(tmp_path: Path):
    """Flat knob shape (ghost_vel, ghost_steps, vel_contour_enabled) should pass."""
    p = tmp_path / "flat_ok.ztprog"
    p.write_text(
        textwrap.dedent(
            """\
            name: flat_knobs
            time_signature: "4/4"
            tempo: 100
            bars_per_chord: 1
            chords: ["G7"]
            style:
              comp: bossa
              bar_steps: 16
              ghost_vel: 45
              ghost_steps: [1, 5, 9, 13]
              vel_contour_enabled: true
              vel_contour_preset: brazil_samba
            """
        ),
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p))
    assert r.returncode == 0
    assert "OK:" in r.stdout


def test_validate_flat_knobs_bad_range(tmp_path: Path):
    """Flat knob shape with out-of-range ghost_steps should fail."""
    p = tmp_path / "flat_bad.ztprog"
    p.write_text(
        textwrap.dedent(
            """\
            name: flat_bad
            time_signature: "2/4"
            chords: ["G7"]
            style:
              comp: samba_2_4
              bar_steps: 8
              ghost_vel: 40
              ghost_steps: [0, 1, 99]
              vel_contour_enabled: false
              vel_contour_preset: nope
            """
        ),
        encoding="utf-8",
    )
    r = _run("validate", "--file", str(p))
    assert r.returncode == 2
    # should catch out-of-range step and unknown preset
    assert "GHOST_STEPS_RANGE" in r.stdout
    assert "VEL_PRESET_UNKNOWN" in r.stdout
