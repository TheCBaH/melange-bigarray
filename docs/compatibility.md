# Compatibility gate decisions

Dune's public library names follow the opam package prefix: select
`melange-bigarray` or `melange-bigarray.compat`. The OCaml module is
`Melange_bigarray`. The latter library exposes an unwrapped `Bigarray` alias
for a rebuilt dependency graph. It is opt-in and does not provide native
Stdlib.Bigarray type identity. Melange 7 does not export Stdlib.Bigarray;
explicitly qualified sources need an explicit source patch.

Bigarray rank 1–4 indexing syntax resolves to ordinary get/set functions with
a lexical alias or the compatibility provider. Separate compilation and
installed artifacts are tested outside the package build directory.

Melange 7 has no standard Nativeint module and rejects `n` literals. Use
`Melange_bigarray.Nativeint.of_int` and its typed primitive-backed operations.
The helper preserves the standard nativeint type and Melange's 32-bit
representation without Obj.magic. Unsupported literals are a required
negative test. Native applications keep using Stdlib.Nativeint.

The 4.14 interface omits Float16 entirely; generation selects the type,
constructor and value on OCaml 5.x. Both interfaces are backed by the full in-memory implementation and required
differential/runtime checks.
