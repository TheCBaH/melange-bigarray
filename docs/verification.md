# Independent verification

The required push/PR matrix selects OCaml 4.14.4, 5.2.1, 5.3.0, 5.4.1 and
5.5.1 with matching Melange 7.0.1 variants. `make ci` runs full interface
compilation, positive/negative installed syntax/provider clients, formatting,
independent differential tests, replay checks, benchmarks, source installation
and a pristine-tree check. All commands run inside the sshd-enabled container.

Native OCaml, js_of_ocaml 6.4.1 and Melange execute the same separately built
test sources. Node 24.19.0 and pinned Playwright Chromium execute both JS
backends. The oracle source/compiler/API licenses and SHA-256 hashes are locked.
Float16 tests exhaust all 65,536 decode patterns and selected rounding borders;
finite values, Int64 bits and signed zero are lossless in reports. Hand-written
goldens supplement oracle agreement. [Declared differences](differences.md).

Each normal run generates at least 1,000 vector and 1,000 matrix operation
sequences, covering every supported kind and both layouts, plus deterministic
rank 0–16, small-shape, ownership, error and complete API tests. The LCG seed is
0x13579bdf + id × 104729 in Int32 arithmetic. `inputs.json` retains ordered
bound/value random draws with source/tool hashes; `differential.json` records
counts, architecture, API coverage and limits. Native address space is capped
at 1 GiB, Node/Chromium heap at 256 MiB, each trace subprocess at 120 seconds,
and each trace payload at 16 MiB. Missing required engines/oracles fail.

On a generated mismatch, `failure.json` retains backend, observation, trace ID,
seed and inputs; the shrinker deletes operation effects while preserving RNG
draws, then reduces dimensions. It verifies the final failure again and retains
`minimized.json`, original/minimized metadata and replay reports. Replay with:

```
make test.offline TRACE_REPLAY=/absolute/path/minimized.json
```

Use the same compiler and source revision. Replay reports explicitly record
that one trace ran; they never substitute for the normal minimum-count gate.
`make test.replay` validates reduced shape/operation replay on every compiler.
The latest compiler additionally injects a lost write into the **test backend**,
checks its detection, then proves operation and shape shrinking. These artifacts
are labeled intentional fault/self-test, not an actual library failure.

`make test.stress` runs 10,000 sequences per family offline. Weekly extended
jobs use floor/latest compilers on AMD64 and ARM64 with Chromium, Firefox and
WebKit. Extended engine reports cover differential traces; required interop and
dependency clients remain Chromium checks. Extended results are separate from
the required support matrix; scheduling a job does not imply its success.
The first complete extended run passed all 12 jobs at `a78c462` on 2026-10-03:
[run 37089600888](https://github.com/TheCBaH/melange-bigarray/actions/runs/37089600888).
The run artifacts record the exact compiler, architecture and browser
versions.

`make test.install` archives the committed SHA, fetches the pinned opam metadata
revision, creates a fresh private root, builds its own matching OCaml compiler,
and installs exact Dune/Melange tools and the declared Python 3 build check. Package build/install and real
external clients then execute inside an enforced network namespace. Clients
compile in a separate directory using only installed package artifacts;
Explicit environment preservation and prefix/provider assertions also verify
the non-root sudo boundary. Loopback-only namespace checks prevent bypass.
Node and Chromium exercise the general client and rebuilt Bytesrw dependency.
No application checkout is present in the container. Source/member/license,
installed metadata/runtime closure and private-root package versions are
reported in `install.json`; the source tar is retained. The root is deleted
on success or failure. The normal toolchain and private-root source install
provide separate evidence.

Required CI artifacts are named `compatibility-<ocaml>`; reports are below
`<ocaml>/`. Read source cleanliness and exact SHA before citing a report.
Local dirty-tree development reports do not meet the promotion gate.
