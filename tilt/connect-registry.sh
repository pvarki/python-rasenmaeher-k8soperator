#!/usr/bin/env bash
# Run by task cluster:up from tilt/. This is the wiring kind does not manage:
# https://kind.sigs.k8s.io/docs/user/local-registry/
set -euo pipefail
runtime="${KIND_EXPERIMENTAL_PROVIDER:?Run task cluster:up}"

connected="$("${runtime}" inspect -f '{{with index .NetworkSettings.Networks "kind"}}true{{end}}' rmk8soperator-registry)"
if [[ "${connected}" != true ]]; then
  "${runtime}" network connect kind rmk8soperator-registry
fi

nodes="$(kind get nodes --name rmk8soperator)"
for node in ${nodes}; do
  "${runtime}" exec "${node}" mkdir -p /etc/containerd/certs.d/localhost:5005
  "${runtime}" exec -i "${node}" cp /dev/stdin /etc/containerd/certs.d/localhost:5005/hosts.toml < registry-hosts.toml
done
