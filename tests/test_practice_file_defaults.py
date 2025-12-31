"""
Tests for practice --file and --program preset defaults.
"""

from __future__ import annotations

import pytest

from zt_band import cli as zcli


# ---------------------------------------------------------------------
# Test clave inference helper
# ---------------------------------------------------------------------


def test_infer_clave_from_style_2_3():
    """Style containing '2_3' should infer son_2_3."""
    assert zcli._infer_clave_from_style_comp("salsa_clave_2_3") == "son_2_3"
    assert zcli._infer_clave_from_style_comp("afro_cuban_2_3") == "son_2_3"


def test_infer_clave_from_style_3_2():
    """Style containing '3_2' should infer son_3_2."""
    assert zcli._infer_clave_from_style_comp("salsa_clave_3_2") == "son_3_2"
    assert zcli._infer_clave_from_style_comp("rumba_3_2_variant") == "son_3_2"


def test_infer_clave_from_style_none():
    """Style without clave pattern should return None."""
    assert zcli._infer_clave_from_style_comp("ballad_basic") is None
    assert zcli._infer_clave_from_style_comp("swing_basic") is None
    assert zcli._infer_clave_from_style_comp(None) is None


# ---------------------------------------------------------------------
# Test ztprog style extraction helper
# ---------------------------------------------------------------------


def test_ztprog_get_style_comp_string():
    """Should extract style when it's a plain string."""
    z = {"style": "ballad_basic"}
    assert zcli._ztprog_get_style_comp(z) == "ballad_basic"


def test_ztprog_get_style_comp_dict():
    """Should extract style.comp when style is a dict."""
    z = {"style": {"comp": "salsa_clave_2_3", "bass": "tumbao_major"}}
    assert zcli._ztprog_get_style_comp(z) == "salsa_clave_2_3"


def test_ztprog_get_style_comp_missing():
    """Should return None when style is missing or invalid."""
    assert zcli._ztprog_get_style_comp({}) is None
    assert zcli._ztprog_get_style_comp({"style": 123}) is None


# ---------------------------------------------------------------------
# Test practice subparser flags
# ---------------------------------------------------------------------


def test_practice_file_flag_exists():
    """practice subparser should accept --file argument."""
    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "practice",
        "--midi-in", "TestIn",
        "--midi-out", "TestOut",
        "--file", "test.ztprog",
    ])
    assert args.file == "test.ztprog"


def test_practice_program_flag_exists():
    """practice subparser should accept --program argument."""
    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "practice",
        "--midi-in", "TestIn",
        "--midi-out", "TestOut",
        "--program", "salsa_minor_Dm",
    ])
    assert args.program == "salsa_minor_Dm"


def test_practice_programs_dir_flag_exists():
    """practice subparser should accept --programs-dir argument."""
    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "practice",
        "--midi-in", "TestIn",
        "--midi-out", "TestOut",
        "--programs-dir", "/custom/path",
    ])
    assert args.programs_dir == "/custom/path"


# ---------------------------------------------------------------------
# Test practice preset defaults (integration tests)
# ---------------------------------------------------------------------


def test_practice_file_applies_tempo_and_infers_clave(monkeypatch, tmp_path):
    """--file should apply tempo and infer clave from style."""
    prog = tmp_path / "programs"
    prog.mkdir()
    p = prog / "salsa_minor_Dm.ztprog"
    p.write_text(
        """
name: salsa_minor_Dm
tempo: 104
chords: [ "Dm7", "Gm7", "A7" ]
style: { comp: salsa_clave_3_2 }
bars_per_chord: 2
""".strip(),
        encoding="utf-8",
    )

    captured = {}

    def fake_practice_lock(spec):
        captured["bpm"] = spec.bpm
        captured["clave"] = spec.clave
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--program", "salsa_minor_Dm",
            "--programs-dir", str(prog),
            "--grid", "16",
            "--no-click",
        ])

    assert abs(captured["bpm"] - 104.0) < 1e-9
    assert captured["clave"] == "son_3_2"


def test_practice_cli_bpm_overrides_file(monkeypatch, tmp_path):
    """Explicit --bpm should override file tempo."""
    prog = tmp_path / "programs"
    prog.mkdir()
    p = prog / "test.ztprog"
    p.write_text("name: x\ntempo: 104\nchords: [\"Dm7\"]\nstyle: ballad_basic\n", encoding="utf-8")

    captured = {}

    def fake_practice_lock(spec):
        captured["bpm"] = spec.bpm
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--file", str(p),
            "--bpm", "140",
            "--programs-dir", str(prog),
            "--no-click",
        ])

    assert abs(captured["bpm"] - 140.0) < 1e-9


def test_practice_cli_clave_overrides_inferred(monkeypatch, tmp_path):
    """Explicit --clave should override inferred clave from style."""
    prog = tmp_path / "programs"
    prog.mkdir()
    p = prog / "test.ztprog"
    p.write_text(
        """
name: x
tempo: 100
chords: ["Dm7"]
style: salsa_clave_3_2
""".strip(),
        encoding="utf-8",
    )

    captured = {}

    def fake_practice_lock(spec):
        captured["clave"] = spec.clave
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    # File style is 3_2 but we explicitly set son_2_3
    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--file", str(p),
            "--clave", "son_2_3",
            "--programs-dir", str(prog),
            "--no-click",
        ])

    assert captured["clave"] == "son_2_3"


def test_practice_no_file_uses_cli_defaults(monkeypatch):
    """Without --file/--program, should use CLI defaults."""
    captured = {}

    def fake_practice_lock(spec):
        captured["bpm"] = spec.bpm
        captured["clave"] = spec.clave
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--no-click",
        ])

    # Default values
    assert abs(captured["bpm"] - 120.0) < 1e-9
    assert captured["clave"] == "son_2_3"
