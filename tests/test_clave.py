"""
Tests for clave grid and quantization utilities.
"""
from zt_band.clave import (
    ClaveGrid,
    clave_hit_steps,
    is_allowed_on_clave,
    quantize_step,
)


class TestClaveGrid:
    def test_grid_defaults(self):
        g = ClaveGrid(bpm=120.0)
        assert g.grid == 16
        assert g.bars_per_cycle == 2
        assert g.clave == "son_2_3"

    def test_seconds_per_beat_120bpm(self):
        g = ClaveGrid(bpm=120.0)
        assert g.seconds_per_beat() == 0.5

    def test_seconds_per_bar_120bpm(self):
        g = ClaveGrid(bpm=120.0)
        # 4 beats per bar at 0.5s each = 2.0s
        assert g.seconds_per_bar() == 2.0

    def test_seconds_per_step_16th_grid(self):
        g = ClaveGrid(bpm=120.0, grid=16)
        # 2.0s bar / 16 steps = 0.125s per step
        assert g.seconds_per_step() == 0.125

    def test_seconds_per_step_8th_grid(self):
        g = ClaveGrid(bpm=120.0, grid=8)
        # 2.0s bar / 8 steps = 0.25s per step
        assert g.seconds_per_step() == 0.25

    def test_steps_per_cycle_16th(self):
        g = ClaveGrid(bpm=120.0, grid=16, bars_per_cycle=2)
        assert g.steps_per_cycle() == 32

    def test_steps_per_cycle_8th(self):
        g = ClaveGrid(bpm=120.0, grid=8, bars_per_cycle=2)
        assert g.steps_per_cycle() == 16


class TestClaveHitSteps:
    def test_son_2_3_16th_grid(self):
        hits = clave_hit_steps(16, "son_2_3")
        # 2-3 clave: 6 hits across 2 bars
        assert len(hits) == 6
        assert hits == [0, 6, 10, 16, 22, 26]

    def test_son_3_2_16th_grid(self):
        hits = clave_hit_steps(16, "son_3_2")
        # 3-2 clave: 5 hits across 2 bars
        assert len(hits) == 5
        assert hits == [0, 6, 10, 16, 22]

    def test_son_2_3_8th_grid(self):
        hits = clave_hit_steps(8, "son_2_3")
        # Approximation on 8th grid (halved, deduplicated)
        assert len(hits) <= 6
        # Should include 0 (first hit)
        assert 0 in hits

    def test_son_3_2_8th_grid(self):
        hits = clave_hit_steps(8, "son_3_2")
        assert len(hits) <= 5
        assert 0 in hits


class TestQuantizeStep:
    def test_nearest_rounds_down(self):
        assert quantize_step(1.4, grid_steps=32, mode="nearest") == 1

    def test_nearest_rounds_up(self):
        assert quantize_step(1.6, grid_steps=32, mode="nearest") == 2

    def test_down_always_floors(self):
        assert quantize_step(1.9, grid_steps=32, mode="down") == 1

    def test_up_always_ceils(self):
        assert quantize_step(1.1, grid_steps=32, mode="up") == 2

    def test_wraps_at_grid_boundary(self):
        # Step 33 should wrap to 1 in a 32-step grid
        assert quantize_step(33.0, grid_steps=32, mode="nearest") == 1


class TestIsAllowedOnClave:
    def test_strict_mode_on_hit(self):
        allowed = [0, 6, 10, 16, 22, 26]
        assert is_allowed_on_clave(0, allowed=allowed, strict=True) is True
        assert is_allowed_on_clave(6, allowed=allowed, strict=True) is True

    def test_strict_mode_off_hit(self):
        allowed = [0, 6, 10, 16, 22, 26]
        assert is_allowed_on_clave(1, allowed=allowed, strict=True) is False
        assert is_allowed_on_clave(15, allowed=allowed, strict=True) is False

    def test_loose_mode_allows_all(self):
        allowed = [0, 6, 10, 16, 22, 26]
        assert is_allowed_on_clave(1, allowed=allowed, strict=False) is True
        assert is_allowed_on_clave(31, allowed=allowed, strict=False) is True
