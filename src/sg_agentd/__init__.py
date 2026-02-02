"""
sg-agentd: Generation Orchestrator

HTTP service that receives GenerationRequest, invokes zt_band,
emits 4-file bundles, and returns GenerationResult.

Phase 3 scope:
  - POST /generate (single-shot, contract-validated)
  - Determinism enforcement
  - Bundle emission with SHA-256 provenance

Phase 4 (future):
  - Attempt budgets & retry
  - Mutation of GenerationPlan
  - Scoring hooks & coach feedback ingestion
"""
__version__ = "0.1.0"
