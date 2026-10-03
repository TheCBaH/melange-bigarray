# Performance measurements and review budgets

Run `make bench` in the development container. Each installed-library workload
has one warmup and seven samples; report the median process CPU time. Native,
js_of_ocaml and Melange share the OCaml workload. Direct typed-array controls
run in the same Node engine; the Int64 control sums paired lanes without
allocating the public Int64 representation. Thus ratios include API/boxing cost.

JavaScript backends and the typed-array control use Node's `process.cpuUsage`;
native uses `Sys.time`. Every result identifies its CPU clock. Use the
`bench.json` artifact for the exact verified source/toolchain;
reports predating the `clock` field used mixed clocks and do not establish a
CPU baseline. Compiler rows include hardware and seven samples per workload.

Scalar/numeric/Int64/complex use 1,000,000 accesses; views use 100,000;
fill/blit process 1,000 × 65,536 Float64 elements. Every result includes
bytes processed, peak child RSS, architecture/CPU information, compiler/Node
versions and source SHA. JavaScript entry sizes exclude imports; standalone
minified and gzip bundle sizes include the benchmark, provider and runtime.
CPU metadata may be masked by the host; raw available cpuinfo is retained.

Budgets are review triggers against a baseline on the **same** hardware and
toolchain: a median slowdown over 25%, peak RSS increase over 20%, or standalone
bundle increase over 10% needs an explanation and a repeated measurement.
Absolute cross-host timing is not a CI pass/fail claim. Hard subprocess and
heap limits still fail hung/runaway benchmarks. No performance optimization
has been accepted solely to improve a benchmark: each future change must
rerun the independent semantics suite. These numbers imply no BLAS throughput.
