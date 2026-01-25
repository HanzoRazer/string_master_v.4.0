"""
Unit tests for groove intent providers.
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from zt_band.groove import (
    IntentContext,
    IntentProvider,
    ManualIntentProvider,
    AnalyzerIntentProvider,
    GrooveProfileStore,
    EvidenceWindow,
    EvidenceWindowProbe,
)
from zt_band.ui.manual_intent import ManualBandControls


# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_context() -> IntentContext:
    return IntentContext(
        profile_id="test_profile",
        bpm=120.0,
        program_name="test_song",
        item_idx=0,
    )


@pytest.fixture
def sample_controls() -> ManualBandControls:
    return ManualBandControls(
        mode="stabilize",
        tightness=0.7,
        assist=0.6,
        expression=0.5,
        humanize_ms=5.0,
        anticipation_bias="neutral",
        horizon_ms=2000,
        confidence=0.85,
    )


# -----------------------------------------------------------------------------
# TESTS
# -----------------------------------------------------------------------------


def test_manual_provider_returns_intent(sample_context: IntentContext, sample_controls: ManualBandControls):
    """ManualIntentProvider should return a valid intent dict."""
    provider = ManualIntentProvider(controls=sample_controls, profile_id="test")
    intent = provider.get_intent(sample_context)
    
    assert intent is not None
    assert isinstance(intent, dict)
    assert intent.get("schema_id") == "groove_control_intent"
    assert intent.get("schema_version") == "v1"
    assert "control_modes" in intent
    assert "tempo" in intent


def test_manual_provider_uses_context_bpm(sample_context: IntentContext, sample_controls: ManualBandControls):
    """ManualIntentProvider should use BPM from context."""
    provider = ManualIntentProvider(controls=sample_controls)
    intent = provider.get_intent(sample_context)
    
    assert intent is not None
    assert intent["tempo"]["target_bpm"] == sample_context.bpm


def test_manual_provider_uses_custom_profile_id(sample_context: IntentContext, sample_controls: ManualBandControls):
    """ManualIntentProvider should use custom profile_id."""
    provider = ManualIntentProvider(controls=sample_controls, profile_id="custom_profile")
    intent = provider.get_intent(sample_context)
    
    assert intent is not None
    assert intent.get("profile_id") == "custom_profile"


def test_analyzer_provider_returns_none(sample_context: IntentContext, tmp_path: Path):
    """AnalyzerIntentProvider should return None when profile doesn't exist."""
    provider = AnalyzerIntentProvider(profile_store_dir=tmp_path)
    intent = provider.get_intent(sample_context)
    
    assert intent is None


def test_intent_context_is_frozen():
    """IntentContext should be immutable (frozen dataclass)."""
    ctx = IntentContext(profile_id="test", bpm=120.0)
    
    with pytest.raises(Exception):  # FrozenInstanceError
        ctx.bpm = 140.0  # type: ignore


def test_providers_implement_protocol(sample_controls: ManualBandControls, tmp_path: Path):
    """Both providers should satisfy IntentProvider protocol."""
    # This is a structural check - if it runs, the Protocol is satisfied
    manual: IntentProvider = ManualIntentProvider(controls=sample_controls)
    analyzer: IntentProvider = AnalyzerIntentProvider(profile_store_dir=tmp_path)
    
    ctx = IntentContext(profile_id="test", bpm=120.0)
    
    # Both should be callable without error
    manual.get_intent(ctx)
    analyzer.get_intent(ctx)


def test_manual_provider_fails_closed_on_error():
    """ManualIntentProvider should return None on error (not raise)."""
    # Create a broken controls object (invalid types)
    broken_controls = ManualBandControls(
        mode="invalid_mode",  # type: ignore
        tightness=-999.0,  # Invalid but won't cause exception in build
        assist=0.5,
        expression=0.5,
        humanize_ms=5.0,
        anticipation_bias="neutral",
        horizon_ms=2000,
        confidence=0.85,
    )
    provider = ManualIntentProvider(controls=broken_controls)
    ctx = IntentContext(profile_id="test", bpm=120.0)
    
    # Should return intent (or None), never raise
    try:
        result = provider.get_intent(ctx)
        # If it returns something, it should be dict or None
        assert result is None or isinstance(result, dict)
    except Exception:
        pytest.fail("ManualIntentProvider should not raise exceptions")


# -----------------------------------------------------------------------------
# H.1: Profile Store Tests
# -----------------------------------------------------------------------------


@pytest.fixture
def valid_profile() -> dict:
    """A minimal GrooveProfileV1 dict."""
    return {
        "schema_id": "groove_profile",
        "schema_version": "v1",
        "profile_id": "test_profile",
        "scope": "device_local",
        "timing_bias": {"mean_offset_ms": 0.0, "stddev_ms": 5.0},
    }


def test_profile_store_loads_valid_profile(tmp_path: Path, valid_profile: dict):
    """GrooveProfileStore should load a valid profile JSON."""
    profile_path = tmp_path / "test_profile.json"
    profile_path.write_text(json.dumps(valid_profile), encoding="utf-8")
    
    store = GrooveProfileStore(root_dir=tmp_path)
    result = store.load_profile("test_profile")
    
    assert result is not None
    assert result["profile_id"] == "test_profile"
    assert result["schema_id"] == "groove_profile"


def test_profile_store_returns_none_for_missing_file(tmp_path: Path):
    """GrooveProfileStore should return None if file doesn't exist."""
    store = GrooveProfileStore(root_dir=tmp_path)
    result = store.load_profile("nonexistent_profile")
    
    assert result is None


def test_profile_store_returns_none_for_wrong_schema_id(tmp_path: Path, valid_profile: dict):
    """GrooveProfileStore should return None if schema_id is wrong."""
    valid_profile["schema_id"] = "wrong_schema"
    profile_path = tmp_path / "test_profile.json"
    profile_path.write_text(json.dumps(valid_profile), encoding="utf-8")
    
    store = GrooveProfileStore(root_dir=tmp_path)
    result = store.load_profile("test_profile")
    
    assert result is None


def test_profile_store_returns_none_for_mismatched_profile_id(tmp_path: Path, valid_profile: dict):
    """GrooveProfileStore should return None if profile_id doesn't match filename."""
    # Profile says "test_profile" but we're loading "other_profile"
    profile_path = tmp_path / "other_profile.json"
    profile_path.write_text(json.dumps(valid_profile), encoding="utf-8")
    
    store = GrooveProfileStore(root_dir=tmp_path)
    result = store.load_profile("other_profile")
    
    assert result is None


def test_profile_store_returns_none_for_invalid_json(tmp_path: Path):
    """GrooveProfileStore should return None for invalid JSON."""
    profile_path = tmp_path / "test_profile.json"
    profile_path.write_text("not valid json {{{", encoding="utf-8")
    
    store = GrooveProfileStore(root_dir=tmp_path)
    result = store.load_profile("test_profile")
    
    assert result is None


# -----------------------------------------------------------------------------
# H.1: Evidence Window Probe Tests
# -----------------------------------------------------------------------------


def test_evidence_window_probe_snapshot():
    """EvidenceWindowProbe should return an EvidenceWindow."""
    probe = EvidenceWindowProbe()
    window = probe.snapshot(horizon_ms=3000)
    
    assert window is not None
    assert isinstance(window, EvidenceWindow)
    assert window.horizon_ms == 3000
    assert window.features == {}


def test_evidence_window_is_frozen():
    """EvidenceWindow should be immutable."""
    window = EvidenceWindow(horizon_ms=2000, features={"test": 1})
    
    with pytest.raises(Exception):  # FrozenInstanceError
        window.horizon_ms = 5000  # type: ignore


# -----------------------------------------------------------------------------
# H.1: Analyzer Provider Scaffold Tests
# -----------------------------------------------------------------------------


def test_analyzer_provider_loads_profile_but_returns_none_with_stub(
    tmp_path: Path, valid_profile: dict, sample_context: IntentContext
):
    """
    AnalyzerIntentProvider should load profile, but return None because
    generate_intent() stub returns None.
    """
    # Override sample_context profile_id to match
    ctx = IntentContext(
        profile_id="test_profile",
        bpm=120.0,
        program_name="test_song",
        item_idx=0,
    )
    
    profile_path = tmp_path / "test_profile.json"
    profile_path.write_text(json.dumps(valid_profile), encoding="utf-8")
    
    provider = AnalyzerIntentProvider(profile_store_dir=tmp_path)
    intent = provider.get_intent(ctx)
    
    # Still returns None because generate_intent() stub returns None
    assert intent is None


def test_analyzer_provider_fails_closed_on_missing_profile(tmp_path: Path, sample_context: IntentContext):
    """AnalyzerIntentProvider should return None if profile doesn't exist."""
    provider = AnalyzerIntentProvider(profile_store_dir=tmp_path)
    intent = provider.get_intent(sample_context)
    
    assert intent is None


def test_analyzer_provider_fails_closed_on_exception(sample_context: IntentContext):
    """AnalyzerIntentProvider should return None on any exception (fail closed)."""
    # Use a non-existent directory to trigger exception
    provider = AnalyzerIntentProvider(profile_store_dir=Path("/nonexistent/path/12345"))
    intent = provider.get_intent(sample_context)
    
    assert intent is None


# -----------------------------------------------------------------------------
# H.2: Groove Layer Bridge Tests
# -----------------------------------------------------------------------------


from zt_band.groove.groove_layer_bridge import (
    _safe_get,
    _map_window_features_to_analyzer_inputs,
    _validate_intent_shape,
    generate_intent,
)


def test_safe_get_simple_path():
    """_safe_get should extract nested values via dot path."""
    d = {"timing": {"mean_offset_ms": -12.5}}
    assert _safe_get(d, "timing.mean_offset_ms") == -12.5


def test_safe_get_missing_path_returns_default():
    """_safe_get should return default for missing paths."""
    d = {"timing": {}}
    assert _safe_get(d, "timing.mean_offset_ms") is None
    assert _safe_get(d, "timing.mean_offset_ms", 0.0) == 0.0


def test_safe_get_non_dict_returns_default():
    """_safe_get should return default if path hits non-dict."""
    d = {"timing": "not_a_dict"}
    assert _safe_get(d, "timing.mean_offset_ms") is None


def test_map_window_features_extracts_horizon():
    """_map_window_features_to_analyzer_inputs should extract horizon_ms."""
    window = EvidenceWindow(horizon_ms=3000, features={})
    result = _map_window_features_to_analyzer_inputs(window)
    
    assert result["horizon_ms"] == 3000
    assert result["engine_salt"] == "zt_band_groove_layer_bridge_v1"


def test_map_window_features_with_timing_data():
    """_map_window_features_to_analyzer_inputs should map timing features."""
    window = EvidenceWindow(
        horizon_ms=2000,
        features={
            "timing": {
                "mean_offset_ms": -10.0,
                "stddev_ms": 5.0,
                "direction": "ahead",
            }
        }
    )
    result = _map_window_features_to_analyzer_inputs(window)
    
    assert result["features"]["timing"]["mean_offset_ms"] == -10.0
    assert result["features"]["timing"]["stddev_ms"] == 5.0
    assert result["features"]["timing"]["direction"] == "ahead"


def test_map_window_features_strips_nones():
    """_map_window_features_to_analyzer_inputs should strip None values."""
    window = EvidenceWindow(horizon_ms=2000, features={})
    result = _map_window_features_to_analyzer_inputs(window)
    
    # Timing should exist but be empty (Nones stripped)
    # Events should have empty lists (not None)
    assert result["features"]["events"]["recent_note_onsets_ms"] == []
    assert result["features"]["events"]["recent_iois_ms"] == []


def test_validate_intent_shape_valid():
    """_validate_intent_shape should accept valid intent."""
    intent = {
        "schema_id": "groove_control_intent",
        "schema_version": "v1",
        "profile_id": "gp_123",
        "control_modes": ["stabilize"],
    }
    result = _validate_intent_shape(intent, "gp_123")
    assert result == intent


def test_validate_intent_shape_wrong_schema_id():
    """_validate_intent_shape should reject wrong schema_id."""
    intent = {
        "schema_id": "wrong_schema",
        "schema_version": "v1",
        "profile_id": "gp_123",
    }
    result = _validate_intent_shape(intent, "gp_123")
    assert result is None


def test_validate_intent_shape_wrong_profile_id():
    """_validate_intent_shape should reject mismatched profile_id."""
    intent = {
        "schema_id": "groove_control_intent",
        "schema_version": "v1",
        "profile_id": "gp_123",
    }
    result = _validate_intent_shape(intent, "gp_different")
    assert result is None


def test_validate_intent_shape_non_dict():
    """_validate_intent_shape should reject non-dict."""
    result = _validate_intent_shape("not a dict", "gp_123")
    assert result is None


def test_generate_intent_returns_none_when_no_integration():
    """generate_intent should return None when no integration available."""
    from datetime import datetime, timezone
    
    profile = {
        "schema_id": "groove_profile",
        "schema_version": "v1",
        "profile_id": "test_profile",
    }
    window = EvidenceWindow(horizon_ms=2000, features={})
    now = datetime.now(timezone.utc)
    
    # Without sg_coach installed or service URL, should return None
    result = generate_intent(profile=profile, window=window, now_utc=now)
    assert result is None


def test_generate_intent_never_raises():
    """generate_intent should never raise, always return None on error."""
    from datetime import datetime, timezone
    
    # Pass garbage inputs
    try:
        result = generate_intent(
            profile=None,  # type: ignore
            window=None,  # type: ignore
            now_utc=datetime.now(timezone.utc),
        )
        assert result is None
    except Exception:
        pytest.fail("generate_intent should never raise")

