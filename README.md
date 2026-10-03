# Melange Bigarray

[![ci](https://github.com/TheCBaH/melange-bigarray/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/TheCBaH/melange-bigarray/actions/workflows/ci.yml)
[![extended](https://github.com/TheCBaH/melange-bigarray/actions/workflows/extended.yml/badge.svg?branch=main)](https://github.com/TheCBaH/melange-bigarray/actions/workflows/extended.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/TheCBaH/melange-bigarray)

Portable in-memory numerical arrays for Melange: the versioned Bigarray API,
shared multidimensional views, typed-array interop and explicit comparison/hash.

Implemented for OCaml 4.14.4, 5.2.1, 5.3.0, 5.4.1 and 5.5.1 with matching
Melange 7.0.1 variants. Float16 is available on 5.x. The required runtime scope
is Node and Chromium; extended engine/platform evidence is tracked separately.
All five required CI rows pass, including independent source installs; a
revision is promoted only after the same checks pass. See
[verification](docs/verification.md).

Select Dune library `melange-bigarray` and alias
`module Bigarray = Melange_bigarray` for ordinary `a.{...}` syntax.
Select `melange-bigarray.compat` consistently when rebuilding dependencies
using plain `Bigarray`. [Provider/Nativeint decisions](docs/compatibility.md).

Arrays support ranks 0–16, C/Fortran layouts, every supported kind and contiguous
slice/sub/reshape/layout views. Storage is capped at 0x3fffffff bytes; Int and
Nativeint are 32-bit. There is no mmap, C/Fortran ABI, Marshal or worker/shared-
memory contract. Generic `(=)`, `compare` and hashing inspect the descriptor;
use `Ops` for array semantics. [Interop/Ops contract](docs/interop-and-ops.md).

Develop inside the sshd-enabled devcontainer. `make deps` prepares locked tools,
then `make ci` runs independent native/jsoo/Melange Node/Chromium tests,
installed clients, replay/shrink checks, benchmarks and fresh-root source
installation. `make test.stress` runs 10,000 bounded traces per family offline.
[Verification](docs/verification.md), [differences](docs/differences.md),
[measurements/budgets](docs/performance.md), [provenance](docs/provenance.md).

Tags, opam submission and npm publication remain separate delivery actions.
