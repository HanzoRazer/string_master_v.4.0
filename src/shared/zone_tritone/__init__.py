from .__about__ import __version__
from .backdoor import (
    add_backdoor_bars,
    build_12bar_roots,
    build_backdoor_blues,
    describe_mode,
    get_bVII,
    needs_soft_guardrail,
)
from .dominant import (
    Dominant7,
    build_dominant,
    transpose,
)
from .generator import (
    DENSITY_MAP,
    DIFF_POLICY,
    Etude,
    EtudeBar,
    SubstitutionPolicy,
    apply_soft_guardrail,
    etude_summary,
    etude_to_pitch_sequence,
    generate_etude,
    generate_multi_chorus_etude,
    generate_phrase,
    generate_phrase_with_guide_tones,
    tritone_probability,
)
from .gravity import (
    dominant_roots_from_tritone,
    gravity_chain,
)
from .markov import (
    build_transition_counts,
    normalize_transition_matrix,
    sample_next_root,
)
from .pc import (
    NOTES,
    name_from_pc,
    pc_from_name,
)
from .tritones import (
    all_tritone_axes,
    is_tritone_pair,
    tritone_axis,
    tritone_partner,
)
from .types import (
    BackdoorMode,
    Difficulty,
    PitchClass,
    ResolutionMode,
    StyleMode,
)
from .zones import (
    is_half_step,
    is_same_zone,
    is_whole_step,
    is_zone_cross,
    zone,
    zone_name,
)
from .andalusian import (
    ANDALUSIAN_OFFSETS,
    ANDALUSIAN_ROMANS,
    ANDALUSIAN_STEPS,
    STYLE_PACKS,
    AndalusianStylePack,
    AndalusianChord,
    andalusian_bass_pcs,
    andalusian_bass_names,
    build_andalusian_cadence,
    build_andalusian_cadence_from_key,
    backdoor_tag_pcs,
    build_backdoor_tag,
)

__all__ = [
    "__version__",
    # types
    "PitchClass",
    "BackdoorMode",
    "ResolutionMode",
    "StyleMode",
    "Difficulty",
    # pc
    "NOTES",
    "pc_from_name",
    "name_from_pc",
    # zones
    "zone",
    "zone_name",
    "is_same_zone",
    "is_zone_cross",
    "is_whole_step",
    "is_half_step",
    # tritones
    "tritone_partner",
    "tritone_axis",
    "is_tritone_pair",
    "all_tritone_axes",
    # gravity
    "dominant_roots_from_tritone",
    "gravity_chain",
    # markov
    "build_transition_counts",
    "normalize_transition_matrix",
    "sample_next_root",
    # dominant
    "Dominant7",
    "build_dominant",
    "transpose",
    # backdoor
    "build_12bar_roots",
    "get_bVII",
    "add_backdoor_bars",
    "build_backdoor_blues",
    "needs_soft_guardrail",
    "describe_mode",
    # generator
    "generate_phrase",
    "generate_phrase_with_guide_tones",
    "generate_etude",
    "generate_multi_chorus_etude",
    "apply_soft_guardrail",
    "tritone_probability",
    "etude_to_pitch_sequence",
    "etude_summary",
    "Etude",
    "EtudeBar",
    "SubstitutionPolicy",
    "DENSITY_MAP",
    "DIFF_POLICY",
    # andalusian
    "ANDALUSIAN_OFFSETS",
    "ANDALUSIAN_ROMANS",
    "ANDALUSIAN_STEPS",
    "STYLE_PACKS",
    "AndalusianStylePack",
    "AndalusianChord",
    "andalusian_bass_pcs",
    "andalusian_bass_names",
    "build_andalusian_cadence",
    "build_andalusian_cadence_from_key",
    "backdoor_tag_pcs",
    "build_backdoor_tag",
]
