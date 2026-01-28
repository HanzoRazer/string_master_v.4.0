#!/usr/bin/env python3
"""
emit_flamenco_pack.py

Reads flamenco_canonical.json and emits organized session playlists.

Output:
  playlists/flamenco_{palo}.ztplay          (8 palo session playlists)
  playlists/flamenco_foundations.ztplay      (1 cross-palo foundations playlist)
  playlists/flamenco_mode_{mode}.ztplay      (3 mode playlists)
  playlists/flamenco_compas_{type}.ztplay    (4 compas family playlists)
  playlists/flamenco_progressive.ztplay      (1 progressive path playlist)
  playlists/flamenco_all_20.ztplay           (1 master playlist)

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
with open(os.path.join(ROOT, "flamenco_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

exercises = canon["exercises"]
backing_tracks = canon["backing_tracks"]
palo_tax = canon["palo_taxonomy"]


# ── Helpers ──

def yaml_str(s):
    """Quote a string for YAML output if needed."""
    if any(c in s for c in ':{}[]&*?|>!%@`#,'):
        return f'"{s}"'
    if s.startswith(("'", '"', "-", " ")):
        return f'"{s}"'
    return f'"{s}"'


def backing_path(ex):
    """Return playlist-relative path to the backing .ztprog for an exercise."""
    bt = ex.get("backing_track")
    if bt is None:
        return None
    # Handle relative paths that start with ../
    if bt.startswith("../"):
        return bt[3:]  # ../programs/x.ztprog -> programs/x.ztprog
    return f"exercises/flamenco/{bt}"


def get_backing_track_info(bt_id):
    """Look up backing track metadata by id."""
    for bt in backing_tracks:
        if bt["id"] == bt_id:
            return bt
    return None


def default_tempo_for_palo(palo):
    """Return a sensible default tempo for a palo."""
    if palo in palo_tax:
        tr = palo_tax[palo].get("tempo_range", [80, 120])
        # Use lower-middle range
        return tr[0] + (tr[1] - tr[0]) // 3
    return 80


def palo_tags(palo):
    """Return tag list for a palo."""
    tags = ["flamenco", palo]
    if palo in palo_tax:
        mode = palo_tax[palo].get("default_mode", "phrygian")
        tags.append(mode)
    return tags


# ── Emitters ──

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


def build_item(ex, repeats=2):
    """Build a playlist item dict from an exercise."""
    bp = backing_path(ex)
    if bp is None:
        # Skip exercises without a playable backing track
        return None
    return {
        "name": ex["title"],
        "file": bp,
        "repeats": repeats,
        "notes": ex.get("focus", ""),
    }


# ── Palo Playlists (one per palo) ──

def emit_palo_playlists(outdir):
    """Emit one session playlist per palo."""
    palos = {}
    for ex in exercises:
        palo = ex["palo"]
        palos.setdefault(palo, []).append(ex)

    emitted = []
    for palo in sorted(palos):
        if palo == "cross_palo":
            continue  # handled separately
        exs = palos[palo]
        # Order: theory (melodic_study) first, then groove (falseta)
        exs.sort(key=lambda e: (0 if e["generation"] == "theory" else 1, e["id"]))

        items = []
        for ex in exs:
            item = build_item(ex)
            if item:
                items.append(item)

        if not items:
            continue

        pid = f"flamenco_{palo}"
        palo_label = palo.replace("_", " ").title()
        title = f"Flamenco: {palo_label} Session"
        tags = palo_tags(palo)
        tempo = default_tempo_for_palo(palo)
        ts = palo_tax.get(palo, {}).get("time_signature", "4/4")
        defaults = {"tempo": tempo, "style": "flamenco"}

        fname = emit_session_playlist(pid, title, "palo_session", tags,
                                      defaults, items, outdir)
        emitted.append((fname, len(items)))

    return emitted


# ── Foundations Playlist (cross-palo exercises) ──

def emit_foundations_playlist(outdir):
    """Emit a foundations playlist for andalusian cadence studies."""
    cross = [ex for ex in exercises if ex["palo"] == "cross_palo"]
    items = []
    for ex in cross:
        item = build_item(ex, repeats=3)
        if item:
            items.append(item)

    if not items:
        return None

    pid = "flamenco_foundations"
    title = "Flamenco: Andalusian Cadence Foundations"
    tags = ["flamenco", "andalusian", "cadence", "phrygian"]
    defaults = {"tempo": 90, "style": "flamenco"}

    fname = emit_session_playlist(pid, title, "foundations", tags,
                                  defaults, items, outdir)
    return (fname, len(items))


# ── Mode Playlists ──

def emit_mode_playlists(outdir):
    """Emit one session playlist per Phrygian mode variant."""
    mode_map = {
        "phrygian": [],
        "phrygian_dominant": [],
        "phrygian_dominant_mixed": [],
        "phrygian_mixed": [],  # malaguena
    }
    for ex in exercises:
        mode = ex["mode"]
        mode_map.setdefault(mode, []).append(ex)

    # Merge phrygian_mixed into phrygian_dominant_mixed (same concept)
    mode_map.setdefault("phrygian_dominant_mixed", []).extend(
        mode_map.pop("phrygian_mixed", [])
    )

    emitted = []
    mode_labels = {
        "phrygian": "Natural Phrygian (Dark, Solemn)",
        "phrygian_dominant": "Phrygian Dominant (Bright, Exotic)",
        "phrygian_dominant_mixed": "Modal Mixing (G/G# Contrast)",
    }

    for mode, exs in sorted(mode_map.items()):
        if not exs:
            continue
        exs.sort(key=lambda e: (e["palo"], e["id"]))

        items = []
        for ex in exs:
            item = build_item(ex)
            if item:
                items.append(item)

        if not items:
            continue

        slug = mode.replace("_mixed", "_mixed")
        pid = f"flamenco_mode_{slug}"
        label = mode_labels.get(mode, mode.replace("_", " ").title())
        title = f"Flamenco: {label}"
        tags = ["flamenco", mode, "modal_study"]
        defaults = {"tempo": 80, "style": "flamenco"}

        fname = emit_session_playlist(pid, title, "mode_session", tags,
                                      defaults, items, outdir)
        emitted.append((fname, len(items)))

    return emitted


# ── Compas Family Playlists ──

def emit_compas_playlists(outdir):
    """Emit one session playlist per compas family."""
    compas_groups = {
        "12_beat": {"label": "12-Beat Compas (Solea/Bulerias)", "palos": {"solea", "bulerias"}},
        "binary_4_4": {"label": "Binary 4/4 (Tangos/Tientos/Rumba/Zambra)",
                       "palos": {"tangos", "tientos", "rumba", "zambra"}},
        "ternary_3_4": {"label": "Ternary 3/4 (Fandango)", "palos": {"fandango"}},
        "free": {"label": "Free Meter (Malaguena)", "palos": {"malaguena"}},
    }

    emitted = []
    for group_key, info in compas_groups.items():
        exs = [ex for ex in exercises if ex["palo"] in info["palos"]]
        exs.sort(key=lambda e: (e["palo"], e["id"]))

        items = []
        for ex in exs:
            item = build_item(ex)
            if item:
                items.append(item)

        if not items:
            continue

        pid = f"flamenco_compas_{group_key}"
        title = f"Flamenco: {info['label']}"
        tags = ["flamenco", group_key, "compas_study"]
        defaults = {"tempo": 80, "style": "flamenco"}

        fname = emit_session_playlist(pid, title, "compas_session", tags,
                                      defaults, items, outdir)
        emitted.append((fname, len(items)))

    return emitted


# ── Progressive Path Playlist ──

def emit_progressive_playlist(outdir):
    """Emit a progressive difficulty path playlist."""
    path_order = canon["playlist_groups"]["progressive_path"]["order"]
    ex_by_id = {ex["id"]: ex for ex in exercises}

    items = []
    for eid in path_order:
        ex = ex_by_id.get(eid)
        if ex is None:
            continue
        item = build_item(ex, repeats=3)
        if item:
            items.append(item)

    if not items:
        return None

    pid = "flamenco_progressive"
    title = "Flamenco: Progressive Path (Foundations to Advanced)"
    tags = ["flamenco", "progressive", "curriculum"]
    defaults = {"tempo": 80, "style": "flamenco"}

    fname = emit_session_playlist(pid, title, "progressive_path", tags,
                                  defaults, items, outdir)
    return (fname, len(items))


# ── Master Playlist ──

def emit_master_playlist(outdir):
    """Emit a master playlist with all 20 exercises."""
    # Order: cross_palo first, then by palo family
    palo_order = ["cross_palo", "solea", "bulerias", "tangos", "tientos",
                  "rumba", "fandango", "malaguena", "zambra"]
    palo_rank = {p: i for i, p in enumerate(palo_order)}

    sorted_exs = sorted(exercises, key=lambda e: (
        palo_rank.get(e["palo"], 99),
        0 if e["generation"] == "theory" else 1,
        e["id"],
    ))

    items = []
    for ex in sorted_exs:
        item = build_item(ex, repeats=1)
        if item:
            items.append(item)

    pid = "flamenco_all_20"
    title = "Flamenco: Complete 20-Exercise Session"
    tags = ["flamenco", "complete", "all_palos"]
    defaults = {"tempo": 80, "style": "flamenco"}

    fname = emit_session_playlist(pid, title, "complete_session", tags,
                                  defaults, items, outdir)
    return (fname, len(items))


# ── Main ──

if __name__ == "__main__":
    play_dir = os.path.join(ROOT, "playlists")
    os.makedirs(play_dir, exist_ok=True)

    total = 0

    # 1. Palo session playlists
    print("Palo session playlists:")
    palo_results = emit_palo_playlists(play_dir)
    for fname, count in palo_results:
        print(f"  {fname} ({count} items)")
        total += 1

    # 2. Foundations playlist
    print("\nFoundations playlist:")
    foundations = emit_foundations_playlist(play_dir)
    if foundations:
        print(f"  {foundations[0]} ({foundations[1]} items)")
        total += 1

    # 3. Mode playlists
    print("\nMode session playlists:")
    mode_results = emit_mode_playlists(play_dir)
    for fname, count in mode_results:
        print(f"  {fname} ({count} items)")
        total += 1

    # 4. Compas family playlists
    print("\nCompas family playlists:")
    compas_results = emit_compas_playlists(play_dir)
    for fname, count in compas_results:
        print(f"  {fname} ({count} items)")
        total += 1

    # 5. Progressive path playlist
    print("\nProgressive path playlist:")
    progressive = emit_progressive_playlist(play_dir)
    if progressive:
        print(f"  {progressive[0]} ({progressive[1]} items)")
        total += 1

    # 6. Master playlist
    print("\nMaster playlist:")
    master = emit_master_playlist(play_dir)
    if master:
        print(f"  {master[0]} ({master[1]} items)")
        total += 1

    print(f"\nTotal playlists emitted: {total}")
    print(f"Output: {play_dir}/")
