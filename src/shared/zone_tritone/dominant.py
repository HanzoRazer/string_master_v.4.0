"""
Dominant chord model for the Zone-Tritone / Hidden Blues Resolution engine.

A dominant 7th chord defines two pitch sets:
- Frame tones: root, 3rd, 5th, b7 (may resolve, land, hold)
- Color tones: b3, 4, b5, 6 (must move, cannot be destinations)

This is the "Bluesette rule" formalized: blues vocabulary is allowed
everywhere, but blues notes are forbidden as points of rest.
"""
from __future__ import annotations

from dataclasses import dataclass

from .types import PitchClass


def transpose(pc: PitchClass, semitones: int) -> PitchClass:
    """Transpose a pitch class by semitones (mod 12)."""
    return (pc + semitones) % 12


@dataclass(frozen=True)
class Dominant7:
    """
    Dominant 7th chord model with frame/color tone separation.
    
    Frame tones (chord tones) may be used as resolution targets.
    Color tones (blues/passing tones) must keep moving.
    """
    root: PitchClass
    
    @property
    def frame(self) -> frozenset[PitchClass]:
        """
        Frame tones: root, major 3rd, 5th, minor 7th.
        These may be phrase-final or metrically strong.
        """
        return frozenset({
            self.root,
            transpose(self.root, 4),   # major 3rd
            transpose(self.root, 7),   # perfect 5th
            transpose(self.root, 10),  # minor 7th
        })
    
    @property
    def color(self) -> frozenset[PitchClass]:
        """
        Color tones: minor 3rd, 4th, b5, 6th.
        These must move; they cannot be destinations in hidden mode.
        """
        return frozenset({
            transpose(self.root, 3),   # minor 3rd (blue note)
            transpose(self.root, 5),   # perfect 4th
            transpose(self.root, 6),   # tritone / b5 (blue note)
            transpose(self.root, 9),   # major 6th
        })
    
    @property
    def third(self) -> PitchClass:
        """Major 3rd (guide tone)."""
        return transpose(self.root, 4)
    
    @property
    def seventh(self) -> PitchClass:
        """Minor 7th (guide tone)."""
        return transpose(self.root, 10)
    
    @property
    def guide_tones(self) -> tuple[PitchClass, PitchClass]:
        """Guide tone pair (3rd, 7th) for voice leading."""
        return (self.third, self.seventh)
    
    def is_frame_tone(self, pc: PitchClass) -> bool:
        """Check if a pitch class is a frame tone of this chord."""
        return (pc % 12) in self.frame
    
    def is_color_tone(self, pc: PitchClass) -> bool:
        """Check if a pitch class is a color tone of this chord."""
        return (pc % 12) in self.color


def build_dominant(root_name: str) -> Dominant7:
    """
    Build a Dominant7 from a root name (e.g., 'C', 'Bb', 'F#').
    """
    from .pc import pc_from_name
    return Dominant7(pc_from_name(root_name))


__all__ = ["Dominant7", "build_dominant", "transpose"]
