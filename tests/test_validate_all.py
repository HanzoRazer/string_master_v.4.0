# tests/test_validate_all.py
"""
Tests for zt-band validate-all subcommand.
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


def test_validate_all_ok(tmp_path: Path):
    """All valid .ztprog files should pass."""
    programs = tmp_path / "programs"
    programs.mkdir()
    (programs / "ok.ztprog").write_text(
        textwrap.dedent("""\
        name: ok
        time_signature: "4/4"
        tempo: 120
        bars_per_chord: 1
        chords: ["Dm7","G7","Cmaj7"]
        style: "swing_basic"
        """),
        encoding="utf-8",
    )
    r = _run("validate-all", str(programs))
    assert r.returncode == 0


def test_validate_all_fails_on_bad(tmp_path: Path):
    """validate-all should fail (exit 2) when any file has issues."""
    programs = tmp_path / "programs"
    programs.mkdir()
    (programs / "bad.ztprog").write_text(
        '{"time_signature":"3/4","chords":["C7"],"style":"swing_basic"}',
        encoding="utf-8",
    )
    r = _run("validate-all", str(programs), "--quiet-ok")
    assert r.returncode == 2
    assert "METER_UNSUPPORTED" in (r.stdout + r.stderr)


def test_validate_all_json(tmp_path: Path):
    """JSON output should include ok, failed count, and results."""
    programs = tmp_path / "programs"
    programs.mkdir()
    (programs / "bad.ztprog").write_text(
        '{"time_signature":"3/4","chords":["C7"],"style":"swing_basic"}',
        encoding="utf-8",
    )
    r = _run("validate-all", str(programs), "--format", "json", "--warn-only")
    assert r.returncode == 0
    assert '"ok": false' in r.stdout
    assert '"failed": 1' in r.stdout


def test_validate_all_warn_only_exits_zero(tmp_path: Path):
    """--warn-only should exit 0 even with failures."""
    programs = tmp_path / "programs"
    programs.mkdir()
    (programs / "bad.ztprog").write_text(
        '{"time_signature":"3/4","chords":["C7"],"style":"swing_basic"}',
        encoding="utf-8",
    )
    r = _run("validate-all", str(programs), "--warn-only")
    assert r.returncode == 0


def test_validate_all_missing_dir():
    """Non-existent directory should exit 2."""
    r = _run("validate-all", "/nonexistent/path/xyz")
    assert r.returncode == 2
    assert "not found" in r.stderr.lower()


def test_validate_all_no_files(tmp_path: Path):
    """Empty directory with no .ztprog files should exit 2."""
    empty = tmp_path / "empty"
    empty.mkdir()
    r = _run("validate-all", str(empty))
    assert r.returncode == 2
    assert "no .ztprog" in r.stderr.lower()


def test_validate_all_quiet_ok_suppresses_ok(tmp_path: Path):
    """--quiet-ok should suppress OK lines, only show failures."""
    programs = tmp_path / "programs"
    programs.mkdir()
    (programs / "good.ztprog").write_text(
        textwrap.dedent("""\
        name: good
        time_signature: "4/4"
        tempo: 120
        bars_per_chord: 1
        chords: ["Dm7","G7"]
        style: "swing_basic"
        """),
        encoding="utf-8",
    )
    (programs / "bad.ztprog").write_text(
        '{"time_signature":"3/4","chords":["C7"],"style":"swing_basic"}',
        encoding="utf-8",
    )
    r = _run("validate-all", str(programs), "--quiet-ok")
    # Should show bad.ztprog failure but not good.ztprog OK
    assert "bad.ztprog" in r.stdout
    assert "good.ztprog" not in r.stdout
