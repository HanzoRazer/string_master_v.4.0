#!/usr/bin/env python3
"""
MIDI Phrase Validator - validates note sequences against pedagogy rulesets.

Tests interval constraints and motion rules from pedagogy_ruleset JSON schemas.

Features:
- Track/channel separation for melody vs accompaniment analysis
- Octave-normalized intervals for pitch-class based rules
- Motion rules: stepwise, enclosure, tendency tone resolution, guide tones
- Configurable rules via JSON pedagogy schemas
- Chord detection mode (simultaneous notes grouped)
"""
import mido
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

# C major scale degree mapping (MIDI note -> scale degree)
# Octave-normalized: any C = 1, any D = 2, etc.
PITCH_CLASS_TO_DEGREE = {
    0: '1',   # C
    2: '2',   # D
    4: '3',   # E
    5: '4',   # F
    7: '5',   # G
    9: '6',   # A
    11: '7',  # B
}

# Chromatic pitch classes (for non-diatonic notes)
PITCH_CLASS_TO_CHROMATIC = {
    0: '1', 1: '#1/b2', 2: '2', 3: '#2/b3', 4: '3', 5: '4',
    6: '#4/b5', 7: '5', 8: '#5/b6', 9: '6', 10: '#6/b7', 11: '7'
}

# Degree string to semitone offset from root
DEGREE_TO_SEMITONE = {
    '1': 0, '2': 2, '3': 4, '4': 5, '5': 7, '6': 9, '7': 11,
    'b2': 1, '#1': 1, 'b3': 3, '#2': 3, 'b5': 6, '#4': 6,
    'b6': 8, '#5': 8, 'b7': 10, '#6': 10,
}

# Chord tones for common chord qualities (scale degrees)
CHORD_TONES = {
    'maj7': {'1', '3', '5', '7'},
    'dom7': {'1', '3', '5', 'b7', '#6/b7'},
    'min7': {'1', 'b3', '#2/b3', '5', 'b7', '#6/b7'},
    'm6': {'1', 'b3', '#2/b3', '5', '6'},
    'default': {'1', '3', '5', '7'},
}

# Guide tones (3rds and 7ths)
GUIDE_TONES = {'3', '7', 'b3', '#2/b3', 'b7', '#6/b7'}


@dataclass
class NoteEvent:
    """A note event with timing and pitch info."""
    midi_note: int
    pitch_class: int
    degree: str
    tick: int
    velocity: int
    channel: int = 0
    track: int = 0

    @property
    def octave(self) -> int:
        return self.midi_note // 12 - 1


@dataclass
class Violation:
    """A rule violation."""
    rule_type: str
    message: str
    notes: Tuple[NoteEvent, ...]
    severity: str = "error"  # error, warning


# ============================================================
# MIDI Extraction with Track/Channel Separation
# ============================================================

def extract_note_events(
    midi_path: str,
    channel_filter: Optional[int] = None,
    track_filter: Optional[int] = None,
    melody_mode: bool = False,
    chord_threshold_ticks: int = 10
) -> List[NoteEvent]:
    """
    Extract note-on events from a MIDI file.

    Args:
        midi_path: Path to MIDI file
        channel_filter: Only include notes from this channel (0-15)
        track_filter: Only include notes from this track index
        melody_mode: If True, extract only the highest note at each time point
        chord_threshold_ticks: Notes within this many ticks are considered simultaneous
    """
    mid = mido.MidiFile(midi_path)
    events = []

    for track_idx, track in enumerate(mid.tracks):
        if track_filter is not None and track_idx != track_filter:
            continue

        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                channel = getattr(msg, 'channel', 0)
                if channel_filter is not None and channel != channel_filter:
                    continue

                pc = msg.note % 12
                degree = PITCH_CLASS_TO_DEGREE.get(pc, PITCH_CLASS_TO_CHROMATIC.get(pc, '?'))
                events.append(NoteEvent(
                    midi_note=msg.note,
                    pitch_class=pc,
                    degree=degree,
                    tick=abs_tick,
                    velocity=msg.velocity,
                    channel=channel,
                    track=track_idx
                ))

    # Sort by tick, then by pitch (for melody extraction)
    events.sort(key=lambda e: (e.tick, -e.midi_note))

    if melody_mode:
        events = _extract_melody_line(events, chord_threshold_ticks)

    return events


def _extract_melody_line(events: List[NoteEvent], threshold: int = 10) -> List[NoteEvent]:
    """Extract melody (highest note at each time point) from chord voicings."""
    if not events:
        return []

    melody = []
    i = 0
    while i < len(events):
        # Group notes that are simultaneous (within threshold)
        group = [events[i]]
        j = i + 1
        while j < len(events) and events[j].tick - events[i].tick <= threshold:
            group.append(events[j])
            j += 1

        # Take highest note in group (already sorted by -midi_note)
        melody.append(group[0])
        i = j

    return melody


def extract_by_register(events: List[NoteEvent], register: str = 'high') -> List[NoteEvent]:
    """
    Split events into register bands and return one.

    Registers:
        'high': notes >= 60 (middle C and above)
        'mid': notes 48-71
        'low': notes < 60 (below middle C)
        'bass': notes < 48
    """
    if register == 'high':
        return [e for e in events if e.midi_note >= 60]
    elif register == 'mid':
        return [e for e in events if 48 <= e.midi_note < 72]
    elif register == 'low':
        return [e for e in events if e.midi_note < 60]
    elif register == 'bass':
        return [e for e in events if e.midi_note < 48]
    return events


# ============================================================
# Interval Helpers
# ============================================================

def interval_semitones(note_a: NoteEvent, note_b: NoteEvent) -> int:
    """Calculate interval in semitones (signed)."""
    return note_b.midi_note - note_a.midi_note


def interval_pitch_class(note_a: NoteEvent, note_b: NoteEvent) -> int:
    """Calculate pitch class interval (0-11, octave-normalized)."""
    return (note_b.pitch_class - note_a.pitch_class) % 12


def interval_abs(note_a: NoteEvent, note_b: NoteEvent) -> int:
    """Calculate absolute interval in semitones."""
    return abs(note_b.midi_note - note_a.midi_note)


def is_step(interval: int) -> bool:
    """Is this interval a step (1 or 2 semitones)?"""
    return abs(interval) <= 2


def is_skip(interval: int) -> bool:
    """Is this interval a skip (3-4 semitones)?"""
    return 3 <= abs(interval) <= 4


def is_leap(interval: int) -> bool:
    """Is this interval a leap (5+ semitones)?"""
    return abs(interval) >= 5


def is_octave_leap(interval: int) -> bool:
    """Is this an octave or larger jump (voice leading between chord voicings)?"""
    return abs(interval) >= 12


# ============================================================
# Interval Rule Validators
# ============================================================

def check_interval_rules(
    events: List[NoteEvent],
    rules: List[Dict],
    use_pitch_class: bool = False
) -> List[Violation]:
    """
    Check interval rules against note sequence.

    Args:
        use_pitch_class: If True, use octave-normalized intervals (mod 12)
    """
    violations = []

    for i in range(len(events) - 1):
        a, b = events[i], events[i + 1]

        # Skip octave leaps (chord voicing jumps, not melodic motion)
        raw_interval = interval_semitones(a, b)
        if is_octave_leap(raw_interval):
            continue

        if use_pitch_class:
            interval = interval_pitch_class(a, b)
            abs_interval = min(interval, 12 - interval)  # Shortest path
        else:
            interval = raw_interval
            abs_interval = abs(interval)

        for rule in rules:
            applies_to = rule.get('applies_to', {})
            group = applies_to.get('group', 'mixed')
            from_deg = applies_to.get('from_degree')
            to_deg = applies_to.get('to_degree')

            # Check if rule applies to this note pair
            if from_deg and to_deg:
                # Specific degree pair rule
                if a.degree != from_deg or b.degree != to_deg:
                    continue
            elif group == 'non_chord_tones':
                # Only apply to non-chord tones (chromatic notes)
                if '/' not in a.degree and '/' not in b.degree:
                    continue

            rule_type = rule.get('rule_type', '')
            value = rule.get('value', 0)
            note = rule.get('note', '')

            if rule_type == 'exact_semitones_between':
                if abs_interval != value:
                    violations.append(Violation(
                        rule_type=rule_type,
                        message=f"{a.degree}->{b.degree}: expected {value} semitones, got {abs_interval}. {note}",
                        notes=(a, b),
                        severity="error"
                    ))

            elif rule_type == 'avoid_semitones_between':
                if abs_interval == value:
                    violations.append(Violation(
                        rule_type=rule_type,
                        message=f"{a.degree}->{b.degree}: avoid {value} semitone interval. {note}",
                        notes=(a, b),
                        severity="warning"
                    ))

            elif rule_type == 'min_semitones_between':
                if abs_interval < value:
                    violations.append(Violation(
                        rule_type=rule_type,
                        message=f"{a.degree}->{b.degree}: minimum {value} semitones, got {abs_interval}. {note}",
                        notes=(a, b),
                        severity="error"
                    ))

            elif rule_type == 'max_semitones_between':
                if abs_interval > value:
                    violations.append(Violation(
                        rule_type=rule_type,
                        message=f"{a.degree}->{b.degree}: maximum {value} semitones, got {abs_interval}. {note}",
                        notes=(a, b),
                        severity="warning"
                    ))

            elif rule_type == 'prefer_semitones_between':
                if abs_interval != value:
                    violations.append(Violation(
                        rule_type=rule_type,
                        message=f"{a.degree}->{b.degree}: prefer {value} semitones, got {abs_interval}. {note}",
                        notes=(a, b),
                        severity="warning"
                    ))

    return violations


# ============================================================
# Motion Rule Validators
# ============================================================

def check_motion_rules(events: List[NoteEvent], rules: List[Dict]) -> List[Violation]:
    """Check motion rules against note sequence."""
    violations = []

    for rule in rules:
        rule_name = rule.get('name', 'unnamed')
        rule_type = rule.get('rule', '')
        scope = rule.get('scope', 'global')
        note = rule.get('note', '')

        if rule_type == 'stepwise_only':
            violations.extend(_check_stepwise_only(events, rule_name, note))

        elif rule_type == 'enclosure_allowed':
            # Enclosures detected in stepwise check - no extra validation needed
            pass

        elif rule_type == 'resolve_tendency_tones':
            violations.extend(_check_tendency_tone_resolution(events, rule_name, note))

        elif rule_type == 'approach_chord_tones_by_half_step':
            violations.extend(_check_half_step_approach(events, rule_name, note))

        elif rule_type == 'target_guide_tones_on_strong_beats':
            violations.extend(_check_guide_tones_on_strong_beats(events, rule_name, note))

    return violations


def _check_stepwise_only(events: List[NoteEvent], rule_name: str, note: str) -> List[Violation]:
    """Check that motion is stepwise (no leaps without enclosure)."""
    violations = []

    for i in range(len(events) - 1):
        a, b = events[i], events[i + 1]
        interval = interval_semitones(a, b)

        # Skip octave leaps (chord voicing, not melodic)
        if is_octave_leap(interval):
            continue

        if is_leap(interval):
            # Check if this could be an enclosure (look ahead)
            is_enclosure = False
            if i + 2 < len(events):
                c = events[i + 2]
                # Enclosure: leap up then step down (or vice versa)
                int_bc = interval_semitones(b, c)
                if not is_octave_leap(int_bc):
                    if (interval > 0 and int_bc < 0 and is_step(int_bc)) or \
                       (interval < 0 and int_bc > 0 and is_step(int_bc)):
                        is_enclosure = True

            # Also allow approach patterns (skip to chord tone)
            is_approach = b.degree in CHORD_TONES['default']

            if not is_enclosure and not is_approach:
                violations.append(Violation(
                    rule_type='stepwise_only',
                    message=f"Leap of {abs(interval)} semitones ({a.degree}->{b.degree}) without enclosure. {note}",
                    notes=(a, b),
                    severity="warning"
                ))

    return violations


def _check_tendency_tone_resolution(events: List[NoteEvent], rule_name: str, note: str) -> List[Violation]:
    """Check that tendency tones resolve correctly (7->1, 4->3)."""
    violations = []

    for i in range(len(events) - 1):
        a, b = events[i], events[i + 1]
        interval = interval_semitones(a, b)

        # Skip octave leaps
        if is_octave_leap(interval):
            continue

        # Use pitch class for resolution check
        pc_interval = interval_pitch_class(a, b)

        # 7 should resolve to 1 (half step up = pc interval 1)
        if a.degree == '7':
            if pc_interval != 1 and b.degree != '1':
                violations.append(Violation(
                    rule_type='resolve_tendency_tones',
                    message=f"Degree 7 should resolve to 1 (half step up), got {a.degree}->{b.degree}. {note}",
                    notes=(a, b),
                    severity="warning"
                ))

        # 4 should resolve to 3 (half step down = pc interval 11)
        if a.degree == '4':
            if pc_interval != 11 and b.degree != '3':
                violations.append(Violation(
                    rule_type='resolve_tendency_tones',
                    message=f"Degree 4 should resolve to 3 (half step down), got {a.degree}->{b.degree}. {note}",
                    notes=(a, b),
                    severity="warning"
                ))

    return violations


def _check_half_step_approach(events: List[NoteEvent], rule_name: str, note: str) -> List[Violation]:
    """Check that chord tones are approached by half step."""
    violations = []
    chord_tones = CHORD_TONES['default']

    for i in range(1, len(events)):
        a, b = events[i - 1], events[i]

        # Skip octave leaps
        interval = interval_semitones(a, b)
        if is_octave_leap(interval):
            continue

        # If b is a chord tone and a is not
        if b.degree in chord_tones and a.degree not in chord_tones:
            abs_int = abs(interval)
            if abs_int != 1 and abs_int != 2:  # Allow whole step approach too
                violations.append(Violation(
                    rule_type='approach_chord_tones_by_half_step',
                    message=f"Chord tone {b.degree} approached by {abs_int} semitones from {a.degree}, prefer step. {note}",
                    notes=(a, b),
                    severity="warning"
                ))

    return violations


def _check_guide_tones_on_strong_beats(
    events: List[NoteEvent],
    rule_name: str,
    note: str,
    ppq: int = 480
) -> List[Violation]:
    """
    Check that guide tones (3rds and 7ths) fall on strong beats.

    Strong beats in 4/4: beats 1 and 3 (ticks 0, ppq*2 within each bar)
    """
    violations = []
    bar_ticks = ppq * 4  # 4/4 time

    for e in events:
        if e.degree in GUIDE_TONES:
            beat_in_bar = (e.tick % bar_ticks) // ppq
            is_strong = beat_in_bar in (0, 2)  # Beats 1 and 3

            if not is_strong:
                violations.append(Violation(
                    rule_type='target_guide_tones_on_strong_beats',
                    message=f"Guide tone {e.degree} on weak beat {beat_in_bar + 1}. {note}",
                    notes=(e,),
                    severity="warning"
                ))

    return violations


# ============================================================
# Main Validation
# ============================================================

def validate_phrase(
    midi_path: str,
    interval_rules: Optional[List[Dict]] = None,
    motion_rules: Optional[List[Dict]] = None,
    melody_mode: bool = False,
    use_pitch_class: bool = False
) -> Tuple[bool, List[Violation]]:
    """
    Validate a MIDI phrase against interval and motion rules.

    Args:
        melody_mode: Extract melody line only (highest note at each time)
        use_pitch_class: Use octave-normalized intervals

    Returns (passed, violations) where passed is True if no errors.
    """
    events = extract_note_events(midi_path, melody_mode=melody_mode)

    if not events:
        return True, []

    violations = []

    if interval_rules:
        violations.extend(check_interval_rules(events, interval_rules, use_pitch_class))

    if motion_rules:
        violations.extend(check_motion_rules(events, motion_rules))

    # Passed if no errors (warnings ok)
    errors = [v for v in violations if v.severity == "error"]
    return len(errors) == 0, violations


def analyze_phrase_stats(midi_path: str, melody_mode: bool = False) -> Dict:
    """Get statistics about a MIDI phrase."""
    events = extract_note_events(midi_path, melody_mode=melody_mode)

    if not events:
        return {"note_count": 0}

    # Filter out octave leaps for interval stats
    intervals = []
    melodic_intervals = []
    for i in range(len(events) - 1):
        raw = interval_semitones(events[i], events[i + 1])
        intervals.append(raw)
        if not is_octave_leap(raw):
            melodic_intervals.append(raw)

    degree_counts = {}
    for e in events:
        degree_counts[e.degree] = degree_counts.get(e.degree, 0) + 1

    steps = sum(1 for i in melodic_intervals if is_step(i))
    skips = sum(1 for i in melodic_intervals if is_skip(i))
    leaps = sum(1 for i in melodic_intervals if is_leap(i) and not is_octave_leap(i))
    octave_jumps = sum(1 for i in intervals if is_octave_leap(i))

    total_melodic = len(melodic_intervals) if melodic_intervals else 1

    # Track/channel distribution
    tracks = set(e.track for e in events)
    channels = set(e.channel for e in events)

    return {
        "note_count": len(events),
        "interval_count": len(intervals),
        "melodic_intervals": len(melodic_intervals),
        "octave_jumps": octave_jumps,
        "steps": steps,
        "skips": skips,
        "leaps": leaps,
        "step_ratio": steps / total_melodic,
        "degree_distribution": degree_counts,
        "pitch_range": max(e.midi_note for e in events) - min(e.midi_note for e in events),
        "lowest_note": min(e.midi_note for e in events),
        "highest_note": max(e.midi_note for e in events),
        "tracks": list(tracks),
        "channels": list(channels),
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    import json

    # Default rules for testing (bebop line rules)
    DEFAULT_INTERVAL_RULES = [
        {
            "applies_to": {"group": "custom", "from_degree": "7", "to_degree": "1"},
            "rule_type": "prefer_semitones_between",
            "value": 1,
            "note": "Leading tone resolution"
        },
        {
            "applies_to": {"group": "non_chord_tones"},
            "rule_type": "avoid_semitones_between",
            "value": 6,
            "note": "Avoid tritone between non-chord tones"
        },
    ]

    DEFAULT_MOTION_RULES = [
        {"name": "stepwise_preferred", "rule": "stepwise_only", "scope": "global", "note": "Bebop lines should be stepwise"},
        {"name": "tendency_resolution", "rule": "resolve_tendency_tones", "scope": "global", "note": "7->1, 4->3"},
        {"name": "half_step_approach", "rule": "approach_chord_tones_by_half_step", "scope": "global", "note": "Approach chord tones by step"},
    ]

    def print_usage():
        print("Usage: python phrase_validate.py <midi_file> [options]")
        print("\nOptions:")
        print("  --stats           Show phrase statistics")
        print("  --melody          Extract melody line only (highest note at each time)")
        print("  --pitch-class     Use octave-normalized intervals (mod 12)")
        print("  --rules <json>    Load rules from pedagogy JSON file")
        print("  --guide-tones     Check guide tones on strong beats")
        print("\nRuns phrase validation on MIDI file with default bebop rules.")

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    midi_file = sys.argv[1]
    show_stats = "--stats" in sys.argv
    melody_mode = "--melody" in sys.argv
    use_pitch_class = "--pitch-class" in sys.argv
    check_guide = "--guide-tones" in sys.argv

    # Check for custom rules file
    rules_file = None
    if "--rules" in sys.argv:
        idx = sys.argv.index("--rules")
        if idx + 1 < len(sys.argv):
            rules_file = sys.argv[idx + 1]

    interval_rules = DEFAULT_INTERVAL_RULES
    motion_rules = list(DEFAULT_MOTION_RULES)

    if check_guide:
        motion_rules.append({
            "name": "guide_tone_placement",
            "rule": "target_guide_tones_on_strong_beats",
            "scope": "global",
            "note": "Guide tones on strong beats"
        })

    if rules_file:
        with open(rules_file, 'r') as f:
            ruleset = json.load(f)
            constraints = ruleset.get('constraints', {})
            interval_rules = constraints.get('interval_rules', DEFAULT_INTERVAL_RULES)
            motion_rules = constraints.get('motion_rules', DEFAULT_MOTION_RULES)

    print(f"\n=== Phrase Validation: {midi_file} ===")
    mode_flags = []
    if melody_mode:
        mode_flags.append("melody")
    if use_pitch_class:
        mode_flags.append("pitch-class")
    if mode_flags:
        print(f"Mode: {', '.join(mode_flags)}")
    print()

    if show_stats:
        stats = analyze_phrase_stats(midi_file, melody_mode=melody_mode)
        print("Statistics:")
        print(f"  Notes: {stats['note_count']}")
        print(f"  Tracks: {stats['tracks']}, Channels: {stats['channels']}")
        print(f"  Pitch range: {stats['pitch_range']} semitones (MIDI {stats['lowest_note']}-{stats['highest_note']})")
        print(f"  Intervals: {stats['interval_count']} total, {stats['melodic_intervals']} melodic, {stats['octave_jumps']} octave jumps")
        print(f"  Motion: {stats['steps']} steps, {stats['skips']} skips, {stats['leaps']} leaps")
        print(f"  Step ratio: {stats['step_ratio']:.1%}")
        print(f"  Degrees: {stats['degree_distribution']}")
        print()

    passed, violations = validate_phrase(
        midi_file,
        interval_rules,
        motion_rules,
        melody_mode=melody_mode,
        use_pitch_class=use_pitch_class
    )

    if not violations:
        print("PASS - No violations found")
    else:
        errors = [v for v in violations if v.severity == "error"]
        warnings = [v for v in violations if v.severity == "warning"]

        print(f"{'PASS' if passed else 'FAIL'} - {len(errors)} errors, {len(warnings)} warnings\n")

        if errors:
            print("ERRORS:")
            for v in errors[:20]:  # Limit output
                print(f"  [{v.rule_type}] {v.message}")
            if len(errors) > 20:
                print(f"  ... and {len(errors) - 20} more errors")

        if warnings:
            print("\nWARNINGS:")
            for v in warnings[:20]:  # Limit output
                print(f"  [{v.rule_type}] {v.message}")
            if len(warnings) > 20:
                print(f"  ... and {len(warnings) - 20} more warnings")

    sys.exit(0 if passed else 1)
