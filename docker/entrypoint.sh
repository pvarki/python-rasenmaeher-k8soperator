#!/bin/bash -l
set -e
if [ "$#" -eq 0 ]; then
  exec rmk8soperator run
fi
case "$1" in
  manifests|install|run)
    exec rmk8soperator "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
