#!/usr/bin/env bash
set -euo pipefail

echo "Running local secret scans..."

# gitleaks (prefer local install) - fallback to docker
if command -v gitleaks >/dev/null 2>&1; then
  echo "Using local gitleaks"
  gitleaks detect --source=. --report-format=json --report-path=gitleaks-report.json || true
else
  echo "gitleaks not installed locally; using docker image"
  docker run --rm -v "$(pwd)":/src:z zricethezav/gitleaks:latest detect --source=/src --report-format=json --report-path=/src/gitleaks-report.json || true
fi

# detect-secrets
if command -v detect-secrets >/dev/null 2>&1; then
  detect-secrets scan > .secrets.baseline.new || true
  echo "detect-secrets scan written to .secrets.baseline.new"
else
  echo "detect-secrets not installed locally. Install with: pip install detect-secrets"
fi

echo "Reports: gitleaks-report.json, .secrets.baseline.new"
