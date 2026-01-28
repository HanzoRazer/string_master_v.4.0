#!/usr/bin/env python3
"""
emit_voicings_pack.py

Reads voicings_canonical.json and generates playlist YAML files for the
Chord Voicings & Drop-2 collection.

Output: playlists/voicing_*.ztplay  (2 playlists)
"""
import json
import os
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT, "voicings_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

exercises = {e["id"]: e for e in canon["exercises"]}
playlists = canon["playlists"]


def yaml_str(s):
    """Quote strings that YAML might misparse."""
    if s is None:
        return "null"
    s = str(s)
    if (s.startswith(("{", "[", "'", '"', "&", "*", "!", "|", ">", "%", "@", "`")) or
        ":" in s or
        s.lower() in ("true", "false", "yes", "no", "null", "on", "off") or
        s.replace("_", "").replace("-", "").replace(".", "").isdigit()):
        return f'"{s}"'
    return s


def emit_playlist(pl):
    """Generate a .ztplay file for a playlist definition (sessionPlaylist format)."""
    lines = [
        f"# Voicings -- {pl['title']}",
        f"# Auto-generated from voicings_canonical.json",
        "",
        f"id: {pl['id']}",
        f'title: "{pl["title"]}"',
        f"tags: [{', '.join(yaml_str(t) for t in pl['tags'])}]",
        "",
        "items:",
    ]

    for eid in pl["exercises"]:
        ex = exercises[eid]
        lines.append(f'  - name: "{ex["title"]}"')
        lines.append(f'    file: "{ex["program_ref"]}"')
        lines.append("")

    return "\n".join(lines)


def main():
    playlist_dir = os.path.join(ROOT, "playlists")
    os.makedirs(playlist_dir, exist_ok=True)

    count = 0
    for pl in playlists:
        content = emit_playlist(pl)
        fname = f"{pl['id']}.ztplay"
        outpath = os.path.join(playlist_dir, fname)
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {fname}")
        count += 1

    print(f"\nTotal playlists: {count}")
    print(f"Output: {playlist_dir}/")


if __name__ == "__main__":
    main()
