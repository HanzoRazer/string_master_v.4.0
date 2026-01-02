"""
Lock Verification Test: Comprehensive stability check for zt-band core.

Verifies:
1. Contract enforcement (determinism + event validation)
2. Timing engine (beat→tick with deterministic rounding)
3. Expressive layer (velocity-only, preserves contract)
4. Output determinism (same inputs → same MIDI bytes)
"""

import filecmp
from pathlib import Path

import mido
from src.zt_band.engine import generate_accompaniment
from src.zt_band.musical_contract import ContractViolation, enforce_determinism_inputs


def test_contract_enforcement():
    """Verify contract catches violations."""
    print("Testing contract enforcement...")

    # Should raise: probabilistic without seed
    try:
        enforce_determinism_inputs(tritone_mode="probabilistic", tritone_seed=None)
        print("  ❌ FAILED: Should have raised ContractViolation")
        return False
    except ContractViolation:
        print("  ✅ Contract blocks probabilistic mode without seed")

    # Should pass: non-probabilistic without seed
    enforce_determinism_inputs(tritone_mode="none", tritone_seed=None)
    print("  ✅ Contract allows deterministic modes without seed")

    return True


def test_deterministic_output():
    """Verify same inputs produce identical MIDI files."""
    print("\nTesting deterministic output...")

    chords = ['Dm7', 'G7', 'Cmaj7', 'A7']

    # Generate twice with identical parameters
    for i in [1, 2]:
        generate_accompaniment(
            chords,
            style_name='swing_basic',
            tempo_bpm=140,
            bars_per_chord=2,
            tritone_mode='none',
            outfile=f'verify_det_{i}.mid'
        )

    # Compare byte-for-byte
    identical = filecmp.cmp('verify_det_1.mid', 'verify_det_2.mid', shallow=False)

    if identical:
        print("  ✅ Deterministic mode produces byte-identical output")
    else:
        print("  ❌ FAILED: Files differ despite identical inputs")

    return identical


def test_probabilistic_determinism():
    """Verify probabilistic mode with seed is deterministic."""
    print("\nTesting probabilistic determinism...")

    chords = ['Cmaj7', 'Am7', 'Dm7', 'G7']

    # Generate twice with same seed
    for i in [1, 2]:
        generate_accompaniment(
            chords,
            style_name='swing_basic',
            tempo_bpm=120,
            bars_per_chord=1,
            tritone_mode='probabilistic',
            tritone_seed=42,
            outfile=f'verify_prob_{i}.mid'
        )

    # Compare
    identical = filecmp.cmp('verify_prob_1.mid', 'verify_prob_2.mid', shallow=False)

    if identical:
        print("  ✅ Probabilistic mode with seed=42 is deterministic")
    else:
        print("  ❌ FAILED: Probabilistic output varies despite same seed")

    return identical


def test_timing_engine():
    """Verify timing engine produces valid MIDI structure."""
    print("\nTesting timing engine...")

    generate_accompaniment(
        ['Cmaj7'],
        style_name='swing_basic',
        tempo_bpm=120,
        bars_per_chord=4,
        tritone_mode='none',
        outfile='verify_timing.mid'
    )

    # Load and inspect
    mid = mido.MidiFile('verify_timing.mid')

    # Verify Type 1 (multiple tracks)
    if mid.type != 1:
        print(f"  ❌ FAILED: Expected Type 1, got Type {mid.type}")
        return False
    print(f"  ✅ MIDI Type 1 (multi-track): {len(mid.tracks)} tracks")

    # Verify ticks_per_beat
    if mid.ticks_per_beat != 480:
        print(f"  ❌ FAILED: Expected ticks_per_beat=480, got {mid.ticks_per_beat}")
        return False
    print(f"  ✅ Canonical ticks_per_beat: {mid.ticks_per_beat}")

    # Verify meta events at time 0
    tempo_track = mid.tracks[0]
    first_events = [msg for msg in tempo_track if msg.time == 0]
    meta_types = [msg.type for msg in first_events if msg.is_meta]

    if 'set_tempo' not in meta_types or 'time_signature' not in meta_types:
        print(f"  ❌ FAILED: Missing tempo/time_sig at t=0. Got: {meta_types}")
        return False
    print("  ✅ Meta events (tempo + time_signature) at time=0")

    # Verify no stuck notes (all note_on have corresponding note_off)
    for i, track in enumerate(mid.tracks):
        active_notes = set()
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                key = (msg.channel, msg.note)
                if key in active_notes:
                    print(f"  ❌ FAILED: Track {i} has overlapping note_on for {key}")
                    return False
                active_notes.add(key)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if key in active_notes:
                    active_notes.remove(key)

        if active_notes:
            print(f"  ❌ FAILED: Track {i} has stuck notes: {active_notes}")
            return False

    print("  ✅ No stuck notes (all note_on have note_off)")

    return True


def test_expressive_layer():
    """Verify expressive layer preserves contract."""
    print("\nTesting expressive layer...")

    # Generate with expressive layer
    comp, bass = generate_accompaniment(
        ['Dm7', 'G7'],
        style_name='swing_basic',
        tempo_bpm=120,
        bars_per_chord=2,
        tritone_mode='none',
    )

    # All events should have valid velocity (20-120 from default profile)
    all_events = list(comp) + list(bass)

    for e in all_events:
        if not (20 <= e.velocity <= 120):
            print(f"  ❌ FAILED: Velocity out of profile range: {e.velocity}")
            return False

    print(f"  ✅ All {len(all_events)} events have velocities in [20, 120]")

    # Check that downbeats were boosted (velocity varies)
    velocities = [e.velocity for e in all_events]
    if len(set(velocities)) < 2:
        print("  ❌ FAILED: No velocity variation (expressive layer not applied?)")
        return False

    print(f"  ✅ Velocity variation detected: {len(set(velocities))} unique values")

    return True


def cleanup():
    """Remove test MIDI files."""
    patterns = ['verify_*.mid', 'test_*.mid']
    for pattern in patterns:
        for f in Path('.').glob(pattern):
            try:
                f.unlink()
            except OSError:
                pass


def main():
    print("=" * 60)
    print("LOCK VERIFICATION TEST")
    print("=" * 60)

    results = []

    results.append(("Contract Enforcement", test_contract_enforcement()))
    results.append(("Deterministic Output", test_deterministic_output()))
    results.append(("Probabilistic Determinism", test_probabilistic_determinism()))
    results.append(("Timing Engine", test_timing_engine()))
    results.append(("Expressive Layer", test_expressive_layer()))

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print("=" * 60)
    if all_passed:
        print("✅ CORE IS LOCKED AND STABLE")
        print("\nYou can now truthfully say:")
        print('  "The MIDI generator core is locked and stable."')
        print('  "New ideas (swing/humanize) can be layered without changing core behavior."')
        print('  "Only stability improvements enter the core."')
    else:
        print("❌ LOCK VERIFICATION FAILED")
        print("One or more tests did not pass.")

    print("=" * 60)

    # Cleanup test files
    cleanup()

    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
