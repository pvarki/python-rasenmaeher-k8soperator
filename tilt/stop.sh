#!/usr/bin/env bash
# Tilt's "down" deletes resources but does not stop its server process.
# Use Tilt's own session metadata to identify this checkout's local process.
set -euo pipefail

if ! session="$(tilt get session Tiltfile --host 127.0.0.1 --port "$2" \
  -o jsonpath='{.spec.tiltfilePath}{"\n"}{.status.pid}' 2>&1)"; then
  case "${session}" in
    *"No tilt apiserver found"*|*"connection refused"*) exit 0 ;;
    *) printf '%s\n' "${session}" >&2; exit 1 ;;
  esac
fi

tiltfile="${session%$'\n'*}"
pid="${session##*$'\n'}"
if [[ "${tiltfile}" != "$1" ]]; then
  echo "Tilt on port $2 belongs to ${tiltfile}; stop it there or use a different TILT_PORT." >&2
  exit 1
fi
if [[ ! "${pid}" =~ ^[0-9]+$ ]] || (( pid <= 1 )); then
  echo "Tilt reported an invalid process ID: ${pid}" >&2
  exit 1
fi

echo "Stopping Tilt (PID ${pid}) on port $2"
kill -TERM "${pid}"
