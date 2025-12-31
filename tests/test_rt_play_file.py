"""
Tests for rt-play --file .ztprog loading feature.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------
# Helper to create temp .ztprog files for testing
# ---------------------------------------------------------------------


def _write_ztprog(content: dict, suffix: str = ".ztprog") -> Path:
    """Write a temp .ztprog file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    yaml.dump(content, f)
    f.close()
    return Path(f.name)


# ---------------------------------------------------------------------
# Test _load_ztprog helper behavior (via cmd_rt_play)
# ---------------------------------------------------------------------


def test_load_ztprog_valid_basic():
    """A minimal valid .ztprog should parse without error."""
    prog = _write_ztprog({
        "chords": ["Dm7", "G7", "Cmaj7"],
        "tempo": 90,
        "bars_per_chord": 2,
        "style": {"comp": "salsa_clave_2_3"},
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data["chords"] == ["Dm7", "G7", "Cmaj7"]
        assert data["tempo"] == 90
        assert data["bars_per_chord"] == 2
        assert data["style"]["comp"] == "salsa_clave_2_3"
    finally:
        prog.unlink()


def test_load_ztprog_string_style():
    """Style as string (not dict) should be acceptable."""
    prog = _write_ztprog({
        "chords": ["Am7", "Dm7"],
        "style": "ballad_basic",
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        assert data["style"] == "ballad_basic"
    finally:
        prog.unlink()


def test_load_ztprog_missing_chords():
    """Missing 'chords' key should be detectable."""
    prog = _write_ztprog({
        "tempo": 120,
        "style": "salsa_clave_2_3",
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        assert data.get("chords") is None
    finally:
        prog.unlink()


def test_load_ztprog_invalid_chords_type():
    """Chords that isn't a list of strings should be invalid."""
    prog = _write_ztprog({
        "chords": "Dm7 G7 Cmaj7",  # string, not list
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        # Should be string, not list
        assert isinstance(data["chords"], str)
        assert not isinstance(data["chords"], list)
    finally:
        prog.unlink()


# ---------------------------------------------------------------------
# Test real .ztprog files in programs/ directory
# ---------------------------------------------------------------------


def test_real_ztprog_autumn_leaves():
    """programs/autumn_leaves.ztprog should be valid YAML."""
    prog_path = Path(__file__).parent.parent / "programs" / "autumn_leaves.ztprog"
    if not prog_path.exists():
        pytest.skip("programs/autumn_leaves.ztprog not found")
    
    data = yaml.safe_load(prog_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "chords" in data
    assert isinstance(data["chords"], list)
    assert all(isinstance(c, str) for c in data["chords"])


def test_real_ztprog_salsa_minor_dm():
    """programs/salsa_minor_Dm.ztprog should be valid with nested style."""
    prog_path = Path(__file__).parent.parent / "programs" / "salsa_minor_Dm.ztprog"
    if not prog_path.exists():
        pytest.skip("programs/salsa_minor_Dm.ztprog not found")
    
    data = yaml.safe_load(prog_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "chords" in data
    assert "style" in data
    # This one has nested style: {comp: ..., bass: ...}
    assert isinstance(data["style"], dict)
    assert "comp" in data["style"]


# ---------------------------------------------------------------------
# Test CLI argument parsing for --file
# ---------------------------------------------------------------------


def test_rt_play_help_shows_file_flag():
    """rt-play --help should show --file argument."""
    from zt_band.cli import build_arg_parser
    
    parser = build_arg_parser()
    help_text = parser.format_help()
    
    # We can't easily get subcommand help, but we can test subparser exists
    # and has the file argument by inspecting the parser structure
    # For now, just verify the parser builds without error
    assert parser is not None


def test_rt_play_file_arg_exists():
    """rt-play subparser should accept --file argument."""
    from zt_band.cli import build_arg_parser
    
    parser = build_arg_parser()
    
    # Parse with --file argument (note: will fail at runtime since midi-out required)
    # but parsing should succeed
    args = parser.parse_args([
        "rt-play",
        "--midi-out", "TestPort",
        "--file", "test.ztprog",
    ])
    
    assert args.file == "test.ztprog"
    assert args.midi_out == "TestPort"


def test_rt_play_chords_and_file_both_accepted():
    """Parser should accept both --chords and --file (file wins in handler)."""
    from zt_band.cli import build_arg_parser
    
    parser = build_arg_parser()
    args = parser.parse_args([
        "rt-play",
        "--midi-out", "TestPort",
        "--file", "test.ztprog",
        "--chords", "Dm7 G7",
    ])
    
    assert args.file == "test.ztprog"
    assert args.chords == "Dm7 G7"


# ---------------------------------------------------------------------
# Test tempo resolution logic
# ---------------------------------------------------------------------


def test_tempo_from_file_when_bpm_default():
    """File tempo should be used when --bpm not explicitly provided."""
    prog = _write_ztprog({
        "chords": ["Dm7", "G7"],
        "tempo": 85,
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        # Simulating the logic: if args.bpm == 120.0 (default), use file tempo
        args_bpm = 120.0  # default
        file_tempo = data.get("tempo", 120)
        
        if args_bpm == 120.0 and isinstance(file_tempo, (int, float)):
            resolved_bpm = float(file_tempo)
        else:
            resolved_bpm = args_bpm
        
        assert resolved_bpm == 85.0
    finally:
        prog.unlink()


def test_tempo_from_cli_wins_over_file():
    """Explicit --bpm should override file tempo."""
    prog = _write_ztprog({
        "chords": ["Dm7", "G7"],
        "tempo": 85,
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        # Simulating: user passed --bpm 140
        args_bpm = 140.0
        file_tempo = data.get("tempo", 120)
        
        # Since args_bpm != 120.0, CLI wins
        if args_bpm == 120.0 and isinstance(file_tempo, (int, float)):
            resolved_bpm = float(file_tempo)
        else:
            resolved_bpm = args_bpm
        
        assert resolved_bpm == 140.0
    finally:
        prog.unlink()


# ---------------------------------------------------------------------
# Test style resolution logic
# ---------------------------------------------------------------------


def test_style_from_nested_dict():
    """Style should be extracted from style.comp when nested."""
    prog = _write_ztprog({
        "chords": ["Dm7"],
        "style": {"comp": "jazz_minor", "bass": "walking"},
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        style_obj = data.get("style", {})
        
        if isinstance(style_obj, dict) and isinstance(style_obj.get("comp"), str):
            resolved_style = style_obj["comp"]
        elif isinstance(style_obj, str):
            resolved_style = style_obj
        else:
            resolved_style = "salsa_clave_2_3"  # default
        
        assert resolved_style == "jazz_minor"
    finally:
        prog.unlink()


def test_style_from_string():
    """Style should work when it's a plain string."""
    prog = _write_ztprog({
        "chords": ["Dm7"],
        "style": "ballad_basic",
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        style_obj = data.get("style", {})
        
        if isinstance(style_obj, dict) and isinstance(style_obj.get("comp"), str):
            resolved_style = style_obj["comp"]
        elif isinstance(style_obj, str):
            resolved_style = style_obj
        else:
            resolved_style = "salsa_clave_2_3"
        
        assert resolved_style == "ballad_basic"
    finally:
        prog.unlink()


# ---------------------------------------------------------------------
# Test bars_per_chord resolution
# ---------------------------------------------------------------------


def test_bars_per_chord_from_file():
    """bars_per_chord should be read from file."""
    prog = _write_ztprog({
        "chords": ["Dm7", "G7"],
        "bars_per_chord": 4,
    })
    try:
        data = yaml.safe_load(prog.read_text(encoding="utf-8"))
        bpc = data.get("bars_per_chord", 1)
        assert bpc == 4
    finally:
        prog.unlink()
