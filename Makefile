# Makefile for Smart Guitar Lab Pack Release
# Provides local verification targets for release asset validation

# -------------------------------------------------------------------
# Attestation policy verification (local / release assets)
#
# Usage:
#   make verify-policy \
#     ASSETS=release-assets \
#     REPO=OWNER/REPO \
#     TAG=v1.2.3
#
# Defaults:
#   ASSETS=release-assets
#   REPO is inferred from git if possible
#   TAG must be provided
# -------------------------------------------------------------------

ASSETS ?= release-assets
REPO ?= $(shell git remote get-url origin 2>/dev/null | sed -E 's#.*github.com[:/](.+)/(.+)(\.git)?#\1/\2#')
TAG ?=

.PHONY: verify-policy
verify-policy:
	@if [ -z "$(TAG)" ]; then \
	  echo "ERR: TAG is required (e.g. make verify-policy TAG=v1.2.3)"; \
	  exit 2; \
	fi
	@if [ ! -d "$(ASSETS)" ]; then \
	  echo "ERR: ASSETS directory not found: $(ASSETS)"; \
	  exit 2; \
	fi
	@if ! command -v gh >/dev/null 2>&1; then \
	  echo "ERR: gh CLI not found"; \
	  exit 2; \
	fi
	@echo "== Attestation policy verification =="
	@echo "Assets dir : $(ASSETS)"
	@echo "Repo       : $(REPO)"
	@echo "Tag        : $(TAG)"
	@echo

	@echo "-- Verifying Lab Pack ZIP policy --"
	@python scripts/release/attestation_policy_engine.py \
	  --subject "$(ASSETS)/Lab_Pack_SG_*.zip" \
	  --repo "$(REPO)" \
	  --tag "$(TAG)" \
	  --policy scripts/release/attestation_policy.json \
	  --schema scripts/release/attestation_schema_min.json \
	  --profile lab_pack_zip \
	  --attestation-type provenance

	@echo
	@echo "-- Verifying verifier policy (if present) --"
	@for f in \
	  $(ASSETS)/verify_release.sh \
	  $(ASSETS)/verify_release.ps1 \
	  $(ASSETS)/verify_attestations.sh ; do \
	  if [ -f "$$f" ]; then \
	    echo "Policy check: $$(basename $$f)"; \
	    python scripts/release/attestation_policy_engine.py \
	      --subject "$$f" \
	      --repo "$(REPO)" \
	      --tag "$(TAG)" \
	      --policy scripts/release/attestation_policy.json \
	      --schema scripts/release/attestation_schema_min.json \
	      --profile verifiers \
	      --attestation-type provenance ; \
	  fi \
	done

	@echo
	@echo "POLICY OK: all checked artifacts satisfy release policy"

.PHONY: help
help:
	@echo "Smart Guitar Lab Pack - Local Verification Targets"
	@echo ""
	@echo "Available targets:"
	@echo "  verify-policy    Verify release assets against attestation policy"
	@echo ""
	@echo "Usage:"
	@echo "  make verify-policy TAG=v1.2.3 [ASSETS=release-assets] [REPO=OWNER/REPO]"
	@echo ""
	@echo "Example:"
	@echo "  # Download release assets"
	@echo "  mkdir -p release-assets"
	@echo "  gh release download v1.2.3 --dir release-assets"
	@echo ""
	@echo "  # Verify policy compliance"
	@echo "  make verify-policy TAG=v1.2.3"
