from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Literal, Any, Dict, Union
import json

import yaml  # type: ignore[import-not-found]


TritoneMode = Literal["none", "all_doms", "probabilistic"]


@dataclass
class ProgramConfig:
    """
    A reusable 'song preset' / program for zt-band.

    Typical .ztprog example (JSON or YAML):

    name: "C major swing demo"
    chords: "Cmaj7 Dm7 G7 Cmaj7"
    style: "swing_basic"
    tempo: 120
    bars_per_chord: 1
    tritone_mode: "none"
    tritone_strength: 1.0
    tritone_seed: null
    outfile: "c_major_swing.mid"
    """
    name: Optional[str]
    chords: List[str]
    style: str
    tempo: int
    bars_per_chord: int
    tritone_mode: TritoneMode
    tritone_strength: float
    tritone_seed: Optional[int]
    outfile: str


DEFAULT_STYLE = "swing_basic"
DEFAULT_TEMPO = 120
DEFAULT_BARS_PER_CHORD = 1
DEFAULT_TRITONE_MODE: TritoneMode = "none"
DEFAULT_TRITONE_STRENGTH = 1.0
DEFAULT_OUTFILE = "backing.mid"


def _parse_chords_field(raw: Any) -> List[str]:
    """
    Accept either:
      - a single string: "Cmaj7 Dm7 G7 Cmaj7"
      - a list of strings: ["Cmaj7", "Dm7", "G7", "Cmaj7"]
    """
    if isinstance(raw, str):
        parts = [tok for tok in raw.strip().split() if tok]
        if not parts:
            raise ValueError("Config 'chords' string was empty.")
        return parts
    if isinstance(raw, list):
        parts = []
        for item in raw:
            if not isinstance(item, str):
                raise TypeError("Config 'chords' list must contain strings only.")
            token = item.strip()
            if token:
                parts.append(token)
        if not parts:
            raise ValueError("Config 'chords' list was empty.")
        return parts
    raise TypeError(
        f"Unsupported type for 'chords' in program config: {type(raw)!r}. "
        "Use a space-separated string or a list of strings."
    )


def _coerce_int(name: str, value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Field '{name}' must be an integer.") from exc


def _coerce_float(name: str, value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Field '{name}' must be a number.") from exc


def _coerce_tritone_mode(value: Any) -> TritoneMode:
    if value is None:
        return DEFAULT_TRITONE_MODE
    if value not in ("none", "all_doms", "probabilistic"):
        raise ValueError(
            f"Invalid tritone_mode '{value}'. "
            "Expected one of: 'none', 'all_doms', 'probabilistic'."
        )
    return value


def load_program_config(path: str | Path) -> ProgramConfig:
    """
    Load a .ztprog file (JSON or YAML) into a ProgramConfig.

    Detection:
      - if the file starts with '{' or '[' → JSON
      - otherwise → YAML (via yaml.safe_load)

    Required fields:
      - chords

    Optional fields (with defaults):
      - name
      - style
      - tempo
      - bars_per_chord
      - tritone_mode
      - tritone_strength
      - tritone_seed
      - outfile
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Program config not found: {p}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Program config file is empty: {p}")

    # Heuristic: JSON if first non-whitespace char is '{' or '['
    first_char = text[0]
    data: Dict[str, Any]

    try:
        if first_char in ("{", "["):
            parsed = json.loads(text)
        else:
            parsed = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            f"Failed to parse program config {p}. "
            "Ensure it is valid JSON or YAML."
        ) from exc

    if not isinstance(parsed, dict):
        raise TypeError(
            f"Program config root must be a mapping/object. Got: {type(parsed)!r}"
        )

    chords_raw = parsed.get("chords")
    if chords_raw is None:
        raise KeyError("Program config is missing required field 'chords'.")

    chords = _parse_chords_field(chords_raw)

    name = parsed.get("name")
    style = parsed.get("style", DEFAULT_STYLE)
    tempo = _coerce_int("tempo", parsed.get("tempo", DEFAULT_TEMPO), DEFAULT_TEMPO)
    bars_per_chord = _coerce_int(
        "bars_per_chord",
        parsed.get("bars_per_chord", DEFAULT_BARS_PER_CHORD),
        DEFAULT_BARS_PER_CHORD,
    )
    tritone_mode = _coerce_tritone_mode(parsed.get("tritone_mode", DEFAULT_TRITONE_MODE))
    tritone_strength = _coerce_float(
        "tritone_strength",
        parsed.get("tritone_strength", DEFAULT_TRITONE_STRENGTH),
        DEFAULT_TRITONE_STRENGTH,
    )
    seed_raw = parsed.get("tritone_seed")
    tritone_seed: Optional[int]
    if seed_raw is None:
        tritone_seed = None
    else:
        tritone_seed = _coerce_int("tritone_seed", seed_raw, 0)

    outfile = parsed.get("outfile", DEFAULT_OUTFILE)

    return ProgramConfig(
        name=name,
        chords=chords,
        style=style,
        tempo=tempo,
        bars_per_chord=bars_per_chord,
        tritone_mode=tritone_mode,
        tritone_strength=tritone_strength,
        tritone_seed=tritone_seed,
        outfile=outfile,
    )
