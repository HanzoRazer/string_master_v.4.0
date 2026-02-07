# Makefile for Smart Guitar Lab Pack Release
# Provides local verification targets for release asset validation

# -------------------------------------------------------------------
# Attestation policy verification (local / release assets)
#
# Usage:
#   make verify-policy TAG=vX.Y.Z [ASSETS=release-assets] [REPO=OWNER/REPO]
#   make gen-policy-receipts TAG=vX.Y.Z [ASSETS=release-assets] [REPO=OWNER/REPO]
#   make diff-policy-receipts OLD=old.canonical.json NEW=new.canonical.json
#
# Defaults:
#   ASSETS=release-assets
#   REPO is inferred from git if possible
#   TAG must be provided
# -------------------------------------------------------------------

ASSETS ?= release-assets
REPO ?= $(shell git remote get-url origin 2>/dev/null | sed -E 's#.*github.com[:/](.+)/(.+)(\.git)?#\1/\2#')
TAG ?=
OLD ?=
NEW ?=

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

.PHONY: verify-receipts
verify-receipts:
	@if [ ! -d "$(ASSETS)" ]; then \
	  echo "ERR: ASSETS directory not found: $(ASSETS)"; \
	  exit 2; \
	fi
	@if ! command -v cosign >/dev/null 2>&1; then \
	  echo "ERR: cosign not found (required for receipt verification)"; \
	  exit 2; \
	fi
	@echo "== Policy receipt verification =="
	@echo "Assets dir : $(ASSETS)"
	@echo

	@echo "-- Verifying policy receipt signatures --"
	@cd "$(ASSETS)" && \
	for r in *.receipt.json; do \
	  if [ -f "$$r" ]; then \
	    if [ ! -f "$${r}.sigstore.json" ]; then \
	      echo "ERR: Missing bundle: $${r}.sigstore.json"; \
	      exit 1; \
	    fi; \
	    cosign verify-blob --bundle "$${r}.sigstore.json" "$$r"; \
	    echo "✓ Receipt signature verified: $$r"; \
	  fi; \
	done

	@echo
	@echo "RECEIPTS OK: all policy receipts cryptographically verified"

.PHONY: gen-policy-receipts
gen-policy-receipts:
	@if [ -z "$(TAG)" ]; then echo "ERR: TAG required (TAG=vX.Y.Z)"; exit 2; fi
	@mkdir -p dist/receipts/runtime dist/receipts/canonical
	@python scripts/release/attestation_policy_engine.py \
	  --subject "$(ASSETS)/Lab_Pack_SG_*.zip" \
	  --repo "$(REPO)" \
	  --tag "$(TAG)" \
	  --policy scripts/release/attestation_policy.json \
	  --schema scripts/release/attestation_schema_min.json \
	  --profile lab_pack_zip \
	  --attestation-type provenance \
	  --canonicalize \
	  --receipt-runtime-out dist/receipts/runtime/policy_receipt_zip.runtime.json \
	  --receipt-canonical-out dist/receipts/canonical/policy_receipt_zip.canonical.json

.PHONY: diff-policy-receipts
diff-policy-receipts:
	@if [ -z "$(OLD)" ] || [ -z "$(NEW)" ]; then \
	  echo "Usage: make diff-policy-receipts OLD=old.canonical.json NEW=new.canonical.json"; exit 2; \
	fi
	@python scripts/release/diff_receipts.py "$(OLD)" "$(NEW)"

.PHONY: help
help:
	@echo "Smart Guitar Lab Pack - Local Verification Targets"
	@echo ""
	@echo "Available targets:"
	@echo "  verify-policy            Verify release assets against attestation policy"
	@echo "  verify-receipts          Verify policy receipt signatures with cosign"
	@echo "  gen-policy-receipts      Generate runtime + canonical receipts locally"
	@echo "  diff-policy-receipts     Compare canonical receipts (drift detection)"
	@echo ""
	@echo "Usage:"
	@echo "  make verify-policy TAG=v1.2.3 [ASSETS=release-assets] [REPO=OWNER/REPO]"
	@echo "  make verify-receipts [ASSETS=release-assets]"
	@echo "  make gen-policy-receipts TAG=v1.2.3 [ASSETS=release-assets] [REPO=OWNER/REPO]"
	@echo "  make diff-policy-receipts OLD=v1.2.2/canonical.json NEW=v1.2.3/canonical.json"
	@echo ""
	@echo "Example:"
	@echo "  # Download release assets"
	@echo "  mkdir -p release-assets"
	@echo "  gh release download v1.2.3 --dir release-assets"
	@echo ""
	@echo "  # Verify policy compliance"
	@echo "  make verify-policy TAG=v1.2.3"
	@echo ""
	@echo "  # Verify cryptographic receipt signatures"
	@echo "  make verify-receipts"
	@echo ""
	@echo "  # Compare canonical receipts for policy drift"
	@echo "  mkdir -p v1.2.2 v1.2.3"
	@echo "  gh release download v1.2.2 --pattern 'policy_receipt_zip.canonical.json' --dir v1.2.2"
	@echo "  gh release download v1.2.3 --pattern 'policy_receipt_zip.canonical.json' --dir v1.2.3"
	@echo "  make diff-policy-receipts OLD=v1.2.2/policy_receipt_zip.canonical.json NEW=v1.2.3/policy_receipt_zip.canonical.json"
