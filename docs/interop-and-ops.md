# Interop and explicit operations

`Interop.import_copy kind layout dimensions value` accepts a JavaScript typed
array and copies its raw bytes. `import_shared` aliases that array's fixed
ArrayBuffer. `export_copy` returns a fresh typed array; `export_shared` returns
a typed view over exactly the Bigarray view's extent. Use ordinary Melange
FFI to consume the abstract `typed_array` result. Dimensions are copied.

Storage types are Float32Array/Float64Array, signed/unsigned 8/16-bit arrays,
Int32Array for Int32/Int/Nativeint, and Uint8Array for Char. Int64 uses paired
Int32 lanes in low-word/high-word order; complex values use paired float lanes
in real/imaginary order; Float16 uses Uint16 bit patterns. Lane count and
element alignment must match the requested dimensions/kind exactly.

Imports validate intrinsic typed-array slots, including cross-realm arrays
and Node Buffer, and reject proxies, spoofed tags, DataView, wrong types,
misaligned lanes, wrong lengths, detached buffers, SharedArrayBuffer and
resizable ArrayBuffer. There is no worker/shared-memory contract. Storage is
limited to 0x3fffffff bytes; dimensions are integers in 0..0x7fffffff, rank 0–16.

Sharing marks all existing aliases of the buffer for detachment checks. After
detachment, content access, mutation, views, copies and Ops raise
Invalid_argument, including for empty arrays. Metadata inspection remains
available. Owned arrays avoid these buffer checks until their storage is
exported with sharing. Callers must not mutate shared storage during an Ops
operation or while a value is a hash-table key.

`Ops.equal` compares kind, layout, shape and physical-order values. NaN makes
equality false, including comparison with itself. Signed zeros compare equal.
`Ops.compare` follows native Bigarray metadata and total floating-point ordering,
including complex real then imaginary components. Hashes include metadata
and values, normalize zeros/NaNs and ignore backing-buffer size, view offset
and ownership. Equal values have equal hashes for the same seed. Numeric hash
identity with OCaml/jsoo or across future releases is not promised.

For a finite, immutable key:

```ocaml
module Key = struct
  type t = (float, Melange_bigarray.float64_elt,
            Melange_bigarray.c_layout) Melange_bigarray.Genarray.t
  let equal = Melange_bigarray.Ops.equal
  let hash = Melange_bigarray.Ops.hash
end
module Table = Hashtbl.Make(Key)
```

Generic `(=)`, `compare` and `Hashtbl.hash` inspect the descriptor, not the
logical Bigarray value. The installed reproducer `test/generic.ml` shows a
view and equal independent copy comparing unequal; hashes change on shared
export; generic NaN self-equality is true while Ops equality is false.
`Marshal.to_string` uses the unsupported `caml_output_value_to_string`
primitive; its negative client must fail compilation.
Node and Chromium audit outputs are retained in each compiler artifact.
No generic runtime hook is installed.

The installed dependency client rebuilds Bytesrw 0.3.0 from commit
347a5e9eaffb2f9b7015ea4aa13b98f959320b4a, including its formatting module.
Source and ISC license hashes are in `tools/oracles.lock.json`. The sole source
patch replaces `Printexc.register_printer printer` with `ignore printer`;
`clients.json` records its patched checksum. Upstream unused-variable warnings
are nonfatal. Melange warns about unsupported binary channel mode primitives;
only in-memory Slice/Reader and Bigarray conversion paths are claimed/tested.
This is a real dependency rebuild, not a port of all its channel APIs.
