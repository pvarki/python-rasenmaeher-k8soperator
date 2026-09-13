#!/usr/bin/env bash
# Wait until the fail-closed Group webhook answers through its Service.
# Pod readiness only proves the listener is up: kube-proxy rejects Service
# traffic until the new endpoint is programmed, so the first Group write can
# still fail with "connection refused". A server-side dry run exercises the
# same admission path without creating anything.
set -euo pipefail

CONTEXT="${KIND_CONTEXT:-kind-rmk8soperator}"
TIMEOUT="${WEBHOOK_TIMEOUT:-120}"
DEADLINE=$((SECONDS + TIMEOUT))

probe() {
  kubectl --context "${CONTEXT}" apply --dry-run=server -f - <<'YAML'
apiVersion: platform.opendefence.fi/v1alpha1
kind: Group
metadata:
  name: webhook-probe
spec:
  name: webhook-probe
  displayName: Webhook probe
YAML
}

while ! output="$(probe 2>&1)"; do
  if ((SECONDS >= DEADLINE)); then
    printf '%s\n' "${output}" >&2
    echo "Group admission webhook did not answer within ${TIMEOUT}s" >&2
    exit 1
  fi
  sleep 2
done
