# src/zt_band/validate.py
"""
Validate .ztprog files for style knobs, meter/steps consistency, and preset correctness
without generating MIDI.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import json

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


def _load_ztprog_raw(path: Path) -> Dict[str, Any]:
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


def _bar_steps_for_meter(time_signature: str) -> Optional[int]:
    """Contract: 4/4 -> 16-step grid (16ths), 2/4 -> 8-step grid (16ths inside 2 beats)."""
    ts = (time_signature or "").strip()
    if ts == "4/4":
        return 16
    if ts == "2/4":
        return 8
    return None


def _as_int_list(x: Any) -> Optional[List[int]]:
    """Convert to list of ints if valid, else None."""
    if x is None:
        return None
    if isinstance(x, list) and all(isinstance(v, int) for v in x):
        return list(x)
    return None


def validate_ztprog_file(path: str | Path) -> List[ValidationIssue]:
    """
    Validate a .ztprog file for style knobs, meter/steps consistency, preset names.

    Returns a list of ValidationIssue (empty = valid).
    """
    p = Path(path)
    issues: List[ValidationIssue] = []

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


def _validate_style_knobs(style: Dict[str, Any], ts: str, bar_steps: Optional[int]) -> List[ValidationIssue]:
    """Validate style knobs: ghost_hits, vel_contour, meter/bar_steps consistency."""
    issues: List[ValidationIssue] = []

    # Optional explicit meter/bar_steps in style block
    style_meter = style.get("meter")
    style_steps = style.get("bar_steps")

    if style_meter is not None and str(style_meter).strip() != ts:
        issues.append(
            ValidationIssue(
                code="METER_MISMATCH",
                message=f"style.meter '{style_meter}' does not match program time_signature '{ts}'.",
                path="style.meter",
            )
        )

    if style_steps is not None:
        if not isinstance(style_steps, int):
            issues.append(
                ValidationIssue(
                    code="BAR_STEPS_TYPE",
                    message="style.bar_steps must be an integer.",
                    path="style.bar_steps",
                )
            )
        elif bar_steps is not None and style_steps != bar_steps:
            issues.append(
                ValidationIssue(
                    code="BAR_STEPS_MISMATCH",
                    message=f"style.bar_steps={style_steps} does not match meter '{ts}' (expected {bar_steps}).",
                    path="style.bar_steps",
                )
            )

    # ---- ghost hits ----
    ghost = style.get("ghost_hits") or style.get("ghost") or {}
    if isinstance(ghost, dict):
        ghost_enabled = bool(ghost.get("enabled", False))
        ghost_steps = ghost.get("steps", None)
        if ghost_steps is not None:
            steps = _as_int_list(ghost_steps)
            if steps is None:
                issues.append(
                    ValidationIssue(
                        code="GHOST_STEPS_TYPE",
                        message="ghost_hits.steps must be a list of integers.",
                        path="style.ghost_hits.steps",
                    )
                )
            else:
                if bar_steps is not None:
                    bad = [s for s in steps if s < 0 or s >= bar_steps]
                    if bad:
                        issues.append(
                            ValidationIssue(
                                code="GHOST_STEPS_RANGE",
                                message=f"ghost_hits.steps contains out-of-range steps {bad} for meter {ts} (0..{bar_steps-1}).",
                                path="style.ghost_hits.steps",
                            )
                        )
                # if steps provided but ghost disabled, warn (not error)
                if not ghost_enabled:
                    issues.append(
                        ValidationIssue(
                            code="GHOST_DISABLED",
                            message="ghost_hits.steps provided but ghost_hits.enabled is false; ghost hits will not apply.",
                            path="style.ghost_hits.enabled",
                        )
                    )
    elif ghost is not None and ghost != {}:
        issues.append(
            ValidationIssue(
                code="GHOST_TYPE",
                message="style.ghost_hits must be a mapping/object.",
                path="style.ghost_hits",
            )
        )

    # ---- velocity contour ----
    vel = style.get("vel_contour") or {}
    if isinstance(vel, dict):
        vel_enabled = bool(vel.get("enabled", False))
        preset = vel.get("preset", None)

        allowed_presets = {"brazil_samba", "none"}
        if preset is not None and preset not in allowed_presets:
            issues.append(
                ValidationIssue(
                    code="VEL_PRESET_UNKNOWN",
                    message=f"vel_contour.preset '{preset}' not recognized. Allowed: {sorted(allowed_presets)}",
                    path="style.vel_contour.preset",
                )
            )

        # Explicitly document: preset=none is allowed, but still requires enabled:true to apply
        # preset: none => neutral multipliers (no shaping), useful for standardizing YAML
        if preset is not None and not vel_enabled:
            issues.append(
                ValidationIssue(
                    code="VEL_DISABLED",
                    message="vel_contour.preset provided but vel_contour.enabled is false; contour will not apply.",
                    path="style.vel_contour.enabled",
                )
            )
    elif vel is not None and vel != {}:
        issues.append(
            ValidationIssue(
                code="VEL_TYPE",
                message="style.vel_contour must be a mapping/object.",
                path="style.vel_contour",
            )
        )

    return issues


def format_issues_text(issues: List[ValidationIssue], file: str) -> str:
    """Format validation issues as human-readable text."""
    if not issues:
        return f"OK: {file}"

    lines = [f"VALIDATION FAILED: {file}", ""]
    for i, iss in enumerate(issues, start=1):
        lines.append(f"{i:02d}. [{iss.code}] {iss.path}: {iss.message}")
    return "\n".join(lines)


def format_issues_json(issues: List[ValidationIssue], file: str) -> str:
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
