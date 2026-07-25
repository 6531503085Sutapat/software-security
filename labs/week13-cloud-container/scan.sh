#!/usr/bin/env bash
# Sandbox/teaching only; for authorized lab use.
#
# Week 13 — Cloud & container misconfiguration scanning with Trivy.
#   1) trivy config  — scans Dockerfiles for misconfigurations (does NOT parse standalone IAM policy JSON — review that manually)
#   2) trivy image   — scans a built image for CVEs (optional)
# All in throwaway containers (--rm). Idempotent — re-run freely.
#
# OWASP 2025 A02 Security Misconfiguration · CWE-732 / CWE-16.

set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${1:-week13-hardened:lab}"

echo "==> [1/2] trivy config — IaC / Dockerfile / IAM misconfiguration scan"
# Expected output: many findings against Dockerfile.insecure (root user,
# latest tag, secrets in ENV, 777 perms). Dockerfile.hardened should be
# clean (or near-clean). Trivy's config scanner does not parse standalone
# AWS IAM policy JSON, so iam-policy-insecure.json / iam-policy-leastpriv.json
# are NOT scanned here — review those manually (see worksheet Task 2).
# Use --severity to focus the class discussion.
docker run --rm -v "$HERE:/src" aquasec/trivy:latest \
  config --severity HIGH,CRITICAL /src || true

echo
echo "==> [2/2] trivy image — CVE scan of the hardened image (optional)"
# Build first:  docker build -f Dockerfile.hardened -t $IMAGE .
# Expected: distroless base yields far fewer findings than a full base image.
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy:latest image --severity HIGH,CRITICAL "$IMAGE" || true
else
  echo "    (image '$IMAGE' not built yet —"
  echo "     run: docker build -f Dockerfile.hardened -t $IMAGE . )"
fi

echo
echo "==> Done. See harden.md for the misconfig -> fix mapping."
