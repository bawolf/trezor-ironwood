# Safe 5 native capacity experiment

Updated 2026-09-10 UTC. The complete synthetic native signing slice now links for
**Safe 5 T3T1/U585**, with **7,168 bytes of flash headroom** in the measured
configuration. No firmware or physical device execution occurred. Stack safety,
concurrent heap use, latency and trusted Safe 5 transport/UI remain open.

## Measured sequence

All attempts use firmware `7105338e3c2c1e681940e17780609881ce53126b`, the unchanged
matching Safe 5 test kernel, Arm GNU 13.3.Rel1, nightly-2026-03-16, universal coin
support, release size optimization/LTO and frozen dependencies. The flash slot is
1,703,936 bytes. Failed links retain their maps and logs; they are not firmware.

| Configuration | Full flash extent | Result |
| --- | ---: | --- |
| Unchanged test baseline | 1,588,736 B | 115,200 B free |
| Retained native core, original test settings | 1,859,072 B | 155,136 B overflow |
| Native + `pyopt`, Rust `debug` still enabled | — | Compile failure: two missing debug qstrs |
| `pyopt`, Rust `debug` off, native feature off | 1,554,432 B | 149,504 B free; paired control |
| Same configuration with native core | 1,824,256 B | 120,320 B overflow |
| Existing upstream small-processor crypto features | 1,783,296 B | 79,360 B overflow |
| Also omit debug-link and optional UI diagnostics | 1,762,816 B | 58,880 B overflow |
| Compute Sinsemilla S points instead of table lookup | 1,696,768 B | 7,168 B free |
| Also apply the two reviewed stack inlining attributes | 1,696,768 B | 7,168 B free; stack gate remains |

These are distinct recorded configurations, not one unchanged-test-preset result.
`pyopt` removes Python debug/logging/test modules and debug protobufs, selects
mpy-cross O3 and removes the diagnostic OOM callback. The Rust `debug=false`
correction is required because the pinned generated translation table otherwise
references qstrs excluded by `PYOPT`. Production remains false; synthetic test
keys, RNG and the native experiment guards remain. No coin family, PCZT bound,
validation, flash boundary, MPU or stack-limit enforcement was removed.

The small-code features are upstream `blake2b_simd/uninline_portable` and
`pasta_curves/uninline-portable`. They remove inlining hints from existing
arithmetic; versions/checksums and function bodies remain unchanged. One optional
direct dependency enables the already-transitive Blake2b feature only when the
native experiment is selected. Feature unification applies across the build.

## What the linked image establishes

An independent reviewer and parent checked frozen artifacts. All 45 static image
checks pass for the first computed-S link. The allocated sections fit and are
disjoint; every file-backed LOAD payload is within the real firmware flash slot.
The parent independently derives the full extent from ELF program headers,
including headers and the initialized-data load. The original baseline also has
an RWX flash LOAD segment; this is not attributed as a new regression here.

- The 131,104-byte guarded arena is aligned inside AUX2 `.buf`, allocated writable
  NOBITS, with no file-backed payload. A zero-file-size LOAD is permitted.
- Stack remains 32,768 bytes. GC occupies `[0x3006d130, 0x30087c00)`, **109,264 B**,
  following all buffers and excluding the arena and stack. This is capacity only.
- Embedded kernel bytes exactly match both the baseline firmware and kernel ELF.
- The builtin module registry reaches the actual begin/sign/cancel wrappers and
  Rust bridge. Executor context gates, atomic operations and canaries remain.
- The original 65,536-byte S table is absent from allocated bytes, with an old
  image positive control and scans for all 2,048 coordinate strings.

The native module remains callable from trusted Python, and its sign operation
internally approves a matching token. There is no frozen Python/boot/wire caller
in this image. That is an unfinished integration boundary, not a production
consent mechanism. No signed binary was generated or flashed.

## Equivalence, speed and stack

The computed-S patch replaces only the table lookup with the same upstream
hash-to-curve generator used by Sinsemilla's exhaustive table test. The index is
u32 encoded as four little-endian bytes. Padding, limits, domains, incomplete
addition, CtOption failures and commitment blinding are retained. A boxed hasher
is created once per invocation after padding, including empty input; this adds
an allocation/failure opportunity and changes arithmetic work and leakage traces.

Host comparison passed **8,056 public-output checks over 2,014 messages**, 16
invalid-length API pairs and nine forced incomplete-addition pairs. Both original
and candidate separately pass the two unchanged upstream tests, including all
1,024 generator comparisons. Shared registry versions/checksums match native
pins, with both small-processor features enabled. The host is 64-bit ARM, release
opt3; these are not 32-bit MCU results or firmware stack/allocator measurements.

The current dependency combination and both stack attributes also pass all
**36 approval conformance tests**, the existing bridge lifecycle test, and three
independent-oracle negative tests. The independent oracle verified two fresh
bridge responses with three new real-spend signatures. Its 15-file report also
contains 13 reused controls; those are not new signing coverage. Test bodies and
fixtures are unchanged, and all 128 shared native registry pins/checksums match.
These host tests cover tampering, consent replay, entropy failure, cancellation,
ABI/input/output bounds and independence from caller storage. They do not measure
MicroPython GC lifetimes or native stack usage. Exact commands, source manifests,
pin checks, failures and accepted results are retained in
`sinsemilla-compute/conformance-work/` under the local evidence root below.

For 2,530-bit messages, warmed host means were 554 µs versus 8,705 µs for hash and
555 µs versus 9,156 µs for commit: about **16× slower**. One additional 16-byte
host allocation was observed per hash invocation, with balanced frees. MCU
latency, stack high-water, allocation failures and physical leakage remain gates.
A compressed table and the pinned secp256k1 small-comb configuration are separate
unaccepted alternatives under investigation; neither is part of this image.

The later inlining experiment reduces the sign entry's local frame from 8,864 to
3,424 bytes. It does not close validation's stack gate: a selected five-function
ordinary-call chain totals **37,184 bytes**, above the 32,768-byte reservation,
before C/VM callers and further callees. This is a static frame subtotal, not a
whole-stack bound or observed overflow. Call-path/state and live-frame analysis
remain necessary. No stack reservation was enlarged to obtain these results.

## Evidence and source delivery

The [source package](../experiments/safe5-native/README.md) supplies the complete
native firmware patch, synthetic bridge and fixtures, dependency patch and stack
attribute patch. Its manifests bind the exact sources. Full clean-checkout build
reproduction and the complete portable runtime harness remain outstanding; this
is not yet an upstream-ready submission.

| Artifact | SHA-256 |
| --- | --- |
| First computed-S ELF | `34b3ad14943383eee84ed4aaf8bf704cb473e489b4b273faa708d39daaa18983` |
| First computed-S map | `bdeb3148af2f4907a95a69f2286d0c1ffcbf1e0a35d4d038b55146d99a129d44` |
| Later stack-attribute ELF | `0e3504b2c6beebc6509d88db887ac893730b8cab8640c744d7843f914f1c0667` |
| Later stack-attribute map | `db79ec47bc17dd156e38c70bf42886f99a20468b5e49acfa7820efc0596989cd` |
| Computed-S library source | `d757bc05f440d158de59c806ca35d6530215467376a467a36891398317580793` |
| Host differential transcript | `3824060fe8b80e0d83af221f4a2756e270cb8bcf5ffe5312373e10f599774ff2` |

Coordinator-local evidence is under `work/safe5-native/`: each `link-*` directory
has commands, full environment, source/protected hashes, log and frozen artifacts;
`linked-review/computed-s/` has independent image inspection;
`sinsemilla-compute/tests-work/` has host comparisons and retained failures.
No private key material or device data was collected. [Review dispositions](reviews/SAFE5_NATIVE.md)
separate accepted source/capacity evidence from unaccepted runtime behavior.

Next: a viable stack/GC layout and additional flash margin, then the Safe 5 emulator trusted review and
legacy-wire flow. Physical tests follow a concrete reviewed image and an attended
installation decision; the unopened device remains untouched.
