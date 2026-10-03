#!/usr/bin/env bash
set -euo pipefail
if [[ ${BIGARRAY_OFFLINE:-0} == 1 ]]; then
    python3 - <<'PY'
import socket
assert all(name == 'lo' for _, name in socket.if_nameindex()), 'offline namespace has a network interface'
PY
    exec "$@"
fi
export BIGARRAY_OFFLINE=1
if [[ $(id -u) == 0 ]]; then
    exec unshare --net -- bash "$0" "$@"
fi
task_env=()
for name in OPAMSWITCH OPAMJOBS OPAMYES OCAML_VERSION CLIENT_PREFIX CLIENT_WORK \
    REPORT_DIR TRACE_REPLAY TRACE_TEST_FAULT TRACE_COUNT BROWSER_ENGINE \
    EXTENDED_TRACE_ONLY; do
    if [[ -v $name ]]; then
        task_env+=("$name=${!name}")
    fi
done
exec sudo -n unshare --net -- setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups -- \
    env BIGARRAY_OFFLINE=1 HOME="$HOME" PATH="$PATH" OPAMROOT="${OPAMROOT:-$HOME/.opam}" \
    "${task_env[@]}" bash "$0" "$@"
