# Declared oracle differences

| Boundary | Contract and test treatment |
| --- | --- |
| Int/Nativeint | Melange stores 32 bits; native host widths vary. Differential values use the shared 32-bit range. Separate Melange overflow probes assert the 32-bit contract. Byte sizes are checked against each backend's kind_size_in_bytes, not equated across widths. |
| Allocation | Melange rejects requests above 0x3fffffff bytes before allocation. Dedicated probes exercise rank/product/byte/view limits; native/jsoo never allocate these giant inputs. |
| Empty axes | Validate every dimension, then return zero without multiplying other axes. Slices follow native bounds checks and reject empty axes; zero-length subviews remain valid. Native older reshape overflow order is not a portable guarantee. |
| Uninitialized contents | Never observed; tests initialize every read element. Owned typed arrays are initially zero. |
| NaN payload | Float observation encodes all NaNs as `nan`; finite float and signed-zero encodings remain exact. Raw copies have separate byte-preservation tests. |
| Exceptions | Compare categories; retain original messages in stderr artifacts. Message spelling is not a portable API claim. |

No other normalization is applied to the differential reports. Every required
backend and browser must run; missing reports or unsupported required tools
fail verification. Current scalar traces use seed 0x13579bdf, at least 1,000
bounded operation sequences and a 16 MiB output budget per report.
