"""
Tests for rt-play --playlist feature.
"""

import pytest

from zt_band import cli as zcli
from zt_band.rt_playlist import load_ztplay

# --- Playlist loading tests ---

def test_load_ztplay_basic(tmp_path):
    """load_ztplay should parse a valid .ztplay file."""
    playlist_file = tmp_path / "test.ztplay"
    playlist_file.write_text("""
id: test_playlist
title: "Test Playlist"
defaults:
  tempo: 100
  bars_per_chord: 2
items:
  - name: "Item 1"
    file: "prog1.ztprog"
    repeats: 2
  - name: "Item 2"
    file: "prog2.ztprog"
    repeats: 3
""")

    playlist = load_ztplay(str(playlist_file))

    assert playlist.id == "test_playlist"
    assert playlist.title == "Test Playlist"
    assert len(playlist.items) == 2
    assert playlist.items[0].name == "Item 1"
    assert playlist.items[0].file == "prog1.ztprog"
    assert playlist.items[0].repeats == 2
    assert playlist.items[1].name == "Item 2"
    assert playlist.items[1].repeats == 3
    assert playlist.defaults["tempo"] == 100


def test_load_ztplay_missing_file():
    """load_ztplay should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_ztplay("nonexistent.ztplay")


def test_load_ztplay_invalid_yaml(tmp_path):
    """load_ztplay should raise ValueError for non-mapping YAML."""
    playlist_file = tmp_path / "bad.ztplay"
    playlist_file.write_text("- just a list\n- not a mapping")

    with pytest.raises(ValueError, match="expected mapping"):
        load_ztplay(str(playlist_file))


def test_load_ztplay_default_repeats(tmp_path):
    """Items without repeats should default to 1."""
    playlist_file = tmp_path / "test.ztplay"
    playlist_file.write_text("""
id: test
title: "Test"
items:
  - name: "No repeats"
    file: "prog.ztprog"
""")

    playlist = load_ztplay(str(playlist_file))
    assert playlist.items[0].repeats == 1


# --- CLI flag tests ---

def test_rt_play_playlist_flag_exists():
    """rt-play subparser should accept --playlist argument."""
    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "rt-play",
        "--midi-out", "DummyOut",
        "--playlist", "test.ztplay",
    ])
    assert args.playlist == "test.ztplay"


def test_rt_play_playlist_and_file_both_accepted():
    """rt-play should accept both --file and --playlist (last wins)."""
    parser = zcli.build_arg_parser()
    # Both can be parsed, but playlist mode takes precedence in cmd_rt_play
    args = parser.parse_args([
        "rt-play",
        "--midi-out", "DummyOut",
        "--playlist", "test.ztplay",
        "--file", "test.ztprog",
    ])
    assert args.playlist == "test.ztplay"
    assert args.file == "test.ztprog"


# --- Integration tests (mocked) ---

def test_rt_playlist_calls_rt_play_cycle_per_item(monkeypatch, tmp_path):
    """rt_play_playlist should call rt_play_cycle once per item with correct max_cycles."""
    # Create playlist
    playlist_file = tmp_path / "test.ztplay"
    playlist_file.write_text("""
id: test
title: "Test"
defaults:
  tempo: 88
items:
  - name: "First"
    file: "prog1.ztprog"
    repeats: 2
  - name: "Second"
    file: "prog2.ztprog"
    repeats: 3
""")

    # Create programs
    prog1 = tmp_path / "prog1.ztprog"
    prog1.write_text("""
name: prog1
tempo: 88
chords: [Dm7, G7]
style: swing_basic
""")

    prog2 = tmp_path / "prog2.ztprog"
    prog2.write_text("""
name: prog2
tempo: 100
chords: [Cmaj7, Am7]
style: bossa_basic
""")

    # Track calls
    calls = []

    def fake_rt_play_cycle(*, events, spec, max_cycles=None):
        calls.append({
            "events_count": len(events),
            "bpm": spec.bpm,
            "max_cycles": max_cycles,
        })

    from zt_band import rt_playlist
    monkeypatch.setattr(rt_playlist, "rt_play_cycle", fake_rt_play_cycle)

    # Run
    rt_playlist.rt_play_playlist(
        playlist_file=str(playlist_file),
        midi_out="DummyOut",
    )

    # Verify
    assert len(calls) == 2
    assert calls[0]["max_cycles"] == 2  # First item repeats=2
    assert calls[1]["max_cycles"] == 3  # Second item repeats=3


def test_rt_playlist_bpm_override(monkeypatch, tmp_path):
    """rt_play_playlist with bpm_override should override program tempo."""
    playlist_file = tmp_path / "test.ztplay"
    playlist_file.write_text("""
id: test
title: "Test"
items:
  - name: "Item"
    file: "prog.ztprog"
    repeats: 1
""")

    prog = tmp_path / "prog.ztprog"
    prog.write_text("""
name: prog
tempo: 100
chords: [Dm7]
style: swing_basic
""")

    calls = []

    def fake_rt_play_cycle(*, events, spec, max_cycles=None):
        calls.append({"bpm": spec.bpm})

    from zt_band import rt_playlist
    monkeypatch.setattr(rt_playlist, "rt_play_cycle", fake_rt_play_cycle)

    # Run with bpm_override
    rt_playlist.rt_play_playlist(
        playlist_file=str(playlist_file),
        midi_out="DummyOut",
        bpm_override=140.0,
    )

    assert calls[0]["bpm"] == 140.0


def test_rt_playlist_uses_program_tempo_when_no_override(monkeypatch, tmp_path):
    """rt_play_playlist without bpm_override should use program tempo."""
    playlist_file = tmp_path / "test.ztplay"
    playlist_file.write_text("""
id: test
title: "Test"
items:
  - name: "Item"
    file: "prog.ztprog"
    repeats: 1
""")

    prog = tmp_path / "prog.ztprog"
    prog.write_text("""
name: prog
tempo: 95
chords: [Am7]
style: ballad_basic
""")

    calls = []

    def fake_rt_play_cycle(*, events, spec, max_cycles=None):
        calls.append({"bpm": spec.bpm})

    from zt_band import rt_playlist
    monkeypatch.setattr(rt_playlist, "rt_play_cycle", fake_rt_play_cycle)

    rt_playlist.rt_play_playlist(
        playlist_file=str(playlist_file),
        midi_out="DummyOut",
        bpm_override=None,
    )

    assert calls[0]["bpm"] == 95
