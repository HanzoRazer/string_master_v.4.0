"""
Deterministic seed derivation for sg_agentd.

Enables reproducible variation across retry attempts without mutation.
Each attempt gets a predictable seed derived from request_id + attempt_index.
"""
from __future__ import annotations

import hashlib
from typing import Optional
from uuid import UUID

# SHA-256 produces 256 bits; we use 31 bits to stay in positive int range
MAX_SEED: int = 2**31 - 1


def derive_base_seed(request_id: UUID) -> int:
    """
    Derive a deterministic base seed from a request_id.
    
    Uses SHA-256 hash of request_id bytes, truncated to 31-bit positive int.
    Same request_id always produces same base seed.
    
    Args:
        request_id: UUID identifying the generation request
        
    Returns:
        31-bit positive integer seed
    """
    digest = hashlib.sha256(request_id.bytes).digest()
    # Take first 4 bytes, interpret as big-endian unsigned int
    raw_int = int.from_bytes(digest[:4], "big")
    # Mask to 31 bits to ensure positive value
    return raw_int & MAX_SEED


def derive_attempt_seed(base_seed: int, attempt_index: int) -> int:
    """
    Derive seed for a specific attempt from base seed.
    
    Each attempt gets a different but deterministic seed.
    
    Args:
        base_seed: Base seed derived from request_id
        attempt_index: 0-indexed attempt number
        
    Returns:
        Attempt-specific seed
    """
    return (base_seed + attempt_index) % (MAX_SEED + 1)


def choose_seed_sequence(
    request_id: UUID,
    attempt_index: int,
    explicit_seed: Optional[int] = None,
) -> int:
    """
    Choose seed for an attempt, preferring explicit seed if provided.
    
    Decision logic:
    - If explicit_seed provided: use it (ignore request_id derivation)
    - Otherwise: derive from request_id + attempt_index
    
    This allows callers to override when they have a specific seed,
    while providing automatic derivation for agentic retry loops.
    
    Args:
        request_id: UUID identifying the generation request
        attempt_index: 0-indexed attempt number
        explicit_seed: Optional user-provided seed
        
    Returns:
        Seed to use for this attempt
    """
    if explicit_seed is not None:
        # User provided explicit seed - honor it exactly
        # (For multi-attempt with explicit seed, we still vary by attempt)
        if attempt_index == 0:
            return explicit_seed
        else:
            return (explicit_seed + attempt_index) % (MAX_SEED + 1)
    
    # Derive from request_id
    base_seed = derive_base_seed(request_id)
    return derive_attempt_seed(base_seed, attempt_index)
