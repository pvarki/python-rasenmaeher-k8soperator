#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=tilt/env.sh
source "${SCRIPT_DIR}/env.sh"

case "${1:-}" in
  up)
    clusters="$(kind get clusters)"
    if ! grep -Fxq "${CLUSTER_NAME}" <<<"${clusters}"; then
      kind create cluster --name "${CLUSTER_NAME}" \
        --config "${SCRIPT_DIR}/cluster.yaml" --wait 120s
    else
      kind export kubeconfig --name "${CLUSTER_NAME}"
    fi

    connected="$("${RUNTIME}" inspect -f '{{with index .NetworkSettings.Networks "kind"}}true{{end}}' "${REGISTRY_NAME}")"
    if [[ "${connected}" != "true" ]]; then
      "${RUNTIME}" network connect kind "${REGISTRY_NAME}"
    fi

    # Host pushes use localhost; node pulls must reach the registry container.
    nodes="$(kind get nodes --name "${CLUSTER_NAME}")"
    for node in ${nodes}; do
      registry_dir="/etc/containerd/certs.d/localhost:${REGISTRY_PORT}"
      "${RUNTIME}" exec "${node}" mkdir -p "${registry_dir}"
      "${RUNTIME}" exec -i "${node}" cp /dev/stdin "${registry_dir}/hosts.toml" <<EOF
[host."http://${REGISTRY_NAME}:5000"]
  capabilities = ["pull", "resolve"]
EOF
    done
    kubectl --context "kind-${CLUSTER_NAME}" apply -f "${SCRIPT_DIR}/registry.yaml"
    kubectl --context "kind-${CLUSTER_NAME}" wait --for=condition=Ready nodes --all --timeout=120s
    ;;
  down) kind delete cluster --name "${CLUSTER_NAME}" ;;
  *) echo "Usage: $0 up|down" >&2; exit 1 ;;
esac
