"""
Groove layer bridge: interface for intent generation.

H.2: Real implementation with local Python and service client integration.

Priority:
  1) Local Python integration (sg_coach/sg_spec if installed)
  2) Service client (SG_GROOVE_SERVICE_URL env var)
  3) None (fail closed)
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, Tuple


ENGINE_SALT = "zt_band_groove_layer_bridge_v1"
SCHEMA_VERSION = "v1"          # matches groove contract version
DEFAULT_TIMEOUT_S = 2.0
RETRY_MAX_ATTEMPTS = 2          # 1 retry => 2 total attempts
RETRY_BACKOFF_S = 0.15          # base backoff before retry
RETRY_JITTER_MAX_S = 0.10       # jitter range added to backoff (deterministic)


def _get_runtime_pkg_version(pkg_name: str = "smart-guitar") -> str | None:
    """
    Best-effort, deterministic package version lookup.
    Returns None if the package is not installed or version is unavailable.
    """
    try:
        return importlib.metadata.version(pkg_name)
    except Exception:
        return None


def _engine_identity() -> str:
    """
    Engine identity for server-side rollout disambiguation.

    Format:
      v1|<engine_salt>[|pkg=<version>]
    """
    base = f"{SCHEMA_VERSION}|{ENGINE_SALT}"
    ver = _get_runtime_pkg_version()
    if ver:
        return f"{base}|pkg={ver}"
    return base


class GrooveLayer(Protocol):
    """
    Interface for a groove-layer intent generator.
    You can later implement this by importing sg-coach/sg-spec or a service client.
    """

    def generate_intent(
        self,
        *,
        profile: Dict[str, Any],
        window: Any,
        now_utc: datetime,
    ) -> Dict[str, Any] | None:
        """
        Generate a GrooveControlIntentV1 from profile and evidence window.

        Returns None if intent cannot be generated.
        """
        ...


def _safe_get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Tiny dotted-path getter for feature mapping:
      _safe_get(features, "timing.mean_offset_ms")
    """
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
        if cur is None:
            return default
    return cur


def _map_window_features_to_analyzer_inputs(window: Any) -> Dict[str, Any]:
    """
    Map EvidenceWindow.features into a stable analyzer input payload.

    Expected feature keys (optional):
      features = {
        "timing": {"mean_offset_ms": ..., "stddev_ms": ..., "direction": ...},
        "tempo": {"bpm_estimate": ..., "drift_slope": ...},
        "dynamics": {"assist_pressure": ...},
        "events": {"recent_note_onsets_ms": [...], "recent_iois_ms": [...]}
      }

    The analyzer can ignore unknown fields; this shape is intentionally additive.
    """
    features = getattr(window, "features", None)
    if not isinstance(features, dict):
        features = {}

    horizon_ms = getattr(window, "horizon_ms", None)
    try:
        horizon_ms = int(horizon_ms) if horizon_ms is not None else 2000
    except Exception:
        horizon_ms = 2000

    payload: Dict[str, Any] = {
        "horizon_ms": horizon_ms,
        "features": {
            "timing": {
                "mean_offset_ms": _safe_get(features, "timing.mean_offset_ms"),
                "stddev_ms": _safe_get(features, "timing.stddev_ms"),
                "direction": _safe_get(features, "timing.direction"),
            },
            "tempo": {
                "bpm_estimate": _safe_get(features, "tempo.bpm_estimate"),
                "drift_slope": _safe_get(features, "tempo.drift_slope"),
            },
            "dynamics": {
                "assist_pressure": _safe_get(features, "dynamics.assist_pressure"),
            },
            "events": {
                "recent_note_onsets_ms": _safe_get(features, "events.recent_note_onsets_ms", []),
                "recent_iois_ms": _safe_get(features, "events.recent_iois_ms", []),
            },
        },
        "engine_salt": ENGINE_SALT,
    }

    # Remove None values to keep payload clean
    def strip_nones(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: strip_nones(v) for k, v in obj.items() if v is not None}
        if isinstance(obj, list):
            return [strip_nones(v) for v in obj]
        return obj

    return strip_nones(payload)


def _validate_intent_shape(intent: Any, profile_id: str) -> Dict[str, Any] | None:
    """Validate that intent has correct GrooveControlIntentV1 shape."""
    if not isinstance(intent, dict):
        return None
    if intent.get("schema_id") != "groove_control_intent":
        return None
    if intent.get("schema_version") != "v1":
        return None
    if intent.get("profile_id") != profile_id:
        return None
    return intent


def _try_local_python(
    *,
    profile: Dict[str, Any],
    window: Any,
    now_utc: datetime,
) -> Dict[str, Any] | None:
    """
    Attempts to generate intent via locally installed sg_coach (preferred),
    optionally validating with sg_spec pydantic models if present.

    Supported callable names (first hit wins):
      - sg_coach.groove_layer.generate_intent
      - sg_coach.groove_layer.generate_control_intent
      - sg_coach.groove_layer.api.generate_intent
    """
    profile_id = str(profile.get("profile_id", ""))

    # Optional: pydantic validation/coercion if sg_spec exists
    gp_obj: Any = profile
    try:
        from sg_spec.schemas.groove_layer import GrooveProfileV1  # type: ignore
        gp_obj = GrooveProfileV1.model_validate(profile)
    except Exception:
        gp_obj = profile

    window_inputs = _map_window_features_to_analyzer_inputs(window)

    candidates: Tuple[Tuple[str, str], ...] = (
        ("sg_coach.groove_layer", "generate_intent"),
        ("sg_coach.groove_layer", "generate_control_intent"),
        ("sg_coach.groove_layer.api", "generate_intent"),
    )

    for mod_name, fn_name in candidates:
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name, None)
            if not callable(fn):
                continue

            produced = fn(profile=gp_obj, window=window_inputs, now_utc=now_utc)
            # If pydantic intent returned, convert to dict
            if hasattr(produced, "model_dump"):
                produced = produced.model_dump(mode="json")

            return _validate_intent_shape(produced, profile_id)
        except Exception:
            continue

    return None


def _det_jitter_s(seed: str, jitter_max_s: float) -> float:
    """
    Deterministic jitter in [0, jitter_max_s].
    Uses sha256(seed) so it is stable under CI and reproducible per seed.
    """
    if jitter_max_s <= 0:
        return 0.0
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    # take first 8 hex digits => 32-bit int
    n = int(h[:8], 16)
    frac = n / float(0xFFFFFFFF)
    return frac * float(jitter_max_s)


def _make_request_id(profile_id: str, now_utc: datetime) -> str:
    """
    Deterministic request id derived from (profile_id, now_utc).
    Stable across retries; attempt index is appended by caller.

    Format:
      sg-<hex12>
    """
    base = f"{profile_id}|{now_utc.isoformat()}"
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return f"sg-{h[:12]}"


def _try_service_client(
    *,
    profile: Dict[str, Any],
    window: Any,
    now_utc: datetime,
    timeout_s: float,
    retry: bool,
    retry_backoff_s: float,
    retry_jitter_s: float,
) -> Dict[str, Any] | None:
    """
    Calls a groove intent service if SG_GROOVE_SERVICE_URL is set.

    Env vars:
      SG_GROOVE_SERVICE_URL=https://... (base URL)
      SG_GROOVE_SERVICE_TOKEN=...       (optional bearer token)

    Endpoint:
      POST {base}/generate_intent
      JSON body: {profile, window, now_utc}

    Retry behavior (service-only):
      - At most 1 retry (2 total attempts) if retry=True
      - Bounded backoff with deterministic jitter
      - Only retries on transient failures (timeout, connection, 429, 5xx)
    """
    base = os.environ.get("SG_GROOVE_SERVICE_URL")
    if not base:
        return None

    token = os.environ.get("SG_GROOVE_SERVICE_TOKEN", "")
    url = base.rstrip("/") + "/generate_intent"

    profile_id = str(profile.get("profile_id", ""))

    body = {
        "profile": profile,
        "window": _map_window_features_to_analyzer_inputs(window),
        "now_utc": now_utc.isoformat().replace("+00:00", "Z"),
    }
    data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url=url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    # Identify client engine + contract + package version (when available)
    req.add_header("X-Engine-Identity", _engine_identity())

    max_attempts = RETRY_MAX_ATTEMPTS if retry else 1
    base_req_id = _make_request_id(profile_id, now_utc)

    for attempt in range(1, max_attempts + 1):
        try:
            # Attach deterministic request id with attempt suffix
            req.add_header("X-Request-Id", f"{base_req_id}-a{attempt}")

            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                status = getattr(resp, "status", 200)
                if status != 200:
                    # Retry only on transient server responses
                    if attempt < max_attempts and (status == 429 or 500 <= status <= 599):
                        seed = f"{ENGINE_SALT}|{profile_id}|http{status}|attempt{attempt}"
                        delay = float(retry_backoff_s) + _det_jitter_s(seed, float(retry_jitter_s))
                        time.sleep(delay)
                        continue
                    return None

                payload = json.loads(resp.read().decode("utf-8"))
                return _validate_intent_shape(payload, profile_id)

        except urllib.error.HTTPError as e:
            # HTTPError is also an exception path; status available via e.code
            code = getattr(e, "code", None)
            if attempt < max_attempts and isinstance(code, int) and (code == 429 or 500 <= code <= 599):
                seed = f"{ENGINE_SALT}|{profile_id}|http{code}|attempt{attempt}"
                delay = float(retry_backoff_s) + _det_jitter_s(seed, float(retry_jitter_s))
                time.sleep(delay)
                continue
            return None

        except (urllib.error.URLError, TimeoutError):
            # Network-ish transient failures: retry once if enabled
            if attempt < max_attempts:
                seed = f"{ENGINE_SALT}|{profile_id}|net|attempt{attempt}"
                delay = float(retry_backoff_s) + _det_jitter_s(seed, float(retry_jitter_s))
                time.sleep(delay)
                continue
            return None

        except Exception:
            # Unknown exception: fail closed, no retry
            return None

    return None


def generate_intent(
    *,
    profile: Dict[str, Any],
    window: Any,
    now_utc: datetime,
    timeout_s: float | None = None,
    retry: bool = True,
    retry_backoff_s: float = RETRY_BACKOFF_S,
    retry_jitter_s: float = RETRY_JITTER_MAX_S,
) -> Dict[str, Any] | None:
    """
    H.2: Real implementation with local Python and service client integration.

    Priority:
      1) Local python integration (sg_coach/sg_spec if installed)
      2) Service client (SG_GROOVE_SERVICE_URL)
      3) None (fail closed)

    Always returns a GrooveControlIntentV1-shaped dict or None.
    Never raises.

    Args:
        profile: GrooveProfileV1 dict
        window: EvidenceWindow with runtime telemetry
        now_utc: Current UTC datetime for intent generation timestamp
        timeout_s: Service client timeout in seconds (default: 2.0)
        retry: Enable service retry on transient failures (default: True)
        retry_backoff_s: Base backoff before retry (default: 0.15)
        retry_jitter_s: Max jitter added to backoff (default: 0.10)

    Returns:
        GrooveControlIntentV1 dict, or None if unavailable
    """
    try:
        # Resolve effective timeout
        eff_timeout = float(timeout_s) if timeout_s is not None else DEFAULT_TIMEOUT_S

        # 1) local python integration
        intent = _try_local_python(profile=profile, window=window, now_utc=now_utc)
        if intent:
            return intent

        # 2) service integration
        intent = _try_service_client(
            profile=profile,
            window=window,
            now_utc=now_utc,
            timeout_s=eff_timeout,
            retry=bool(retry),
            retry_backoff_s=float(retry_backoff_s),
            retry_jitter_s=float(retry_jitter_s),
        )
        if intent:
            return intent

        return None
    except Exception:
        return None
