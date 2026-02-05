#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REAPER_DIR = REPO_ROOT / "scripts" / "reaper"

FAIL = 0

def fail(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"FAIL: {msg}")

def ok(msg: str) -> None:
    print(f"OK:   {msg}")

def scan_text_files():
    if not REAPER_DIR.exists():
        fail(f"Missing directory: {REAPER_DIR}")
        return

    lua_files = sorted([p for p in REAPER_DIR.rglob("*.lua") if "_deprecated" not in p.parts])
    if not lua_files:
        fail("No .lua files found under scripts/reaper")
        return

    bad_dkjson = []
    bad_7878 = []
    bad_osexec = []

    for p in lua_files:
        txt = p.read_text(encoding="utf-8", errors="replace")

        if "dkjson.lua" in txt:
            bad_dkjson.append(p)

        # catch localhost:7878 and :7878 broadly (but avoid false positives in comments? we still fail)
        if "7878" in txt:
            if "8420" not in txt:  # allow docs mentioning both; scripts should not mention 7878 at all
                bad_7878.append(p)
            else:
                # if both are present, still suspicious: treat as fail
                bad_7878.append(p)

        # os.execute is banned in network/hotkey scripts; we ban it across all blessed lua in reaper dir
        if "os.execute(" in txt:
            bad_osexec.append(p)

    if bad_dkjson:
        fail("Found forbidden reference 'dkjson.lua' in:\n  " + "\n  ".join(str(p.relative_to(REPO_ROOT)) for p in bad_dkjson))
    else:
        ok("No dkjson.lua references")

    if bad_7878:
        fail("Found forbidden port reference '7878' in:\n  " + "\n  ".join(str(p.relative_to(REPO_ROOT)) for p in bad_7878))
    else:
        ok("No 7878 references")

    if bad_osexec:
        fail("Found forbidden 'os.execute(' usage in:\n  " + "\n  ".join(str(p.relative_to(REPO_ROOT)) for p in bad_osexec))
    else:
        ok("No os.execute usage in scripts/reaper (blessed)")

def check_contract_doc():
    contract = REPO_ROOT / "docs" / "contracts" / "SG_REAPER_CONTRACT_V1.md"
    if contract.exists():
        ok("Contract doc present")
    else:
        fail("Missing contract doc: docs/contracts/SG_REAPER_CONTRACT_V1.md")

def main() -> int:
    check_contract_doc()
    scan_text_files()
    if FAIL:
        print(f"\nGUARD RESULT: FAIL ({FAIL})")
        return 1
    print("\nGUARD RESULT: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
