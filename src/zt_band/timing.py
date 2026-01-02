"""
Canonical MIDI writer with timing engine and contract enforcement.

Single source of truth for MIDI generation:
- Enforces meta events at time 0
- Prevents stuck notes
- Validates all events before writing
- Produces Type 1 MIDI files
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

from .contract import ContractViolation, MidiContract, NoteEvent, ProgramSpec, validate_events


def build_midi_type1(
    *,
    program: ProgramSpec,
    events: Iterable[NoteEvent],
    track_order: list[str] | None = None,
    contract: MidiContract = MidiContract(),
) -> MidiFile:
    """
    Single canonical MIDI writer. Everything funnels through this.
    """
    program.validate()
    ev = list(events)
    validate_events(ev)

    mid = MidiFile(type=1, ticks_per_beat=program.ticks_per_beat)

    # --- Meta track (tempo + time sig at time 0)
    meta = MidiTrack()
    meta.append(MetaMessage("track_name", name="Meta", time=0))
    if contract.require_tempo_at_zero:
        meta.append(MetaMessage("set_tempo", tempo=bpm2tempo(program.tempo_bpm), time=0))
    if contract.require_timesig_at_zero:
        meta.append(MetaMessage("time_signature", numerator=program.time_sig_num, denominator=program.time_sig_den, time=0))
    mid.tracks.append(meta)

    # --- Group events by track name
    by_track: dict[str, list[NoteEvent]] = defaultdict(list)
    for e in ev:
        by_track[e.track].append(e)

    names = track_order or sorted(by_track.keys())
    for name in names:
        tr = MidiTrack()
        if contract.require_track_names:
            tr.append(MetaMessage("track_name", name=name, time=0))

        # Convert NoteEvents to on/off messages, then delta-time encode
        msgs: list[tuple[int, Message]] = []
        for e in sorted(by_track.get(name, []), key=lambda x: (x.start_tick, x.note, x.channel)):
            on = Message("note_on", channel=e.channel, note=e.note, velocity=e.velocity, time=0)
            off = Message("note_off", channel=e.channel, note=e.note, velocity=0, time=0)
            msgs.append((e.start_tick, on))
            msgs.append((e.start_tick + e.dur_tick, off))

        _append_delta_encoded(tr, msgs)
        mid.tracks.append(tr)

    # Final enforcement pass (stuck notes + meta-at-zero)
    enforce_contract(mid, contract)
    return mid


def _append_delta_encoded(track: MidiTrack, timed_msgs: list[tuple[int, Message]]) -> None:
    timed_msgs.sort(key=lambda x: (x[0], 0 if x[1].type == "note_off" else 1))
    last_tick = 0
    for tick, msg in timed_msgs:
        dt = tick - last_tick
        if dt < 0:
            raise ContractViolation("negative delta-time encountered")
        msg.time = dt
        track.append(msg)
        last_tick = tick


def enforce_contract(mid: MidiFile, contract: MidiContract) -> None:
    if contract.require_type_1 and mid.type != 1:
        raise ContractViolation(f"MIDI must be type 1; got type={mid.type}")

    # Meta track must exist
    if not mid.tracks:
        raise ContractViolation("MIDI has no tracks")

    # Check tempo/timesig at time 0 on track 0
    if contract.require_tempo_at_zero or contract.require_timesig_at_zero:
        tempo_ok = not contract.require_tempo_at_zero
        ts_ok = not contract.require_timesig_at_zero
        t0 = mid.tracks[0]
        t_accum = 0
        for msg in t0:
            t_accum += getattr(msg, "time", 0)
            if t_accum != 0:
                break
            if isinstance(msg, MetaMessage) and msg.type == "set_tempo":
                tempo_ok = True
            if isinstance(msg, MetaMessage) and msg.type == "time_signature":
                ts_ok = True
        if not tempo_ok:
            raise ContractViolation("Missing tempo event at time 0 in meta track")
        if not ts_ok:
            raise ContractViolation("Missing time_signature event at time 0 in meta track")

    if contract.forbid_stuck_notes:
        _assert_no_stuck_notes(mid)


def _assert_no_stuck_notes(mid: MidiFile) -> None:
    """
    Scan delta-timed tracks and ensure note_on/note_off balance per (track, channel, note).
    """
    for ti, tr in enumerate(mid.tracks):
        active = defaultdict(int)  # (ch,note)->count
        for msg in tr:
            if not isinstance(msg, Message):
                continue
            if msg.type == "note_on" and msg.velocity > 0:
                active[(msg.channel, msg.note)] += 1
            elif msg.type in ("note_off", "note_on") and (msg.type == "note_off" or msg.velocity == 0):
                if active[(msg.channel, msg.note)] > 0:
                    active[(msg.channel, msg.note)] -= 1

        stuck = [(k, c) for k, c in active.items() if c != 0]
        if stuck:
            raise ContractViolation(f"Track {ti} has stuck notes: {stuck[:6]}{'...' if len(stuck) > 6 else ''}")
