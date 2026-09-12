#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=tilt/env.sh
source "${SCRIPT_DIR}/env.sh"

"${RUNTIME}" info >/dev/null
case "${1:-}" in
  up)
    if "${RUNTIME}" container inspect "${REGISTRY_NAME}" >/dev/null 2>&1; then
      "${RUNTIME}" start "${REGISTRY_NAME}" >/dev/null
    else
      "${RUNTIME}" run -d --restart=always \
        -p "127.0.0.1:${REGISTRY_PORT}:5000" \
        --name "${REGISTRY_NAME}" docker.io/library/registry:3
    fi
    ;;
  down)
    if "${RUNTIME}" container inspect "${REGISTRY_NAME}" >/dev/null 2>&1; then
      "${RUNTIME}" rm -f "${REGISTRY_NAME}"
    fi
    ;;
  *) echo "Usage: $0 up|down" >&2; exit 1 ;;
esac
