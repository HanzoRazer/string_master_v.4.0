"""
Tests for rt-play --program and program resolution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from zt_band import cli as zcli

# ---------------------------------------------------------------------
# Test _resolve_ztprog_program helper
# ---------------------------------------------------------------------


def test_resolve_program_by_stem(tmp_path):
    """Should resolve program by stem name (no extension)."""
    progdir = tmp_path / "programs"
    progdir.mkdir()
    f = progdir / "salsa_minor_Dm.ztprog"
    f.write_text("name: x\ntempo: 100\nchords: [\"Dm7\"]\nstyle: {comp: ballad_basic}\n", encoding="utf-8")

    got = zcli._resolve_ztprog_program("salsa_minor_Dm", programs_dir=str(progdir))
    assert Path(got).name == "salsa_minor_Dm.ztprog"


def test_resolve_program_by_filename(tmp_path):
    """Should resolve program by full filename with extension."""
    progdir = tmp_path / "programs"
    progdir.mkdir()
    f = progdir / "Foo.ztprog"
    f.write_text("name: x\ntempo: 100\nchords: [\"C\"]\n", encoding="utf-8")

    got = zcli._resolve_ztprog_program("Foo.ztprog", programs_dir=str(progdir))
    assert Path(got).name == "Foo.ztprog"


def test_resolve_program_case_insensitive(tmp_path):
    """Resolution should be case-insensitive."""
    progdir = tmp_path / "programs"
    progdir.mkdir()
    f = progdir / "Salsa_Minor_Dm.ztprog"
    f.write_text("name: x\ntempo: 100\nchords: [\"Dm7\"]\n", encoding="utf-8")

    got = zcli._resolve_ztprog_program("salsa_minor_dm", programs_dir=str(progdir))
    assert Path(got).name == "Salsa_Minor_Dm.ztprog"


def test_resolve_program_direct_path(tmp_path):
    """Should accept direct file path if it exists."""
    f = tmp_path / "my_prog.ztprog"
    f.write_text("name: x\nchords: [\"C\"]\n", encoding="utf-8")

    got = zcli._resolve_ztprog_program(str(f), programs_dir="nonexistent")
    assert got == str(f)


def test_resolve_program_not_found(tmp_path):
    """Should raise SystemExit if program not found."""
    progdir = tmp_path / "programs"
    progdir.mkdir()
    (progdir / "other.ztprog").write_text("name: x\nchords: [\"C\"]\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="Program not found"):
        zcli._resolve_ztprog_program("nonexistent", programs_dir=str(progdir))


def test_resolve_program_empty_dir(tmp_path):
    """Should raise SystemExit if no .ztprog files in dir."""
    progdir = tmp_path / "programs"
    progdir.mkdir()

    with pytest.raises(SystemExit, match="No .ztprog files found"):
        zcli._resolve_ztprog_program("anything", programs_dir=str(progdir))


# ---------------------------------------------------------------------
# Test rt-play --program integration
# ---------------------------------------------------------------------


def test_rt_play_program_flag_exists():
    """rt-play subparser should accept --program argument."""
    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "rt-play",
        "--midi-out", "TestPort",
        "--program", "salsa_minor_Dm",
    ])
    assert args.program == "salsa_minor_Dm"


def test_rt_play_programs_dir_flag_exists():
    """rt-play subparser should accept --programs-dir argument."""
    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "rt-play",
        "--midi-out", "TestPort",
        "--programs-dir", "/custom/path",
    ])
    assert args.programs_dir == "/custom/path"


def test_rt_play_program_resolves_to_file(monkeypatch, tmp_path):
    """--program should resolve to --file and use file settings."""
    progdir = tmp_path / "programs"
    progdir.mkdir()
    p = progdir / "test_prog.ztprog"
    p.write_text(
        """
name: test_prog
tempo: 95
bars_per_chord: 2
chords: [ "Am7", "Dm7", "E7" ]
style: { comp: ballad_basic }
""".strip(),
        encoding="utf-8",
    )

    captured = {}

    def fake_rt_play_cycle(*, events, spec, backend="mido", late_drop=None, panic=True):
        captured["bpm"] = spec.bpm
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "rt_play_cycle", fake_rt_play_cycle)

    with pytest.raises(SystemExit):
        zcli.main([
            "rt-play",
            "--midi-out", "DummyOut",
            "--program", "test_prog",
            "--programs-dir", str(progdir),
            "--grid", "16",
            "--clave", "son_2_3",
            "--no-click",
        ])

    # Should use file tempo (95) since --bpm not explicit
    assert abs(captured["bpm"] - 95.0) < 1e-9
