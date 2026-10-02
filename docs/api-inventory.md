# Versioned API inventory

`api/<version>.mli` records every upstream declaration, its full type and
primitive spelling. All five files come from commit- and SHA-256-locked
OCaml sources in `tools/oracles.lock.json`. Primitive declarations are an
inventory; the Melange interface will expose ordinary `val` declarations.

| Version | Kinds | API differences |
| --- | --- | --- |
| 4.14.4 | 13 | No Float16 type, constructor or value |
| 5.2.1 | 14 | Adds Float16; same array operations |
| 5.3.0 | 14 | Same declarations as 5.2.1; documentation corrections |
| 5.4.1 | 14 | Interface byte-identical to 5.3.0 |
| 5.5.1 | 14 | Interface byte-identical to 5.3.0 |

All versions expose Array0–3, Genarray, create/init, inspection, access,
fill/blit, constructors, sub/slice, layout change, specialized/generic
conversions and reshape. Unsafe access is exposed only by Array1–3.
Char uses the standard int8_unsigned_elt phantom. Array types declare all
three parameters injective. Layout/element phantom types retain their
standard constructors. Genarray ranks are 0–16; rank zero has one element.
Fortran coordinates start at one, with the first axis varying fastest.
C coordinates start at zero, with the last axis varying fastest.

Slice fixes leading C axes or trailing Fortran axes. Sub chooses the leading
C axis or trailing Fortran axis. Views, reshape and change_layout share
storage; layout changes reverse dimensions. Initializers iterate in physical
order. Nested constructors reject ragged shapes, even on an empty inner axis.
Blit checks rank/shape and uses memmove; kind/layout compatibility follows
from the typed signature. Fill/blit operate on the view extent only.

Float16 writes narrow via float32 before half, with ties-to-even. Native
conversion may use hardware or software, selected by the host build. NaN
payloads are not portable. 5.5.1 runtime includes checked reshape products;
regressions must also run against older versions with bounded requests.
Comparison sorts kind/layout and rank in reverse numeric order, then dimensions
and physical values lexicographically; unordered float equality requires
separate NaN tests. Generic runtime hooks and Marshal are outside V1.

The library's proposed 0x3fffffff byte ceiling and 32-bit Int/Nativeint are
explicit differences. Owned JavaScript buffers initialize to zero, while
native uninitialized contents are excluded from comparisons. Empty shapes
validate every dimension but avoid multiplying nonzero axes. Allocation
exhaustion is a runtime error, not a promise that the ceiling is allocatable.
