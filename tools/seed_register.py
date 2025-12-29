#!/usr/bin/env python3
"""
seed_register.py

Create a *.seed.json file from the canonical template.
This tool does NOT analyze audio or MIDI.
It exists purely to enforce provenance discipline.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


TEMPLATE = {
    "source_category": "",
    "provider": "",
    "created_at": "",
    "license_notes": "",
    "source_reference": "",
    "assets": {
        "audio": [],
        "midi": [],
        "stems": []
    },
    "tags": [],
    "notes": ""
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a .seed.json metadata file next to a seed asset."
    )
    parser.add_argument(
        "target",
        help="Path where the .seed.json file should be created "
             "(file or directory).",
    )
    parser.add_argument(
        "--category",
        required=True,
        choices=[
            "handcrafted",
            "public_domain_or_open",
            "licensed_third_party",
            "ai_generated_external",
        ],
        help="Seed source category.",
    )
    parser.add_argument(
        "--provider",
        default="",
        help="Creator, vendor, or AI provider name.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Short human-readable purpose for this seed.",
    )

    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()

    if target.is_dir():
        seed_path = target / f"{target.name}.seed.json"
    else:
        seed_path = target.with_suffix(target.suffix + ".seed.json")

    if seed_path.exists():
        raise SystemExit(f"Seed file already exists: {seed_path}")

    data = TEMPLATE.copy()
    data["source_category"] = args.category
    data["provider"] = args.provider
    data["created_at"] = date.today().isoformat()
    data["notes"] = args.notes

    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

    print(f"Created seed metadata: {seed_path}")


if __name__ == "__main__":
    main()
