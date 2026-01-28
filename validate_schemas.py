#!/usr/bin/env python3
"""
validate_schemas.py

Validates all .ztex, .ztprog, and .ztplay files against their JSON schemas.
Reports mismatches and counts pass/fail by file type.

Usage:
    python validate_schemas.py           # validate all files
    python validate_schemas.py --verbose  # show per-file results
"""
import os
import sys
import json
import glob
import yaml
import jsonschema
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(ROOT, "schemas")

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv


def load_schema(name):
    path = os.path.join(SCHEMAS_DIR, name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_files(pattern):
    """Recursively find files matching a glob pattern."""
    return sorted(glob.glob(os.path.join(ROOT, pattern), recursive=True))


def validate_file(data, schema, path):
    """Validate a single file against a schema. Returns list of error strings."""
    errors = []
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        # Collect all errors, not just the first
        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(data):
            rel = os.path.relpath(path, ROOT)
            msg = error.message
            if error.absolute_path:
                loc = " -> ".join(str(p) for p in error.absolute_path)
                errors.append(f"  {rel}: [{loc}] {msg}")
            else:
                errors.append(f"  {rel}: {msg}")
    except Exception as e:
        rel = os.path.relpath(path, ROOT)
        errors.append(f"  {rel}: PARSE ERROR: {e}")
    return errors


def main():
    ztex_schema = load_schema("ztex.schema.json")
    ztprog_schema = load_schema("ztprog.schema.json")
    ztplay_schema = load_schema("ztplay.schema.json")

    results = defaultdict(lambda: {"pass": 0, "fail": 0, "errors": []})

    # ── .ztex files ──
    ztex_files = find_files("**/*.ztex")
    for path in ztex_files:
        data = load_yaml(path)
        if data is None:
            results["ztex"]["fail"] += 1
            results["ztex"]["errors"].append(f"  {os.path.relpath(path, ROOT)}: empty/null YAML")
            continue
        errs = validate_file(data, ztex_schema, path)
        if errs:
            results["ztex"]["fail"] += 1
            results["ztex"]["errors"].extend(errs)
        else:
            results["ztex"]["pass"] += 1
        if VERBOSE and not errs:
            print(f"  PASS  {os.path.relpath(path, ROOT)}")

    # ── .ztprog files ──
    ztprog_files = find_files("**/*.ztprog")
    for path in ztprog_files:
        data = load_yaml(path)
        if data is None:
            results["ztprog"]["fail"] += 1
            results["ztprog"]["errors"].append(f"  {os.path.relpath(path, ROOT)}: empty/null YAML")
            continue
        errs = validate_file(data, ztprog_schema, path)
        if errs:
            results["ztprog"]["fail"] += 1
            results["ztprog"]["errors"].extend(errs)
        else:
            results["ztprog"]["pass"] += 1
        if VERBOSE and not errs:
            print(f"  PASS  {os.path.relpath(path, ROOT)}")

    # ── .ztplay files ──
    ztplay_files = find_files("**/*.ztplay")
    for path in ztplay_files:
        data = load_yaml(path)
        if data is None:
            results["ztplay"]["fail"] += 1
            results["ztplay"]["errors"].append(f"  {os.path.relpath(path, ROOT)}: empty/null YAML")
            continue
        errs = validate_file(data, ztplay_schema, path)
        if errs:
            results["ztplay"]["fail"] += 1
            results["ztplay"]["errors"].extend(errs)
        else:
            results["ztplay"]["pass"] += 1
        if VERBOSE and not errs:
            print(f"  PASS  {os.path.relpath(path, ROOT)}")

    # ── Report ──
    total_pass = 0
    total_fail = 0
    print("\n" + "=" * 60)
    print("Schema Validation Report")
    print("=" * 60)

    for ftype in ("ztex", "ztprog", "ztplay"):
        r = results[ftype]
        p, f = r["pass"], r["fail"]
        total_pass += p
        total_fail += f
        status = "PASS" if f == 0 else "FAIL"
        print(f"\n.{ftype}: {p} pass, {f} fail  [{status}]")
        if r["errors"]:
            # Show first 10 errors per type to avoid flood
            shown = r["errors"][:10]
            for e in shown:
                print(e)
            if len(r["errors"]) > 10:
                print(f"  ... and {len(r['errors']) - 10} more errors")

    print(f"\n{'=' * 60}")
    print(f"Total: {total_pass} pass, {total_fail} fail")
    if total_fail == 0:
        print("ALL FILES VALID")
    else:
        print(f"FAILURES: {total_fail} files need attention")
    print("=" * 60)

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
