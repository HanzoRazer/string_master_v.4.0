"""
Real-time MIDI scheduler and practice quantizer.

Provides:
- rt_play_cycle: Real-time playback aligned to clave grid
- practice_lock_to_clave: MIDI IN quantized/locked to clave grid -> MIDI OUT
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, Literal

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

from .senders import create_sender

from .clave import ClaveGrid, clave_hit_steps, is_allowed_on_clave, quantize_step


@dataclass(frozen=True)
class RtSpec:
    midi_out: str
    midi_in: str | None = None

    bpm: float = 120.0
    grid: Literal[8, 16] = 16
    clave: Literal["son_2_3", "son_3_2"] = "son_2_3"

    # Scheduler behavior
    lookahead_s: float = 0.05    # how far ahead to schedule
    tick_s: float = 0.01         # loop sleep

    # Practice behavior
    practice_strict: bool = True
    practice_window_ms: float = 0.0  # tolerance window (ms) around nearest clave hit
    practice_window_on_ms: float | None = None  # override for NOTE-ON only
    practice_window_off_ms: float | None = None  # override for NOTE-OFF (defaults loose)
    practice_quantize: Literal["nearest", "down", "up"] = "nearest"
    practice_reject_offgrid: bool = False  # if True, drop notes not on allowed steps (strict mode)

    # Click
    click: bool = True
    click_note: int = 37  # rimshot-ish
    click_vel: int = 40
    click_channel: int = 9  # GM drums

    # Telemetry (bar boundary CC)
    bar_cc_enabled: bool = False
    bar_cc_channel: int = 15  # 0-15 (default 16th MIDI channel)
    bar_cc_countdown: int = 20  # CC number for bars-remaining countdown
    bar_cc_index: int = 21  # CC number for bar index count-up
    bar_cc_section: int = 22  # CC number for section/item marker
    bars_limit: int | None = None  # total bars for countdown calculation

    # Performance controls (E2E wiring)
    velocity_mul: float = 1.0  # Note-on velocity scaling from arranger


def _now() -> float:
    return time.monotonic()


@dataclass(frozen=True)
class LateDropPolicy:
    """
    Late-event handling policy for realtime playback.

    Design goals:
      - never destabilize core timing/contract
      - preserve telemetry and core musical hits
      - drop ornaments first (click + low-velocity ghost note-ons)
      - never drop note_off (prevents stuck notes)
    """
    enabled: bool = True
    late_drop_ms: int = 35
    ghost_note_on_max_vel: int = 22  # <= this velocity is treated as "ornament"

    def late_drop_s(self) -> float:
        return max(0, self.late_drop_ms) / 1000.0

    def is_ornament(self, msg: mido.Message) -> bool:
        """
        Returns True if this MIDI message is considered expendable
        (ornament/ghost) and can be dropped when late.
        """
        if msg.type != "note_on":
            return False
        # velocity-based ornament classification
        # structural notes (comp/bass) must survive late scheduling
        try:
            vel = int(msg.velocity)
        except Exception:
            return False
        # note_on with vel=0 is actually note-off -- never drop
        if vel == 0:
            return False
        return vel <= self.ghost_note_on_max_vel

    def should_drop(self, *, due_s: float, now_s: float, msg: mido.Message) -> bool:
        """
        Returns True if this message should be dropped due to lateness.
        Only ornaments are dropped; structural notes always survive.
        """
        if not self.enabled:
            return False

        lateness_ms = (now_s - due_s) * 1000.0
        if lateness_ms <= self.late_drop_ms:
            return False
        # only drop if expendable ornament
        return self.is_ornament(msg)


def _panic_cleanup(sender, *, channels: Iterable[int] = range(16)) -> None:
    """
    Belt-and-suspenders: send a minimal 'panic' sequence to prevent stuck notes
    when rt-play exits (Ctrl+C, exceptions, etc).
    """
    for ch in channels:
        # All Sound Off (120), Reset All Controllers (121), All Notes Off (123)
        try:
            sender.send(mido.Message("control_change", channel=int(ch), control=120, value=0))
            sender.send(mido.Message("control_change", channel=int(ch), control=121, value=0))
            sender.send(mido.Message("control_change", channel=int(ch), control=123, value=0))
            # Sustain off (64) is a common cause of "stuck" sounding notes
            sender.send(mido.Message("control_change", channel=int(ch), control=64, value=0))
        except Exception:
            # Never let cleanup throw during shutdown
            pass


def _should_drop_click(*, lateness_s: float, policy: LateDropPolicy) -> bool:
    if not policy.enabled:
        return False
    return lateness_s > policy.late_drop_s()


def _should_drop_note_on(*, msg: mido.Message, lateness_s: float, policy: LateDropPolicy) -> bool:
    """
    Drop only low-velocity ornament note-ons when late.
    Never drop note-offs (handled elsewhere).
    """
    if not policy.enabled:
        return False
    if msg.type != "note_on":
        return False
    # Many systems represent note_off as note_on vel=0; treat that as NEVER dropped.
    if getattr(msg, "velocity", 0) == 0:
        return False
    if lateness_s <= policy.late_drop_s():
        return False
    return int(getattr(msg, "velocity", 127)) <= policy.ghost_note_on_max_vel


def _cycle_time(grid: ClaveGrid) -> float:
    return grid.seconds_per_bar() * grid.bars_per_cycle


def _t_to_step(t_in_cycle: float, grid: ClaveGrid) -> float:
    return t_in_cycle / grid.seconds_per_step()


def _step_to_t(step_i: int, grid: ClaveGrid) -> float:
    return step_i * grid.seconds_per_step()


def _send_at(outport, msg, when: float) -> None:
    """
    Busy-wait is avoided; caller uses lookahead scheduling.
    """
    # msg.time is ignored for realtime; we schedule by wall clock.
    outport.send(msg)


def _make_click_msgs(grid: ClaveGrid, spec: RtSpec) -> list[tuple[int, mido.Message]]:
    """
    Returns list of (step_i, msg) for click hits in a 2-bar cycle.
    Click follows clave hit steps (so you hear the grid).
    """
    if not spec.click:
        return []
    if not MIDO_AVAILABLE:
        return []
    hits = clave_hit_steps(grid.grid, grid.clave)
    out = []
    for s in hits:
        out.append((s, mido.Message("note_on", channel=spec.click_channel, note=spec.click_note, velocity=spec.click_vel, time=0)))
        out.append((s + 1, mido.Message("note_off", channel=spec.click_channel, note=spec.click_note, velocity=0, time=0)))
    return out


def rt_play_cycle(
    *,
    events: list[tuple[int, mido.Message]],
    spec: RtSpec,
    max_cycles: int | None = None,
    backend: str = "mido",
    late_drop: LateDropPolicy | None = None,
    panic: bool = True,
) -> None:
    """
    Real-time scheduler: repeatedly plays a 2-bar cycle of step-indexed MIDI messages.
    events: list of (step_i, Message) in cycle coordinates (0..steps_per_cycle-1)

    If max_cycles is set, exits after that many cycles. Otherwise loops forever.
    Press Ctrl+C to stop.
    """
    if not MIDO_AVAILABLE:
        raise RuntimeError("mido is not installed; cannot use realtime features")

    grid = ClaveGrid(bpm=spec.bpm, grid=spec.grid, clave=spec.clave)
    steps_per_cycle = grid.steps_per_cycle()
    cycle_len = _cycle_time(grid)
    bar_len = grid.seconds_per_bar()

    events_sorted = sorted(((s % steps_per_cycle), msg) for s, msg in events)

    # Use sender factory for backend abstraction (mido or rtmidi)
    raw_sender = create_sender(backend=backend, port_name=spec.midi_out)

    # Wrap with VelocityAssistSender if velocity_mul != 1.0
    if spec.velocity_mul != 1.0:
        from .midi.velocity_assist_sender import VelocityAssistSender
        sender = VelocityAssistSender(sender=raw_sender, velocity_mul=spec.velocity_mul)
    else:
        sender = raw_sender

    try:
        t0 = _now()
        next_cycle_start = t0

        # optional click layer
        click_events = _make_click_msgs(grid, spec)
        click_sorted = sorted(((s % steps_per_cycle), msg) for s, msg in click_events)

        # schedule loop
        i = 0
        ci = 0
        cycle_count = 0

        # bar CC tracking
        bars_per_cycle = 2
        total_bars = (max_cycles * bars_per_cycle) if max_cycles else None
        bars_in_cycle_emitted = [False, False]  # track which bars in current cycle have had CC emitted

        print(f"RT Play: {spec.bpm} BPM, grid={spec.grid}, clave={spec.clave}, backend={backend}")
        print(f"Output: {spec.midi_out}")
        if max_cycles:
            print(f"Cycles: {max_cycles}")
        else:
            print("Press Ctrl+C to stop...")
        if spec.bar_cc_enabled:
            print(f"Bar CC: channel={spec.bar_cc_channel}, countdown=CC#{spec.bar_cc_countdown}, index=CC#{spec.bar_cc_index}")

        while True:
            # Check cycle limit
            if max_cycles and cycle_count >= max_cycles:
                break

            now = _now()

            # advance cycle start if we're past it
            while now >= next_cycle_start + cycle_len:
                next_cycle_start += cycle_len
                i = 0
                ci = 0
                cycle_count += 1
                bars_in_cycle_emitted = [False, False]
                if max_cycles and cycle_count >= max_cycles:
                    break

            # emit bar CC messages at bar boundaries
            if spec.bar_cc_enabled:
                elapsed_in_cycle = now - next_cycle_start
                for bar_in_cycle in range(bars_per_cycle):
                    bar_start = bar_in_cycle * bar_len
                    if elapsed_in_cycle >= bar_start and not bars_in_cycle_emitted[bar_in_cycle]:
                        # calculate countdown (bars remaining) and bar index
                        current_bar_index = (cycle_count * bars_per_cycle) + bar_in_cycle
                        if total_bars is not None:
                            bars_remaining = max(0, total_bars - current_bar_index - 1)
                        else:
                            bars_remaining = 127  # no countdown in infinite mode

                        # emit CC messages
                        from .realtime_telemetry import make_bar_cc_messages
                        cc_msgs = make_bar_cc_messages(
                            channel=spec.bar_cc_channel,
                            cc_countdown=spec.bar_cc_countdown,
                            cc_index=spec.bar_cc_index,
                            bars_remaining=bars_remaining,
                            bar_index=current_bar_index,
                        )
                        for msg in cc_msgs:
                            sender.send(msg)
                        bars_in_cycle_emitted[bar_in_cycle] = True

            # schedule events within lookahead window
            window_end = now + spec.lookahead_s

            # main events
            while i < len(events_sorted):
                step_i, msg = events_sorted[i]
                due = next_cycle_start + _step_to_t(step_i, grid)
                if due > window_end:
                    break
                if due <= now:
                    lateness_s = now - due
                    # Late-drop only applies to ornament note-ons; never drop note-off
                    if msg.type == "note_on" and _should_drop_note_on(msg=msg, lateness_s=lateness_s, policy=policy):
                        i += 1
                        continue
                    _send_at(sender, msg, due)
                i += 1

            # click events
            while ci < len(click_sorted):
                step_i, msg = click_sorted[ci]
                due = next_cycle_start + _step_to_t(step_i, grid)
                if due > window_end:
                    break
                if due <= now:
                    lateness_s = now - due
                    if _should_drop_click(lateness_s=lateness_s, policy=policy):
                        ci += 1
                        continue
                    _send_at(sender, msg, due)
                ci += 1

            time.sleep(spec.tick_s)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        # PANIC CLEANUP FIRST (if enabled), then close the port.
        # Use raw_sender for cleanup since it owns the MIDI port.
        if panic:
            _panic_cleanup(raw_sender)
        try:
            raw_sender.close()
        except Exception:
            pass


def practice_lock_to_clave(spec: RtSpec) -> None:
    """
    MIDI IN -> quantize/lock to clave grid -> MIDI OUT.

    Press Ctrl+C to stop.
    """
    if not MIDO_AVAILABLE:
        raise RuntimeError("mido is not installed; cannot use realtime features")

    if not spec.midi_in:
        raise ValueError("practice requires midi_in")

    grid = ClaveGrid(bpm=spec.bpm, grid=spec.grid, clave=spec.clave)
    steps_per_cycle = grid.steps_per_cycle()
    cycle_len = _cycle_time(grid)
    allowed = clave_hit_steps(grid.grid, grid.clave)

    print(f"Practice Mode: {spec.bpm} BPM, grid={spec.grid}, clave={spec.clave}")
    print(f"Input: {spec.midi_in}")
    print(f"Output: {spec.midi_out}")
    print(f"Strict: {spec.practice_strict}, Quantize: {spec.practice_quantize}")
    print("Press Ctrl+C to stop...")

    with mido.open_input(spec.midi_in) as inport, mido.open_output(spec.midi_out) as outport:
        t0 = _now()

        # optional click
        click_events = _make_click_msgs(grid, spec)
        click_sorted = sorted(((s % steps_per_cycle), msg) for s, msg in click_events)
        ci = 0
        next_cycle_start = t0

        try:
            while True:
                now = _now()

                # maintain cycle alignment
                while now >= next_cycle_start + cycle_len:
                    next_cycle_start += cycle_len
                    ci = 0

                # schedule click within lookahead
                if spec.click:
                    window_end = now + spec.lookahead_s
                    while ci < len(click_sorted):
                        step_i, msg = click_sorted[ci]
                        due = next_cycle_start + _step_to_t(step_i, grid)
                        if due > window_end:
                            break
                        if due <= now:
                            outport.send(msg)
                        ci += 1

                # read input messages (non-blocking-ish)
                for msg in inport.iter_pending():
                    if msg.type not in ("note_on", "note_off"):
                        outport.send(msg)
                        continue

                    # Determine note type: note_on with velocity>0 vs note_off (or note_on with velocity=0)
                    is_note_on = (msg.type == "note_on" and getattr(msg, "velocity", 0) > 0)
                    is_note_off = (msg.type == "note_off" or (msg.type == "note_on" and getattr(msg, "velocity", 0) == 0))

                    # Compute per-type windows
                    base_window_s = max(0.0, spec.practice_window_ms) / 1000.0
                    if spec.practice_window_on_ms is not None:
                        on_window_s = max(0.0, spec.practice_window_on_ms) / 1000.0
                    else:
                        on_window_s = base_window_s
                    if spec.practice_window_off_ms is not None:
                        off_window_s = max(0.0, spec.practice_window_off_ms) / 1000.0
                    else:
                        # Default NOTE-OFF window: looser to prevent choke artifacts in legato
                        off_window_s = max(base_window_s * 4.0, 0.080)  # >= 80ms or 4x base

                    # map arrival time to step in current cycle
                    t_in_cycle = (now - next_cycle_start) % cycle_len
                    step_f = _t_to_step(t_in_cycle, grid)
                    step_i = quantize_step(step_f, grid_steps=steps_per_cycle, mode=spec.practice_quantize)

                    if spec.practice_strict:
                        ok = is_allowed_on_clave(step_i, allowed=allowed, strict=True)
                        if not ok:
                            # Find nearest allowed hit step
                            nearest = min(allowed, key=lambda a: abs(a - step_i))

                            # Window check: if actual time is within ±window of nearest hit, pass-through
                            win_s = on_window_s if is_note_on else off_window_s
                            if win_s > 0.0:
                                nearest_due = next_cycle_start + _step_to_t(nearest, grid)
                                # Handle cycle boundary wrap
                                if nearest_due < now - (cycle_len / 2.0):
                                    nearest_due += cycle_len
                                elif nearest_due > now + (cycle_len / 2.0):
                                    nearest_due -= cycle_len
                                if abs(nearest_due - now) <= win_s:
                                    # Within tolerance: send immediately without snapping
                                    outport.send(msg)
                                    continue

                            # NOTE-OFF safety: never reject note-off to prevent stuck notes
                            if is_note_off:
                                outport.send(msg)
                                continue

                            # For NOTE-ON: reject or snap based on settings
                            if spec.practice_reject_offgrid:
                                continue
                            step_i = nearest

                    # schedule output at the quantized step boundary (in this cycle)
                    due = next_cycle_start + _step_to_t(step_i, grid)

                    # If due is in the past (late), push to next step boundary
                    if due < now:
                        due += grid.seconds_per_step()

                    # Sleep tiny amount if needed then send (kept simple; can be improved later)
                    wait = due - _now()
                    if wait > 0:
                        time.sleep(min(wait, spec.lookahead_s))

                    outport.send(msg)

                time.sleep(spec.tick_s)
        except KeyboardInterrupt:
            print("\nStopped.")


def list_midi_ports() -> tuple[list[str], list[str]]:
    """Return (input_names, output_names) for available MIDI ports."""
    if not MIDO_AVAILABLE:
        return [], []
    try:
        return list(mido.get_input_names()), list(mido.get_output_names())
    except Exception:
        # rtmidi backend may not be installed
        return [], []
