# Source and license provenance

The implementation is newly written, under MIT. No sibling implementation
files have been copied.

`api/*.mli` transcribes the complete upstream declarations, including native
primitive names, for inventory only. OCaml is LGPL-2.1 with its linking
exception; upstream copyright and license are retained under `licenses/`.
Oracles are downloaded to `.cache/oracles` using `tools/oracles.lock.json`.
Every download is pinned to a source commit and checked by SHA-256.
js_of_ocaml 6.4.1 is LGPL-2.1-or-later with its linking exception. Its runtime is a
verification reference, not a library runtime dependency. Melange compiler
source is inspected to characterize rejected primitives, not imported.

The GitHub repository and opam package directory were absent at lookup on
2026-10-02. The new GitHub repository now reserves the repository name;
opam submission remains a separate action.
