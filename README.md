# Melange Bigarray

Portable numerical arrays for Melange, under development on `devel`.

The compiler/provider gate passes on OCaml 4.14.4, 5.2.1, 5.3.0, 5.4.1 and
5.5.1 with matching Melange 7.0.1 variants. Storage and complete Array0/Array1
are implemented; full multidimensional and extension APIs are still in progress.

Select Dune library `melange-bigarray`, then alias
`module Bigarray = Melange_bigarray` for ordinary `a.{...}` syntax.
Select `melange-bigarray.compat` consistently when rebuilding dependencies
using plain `Bigarray`. [Provider and Nativeint decisions](docs/compatibility.md).

All development and CI commands use the sshd-enabled devcontainer. Prepare with
`make deps`; run `make ci`. Native/jsoo/Melange traces include Node and pinned
Chromium and run in an enforced network namespace. `make test.stress` runs
10,000 generated traces. [Declared runtime differences](docs/differences.md).

[Source/license provenance](docs/provenance.md). Publication is separate from
implementation and verification; no V1 release is claimed yet.
