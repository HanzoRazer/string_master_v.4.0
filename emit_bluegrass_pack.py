#!/usr/bin/env python3
"""
emit_bluegrass_pack.py

Reads bluegrass_canonical.json and emits organized session playlists.

Output:
  playlists/bluegrass_licks.ztplay              (G lick vocabulary)
  playlists/bluegrass_folk_melodies.ztplay       (folk melody etudes)
  playlists/bluegrass_fiddle_tunes.ztplay        (fiddle tune studies)
  playlists/bluegrass_intro_phrases.ztplay       (intro licks)
  playlists/bluegrass_waltz.ztplay               (3/4 exercises)
  playlists/bluegrass_progressive.ztplay         (curriculum path)
  playlists/bluegrass_all_14.ztplay              (master)

Does NOT regenerate existing .ztex or .ztprog files.
"""
import json
import os
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT, "bluegrass_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

exercises = canon["exercises"]
ex_by_id = {ex["id"]: ex for ex in exercises}
backing_tracks = {bt["id"]: bt for bt in canon["backing_tracks"]}
groups = canon["playlist_groups"]


def yaml_str(s):
    if any(c in s for c in ':{}[]&*?|>!%@`#,'):
        return f'"{s}"'
    if s.startswith(("'", '"', "-", " ")):
        return f'"{s}"'
    return f'"{s}"'


def exercise_prog_path(ex):
    bt_id = ex.get("backing_track")
    if bt_id and bt_id in backing_tracks:
        bt = backing_tracks[bt_id]
        # Lick progs use exercise id, etudes use backing id
        if ex["category"] == "licks":
            return f"exercises/bluegrass/{ex['id']}.ztprog"
        else:
            return f"exercises/bluegrass/{bt_id}.ztprog"
    return f"exercises/bluegrass/{ex['id']}.ztprog"


def build_item(ex, repeats=2):
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
        lines.append(f"    repeats: {item.get('repeats', 2)}")
        if item.get("notes"):
            lines.append(f"    notes: {yaml_str(item['notes'])}")
        lines.append("")

    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


def emit_category_playlists(outdir):
    cat_meta = {
        "licks": {
            "title": "Bluegrass: G Flatpicking Licks",
            "tags": ["bluegrass", "flatpicking", "licks", "G"],
            "tempo": 90,
        },
        "folk_melodies": {
            "title": "Bluegrass: Folk Melody Etudes",
            "tags": ["bluegrass", "traditional", "folk", "melody"],
            "tempo": 80,
        },
        "fiddle_tunes": {
            "title": "Bluegrass: Fiddle Tune Studies",
            "tags": ["bluegrass", "fiddle_tune", "flatpicking"],
            "tempo": 100,
        },
        "intro_phrases": {
            "title": "Bluegrass: Intro Phrases & Kick-Offs",
            "tags": ["bluegrass", "intro", "kick_off"],
            "tempo": 92,
        },
    }

    emitted = []
    for cat_key, ex_ids in groups["by_category"].items():
        meta = cat_meta[cat_key]
        items = []
        for eid in ex_ids:
            ex = ex_by_id.get(eid)
            if ex:
                items.append(build_item(ex, repeats=3 if cat_key == "licks" else 2))
        if not items:
            continue

        pid = f"bluegrass_{cat_key}"
        defaults = {"tempo": meta["tempo"], "style": "bluegrass"}
        fname = emit_session_playlist(pid, meta["title"], "category_session",
                                      meta["tags"], defaults, items, outdir)
        emitted.append((fname, len(items)))

    return emitted


def emit_waltz_playlist(outdir):
    waltz_exs = [ex for ex in exercises if ex["meter"] == "3/4"]
    if not waltz_exs:
        return None

    items = [build_item(ex, repeats=2) for ex in waltz_exs]
    pid = "bluegrass_waltz"
    title = "Bluegrass: Waltz Time (3/4) Studies"
    tags = ["bluegrass", "waltz", "3_4", "folk"]
    defaults = {"tempo": 76, "style": "waltz"}
    fname = emit_session_playlist(pid, title, "meter_session",
                                  tags, defaults, items, outdir)
    return (fname, len(items))


def emit_progressive_playlist(outdir):
    path_order = groups["progressive_path"]["order"]
    items = []
    for eid in path_order:
        ex = ex_by_id.get(eid)
        if ex:
            items.append(build_item(ex, repeats=2))
    if not items:
        return None

    pid = "bluegrass_progressive"
    title = "Bluegrass: Progressive Path (Licks to Performance)"
    tags = ["bluegrass", "progressive", "curriculum"]
    defaults = {"tempo": 90, "style": "bluegrass"}
    fname = emit_session_playlist(pid, title, "progressive_path",
                                  tags, defaults, items, outdir)
    return (fname, len(items))


def emit_master_playlist(outdir):
    cat_order = ["licks", "folk_melodies", "fiddle_tunes", "intro_phrases"]
    cat_rank = {c: i for i, c in enumerate(cat_order)}

    sorted_exs = sorted(exercises, key=lambda e: (
        cat_rank.get(e["category"], 99),
        e["id"],
    ))

    items = [build_item(ex, repeats=1) for ex in sorted_exs]

    pid = "bluegrass_all_14"
    title = "Bluegrass: Complete 14-Exercise Session"
    tags = ["bluegrass", "complete", "all_categories"]
    defaults = {"tempo": 90, "style": "bluegrass"}
    fname = emit_session_playlist(pid, title, "complete_session",
                                  tags, defaults, items, outdir)
    return (fname, len(items))


if __name__ == "__main__":
    play_dir = os.path.join(ROOT, "playlists")
    os.makedirs(play_dir, exist_ok=True)

    total = 0

    print("Category session playlists:")
    cat_results = emit_category_playlists(play_dir)
    for fname, count in cat_results:
        print(f"  {fname} ({count} items)")
        total += 1

    print("\nWaltz playlist:")
    waltz = emit_waltz_playlist(play_dir)
    if waltz:
        print(f"  {waltz[0]} ({waltz[1]} items)")
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
