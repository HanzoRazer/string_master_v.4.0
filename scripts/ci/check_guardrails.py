#!/usr/bin/env python3
"""
scripts/ci/check_guardrails.py

CI guardrail checks for Smart Guitar repos.
Prevents cross-contamination and enforces boundaries.

Usage:
    python scripts/ci/check_guardrails.py [--repo embedded|cloud]

Exit codes:
    0 = all checks pass
    1 = guardrail violation detected
"""

import argparse
import re
import sys
from pathlib import Path


# Forbidden imports in embedded repo (no cloud SDKs)
EMBEDDED_FORBIDDEN = [
    r"\bimport\s+openai\b",
    r"\bfrom\s+openai\b",
    r"\bimport\s+anthropic\b",
    r"\bfrom\s+anthropic\b",
    r"\bimport\s+boto3\b",
    r"\bfrom\s+boto3\b",
    r"\bimport\s+botocore\b",
    r"\bfrom\s+botocore\b",
    r"\bimport\s+google\.cloud\b",
    r"\bfrom\s+google\.cloud\b",
]

# Forbidden imports in cloud repo (no embedded engine)
CLOUD_FORBIDDEN = [
    r"\bfrom\s+zt_band\b",
    r"\bimport\s+zt_band\b",
    r"\bfrom\s+shared\.zone_tritone\b",
    r"\bimport\s+shared\.zone_tritone\b",
]

# Exempt files (can use forbidden imports with comment)
EXEMPT_MARKER = "# guardrail-exempt:"

# File extensions to check
CHECK_EXTENSIONS = {".py"}


def find_python_files(root: Path) -> list[Path]:
    """Find all Python files in the repo."""
    files = []
    for ext in CHECK_EXTENSIONS:
        files.extend(root.rglob(f"*{ext}"))
    return files


def check_file(filepath: Path, patterns: list[str]) -> list[tuple[int, str, str]]:
    """
    Check a file for forbidden patterns.
    
    Returns list of (line_number, line_content, matched_pattern) tuples.
    """
    violations = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return violations
    
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        # Skip exempted lines
        if EXEMPT_MARKER in line:
            continue
        
        for pattern in patterns:
            if re.search(pattern, line):
                violations.append((i, line.strip(), pattern))
    
    return violations


def main():
    parser = argparse.ArgumentParser(description="CI guardrail checks")
    parser.add_argument(
        "--repo",
        choices=["embedded", "cloud"],
        default="embedded",
        help="Which repo type to check (default: embedded)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to check (default: current directory)",
    )
    args = parser.parse_args()
    
    # Select patterns based on repo type
    if args.repo == "embedded":
        patterns = EMBEDDED_FORBIDDEN
        repo_desc = "embedded (no cloud SDKs)"
    else:
        patterns = CLOUD_FORBIDDEN
        repo_desc = "cloud (no embedded engine)"
    
    print(f"Checking guardrails for: {repo_desc}")
    print(f"Root: {args.root.absolute()}")
    print()
    
    # Find and check files
    files = find_python_files(args.root)
    total_violations = 0
    
    for filepath in files:
        # Skip __pycache__ and .venv
        if "__pycache__" in str(filepath) or ".venv" in str(filepath):
            continue
        
        violations = check_file(filepath, patterns)
        if violations:
            rel_path = filepath.relative_to(args.root)
            print(f"VIOLATION: {rel_path}")
            for line_num, line_content, pattern in violations:
                print(f"  Line {line_num}: {line_content}")
                print(f"    Pattern: {pattern}")
            print()
            total_violations += len(violations)
    
    # Summary
    print("=" * 60)
    if total_violations == 0:
        print("✓ All guardrail checks passed")
        return 0
    else:
        print(f"✗ {total_violations} guardrail violation(s) found")
        print()
        print("To exempt a line, add comment: # guardrail-exempt: <reason>")
        return 1


if __name__ == "__main__":
    sys.exit(main())
