"""
Tests for practice autostrict when salsa/clave presets detected.
"""

import pytest

from zt_band import cli as zcli

# ---------------------------------------------------------------------
# Test _infer_strict_from_style_comp helper
# ---------------------------------------------------------------------


def test_infer_strict_from_style_salsa():
    """Style containing 'salsa' should infer strict=True."""
    assert zcli._infer_strict_from_style_comp("salsa_clave_2_3") is True
    assert zcli._infer_strict_from_style_comp("salsa_basic") is True


def test_infer_strict_from_style_clave():
    """Style containing 'clave' should infer strict=True."""
    assert zcli._infer_strict_from_style_comp("afro_clave_pattern") is True
    assert zcli._infer_strict_from_style_comp("rumba_clave") is True


def test_infer_strict_from_style_non_salsa():
    """Style without salsa/clave should return False."""
    assert zcli._infer_strict_from_style_comp("ballad_basic") is False
    assert zcli._infer_strict_from_style_comp("swing_basic") is False
    assert zcli._infer_strict_from_style_comp(None) is False


# ---------------------------------------------------------------------
# Integration tests: autostrict for salsa presets
# ---------------------------------------------------------------------


def test_practice_program_autostrict_for_salsa(monkeypatch, tmp_path):
    """Salsa-ish style should auto-enable strict mode."""
    prog = tmp_path / "programs"
    prog.mkdir()
    p = prog / "salsa_minor_Dm.ztprog"
    p.write_text(
        """
name: salsa_minor_Dm
tempo: 104
chords: [ "Dm7", "Gm7", "A7" ]
style: { comp: salsa_clave_2_3 }
bars_per_chord: 2
""".strip(),
        encoding="utf-8",
    )

    captured = {}

    def fake_practice_lock(spec):
        captured["strict"] = spec.practice_strict
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--program", "salsa_minor_Dm",
            "--programs-dir", str(prog),
            "--no-click",
        ])

    assert captured["strict"] is True


def test_practice_loose_overrides_autostrict(monkeypatch, tmp_path):
    """Explicit --loose should override auto-strict from salsa style."""
    prog = tmp_path / "programs"
    prog.mkdir()
    p = prog / "salsa_minor_Dm.ztprog"
    p.write_text(
        "name: x\ntempo: 104\nchords: [\"Dm7\"]\nstyle: salsa_clave_2_3\n",
        encoding="utf-8",
    )

    captured = {}

    def fake_practice_lock(spec):
        captured["strict"] = spec.practice_strict
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--file", str(p),
            "--loose",
            "--no-click",
        ])

    assert captured["strict"] is False


def test_practice_strict_explicit_overrides_default(monkeypatch, tmp_path):
    """Explicit --strict should stick even for non-salsa style."""
    prog = tmp_path / "programs"
    prog.mkdir()
    p = prog / "ballad.ztprog"
    p.write_text(
        "name: x\ntempo: 80\nchords: [\"Cmaj7\"]\nstyle: ballad_basic\n",
        encoding="utf-8",
    )

    captured = {}

    def fake_practice_lock(spec):
        captured["strict"] = spec.practice_strict
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--file", str(p),
            "--strict",
            "--no-click",
        ])

    assert captured["strict"] is True


def test_practice_no_preset_uses_default_strict(monkeypatch):
    """Without preset file, default strict should be False (user must opt-in or use salsa preset)."""
    captured = {}

    def fake_practice_lock(spec):
        captured["strict"] = spec.practice_strict
        raise SystemExit(0)

    monkeypatch.setattr(zcli, "practice_lock_to_clave", fake_practice_lock)

    with pytest.raises(SystemExit):
        zcli.main([
            "practice",
            "--midi-in", "DummyIn",
            "--midi-out", "DummyOut",
            "--no-click",
        ])

    # Parser default is False (loose by default, strict only with salsa preset or explicit --strict)
    assert captured["strict"] is False
