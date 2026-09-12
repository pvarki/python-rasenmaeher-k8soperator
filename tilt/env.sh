#!/usr/bin/env bash
# Shared settings for the local cluster and registry lifecycle scripts.
export KIND_EXPERIMENTAL_PROVIDER="${KIND_EXPERIMENTAL_PROVIDER:-podman}"
case "${KIND_EXPERIMENTAL_PROVIDER}" in
  docker|podman) ;;
  *) echo "KIND_EXPERIMENTAL_PROVIDER must be docker or podman" >&2; exit 1 ;;
esac
export RUNTIME="${KIND_EXPERIMENTAL_PROVIDER}"
export CLUSTER_NAME="rmk8soperator"
# Keep the existing name so upgrades reuse the registry and its cached images.
export REGISTRY_NAME="ctlptl-registry"
export REGISTRY_PORT="5005"
