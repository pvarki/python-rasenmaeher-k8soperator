#!/usr/bin/env bash
# Wait for the cert-manager CA Certificate and write PEM for --ca-file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${ROOT}/.certs"
CA="${CERT_DIR}/ca.crt"
NS="${CLOUDCOIL_NAMESPACE:-opendefence-system}"
CONTEXT="${KIND_CONTEXT:-kind-rmk8soperator}"

mkdir -p "${CERT_DIR}"
kubectl --context "${CONTEXT}" wait --for=condition=Ready \
  "certificate/operator-ca" "certificate/operator-tls" -n "${NS}" --timeout=180s
tmp="$(mktemp "${CERT_DIR}/ca.crt.XXXXXX")"
trap 'rm -f "${tmp}"' EXIT
kubectl --context "${CONTEXT}" get secret operator-ca -n "${NS}" \
  -o jsonpath='{.data.ca\.crt}' | base64 -d > "${tmp}"
if ! grep -q -- "-----BEGIN CERTIFICATE-----" "${tmp}"; then
  echo "operator-ca Secret is missing a PEM ca.crt" >&2
  exit 1
fi
if [[ -f "${CA}" ]] && cmp -s "${tmp}" "${CA}"; then
  exit 0
fi
mv "${tmp}" "${CA}"
trap - EXIT
