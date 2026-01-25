from __future__ import annotations

import argparse
import importlib
import re
from collections import Counter
from typing import Any


REQUIRED_ATTRS = ("id", "family", "max_density", "min_energy", "max_energy")
VALID_FAMILIES = {"straight", "swing", "shuffle", "free"}

# Optional quality rule: prog_style lookup consistency
ENFORCE_KEY_EQUALS_ID = True

_ID_RE = re.compile(r"^[a-z0-9_]+$")


def _getattr(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _as_int(x: Any) -> int | None:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def _import_registry(module_path: str, registry_name: str) -> dict:
    mod = importlib.import_module(module_path)
    reg = getattr(mod, registry_name, None)
    if not isinstance(reg, dict):
        raise TypeError(f"{module_path}.{registry_name} is not a dict")
    if not reg:
        raise ValueError(f"{module_path}.{registry_name} is empty")
    return reg


def _fmt_pat_snapshot(pat: Any) -> str:
    pid = _getattr(pat, "id")
    fam = _getattr(pat, "family")
    md = _getattr(pat, "max_density")
    emin = _getattr(pat, "min_energy")
    emax = _getattr(pat, "max_energy")
    return f"id={pid!r}, family={fam!r}, max_density={md!r}, min_energy={emin!r}, max_energy={emax!r}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate STYLE_REGISTRY pattern metadata required by choose_pattern().")
    ap.add_argument(
        "--module",
        default="zt_band.arranger.patterns",
        help="Python module containing the registry (default: zt_band.arranger.patterns)",
    )
    ap.add_argument(
        "--registry-name",
        default="STYLE_REGISTRY",
        help="Registry variable name in the module (default: STYLE_REGISTRY)",
    )

    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true", help="Fail CI on strict checks + quality checks (default).")
    mode.add_argument("--warn", action="store_true", help="Fail CI only on strict checks; print quality issues as WARN.")
    args = ap.parse_args(argv)

    strict_mode = True
    if args.warn:
        strict_mode = False  # strict checks still fail; quality checks become warnings

    try:
        registry = _import_registry(args.module, args.registry_name)
    except Exception as e:
        print(f"[pattern-metadata] FAIL: cannot load registry: {args.module}.{args.registry_name}: {e}")
        return 2

    failures: list[str] = []
    warnings: list[str] = []

    seen_ids: set[str] = set()
    family_counts: Counter[str] = Counter()
    density_caps: Counter[int] = Counter()
    energy_ranges: Counter[str] = Counter()

    for key, pat in registry.items():
        prefix = f"[{key}]"

        # Snapshot for actionable output
        snap = _fmt_pat_snapshot(pat)

        # -------------------------
        # STRICT checks (always enforced)
        # -------------------------

        missing = [a for a in REQUIRED_ATTRS if _getattr(pat, a) is None]
        if missing:
            failures.append(
                f"{prefix} missing attrs {missing} :: {snap}\n"
                f"  Fix: add fields {missing} to this pattern object (required by choose_pattern)."
            )
            continue

        pid = str(_getattr(pat, "id"))
        fam = str(_getattr(pat, "family"))
        max_density = _as_int(_getattr(pat, "max_density"))
        min_energy = _as_int(_getattr(pat, "min_energy"))
        max_energy = _as_int(_getattr(pat, "max_energy"))

        # id uniqueness
        if pid in seen_ids:
            failures.append(
                f"{prefix} duplicate pattern.id '{pid}' :: {snap}\n"
                f"  Fix: ensure each pattern has a unique id."
            )
        else:
            seen_ids.add(pid)

        # family validity
        if fam not in VALID_FAMILIES:
            failures.append(
                f"{prefix} invalid family '{fam}' :: {snap}\n"
                f"  Fix: set family to one of {sorted(VALID_FAMILIES)}."
            )

        # bounds
        if max_density is None or not (0 <= max_density <= 2):
            failures.append(
                f"{prefix} max_density={max_density!r} out of range [0..2] :: {snap}\n"
                f"  Fix: max_density must be int 0..2 (sparse=0, normal=1, dense=2)."
            )
        if min_energy is None or not (0 <= min_energy <= 2):
            failures.append(
                f"{prefix} min_energy={min_energy!r} out of range [0..2] :: {snap}\n"
                f"  Fix: min_energy must be int 0..2 (low=0, mid=1, high=2)."
            )
        if max_energy is None or not (0 <= max_energy <= 2):
            failures.append(
                f"{prefix} max_energy={max_energy!r} out of range [0..2] :: {snap}\n"
                f"  Fix: max_energy must be int 0..2 (low=0, mid=1, high=2)."
            )
        if (
            min_energy is not None
            and max_energy is not None
            and min_energy > max_energy
        ):
            failures.append(
                f"{prefix} min_energy={min_energy} > max_energy={max_energy} :: {snap}\n"
                f"  Fix: ensure min_energy <= max_energy."
            )

        # -------------------------
        # PASS summary stats (collected regardless)
        # -------------------------
        family_counts[fam] += 1
        if max_density is not None:
            density_caps[max_density] += 1
        if min_energy is not None and max_energy is not None:
            energy_ranges[f"{min_energy}-{max_energy}"] += 1

        # -------------------------
        # QUALITY checks (strict or warn)
        # -------------------------

        # key == id consistency (prog_style lookup guarantee)
        if ENFORCE_KEY_EQUALS_ID and str(key) != pid:
            msg = (
                f"{prefix} registry key '{key}' != pattern.id '{pid}' :: {snap}\n"
                f"  Fix: rename registry key to '{pid}' OR set pattern.id to '{key}'."
            )
            (failures if strict_mode else warnings).append(msg)

        # optional id naming convention (helps keep YAML/CLI sane)
        if not _ID_RE.match(pid):
            msg = (
                f"{prefix} pattern.id '{pid}' violates naming convention ^[a-z0-9_]+$ :: {snap}\n"
                f"  Fix: use lowercase snake_case id (e.g. 'swing_basic')."
            )
            (failures if strict_mode else warnings).append(msg)

    # Second pass quality check: ensure every pattern.id is present as a key
    if ENFORCE_KEY_EQUALS_ID:
        missing_keys = []
        for _, pat in registry.items():
            pid = str(_getattr(pat, "id"))
            if pid not in registry:
                missing_keys.append(pid)
        if missing_keys:
            msg = (
                f"[registry] pattern.id not present as registry key for: {sorted(set(missing_keys))}\n"
                f"  Fix: ensure STYLE_REGISTRY keys include every pattern.id exactly (key==id)."
            )
            (failures if strict_mode else warnings).append(msg)

    # Emit warnings (if any) but only fail on failures
    if warnings:
        print("[pattern-metadata] WARN:")
        for w in warnings:
            print(f" - {w}")

    if failures:
        print("[pattern-metadata] FAIL: STYLE_REGISTRY metadata issues detected:")
        for f in failures:
            print(f" - {f}")
        print("\n[pattern-metadata] Strict requirements:")
        print("  - required attrs: id, family, max_density, min_energy, max_energy")
        print("  - family in {straight, swing, shuffle, free}")
        print("  - max_density in [0..2], min_energy/max_energy in [0..2], min<=max")
        print("\n[pattern-metadata] Tip: run with --warn to downgrade quality checks to warnings.")
        return 1

    # PASS summary
    total = len(registry)
    print(f"[pattern-metadata] PASS: {total} patterns validated ({args.module}.{args.registry_name})")

    fam_line = ", ".join([f"{k}={family_counts.get(k, 0)}" for k in sorted(VALID_FAMILIES)])
    print(f"[pattern-metadata] Summary: families: {fam_line}")

    dens_line = ", ".join([f"{k}={density_caps.get(k, 0)}" for k in [0, 1, 2]])
    print(f"[pattern-metadata] Summary: max_density caps: {dens_line} (0=sparse, 1=normal, 2=dense)")

    # energy ranges in sorted order for stability
    er_items = sorted(energy_ranges.items(), key=lambda kv: kv[0])
    if er_items:
        er_line = ", ".join([f"{k}={v}" for k, v in er_items])
        print(f"[pattern-metadata] Summary: energy ranges (min-max): {er_line} (0=low, 1=mid, 2=high)")
    else:
        print("[pattern-metadata] Summary: energy ranges: (none)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
