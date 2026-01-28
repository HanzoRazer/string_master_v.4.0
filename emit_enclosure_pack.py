#!/usr/bin/env python3
"""
emit_enclosure_pack.py

Reads enclosures_canonical.json and emits organized session playlists.

Output:
  playlists/enclosure_foundations.ztplay       (tier 1: basic types)
  playlists/enclosure_chord_quality.ztplay     (tier 2: chord quality targeting)
  playlists/enclosure_progressions.ztplay      (tier 3: ii-V-I and resolution)
  playlists/enclosure_advanced.ztplay          (tier 4: turnarounds, Barry Harris)
  playlists/enclosure_context_major.ztplay     (by chord context)
  playlists/enclosure_context_dominant.ztplay
  playlists/enclosure_context_ii_v_i.ztplay
  playlists/enclosure_progressive.ztplay       (curriculum path)
  playlists/enclosure_all_14.ztplay            (master)

Does NOT regenerate existing .ztex or .ztprog files (they are hand-crafted).
"""
import json
import os
import sys

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── Load canonical data ──
with open(os.path.join(ROOT, "enclosures_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

exercises = canon["exercises"]
ex_by_id = {ex["id"]: ex for ex in exercises}
tiers = canon["difficulty_tiers"]
contexts = canon["chord_contexts"]
groups = canon["playlist_groups"]


# ── Helpers ──

def yaml_str(s):
    """Quote a string for YAML output."""
    if any(c in s for c in ':{}[]&*?|>!%@`#,'):
        return f'"{s}"'
    if s.startswith(("'", '"', "-", " ")):
        return f'"{s}"'
    return f'"{s}"'


def exercise_prog_path(ex):
    """Return playlist-relative path to the .ztprog for an exercise."""
    return f"exercises/enclosures/{ex['id']}.ztprog"


def build_item(ex, repeats=2):
    """Build a playlist item dict from an exercise."""
    return {
        "name": ex["title"],
        "file": exercise_prog_path(ex),
        "repeats": repeats,
        "notes": ex.get("focus", ""),
    }


def emit_session_playlist(playlist_id, title, category, tags, defaults,
                          items, outdir):
    """Emit a .ztplay session playlist file."""
    fname = f"{playlist_id}.ztplay"
    lines = [
        f"id: {playlist_id}",
        f"title: {yaml_str(title)}",
        f"category: {category}",
        f"tags: [{', '.join(tags)}]",
        "",
        "defaults:",
    ]
    for dk, dv in defaults.items():
        lines.append(f"  {dk}: {dv}")
    lines.append("")
    lines.append("items:")

    for item in items:
        lines.append(f"  - name: {yaml_str(item['name'])}")
        lines.append(f"    file: {yaml_str(item['file'])}")
        lines.append(f"    repeats: {item.get('repeats', 2)}")
        if item.get("notes"):
            lines.append(f"    notes: {yaml_str(item['notes'])}")
        lines.append("")

    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


# ── Tier Playlists ──

def emit_tier_playlists(outdir):
    """Emit one session playlist per difficulty tier."""
    tier_meta = {
        "foundations": {
            "title": "Enclosures: Foundations (Basic Types)",
            "tags": ["enclosure", "bebop", "foundations"],
        },
        "chord_quality": {
            "title": "Enclosures: Chord Quality Targeting",
            "tags": ["enclosure", "bebop", "chord_quality"],
        },
        "progressions": {
            "title": "Enclosures: Progressions & Resolution",
            "tags": ["enclosure", "bebop", "ii_v_i", "resolution"],
        },
        "advanced": {
            "title": "Enclosures: Advanced Patterns (Turnarounds & Barry Harris)",
            "tags": ["enclosure", "bebop", "advanced", "barry_harris"],
        },
    }

    emitted = []
    for tier_key, ex_ids in groups["by_tier"].items():
        meta = tier_meta[tier_key]
        items = []
        for eid in ex_ids:
            ex = ex_by_id.get(eid)
            if ex:
                items.append(build_item(ex, repeats=3))
        if not items:
            continue

        pid = f"enclosure_{tier_key}"
        defaults = {"tempo": 72, "style": "swing"}
        fname = emit_session_playlist(pid, meta["title"], "tier_session",
                                      meta["tags"], defaults, items, outdir)
        emitted.append((fname, len(items)))

    return emitted


# ── Context Playlists ──

def emit_context_playlists(outdir):
    """Emit one session playlist per chord context group."""
    context_meta = {
        "major": {
            "title": "Enclosures: Major Harmony (Imaj7 / I6)",
            "tags": ["enclosure", "bebop", "major", "Imaj7"],
        },
        "dominant": {
            "title": "Enclosures: Dominant Harmony (V7 / V7alt)",
            "tags": ["enclosure", "bebop", "dominant", "V7"],
        },
        "ii_v_i": {
            "title": "Enclosures: ii-V-I Cadence",
            "tags": ["enclosure", "bebop", "ii_v_i", "cadence"],
        },
    }

    emitted = []
    for ctx_key, ex_ids in groups["by_context"].items():
        meta = context_meta[ctx_key]
        items = []
        for eid in ex_ids:
            ex = ex_by_id.get(eid)
            if ex:
                items.append(build_item(ex, repeats=2))
        if not items:
            continue

        pid = f"enclosure_context_{ctx_key}"
        defaults = {"tempo": 72, "style": "swing"}
        fname = emit_session_playlist(pid, meta["title"], "context_session",
                                      meta["tags"], defaults, items, outdir)
        emitted.append((fname, len(items)))

    return emitted


# ── Progressive Path ──

def emit_progressive_playlist(outdir):
    """Emit a progressive difficulty path playlist."""
    path_order = groups["progressive_path"]["order"]
    items = []
    for eid in path_order:
        ex = ex_by_id.get(eid)
        if ex:
            items.append(build_item(ex, repeats=3))
    if not items:
        return None

    pid = "enclosure_progressive"
    title = "Enclosures: Progressive Path (Foundations to Advanced)"
    tags = ["enclosure", "bebop", "progressive", "curriculum"]
    defaults = {"tempo": 72, "style": "swing"}
    fname = emit_session_playlist(pid, title, "progressive_path",
                                  tags, defaults, items, outdir)
    return (fname, len(items))


# ── Master Playlist ──

def emit_master_playlist(outdir):
    """Emit a master playlist with all 14 exercises."""
    tier_order = ["foundations", "chord_quality", "progressions", "advanced"]
    tier_rank = {t: i for i, t in enumerate(tier_order)}

    sorted_exs = sorted(exercises, key=lambda e: (
        tier_rank.get(e["difficulty_tier"], 99),
        e["id"],
    ))

    items = []
    for ex in sorted_exs:
        items.append(build_item(ex, repeats=1))

    pid = "enclosure_all_14"
    title = "Enclosures: Complete 14-Exercise Session"
    tags = ["enclosure", "bebop", "complete"]
    defaults = {"tempo": 72, "style": "swing"}
    fname = emit_session_playlist(pid, title, "complete_session",
                                  tags, defaults, items, outdir)
    return (fname, len(items))


# ── Main ──

if __name__ == "__main__":
    play_dir = os.path.join(ROOT, "playlists")
    os.makedirs(play_dir, exist_ok=True)

    total = 0

    # 1. Tier playlists
    print("Tier session playlists:")
    tier_results = emit_tier_playlists(play_dir)
    for fname, count in tier_results:
        print(f"  {fname} ({count} items)")
        total += 1

    # 2. Context playlists
    print("\nContext session playlists:")
    context_results = emit_context_playlists(play_dir)
    for fname, count in context_results:
        print(f"  {fname} ({count} items)")
        total += 1

    # 3. Progressive path
    print("\nProgressive path playlist:")
    progressive = emit_progressive_playlist(play_dir)
    if progressive:
        print(f"  {progressive[0]} ({progressive[1]} items)")
        total += 1

    # 4. Master
    print("\nMaster playlist:")
    master = emit_master_playlist(play_dir)
    if master:
        print(f"  {master[0]} ({master[1]} items)")
        total += 1

    print(f"\nTotal playlists emitted: {total}")
    print(f"Output: {play_dir}/")
