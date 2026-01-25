from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from zt_band.adapters.arranger_intent_adapter import build_arranger_control_plan
from zt_band.arranger.arranger_engine_adapter import to_selection_request
from zt_band.arranger.engine import choose_pattern
from zt_band.arranger.performance_controls import derive_runtime_performance_controls
from zt_band.midi.humanizer import DeterministicHumanizer
from zt_band.midi.velocity_assist_sender import VelocityAssistSender

ENGINE_IDENTITY = "e2e_gate_v1"


@dataclass(frozen=True)
class ReplayResult:
    ok: bool
    message: str
    failures: Optional[List[str]] = None


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _dump_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stable_lines(obj: Dict[str, Any]) -> List[str]:
    return _dump_json(obj).splitlines(keepends=True)


def _git_sha_or_unknown(repo_root: Path) -> str:
    env_sha = os.environ.get("GITHUB_SHA")
    if env_sha:
        return env_sha[:12]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def _ticks_to_seconds(ticks: int, bpm: float, ticks_per_beat: int) -> float:
    # Standard conversion: beats = ticks / tpb; seconds = beats * (60/bpm)
    return (float(ticks) / float(ticks_per_beat)) * (60.0 / float(bpm))


def _printable_diff(expected: Dict[str, Any], produced: Dict[str, Any]) -> str:
    a = _stable_lines(expected)
    b = _stable_lines(produced)
    diff = difflib.unified_diff(a, b, fromfile="expected.json", tofile="produced.json", lineterm="")
    return "\n".join(diff) + "\n"


def _write_diff_txt(*, vector_dir: Path, expected: Dict[str, Any], produced: Dict[str, Any]) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    sha = _git_sha_or_unknown(repo_root)
    vector_name = vector_dir.name
    rel_path = f"fixtures/golden/e2e_vectors/{vector_name}"

    header = [
        f"# Vector: {vector_name}",
        f"# Reproduce: python -m zt_band.e2e.e2e_replay_gate_v1 {rel_path}",
        f"# Engine git sha: {sha}",
        f"# Engine identity: {ENGINE_IDENTITY}",
        "",
    ]
    body = _printable_diff(expected, produced)
    (vector_dir / "_diff.txt").write_text("\n".join(header) + body, encoding="utf-8")


def _cleanup_artifacts(vector_dir: Path) -> None:
    for name in ("_diff.txt", "_produced.json"):
        p = vector_dir / name
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass


def _ensure_changelog_exists(changelog_path: Path) -> None:
    if changelog_path.exists():
        return
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    changelog_path.write_text(
        (
            "# End-to-End Vectors Changelog\n\n"
            "This changelog must be updated whenever `expected.json` is updated via `--update-golden`.\n\n"
            "Format:\n"
            "- YYYY-MM-DD — vector_name — short reason\n"
        ),
        encoding="utf-8",
    )


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _append_changelog_entry(changelog_path: Path, vector_name: str, reason: str) -> None:
    _ensure_changelog_exists(changelog_path)
    with changelog_path.open("a", encoding="utf-8") as f:
        f.write(f"- {_today_utc()} — {vector_name} — {reason.strip()}\n")


def _assert_changelog_bumped_or_bump(*, changelog_path: Path, vector_name: str, bump_reason: Optional[str]) -> None:
    _ensure_changelog_exists(changelog_path)
    text = changelog_path.read_text(encoding="utf-8")
    if vector_name in text:
        return
    if bump_reason and bump_reason.strip():
        _append_changelog_entry(changelog_path, vector_name, bump_reason)
        return
    raise RuntimeError(
        f"Refusing to update goldens for {vector_name} because changelog not bumped.\n"
        f"Add an entry to {changelog_path} mentioning '{vector_name}', or re-run with:\n"
        f'  --bump-changelog "short reason"\n'
    )


# ----- minimal fake pattern objects for deterministic selection -----

class _P:
    def __init__(self, *, id: str, family: str, max_density: int, min_energy: int, max_energy: int):
        self.id = id
        self.family = family
        self.max_density = max_density
        self.min_energy = min_energy
        self.max_energy = max_energy


def _pattern_library_fixture() -> List[Any]:
    """
    Stable, minimal library for e2e canary.
    These are designed to exercise filtering + deterministic pick.
    """
    return [
        _P(id="straight_basic", family="straight", max_density=2, min_energy=0, max_energy=2),
        _P(id="swing_basic",    family="swing",    max_density=2, min_energy=0, max_energy=2),
        _P(id="shuffle_push",   family="shuffle",  max_density=2, min_energy=1, max_energy=2),
        _P(id="free_sparse",    family="free",     max_density=0, min_energy=0, max_energy=1),
    ]


# ----- fake sender/msg for velocity assist E2E testing -----

class _FakeSender:
    """Collects sent messages for verification."""
    def __init__(self) -> None:
        self.sent: List[Any] = []

    def send(self, msg: Any) -> None:
        self.sent.append(msg)


class _FakeMsg:
    """Minimal message object with type/velocity for E2E velocity testing."""
    def __init__(self, *, type: str, velocity: int) -> None:
        self.type = type
        self.velocity = velocity

    def copy(self, **kwargs: Any) -> "_FakeMsg":
        v = kwargs.get("velocity", self.velocity)
        return _FakeMsg(type=self.type, velocity=v)


def _compute_produced(vector_dir: Path) -> Dict[str, Any]:
    intent = _load_json(vector_dir / "intent.json")
    evspec = _load_json(vector_dir / "events.json")

    # Detect vector type: timing vectors have "events", velocity vectors have "notes" or "note"
    is_timing_vector = "events" in evspec
    is_velocity_vector = "notes" in evspec or "note" in evspec

    # ---- Shared: extract intent signals for performance controls ----
    tempo_section = intent.get("tempo", {})
    dynamics_section = intent.get("dynamics", {})
    timing_section = intent.get("timing", {})

    lock_strength = float(tempo_section.get("lock_strength", 0.5))
    expression_window = float(dynamics_section.get("expression_window", 0.5))
    assist_gain = float(dynamics_section.get("assist_gain", 0.5))
    anticipation_bias = str(timing_section.get("anticipation_bias", "neutral"))

    # Map lock_strength → tightness (same directionality in this policy)
    tightness = lock_strength

    base_humanize_ms = 7.5  # baseline
    perf = derive_runtime_performance_controls(
        base_humanize_ms=base_humanize_ms,
        tightness=tightness,
        expression_window=expression_window,
        assist_gain=assist_gain,
        anticipation_bias=anticipation_bias,
    )

    # ---- B) Velocity vector path (E2E.5 canary) ----
    if is_velocity_vector:
        # Support both "notes" (list) and "note" (single) for backward compat
        notes = evspec.get("notes")
        if notes is None:
            notes = [evspec["note"]]

        fake_sender = _FakeSender()
        assisted = VelocityAssistSender(sender=fake_sender, velocity_mul=float(perf.velocity_mul))

        cases: List[Dict[str, int]] = []
        for n in notes:
            original_velocity = int(n.get("velocity", 80))
            msg = _FakeMsg(type=str(n.get("type", "note_on")), velocity=original_velocity)

            assisted.send(msg)
            sent = fake_sender.sent[-1]
            scaled_velocity = int(getattr(sent, "velocity", original_velocity))

            cases.append({
                "original_velocity": original_velocity,
                "scaled_velocity": scaled_velocity,
            })

        return {
            "velocity_mul": round(float(perf.velocity_mul), 6),
            "cases": cases,
        }

    # ---- A) Timing vector path (existing E2E.1-4 behavior) ----
    if not is_timing_vector:
        raise ValueError(f"Vector {vector_dir.name} has neither 'events' nor 'note' in events.json")

    bpm = float(evspec["bpm"])
    tpb = int(evspec["ticks_per_beat"])
    raw_events = evspec["events"]

    plan = build_arranger_control_plan(intent)
    req = to_selection_request(plan, seed=str(intent.get("profile_id", "default")))

    patterns = _pattern_library_fixture()
    chosen = choose_pattern(patterns, req)
    chosen_id = getattr(chosen, "id", "unknown")

    # Deterministic humanizer:
    # seed uses profile_id (stable player personality); tick_index is enumerate index.
    humanizer = DeterministicHumanizer(seed=str(intent.get("profile_id", "default")), mode="smooth", smooth_period=16)

    offsets: List[float] = []
    for tick_index, item in enumerate(raw_events[:10]):
        abs_tick = int(item["abs_tick"])
        mtype = str(item["msg"].get("type", "cc"))
        is_note_on = mtype == "note_on"
        channel = "note" if mtype in ("note_on", "note_off") else "cc"

        base_s = _ticks_to_seconds(abs_tick, bpm, tpb)
        jit_s = humanizer.jitter_ms(tick_index=tick_index, humanize_ms=perf.effective_humanize_ms, channel=channel) / 1000.0

        # E2E.3: apply anticipation bias to note_on only (avoid note_off length skew)
        bias_s = (perf.note_bias_ms / 1000.0) if is_note_on else 0.0

        offsets.append(base_s + jit_s + bias_s)

    # Round for stable JSON + human readability
    offsets_r = [round(x, 9) for x in offsets]

    return {
        "chosen_pattern_id": str(chosen_id),
        "target_offsets_s_first10": offsets_r,
        "effective_humanize_ms": round(perf.effective_humanize_ms, 4),
        "velocity_mul": round(perf.velocity_mul, 4),
        "note_bias_ms": round(perf.note_bias_ms, 4),
    }


def replay_vector_dir(
    vector_dir: Path,
    *,
    update_golden: bool,
    changelog_path: Path,
    bump_changelog_reason: Optional[str],
) -> ReplayResult:
    expected_path = vector_dir / "expected.json"
    produced = _compute_produced(vector_dir)

    expected = _load_json(expected_path) if expected_path.exists() else {}

    if produced != expected:
        (vector_dir / "_produced.json").write_text(_dump_json(produced), encoding="utf-8")
        _write_diff_txt(vector_dir=vector_dir, expected=expected, produced=produced)

        if update_golden:
            _assert_changelog_bumped_or_bump(
                changelog_path=changelog_path,
                vector_name=vector_dir.name,
                bump_reason=bump_changelog_reason,
            )
            expected_path.write_text(_dump_json(produced), encoding="utf-8")
            return ReplayResult(True, f"Updated golden: {vector_dir.name}")

        return ReplayResult(False, f"Replay mismatch in {vector_dir.name} (artifacts: _diff.txt, _produced.json)", [vector_dir.name])

    _cleanup_artifacts(vector_dir)
    return ReplayResult(True, f"Replay OK: {vector_dir.name}")


def replay_all(
    root: Path,
    *,
    update_golden: bool,
    changelog_path: Path,
    bump_changelog_reason: Optional[str],
) -> ReplayResult:
    if not root.exists():
        return ReplayResult(False, f"Vectors root not found: {root}")

    vec_dirs = sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("vector_")])
    if not vec_dirs:
        return ReplayResult(False, f"No vector_* directories found under {root}")

    failures: List[str] = []
    for vd in vec_dirs:
        res = replay_vector_dir(
            vd,
            update_golden=update_golden,
            changelog_path=changelog_path,
            bump_changelog_reason=bump_changelog_reason,
        )
        if not res.ok:
            failures.extend(res.failures or [vd.name])

    if failures:
        return ReplayResult(False, f"{len(failures)} vector(s) failed replay: {failures}", failures)

    return ReplayResult(True, f"All vectors passed ({len(vec_dirs)})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Vector dir (vector_*) OR vectors root (contains vector_* dirs).")
    ap.add_argument("--update-golden", action="store_true")
    ap.add_argument("--bump-changelog", default=None)
    ap.add_argument("--changelog", default=None)
    args = ap.parse_args()

    p = Path(args.path)
    repo_root = Path(__file__).resolve().parents[3]
    changelog_path = Path(args.changelog) if args.changelog else (repo_root / "fixtures" / "golden" / "e2e_vectors" / "CHANGELOG.md")

    prefix = f"[e2e-replay][engine={ENGINE_IDENTITY}]"

    if p.is_dir() and p.name.startswith("vector_"):
        res = replay_vector_dir(
            p,
            update_golden=args.update_golden,
            changelog_path=changelog_path,
            bump_changelog_reason=args.bump_changelog,
        )
    else:
        res = replay_all(
            p,
            update_golden=args.update_golden,
            changelog_path=changelog_path,
            bump_changelog_reason=args.bump_changelog,
        )

    if res.ok:
        print(f"{prefix} PASS: {res.message}")
        return 0
    print(f"{prefix} FAIL: {res.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
