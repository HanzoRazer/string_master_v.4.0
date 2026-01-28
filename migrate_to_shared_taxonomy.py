#!/usr/bin/env python3
"""
migrate_to_shared_taxonomy.py

Migrates all *_canonical.json files to use the shared taxonomy.json vocabulary.
- Replaces pack-local style_taxonomy with references to shared IDs
- Replaces pack-local technique_taxonomy with references to shared IDs
- Adds taxonomy_ref field pointing to taxonomy.json
- Preserves all exercise data

Run: python migrate_to_shared_taxonomy.py [--dry-run]
"""
import json
import glob
import os
import sys
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# Load shared taxonomy
with open(os.path.join(ROOT, "taxonomy.json"), encoding="utf-8") as f:
    TAXONOMY = json.load(f)

STYLE_MAP = TAXONOMY["migration_map"]["style_families"]
TECHNIQUE_MAP = TAXONOMY["migration_map"]["techniques"]

# Build reverse lookup for validation
VALID_STYLES = {s["id"] for s in TAXONOMY["style_families"]}
VALID_TECHNIQUES = {t["id"] for t in TAXONOMY["technique_categories"]}


def migrate_style_family(old_id):
    """Map old pack-specific style ID to shared taxonomy ID."""
    if old_id in VALID_STYLES:
        return old_id  # Already a valid shared ID
    if old_id in STYLE_MAP:
        return STYLE_MAP[old_id]
    # Fuzzy match: try partial matches
    for old, new in STYLE_MAP.items():
        if old in old_id or old_id in old:
            return new
    print(f"  WARNING: Unknown style family '{old_id}' - keeping as-is")
    return old_id


def migrate_technique(old_id):
    """Map old pack-specific technique ID to shared taxonomy ID."""
    if old_id in VALID_TECHNIQUES:
        return old_id  # Already a valid shared ID
    if old_id in TECHNIQUE_MAP:
        return TECHNIQUE_MAP[old_id]
    # Fuzzy match
    for old, new in TECHNIQUE_MAP.items():
        if old in old_id or old_id in old:
            return new
    print(f"  WARNING: Unknown technique '{old_id}' - keeping as-is")
    return old_id


def migrate_canonical(filepath, dry_run=False):
    """Migrate a single canonical JSON to use shared taxonomy."""
    print(f"\nProcessing: {os.path.basename(filepath)}")

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    pack_id = data.get("pack_id", "unknown")

    # Track migrations
    style_migrations = {}
    technique_migrations = {}

    # Build local ID -> shared ID maps from pack's taxonomy
    local_style_map = {}
    local_technique_map = {}

    if "style_taxonomy" in data:
        for fam in data["style_taxonomy"].get("families", []):
            old_id = fam["id"]
            new_id = migrate_style_family(old_id)
            local_style_map[old_id] = new_id
            if old_id != new_id:
                style_migrations[old_id] = new_id

    if "technique_taxonomy" in data:
        for cat in data["technique_taxonomy"].get("categories", []):
            old_id = cat["id"]
            new_id = migrate_technique(old_id)
            local_technique_map[old_id] = new_id
            if old_id != new_id:
                technique_migrations[old_id] = new_id

    # Update exercises to use new IDs
    exercises_updated = 0
    for ex in data.get("exercises", []):
        if "style_family" in ex:
            old = ex["style_family"]
            if old in local_style_map:
                ex["style_family"] = local_style_map[old]
                exercises_updated += 1
        if "technique" in ex:
            old = ex["technique"]
            if old in local_technique_map:
                ex["technique"] = local_technique_map[old]
                exercises_updated += 1

    # Remove pack-local taxonomies, add reference to shared
    if "style_taxonomy" in data:
        del data["style_taxonomy"]
    if "technique_taxonomy" in data:
        del data["technique_taxonomy"]

    data["taxonomy_ref"] = "taxonomy.json"

    # Report changes
    print(f"  Style migrations: {len(style_migrations)}")
    for old, new in style_migrations.items():
        print(f"    {old} -> {new}")
    print(f"  Technique migrations: {len(technique_migrations)}")
    for old, new in technique_migrations.items():
        print(f"    {old} -> {new}")
    print(f"  Exercises updated: {exercises_updated}")

    if not dry_run:
        # Backup original
        backup_dir = os.path.join(ROOT, "backup_pre_migration")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy(filepath, os.path.join(backup_dir, os.path.basename(filepath)))

        # Write migrated version
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  WRITTEN: {filepath}")
    else:
        print(f"  [DRY RUN] Would write: {filepath}")

    return {
        "pack_id": pack_id,
        "style_migrations": style_migrations,
        "technique_migrations": technique_migrations,
        "exercises_updated": exercises_updated
    }


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No files will be modified")
        print("=" * 60)

    print(f"\nShared taxonomy: {len(VALID_STYLES)} style families, {len(VALID_TECHNIQUES)} techniques")

    canonical_files = sorted(glob.glob(os.path.join(ROOT, "*_canonical.json")))
    print(f"Found {len(canonical_files)} canonical files to migrate")

    results = []
    for filepath in canonical_files:
        result = migrate_canonical(filepath, dry_run=dry_run)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)

    total_style = sum(len(r["style_migrations"]) for r in results)
    total_technique = sum(len(r["technique_migrations"]) for r in results)
    total_exercises = sum(r["exercises_updated"] for r in results)

    print(f"Files processed: {len(results)}")
    print(f"Style family migrations: {total_style}")
    print(f"Technique migrations: {total_technique}")
    print(f"Exercise fields updated: {total_exercises}")

    if dry_run:
        print("\nRun without --dry-run to apply changes.")
    else:
        print(f"\nBackups saved to: {os.path.join(ROOT, 'backup_pre_migration')}/")
        print("Migration complete!")


if __name__ == "__main__":
    main()
