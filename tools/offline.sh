#!/usr/bin/env bash
set -euo pipefail
if [[ ${BIGARRAY_OFFLINE:-0} == 1 ]]; then
    exec "$@"
fi
export BIGARRAY_OFFLINE=1
if [[ $(id -u) == 0 ]]; then
    exec unshare --net -- "$@"
fi
exec sudo -n unshare --net -- setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups -- \
    env BIGARRAY_OFFLINE=1 HOME="$HOME" PATH="$PATH" OPAMROOT="${OPAMROOT:-$HOME/.opam}" "$@"
