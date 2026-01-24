# zt_band/adapters/arranger_replay_gate_v1.py
"""
Arranger golden vector replay gate.

Validates that build_arranger_control_plan() produces deterministic outputs
matching expected_plan.json fixtures.

Usage:
    python -m zt_band.adapters.arranger_replay_gate_v1 fixtures/golden/arranger_vectors
    python -m zt_band.adapters.arranger_replay_gate_v1 fixtures/golden/arranger_vectors --update-golden --bump-changelog "reason"
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from zt_band.adapters.arranger_intent_adapter import build_arranger_control_plan


ENGINE_IDENTITY: str = "arranger_stub_v1"


@dataclass(frozen=True)
class ReplayResult:
    ok: bool
    message: str
    failures: Optional[List[str]] = None


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _dump_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stable_json_lines(obj: Dict[str, Any]) -> List[str]:
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


def _write_diff_txt(*, vector_dir: Path, expected: Dict[str, Any], produced: Dict[str, Any]) -> None:
    a = _stable_json_lines(expected)
    b = _stable_json_lines(produced)

    diff = difflib.unified_diff(
        a,
        b,
        fromfile="expected_plan.json",
        tofile="produced_plan.json",
        lineterm="",
    )

    repo_root = Path(__file__).resolve().parents[3]
    sha = _git_sha_or_unknown(repo_root)
    vector_name = vector_dir.name
    rel_path = f"fixtures/golden/arranger_vectors/{vector_name}"

    header = [
        f"# Vector: {vector_name}",
        f"# Reproduce: python -m zt_band.adapters.arranger_replay_gate_v1 {rel_path}",
        f"# Engine git sha: {sha}",
        f"# Engine identity: {ENGINE_IDENTITY}",
        "",
    ]
    out = "\n".join(header + list(diff)) + "\n"
    (vector_dir / "_diff.txt").write_text(out, encoding="utf-8")


def _cleanup_artifacts(vector_dir: Path) -> None:
    for name in ("_diff.txt", "_produced.plan.json"):
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
            "# Arranger Vectors Changelog\n\n"
            "This changelog must be updated whenever `expected_plan.json` is updated via `--update-golden`.\n\n"
            "Format:\n"
            "- YYYY-MM-DD — vector_name — short reason\n"
        ),
        encoding="utf-8",
    )


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _append_changelog_entry(changelog_path: Path, vector_name: str, reason: str) -> None:
    _ensure_changelog_exists(changelog_path)
    line = f"- {_today_utc()} — {vector_name} — {reason.strip()}\n"
    with changelog_path.open("a", encoding="utf-8") as f:
        f.write(line)


def _changelog_has_vector_entry(text: str, vector_name: str) -> bool:
    return vector_name in text


def _assert_changelog_bumped_or_bump(
    *,
    changelog_path: Path,
    vector_name: str,
    bump_reason: Optional[str],
) -> None:
    _ensure_changelog_exists(changelog_path)
    text = changelog_path.read_text(encoding="utf-8")
    if _changelog_has_vector_entry(text, vector_name):
        return
    if bump_reason and bump_reason.strip():
        _append_changelog_entry(changelog_path, vector_name, bump_reason)
        return
    raise RuntimeError(
        f"Refusing to update goldens for {vector_name} because changelog not bumped.\n"
        f"Add an entry to {changelog_path} mentioning '{vector_name}', or re-run with:\n"
        f'  --bump-changelog "short reason"\n'
    )


def replay_vector_dir(
    vector_dir: Path,
    *,
    update_golden: bool,
    changelog_path: Path,
    bump_changelog_reason: Optional[str],
) -> ReplayResult:
    intent_p = vector_dir / "intent.json"
    exp_p = vector_dir / "expected_plan.json"
    meta_p = vector_dir / "meta.json"

    if not intent_p.exists() or not exp_p.exists():
        return ReplayResult(False, f"Missing required files in {vector_dir}", [vector_dir.name])

    intent = _load_json(intent_p)
    expected = _load_json(exp_p)
    _ = _load_json(meta_p) if meta_p.exists() else {}

    plan = build_arranger_control_plan(intent)

    # Convert dataclass -> dict for stable compare
    produced = plan.__dict__.copy()

    if produced != expected:
        _write_diff_txt(vector_dir=vector_dir, expected=expected, produced=produced)
        (vector_dir / "_produced.plan.json").write_text(_dump_json(produced), encoding="utf-8")

        if update_golden:
            try:
                _assert_changelog_bumped_or_bump(
                    changelog_path=changelog_path,
                    vector_name=vector_dir.name,
                    bump_reason=bump_changelog_reason,
                )
            except Exception as e:
                return ReplayResult(False, str(e), [vector_dir.name])

            exp_p.write_text(_dump_json(produced), encoding="utf-8")
            return ReplayResult(True, f"Updated golden: {vector_dir.name}")

        return ReplayResult(
            False,
            f"Replay mismatch in {vector_dir.name} (artifacts: _diff.txt, _produced.plan.json)",
            [vector_dir.name],
        )

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

    if update_golden:
        return ReplayResult(True, f"Goldens updated OK ({len(vec_dirs)} vector(s))")

    return ReplayResult(True, f"All vectors passed ({len(vec_dirs)})")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Arranger golden vector replay gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("path", help="Vector dir (vector_*) OR vectors root (contains vector_* dirs).")
    ap.add_argument("--update-golden", action="store_true", help="Update expected_plan.json to match produced output")
    ap.add_argument("--bump-changelog", default=None, help="Reason for changelog entry (required if updating new vector)")
    ap.add_argument("--changelog", default=None, help="Path to CHANGELOG.md (default: auto-detect)")
    args = ap.parse_args()

    p = Path(args.path)
    repo_root = Path(__file__).resolve().parents[3]
    changelog_path = (
        Path(args.changelog)
        if args.changelog
        else (repo_root / "fixtures" / "golden" / "arranger_vectors" / "CHANGELOG.md")
    )

    prefix = f"[arranger-replay][engine={ENGINE_IDENTITY}]"

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
