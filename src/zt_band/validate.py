# src/zt_band/validate.py
"""
Validate .ztprog files for style knobs, meter/steps consistency, and preset correctness
without generating MIDI.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # pyyaml
except Exception:  # pragma: no cover
    yaml = None


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue with code, message, and config path."""
    code: str
    message: str
    path: str  # dotted path into config, e.g. "style.vel_contour.preset"


def _load_ztprog_raw(path: Path) -> dict[str, Any]:
    """Load a .ztprog file as raw dict (JSON or YAML)."""
    if not path.exists():
        raise FileNotFoundError(str(path))

    text = path.read_text(encoding="utf-8")

    # JSON first if it looks like JSON
    s = text.lstrip()
    if s.startswith("{") or s.startswith("["):
        obj = json.loads(text)
        if not isinstance(obj, dict):
            raise ValueError("ztprog root must be a mapping/object")
        return obj

    # YAML fallback
    if yaml is None:
        raise ImportError("pyyaml is required to parse YAML .ztprog files")
    obj = yaml.safe_load(text)
    if not isinstance(obj, dict):
        raise ValueError("ztprog root must be a mapping/object")
    return obj


def _bar_steps_for_meter(time_signature: str) -> int | None:
    """Contract: 4/4 -> 16-step grid (16ths), 2/4 -> 8-step grid (16ths inside 2 beats)."""
    ts = (time_signature or "").strip()
    if ts == "4/4":
        return 16
    if ts == "2/4":
        return 8
    return None


def _as_int_list(x: Any) -> list[int] | None:
    """Convert to list of ints if valid, else None."""
    if x is None:
        return None
    if isinstance(x, list) and all(isinstance(v, int) for v in x):
        return list(x)
    return None


def validate_ztprog_file(path: str | Path) -> list[ValidationIssue]:
    """
    Validate a .ztprog file for style knobs, meter/steps consistency, preset names.

    Returns a list of ValidationIssue (empty = valid).
    """
    p = Path(path)
    issues: list[ValidationIssue] = []

    try:
        cfg = _load_ztprog_raw(p)
    except Exception as e:
        return [ValidationIssue(code="LOAD_ERROR", message=str(e), path="(file)")]

    # ---- meter basics ----
    ts = str(cfg.get("time_signature") or cfg.get("time_sig") or "4/4").strip()
    if "time_sig" in cfg:
        issues.append(
            ValidationIssue(
                code="KEY_RENAME",
                message="Use 'time_signature', not 'time_sig'.",
                path="time_sig",
            )
        )

    bar_steps = _bar_steps_for_meter(ts)
    if bar_steps is None:
        issues.append(
            ValidationIssue(
                code="METER_UNSUPPORTED",
                message=f"Unsupported time_signature '{ts}'. Expected '2/4' or '4/4'.",
                path="time_signature",
            )
        )

    # ---- style knobs checks (only if style is a dict) ----
    style = cfg.get("style")
    if isinstance(style, dict):
        issues.extend(_validate_style_knobs(style, ts, bar_steps))
    elif isinstance(style, str):
        # If they used a plain style name, no knobs to validate.
        pass
    elif style is None:
        issues.append(
            ValidationIssue(
                code="STYLE_MISSING",
                message="Missing 'style'. Provide a style name or style config object.",
                path="style",
            )
        )
    else:
        issues.append(
            ValidationIssue(
                code="STYLE_TYPE",
                message="style must be a string or a mapping/object.",
                path="style",
            )
        )

    return issues


def _beats_per_bar(ts: str) -> int | None:
    """Return beats per bar for supported meters."""
    ts = (ts or "").strip()
    if ts == "4/4":
        return 4
    if ts == "2/4":
        return 2
    return None


def _normalize_style_knobs(style: dict[str, Any], ts: str, bar_steps: int | None) -> tuple[dict[str, Any], list[ValidationIssue]]:
    """
    Normalize nested YAML sugar into canonical flat StylePattern fields.

    Accepts either:
      - canonical flat knobs (StylePattern fields)
      - nested sugar: ghost_hits{enabled,steps,...}, vel_contour{enabled,preset}

    Returns (flat, issues) where flat is a dict of StylePattern field values.
    Flat fields always take precedence over nested sugar.
    """
    issues: list[ValidationIssue] = []
    flat: dict[str, Any] = {}

    # --- ghost hits (nested sugar -> flat) ---
    ghost_nested = style.get("ghost_hits") or style.get("ghost")
    if ghost_nested is not None and not isinstance(ghost_nested, dict):
        issues.append(ValidationIssue("GHOST_TYPE", "style.ghost_hits must be a mapping/object.", "style.ghost_hits"))
    elif isinstance(ghost_nested, dict):
        enabled = bool(ghost_nested.get("enabled", False))
        steps = ghost_nested.get("steps", None)
        vel = ghost_nested.get("vel", None)
        glb = ghost_nested.get("len_beats", None)

        # Map to canonical flat fields
        if vel is None:
            # If enabled but no velocity → safe default; else disabled
            vel = 14 if enabled else 0
        flat["ghost_vel"] = int(vel)
        if steps is not None:
            flat["ghost_steps"] = steps
        if glb is not None:
            flat["ghost_len_beats"] = float(glb)

    # Flat fields override nested sugar
    for k in ("ghost_vel", "ghost_steps", "ghost_len_beats"):
        if k in style:
            flat[k] = style[k]

    # --- pickup (flat only, no nested sugar yet) ---
    for k in ("pickup_beat", "pickup_vel"):
        if k in style:
            flat[k] = style[k]

    # --- vel contour (nested sugar -> flat) ---
    vel_nested = style.get("vel_contour")
    if vel_nested is not None and not isinstance(vel_nested, dict):
        issues.append(ValidationIssue("VEL_TYPE", "style.vel_contour must be a mapping/object.", "style.vel_contour"))
    elif isinstance(vel_nested, dict):
        enabled = bool(vel_nested.get("enabled", False))
        preset = vel_nested.get("preset", None)

        flat["vel_contour_enabled"] = enabled

        # preset expansion (maps into canonical multipliers)
        if preset is not None:
            preset_str = str(preset).strip()
            allowed = {"none", "brazil_samba"}
            if preset_str not in allowed:
                issues.append(ValidationIssue(
                    "VEL_PRESET_UNKNOWN",
                    f"vel_contour.preset '{preset_str}' not recognized. Allowed: {sorted(allowed)}",
                    "style.vel_contour.preset",
                ))
            else:
                if preset_str == "none":
                    flat.update({
                        "vel_contour_soft": 1.0,
                        "vel_contour_strong": 1.0,
                        "vel_contour_pickup": 1.0,
                        "vel_contour_ghost": 1.0,
                    })
                elif preset_str == "brazil_samba":
                    flat.update({
                        "vel_contour_soft": 0.82,
                        "vel_contour_strong": 1.08,
                        "vel_contour_pickup": 0.65,
                        "vel_contour_ghost": 0.55,
                    })

        # Explicit multipliers in nested dict override preset defaults
        for suffix in ("soft", "strong", "pickup", "ghost"):
            key = f"vel_contour_{suffix}"
            if suffix in vel_nested:
                flat[key] = vel_nested[suffix]
            elif key in vel_nested:
                flat[key] = vel_nested[key]

    # Flat contour fields override nested sugar
    for k in ("vel_contour_enabled", "vel_contour_soft", "vel_contour_strong", "vel_contour_pickup", "vel_contour_ghost"):
        if k in style:
            flat[k] = style[k]

    return flat, issues


def _validate_style_knobs(style: dict[str, Any], ts: str, bar_steps: int | None) -> list[ValidationIssue]:
    """
    Validate style knobs against canonical StylePattern contract.

    1. Normalizes nested sugar → flat canonical fields
    2. Validates flat fields strictly (types, ranges)
    """
    issues: list[ValidationIssue] = []

    # --- meter / bar_steps consistency (existing logic) ---
    style_meter = style.get("meter")
    style_steps = style.get("bar_steps")

    if style_meter is not None and str(style_meter).strip() != ts:
        issues.append(ValidationIssue(
            "METER_MISMATCH",
            f"style.meter '{style_meter}' does not match program time_signature '{ts}'.",
            "style.meter",
        ))

    if style_steps is not None:
        if not isinstance(style_steps, int):
            issues.append(ValidationIssue(
                "BAR_STEPS_TYPE",
                "style.bar_steps must be an integer.",
                "style.bar_steps",
            ))
        elif bar_steps is not None and style_steps != bar_steps:
            issues.append(ValidationIssue(
                "BAR_STEPS_MISMATCH",
                f"style.bar_steps={style_steps} does not match meter '{ts}' (expected {bar_steps}).",
                "style.bar_steps",
            ))

    # --- normalize nested sugar → flat canonical fields ---
    flat, norm_issues = _normalize_style_knobs(style, ts, bar_steps)
    issues.extend(norm_issues)

    # --- validate ghost fields (canonical: ghost_vel, ghost_steps, ghost_len_beats) ---
    ghost_vel = flat.get("ghost_vel", 0)
    ghost_steps = flat.get("ghost_steps")
    ghost_len = flat.get("ghost_len_beats")

    # ghost_vel: int in 0..127
    if ghost_vel is not None:
        if not isinstance(ghost_vel, int) or ghost_vel < 0 or ghost_vel > 127:
            issues.append(ValidationIssue(
                "GHOST_VEL_RANGE",
                f"ghost_vel must be int 0..127, got {ghost_vel!r}.",
                "style.ghost_vel",
            ))

    # ghost_steps: list[int] in [0, bar_steps-1]
    if ghost_steps is not None:
        steps = _as_int_list(ghost_steps)
        if steps is None:
            issues.append(ValidationIssue(
                "GHOST_STEPS_TYPE",
                "ghost_steps must be a list of integers.",
                "style.ghost_steps",
            ))
        else:
            if bar_steps is not None:
                bad = [s for s in steps if s < 0 or s >= bar_steps]
                if bad:
                    issues.append(ValidationIssue(
                        "GHOST_STEPS_RANGE",
                        f"ghost_steps contains out-of-range steps {bad} for meter {ts} (0..{bar_steps-1}).",
                        "style.ghost_steps",
                    ))
            # Warn if steps provided but velocity is 0 (ghost disabled)
            if ghost_vel == 0 and steps:
                issues.append(ValidationIssue(
                    "GHOST_DISABLED",
                    "ghost_steps provided but ghost_vel=0; ghost hits will not apply.",
                    "style.ghost_vel",
                ))

    # ghost_len_beats: positive float
    if ghost_len is not None:
        if not isinstance(ghost_len, (int, float)) or ghost_len <= 0:
            issues.append(ValidationIssue(
                "GHOST_LEN_RANGE",
                f"ghost_len_beats must be a positive number, got {ghost_len!r}.",
                "style.ghost_len_beats",
            ))

    # --- validate pickup fields (canonical: pickup_beat, pickup_vel) ---
    pickup_beat = flat.get("pickup_beat")
    pickup_vel = flat.get("pickup_vel")
    beats_per = _beats_per_bar(ts)

    if pickup_beat is not None:
        if not isinstance(pickup_beat, (int, float)):
            issues.append(ValidationIssue(
                "PICKUP_BEAT_TYPE",
                f"pickup_beat must be a number, got {type(pickup_beat).__name__}.",
                "style.pickup_beat",
            ))
        elif beats_per is not None and (pickup_beat < 0 or pickup_beat >= beats_per):
            issues.append(ValidationIssue(
                "PICKUP_BEAT_RANGE",
                f"pickup_beat must be in [0, {beats_per}) for meter {ts}, got {pickup_beat}.",
                "style.pickup_beat",
            ))

    if pickup_vel is not None:
        if not isinstance(pickup_vel, int) or pickup_vel < 1 or pickup_vel > 127:
            issues.append(ValidationIssue(
                "PICKUP_VEL_RANGE",
                f"pickup_vel must be int 1..127, got {pickup_vel!r}.",
                "style.pickup_vel",
            ))

    # --- validate vel contour fields (canonical: vel_contour_enabled, vel_contour_soft/strong/pickup/ghost) ---
    vel_enabled = flat.get("vel_contour_enabled", False)
    multiplier_fields = ["vel_contour_soft", "vel_contour_strong", "vel_contour_pickup", "vel_contour_ghost"]

    for mf in multiplier_fields:
        val = flat.get(mf)
        if val is not None:
            if not isinstance(val, (int, float)) or val <= 0:
                issues.append(ValidationIssue(
                    "VEL_MULT_RANGE",
                    f"{mf} must be a positive number, got {val!r}.",
                    f"style.{mf}",
                ))

    # Warn if multipliers provided but vel_contour_enabled is false
    has_multipliers = any(flat.get(mf) is not None for mf in multiplier_fields)
    if has_multipliers and not vel_enabled:
        issues.append(ValidationIssue(
            "VEL_DISABLED",
            "vel_contour multipliers provided but vel_contour_enabled=false; contour will not apply.",
            "style.vel_contour_enabled",
        ))

    return issues


def format_issues_text(issues: list[ValidationIssue], file: str) -> str:
    """Format validation issues as human-readable text."""
    if not issues:
        return f"OK: {file}"

    lines = [f"VALIDATION FAILED: {file}", ""]
    for i, iss in enumerate(issues, start=1):
        lines.append(f"{i:02d}. [{iss.code}] {iss.path}: {iss.message}")
    return "\n".join(lines)


def format_issues_json(issues: list[ValidationIssue], file: str) -> str:
    """Format validation issues as JSON (for CI/machine consumption)."""
    payload = {
        "file": file,
        "ok": (len(issues) == 0),
        "issues": [
            {"code": x.code, "path": x.path, "message": x.message}
            for x in issues
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=False)
