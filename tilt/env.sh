#!/usr/bin/env bash
# Shared settings for the local cluster and registry lifecycle scripts.
KIND_EXPERIMENTAL_PROVIDER="$(bash "$(dirname "${BASH_SOURCE[0]}")/runtime.sh")"
export KIND_EXPERIMENTAL_PROVIDER
export RUNTIME="${KIND_EXPERIMENTAL_PROVIDER}"
export CLUSTER_NAME="rmk8soperator"
# Keep the existing name so upgrades reuse the registry and its cached images.
export REGISTRY_NAME="ctlptl-registry"
export REGISTRY_PORT="5005"
