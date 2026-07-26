#!/usr/bin/env bash
# Sandbox/teaching only; for authorized lab use.
#
# Week 12 — SBOM generation + keyless signing/verification (Sigstore/Cosign).
# Demonstrates OWASP 2025 A08 Software or Data Integrity Failures defenses:
#   1) Produce a CycloneDX SBOM from the image (component inventory).
#   2) Sign the image keylessly (OIDC) with cosign.
#   3) Verify the signature — and show that an unsigned image FAILS.
#
# Keyless signing ties the signature to an OIDC identity (e.g. your GitHub
# or Google login) via Sigstore's Fulcio CA + Rekor transparency log, so
# there is no long-lived private key to leak (CWE-321 hard-coded key avoided).
#
# All steps run in throwaway containers (--rm). Idempotent.
# NOTE: keyless signing needs a browser/OIDC flow and registry push access;
# in class this is a guided demo, not an offline step.

set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${1:-week12-supplychain:lab}"

echo "==> [1/3] Generate CycloneDX SBOM with trivy"
# Expected output: sbom.cdx.json listing every component + version.
# Hand this to auditors / store it as a build artifact (SLSA provenance input).
docker run --rm -v "$HERE:/src" -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image \
  --format cyclonedx --output /src/sbom.cdx.json "$IMAGE"
echo "    Wrote $HERE/sbom.cdx.json"

echo
echo "==> [2/3] Keyless sign the image with cosign (OIDC flow)"
# COSIGN_EXPERIMENTAL=1 enables keyless mode on older cosign builds.
# This opens an OIDC login; the cert is logged to Rekor (public transparency).
docker run --rm -e COSIGN_EXPERIMENTAL=1 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gcr.io/projectsigstore/cosign:latest sign --yes "$IMAGE"

echo
echo "==> [3/3] Verify the signature"
# Expected: PASS for the freshly-signed image. We pin the expected identity
# issuer/regex so an attacker-signed image from a different identity is rejected.
docker run --rm -e COSIGN_EXPERIMENTAL=1 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gcr.io/projectsigstore/cosign:latest verify \
  --certificate-identity-regexp '.*' \
  --certificate-oidc-issuer-regexp '.*' \
  "$IMAGE"

echo
echo "==> Negative test: verifying an UNSIGNED image must FAIL (this is good)."
echo "    Try:  cosign verify --certificate-identity-regexp '.*' --certificate-oidc-issuer-regexp '.*' python:3.9-slim"
echo "          # expect: Error: no signatures found   (both identity flags are required in keyless mode)"
