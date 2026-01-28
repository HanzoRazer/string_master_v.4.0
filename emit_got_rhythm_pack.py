#!/usr/bin/env python3
"""
emit_got_rhythm_pack.py

Reads got_rhythm_canonical.json and emits organized session playlists.

Output:
  playlists/got_rhythm_enclosures.ztplay     (enclosure-focused studies)
  playlists/got_rhythm_motion.ztplay         (melodic motion studies)
  playlists/got_rhythm_progressive.ztplay    (curriculum path)
  playlists/got_rhythm_all_4.ztplay          (master)

Does NOT regenerate existing .ztex or .ztprog files.
"""
import json
import os
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT, "got_rhythm_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

exercises = canon["exercises"]
ex_by_id = {ex["id"]: ex for ex in exercises}
groups = canon["playlist_groups"]


def yaml_str(s):
    if any(c in s for c in ':{}[]&*?|>!%@`#,'):
        return f'"{s}"'
    if s.startswith(("'", '"', "-", " ")):
        return f'"{s}"'
    return f'"{s}"'


def exercise_prog_path(ex):
    return f"exercises/got_rhythm/{ex['id']}.ztprog"


def build_item(ex, repeats=3):
    return {
        "name": ex["title"],
        "file": exercise_prog_path(ex),
        "repeats": repeats,
        "notes": ex.get("focus", ""),
    }


def emit_session_playlist(playlist_id, title, category, tags, defaults,
                          items, outdir):
    fname = f"{playlist_id}.ztplay"
    lines = [
        f"id: {playlist_id}",
        f"title: {yaml_str(title)}",
        f"category: {category}",
        f"tags: [{', '.join(yaml_str(t) for t in tags)}]",
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
        lines.append(f"    repeats: {item.get('repeats', 3)}")
        if item.get("notes"):
            lines.append(f"    notes: {yaml_str(item['notes'])}")
        lines.append("")

    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


def emit_technique_playlists(outdir):
    tech_meta = {
        "enclosures": {
            "title": "Got Rhythm: Enclosure Studies",
            "tags": ["got_rhythm", "bebop", "barry_harris", "enclosure"],
        },
        "melodic_motion": {
            "title": "Got Rhythm: Melodic Motion Studies",
            "tags": ["got_rhythm", "bebop", "barry_harris", "melodic_motion"],
        },
    }

    emitted = []
    for tech_key, ex_ids in groups["by_technique"].items():
        meta = tech_meta[tech_key]
        items = []
        for eid in ex_ids:
            ex = ex_by_id.get(eid)
            if ex:
                items.append(build_item(ex, repeats=3))
        if not items:
            continue

        pid = f"got_rhythm_{tech_key}"
        defaults = {"tempo": 120, "style": "swing"}
        fname = emit_session_playlist(pid, meta["title"], "technique_session",
                                      meta["tags"], defaults, items, outdir)
        emitted.append((fname, len(items)))

    return emitted


def emit_progressive_playlist(outdir):
    path_order = groups["progressive_path"]["order"]
    items = []
    for eid in path_order:
        ex = ex_by_id.get(eid)
        if ex:
            items.append(build_item(ex, repeats=3))
    if not items:
        return None

    pid = "got_rhythm_progressive"
    title = "Got Rhythm: Progressive Path (Studies 1–4)"
    tags = ["got_rhythm", "bebop", "barry_harris", "progressive", "curriculum"]
    defaults = {"tempo": 120, "style": "swing"}
    fname = emit_session_playlist(pid, title, "progressive_path",
                                  tags, defaults, items, outdir)
    return (fname, len(items))


def emit_master_playlist(outdir):
    sorted_exs = sorted(exercises, key=lambda e: e["study_number"])
    items = [build_item(ex, repeats=2) for ex in sorted_exs]

    pid = "got_rhythm_all_4"
    title = "Got Rhythm: Complete 4-Study Session"
    tags = ["got_rhythm", "bebop", "barry_harris", "complete"]
    defaults = {"tempo": 120, "style": "swing"}
    fname = emit_session_playlist(pid, title, "complete_session",
                                  tags, defaults, items, outdir)
    return (fname, len(items))


if __name__ == "__main__":
    play_dir = os.path.join(ROOT, "playlists")
    os.makedirs(play_dir, exist_ok=True)

    total = 0

    print("Technique session playlists:")
    tech_results = emit_technique_playlists(play_dir)
    for fname, count in tech_results:
        print(f"  {fname} ({count} items)")
        total += 1

    print("\nProgressive path playlist:")
    progressive = emit_progressive_playlist(play_dir)
    if progressive:
        print(f"  {progressive[0]} ({progressive[1]} items)")
        total += 1

    print("\nMaster playlist:")
    master = emit_master_playlist(play_dir)
    if master:
        print(f"  {master[0]} ({master[1]} items)")
        total += 1

    print(f"\nTotal playlists emitted: {total}")
    print(f"Output: {play_dir}/")
