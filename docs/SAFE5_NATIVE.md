# Safe 5 native capacity experiment

Updated 2026-09-10 UTC. The complete synthetic native signing slice now links for
**Safe 5 T3T1/U585**, with **27,136 bytes of flash headroom** in the latest measured
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
| Also select the supported secp256k1 2 KiB signing table | 1,676,288 B | 27,648 B free; stack gate remains |
| Also reserve 48 KiB stack and use static split GC | 1,676,800 B | 27,136 B free; runtime gates remain |

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
A compressed Sinsemilla table has passed host comparisons but remains a separate
unaccepted alternative with no native image measurement.

The later inlining experiment reduces the sign entry's local frame from 8,864 to
3,424 bytes. It does not close validation's stack gate: a selected five-function
ordinary-call chain totals **37,184 bytes**, above the 32,768-byte reservation,
before C/VM callers and further callees. This is a static frame subtotal, not a
whole-stack bound or observed overflow. Call-path/state and live-frame analysis
remain necessary. No stack reservation was enlarged to obtain these results.

## Additional flash margin

The latest native build replaces the unused `ECMULT_GEN_PREC_BITS=2` define with
the pinned upstream 2 KiB configuration, `COMB_BLOCKS=2` and `COMB_TEETH=5`.
Arithmetic, context layout, blinding, modules and verification window are unchanged.
The actual image saves **20,480 bytes**, with a single 2,048-byte signing table.
All six arithmetic/table/Trezor-wrapper compiler commands have matching settings;
the previous 22,528-byte linked table is retained as a positive control. Forty
static image/configuration checks pass, with unchanged kernel bytes, 32 KiB stack
and 109,264-byte GC region. This is a compile/link result, not target execution.

The ordinary upstream host suites pass 96 named cases per run in four runs: both
table sizes, with and without extra internal VERIFY assertions. These repeated
case counts do not claim 384 different tests. Host arithmetic and callbacks differ
from the MCU configuration; target functional, timing and leakage checks remain.
Fable5.1 and an independent clarity/source reviewer accepted the isolated experiment.
The shared wrapper change needs broader consumer testing before upstream promotion.

## Larger native stack and split GC

The latest native image reserves **49,152 bytes for stack**, **92,880 raw bytes
for the primary GC region**, and **41,696 raw bytes for the second GC region**.
The second region occupies the unused AUX1 tail after every existing reservation,
including the UI buffers. Metadata consumes part of each region; a single object
cannot use their summed capacity. The primary region is 16 KiB smaller than in
the preceding image. Maximum PCZT/response and transaction limits are unchanged.

The four-file patch uses xbuild's existing linker selector and MicroPython's
existing `gc_add` API. It exports split=1/AUTO=0 consistently, registers the static
region directly after GC initialization, and retains the ordinary kernel, MPU,
executor/canary guards, 256-byte PSPLIM margin and 1 KiB Python stack margin.
Only the existing native experiment selects the derivative linker. The ordinary
linker is untouched. The native feature now requires pyopt so the existing
single-area debug memory inspector cannot silently omit the second heap.

The real compile/link passed in 38.88 seconds. **34 static image/configuration
checks pass**: disjoint slot placement, writable NOBITS secondary heap/arena,
unchanged kernel, actual 48 KiB Core header, all selected C macro settings, and
the machine-code order `gc_init` → `gc_add` → `mp_init`. Flash grows by 512 bytes.
An actual ARM C probe measures the area as 32 bytes and memory state as 564 bytes,
both aligned to four. A Rust probe fails E0432 because the selected generated
bindings omit both C-owned structures. An independent audit of the selected
bindings, 1,715 resolved target source/dependency files, assembly and 126 Rust
archives finds no changed state representation crossing this interface. The
requested size comparison therefore has no Rust counterpart; this is not a
functional ABI failure. The failed probe remains recorded, and no unnecessary
allowlist or handwritten structure was added. This closes only that specific
structure-boundary concern, not rooting, general FFI or runtime safety. Exact
provenance and disposition are in `memory-next/abi-check/ABI_BOUNDARY.md`.

Three host processes using unchanged pinned vendored GC code pass cross-region
graph, collection/exhaustion/reuse and oversized-contiguous-allocation checks.
Addresses were checked against both observed regions. The audit now requires
their combined ranges to equal the independently printed GC total, rejecting
truncated abbreviated dumps. These are 64-bit Unix tests, with equal libc-backed
regions and ordinary conservative roots; they establish no MCU stack, DMA,
firmware reset or maximum-size PCZT/response lifetime result.

Fable5.1 reviewed the full layout and a separate pyopt/host-evidence follow-up;
independent clarity reviews covered both source revisions. The 48 KiB reservation
is still a measurement candidate, not a proven complete stack bound. Its source,
tests, review dispositions and linked evidence are under `memory-next/` in the
coordinator evidence directory. Two verifier preflights failed on the legitimate
zero-sized nonallocated TLS section; both remain recorded. Corrected inspection
checks its zero size and linker symbols explicitly; no firmware changed for it.

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
| Latest compact-secp ELF | `ac8acf06e07ccd254b1218e048b652b45fac6369e0782bcfb4f74755ccc31979` |
| Latest compact-secp map | `92b8be17b8aea37a26ae258c7dc8c724940b6ddec8bd3fae65dfeb7a40a17d64` |
| Latest split-GC ELF | `ab110d7e1709c4e3b28f6042226c489a738b1d5819f42ad546ee9b59d1452c12` |
| Latest split-GC map | `28d7481aa6c42ae64b4c3dd1702ae3b65729c941d55d083f2172072f195049af` |
| Computed-S library source | `d757bc05f440d158de59c806ca35d6530215467376a467a36891398317580793` |
| Host differential transcript | `3824060fe8b80e0d83af221f4a2756e270cb8bcf5ffe5312373e10f599774ff2` |

Coordinator-local evidence is under `work/safe5-native/`: each `link-*` directory
has commands, full environment, source/protected hashes, log and frozen artifacts;
`linked-review/computed-s/` has independent image inspection;
`sinsemilla-compute/tests-work/` has host comparisons and retained failures.
No private key material or device data was collected. [Review dispositions](reviews/SAFE5_NATIVE.md)
separate accepted source/capacity evidence from unaccepted runtime behavior.

Next: finish the native layout/stack acceptance checks, then the Safe 5 emulator trusted review and
legacy-wire flow. Physical tests follow a concrete reviewed image and an attended
installation decision; the unopened device remains untouched.

## Safe5 emulator build checkpoint

An independent copy of the retained Safe7 transport overlay now compiles the
T3T1 test emulator with Delizia and legacy wire. This uses the retained host
allocator/dependencies, not the native 48 KiB/split-GC configuration. Only the
reviewed exact model/layout/protocol guard changed; all 31,076 copied inputs were
rehashed after generation/build. The standard protobuf generation preserved
existing generated files. Compile completed in 209.42 seconds without execution.
Binary SHA256: `b028f7002a402ffc5c8f1a816ac5f1512b611a3d7d8eb27751512bc97332c44b`.
Local evidence: `work/safe5-emulator-prep/build-03/` in the coordinator workspace.

The first wrapper attempt could not initialize a nested macOS sandbox. The second
reached protoc but could not open its inherited stdout descriptor. Both failed
attempts remain saved. The third uses the explicit offline sandbox with narrowly
allowed standard-output/error descriptors in addition to its owned directory;
network and other file writes remain denied. No generator or firmware code was
changed to bypass those failures. Cancellation/layout exploration is separate.

## Current stack path follow-up

The settled `ab110d7e…` image has a source-feasible parsing/FVK path totaling
42,016 bytes across twelve nested frames, including the C builtin entry. The
previous 37,184-byte five-Rust-frame subtotal omitted 4,832 bytes. The largest
frames are Engine.begin (13,984), bundle parsing (8,880) and action parsing
(8,032). Its nominal 7,136-byte gap to the 48 KiB reservation must still cover
interpreter callers, exceptions and other unresolved edges. No definite overflow
or sufficient margin is established. Cold table initialization, sighash and
verify_bundle are sequential paths and are not added to this subtotal. Frozen
source conditions, call addresses and frame metadata are retained in the owned
`work/safe5-stack-current/` report. No native execution occurred.

## Isolated parser boundary and first rendered exploration

The seven-line private parser-boundary experiment passed Fable5.1 and independent
clarity review for compile-only testing. The isolated image now links as
`0481ef96c34419a3538c1420d016f3292ba03d35d3dd0570d203f56a8e8066b0`.
Its bridge has a 5,408-byte frame and directly calls the separate 11,488-byte
decoder helper; Engine::begin no longer has a standalone symbol. This does not
mean Engine uses zero stack. Both complete live paths remain under examination.
The image occupies 1,675,776 flash bytes. A generated version-header difference
and relocated crate paths prevent attributing its 1,024-byte reduction solely
to the helper. This candidate is not adopted into the settled snapshot.

The first cold attempt failed after 703.64 seconds because protoc could not open
/dev/stdout in the host sandbox. An approved retry reused only the isolated partial
cache and succeeded in 155.90 seconds, within the original deadline. Source and
checked donor hashes remained unchanged. No firmware execution occurred.

The separate host emulator completed its first bounded receiver-menu exploration
in 16.82 seconds. Actual traces showed the synthetic context, payment amount,
complete 86-character raw receiver and Cancel menu. The menu touch did not reach
the confirmation screen before the five-second bound. No ActionCancelled or
signed response was observed. The driver recorded incomplete exploration and a
nonzero emulator exit; its log ends with KeyboardInterrupt. Supervisor cleanup
left no process-group survivor. These are preserved failures, not a cancellation
or clean-runtime pass. Final-hold exploration has not run.

Both driver source reviews and the independent parent readability dispositions
preceded this exploratory run. Corrections addressed transitions, receiver
pagination, evidence preservation and excessive screenshot hashing. Actual source
inspection corrected a shared reviewer misconception: DebugLink's constructor
already opens its transport; the added redundant open was removed. Fable did not
review the final corrected hash as a product-acceptance candidate.

[Follow-up result identities](../experiments/safe5-native/FOLLOWUP_RESULTS.json)
bind these claims to retained raw evidence. The coordinator's local harness and
logs are not yet a portable reproduction package. Physical hardware is untouched.

The subsequent selected-path comparison finds 31,504 semantic frame bytes and
32,408 decoding frame bytes in the candidate, versus 42,016 and 31,432 in the
baseline. The helper returns before the semantic call. The larger of those two
new subtotals is 9,608 bytes below the old semantic subtotal. Whole-program and
decoder maximum, runtime execution and a matched fresh control remain absent.

The menu's actual touch rectangle includes the original coordinate. Source and
timer evidence instead indicated a likely touch during the 350 ms attach lockout.
A fresh owned driver copy added one 400 ms wait after observing the menu; 13
offline preflight checks passed. The fresh receiver-menu run then displayed
"Cancel sign", received ActionCancelled after the confirming tap, and returned
home. A separate final-screen run observed no response to a 300 ms press through
the subsequent 2.3-second wait, then received ActionCancelled after host Cancel
and returned home. Durations were 7.53 and 12.36 seconds. Neither produced a
signed response. Both overall results remain failed because requested SIGINT
shutdown produced KeyboardInterrupt/exit 1. There were no process-group survivors.
Native sign-entry instrumentation and measured allocator cleanup remain missing.
The first failed attempt remains in its original directory, unmodified.
