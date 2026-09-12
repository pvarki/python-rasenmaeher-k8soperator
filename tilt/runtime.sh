#!/usr/bin/env bash
# One provider selection for kind, the registry, and Tilt's image builder.
set -euo pipefail

runtime="${KIND_EXPERIMENTAL_PROVIDER:-}"
if [[ -z "${runtime}" ]]; then
  case "$(uname -s)" in
    Darwin) runtime=podman ;;
    *) runtime=docker ;;
  esac
fi
case "${runtime}" in
  docker|podman) printf '%s\n' "${runtime}" ;;
  *) echo "KIND_EXPERIMENTAL_PROVIDER must be docker or podman" >&2; exit 1 ;;
esac
