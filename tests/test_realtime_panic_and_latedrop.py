import mido

from zt_band.realtime import LateDropPolicy, _panic_cleanup, _should_drop_click, _should_drop_note_on


class _FakeSender:
    def __init__(self):
        self.sent = []
        self.closed = False

    def send(self, msg):
        self.sent.append(msg)

    def close(self):
        self.closed = True


def test_panic_cleanup_sends_ccs_for_each_channel():
    s = _FakeSender()
    _panic_cleanup(s, channels=[0, 1])
    # 4 CC messages per channel: 120,121,123,64
    assert len(s.sent) == 8
    controls = [m.control for m in s.sent if m.type == "control_change"]
    assert controls.count(120) == 2
    assert controls.count(121) == 2
    assert controls.count(123) == 2
    assert controls.count(64) == 2


def test_late_drop_click_only_when_late_over_threshold():
    policy = LateDropPolicy(enabled=True, late_drop_ms=35)
    assert _should_drop_click(lateness_s=0.001, policy=policy) is False
    assert _should_drop_click(lateness_s=0.100, policy=policy) is True


def test_late_drop_note_on_drops_only_low_velocity_note_ons_when_late():
    policy = LateDropPolicy(enabled=True, late_drop_ms=35, ghost_note_on_max_vel=22)
    ghost = mido.Message("note_on", note=60, velocity=18, channel=0)
    strong = mido.Message("note_on", note=60, velocity=90, channel=0)
    off_as_on = mido.Message("note_on", note=60, velocity=0, channel=0)  # note_off style

    assert _should_drop_note_on(msg=ghost, lateness_s=0.100, policy=policy) is True
    assert _should_drop_note_on(msg=strong, lateness_s=0.100, policy=policy) is False
    assert _should_drop_note_on(msg=off_as_on, lateness_s=0.100, policy=policy) is False
    # Not late => never drop
    assert _should_drop_note_on(msg=ghost, lateness_s=0.001, policy=policy) is False


def test_late_drop_policy_disabled():
    policy = LateDropPolicy(enabled=False, late_drop_ms=35, ghost_note_on_max_vel=22)
    ghost = mido.Message("note_on", note=60, velocity=18, channel=0)
    
    # When disabled, nothing is dropped
    assert _should_drop_click(lateness_s=0.100, policy=policy) is False
    assert _should_drop_note_on(msg=ghost, lateness_s=0.100, policy=policy) is False


def test_late_drop_never_drops_note_off():
    policy = LateDropPolicy(enabled=True, late_drop_ms=35, ghost_note_on_max_vel=22)
    note_off = mido.Message("note_off", note=60, velocity=0, channel=0)
    
    # note_off messages are never dropped (prevents stuck notes)
    assert _should_drop_note_on(msg=note_off, lateness_s=0.100, policy=policy) is False
