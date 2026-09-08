# Safe 7 compile-only allocator link

A separate derivative of firmware pin
`7105338e3c2c1e681940e17780609881ce53126b` links the unchanged approval core into
the actual Safe 7 test-preset firmware. The final ELF retains validation, approval,
RedPallas signing and PCZT serialization code, and reserves an independent Rust
arena outside the MicroPython GC region. **The image was not executed. Its 4 KiB
arena is deliberately too small to run signing.**

This is a static integration experiment. Its synthetic boot hook uses fixed public
keys and RNG and automatically approves its embedded fixture. It is not a runtime
firmware proposal, transport endpoint, trusted-consent implementation or image to
flash. Production and emulator integration require separate work.

## Paired memory layout

Both builds use the official hardware `test` preset, source-pinned nightly,
Thumb target, optimization `z`, LTO, one codegen unit and `panic=immediate-abort`.
Linker regions, minimum-heap assertions and component gates remain unchanged.
The [baseline document](TARGET_FIRMWARE_BASELINE.md) describes its test-key and
embedded-component limitations.

| Region | Unchanged baseline | Allocator derivative | Difference |
| --- | ---: | ---: | ---: |
| Application stack reservation | 32,768 | 32,768 | 0 |
| Data | 512 | 512 | 0 |
| BSS | 15,252 | 19,460 | +4,208 |
| Buffer section | 72,676 | 72,676 | 0 |
| MicroPython GC region | 697,992 | 693,784 | −4,208 |
| Firmware image extent | 2,369,536 | 2,634,752 | +265,216 |
| Flash slot remaining | 1,046,528 | 781,312 | −265,216 |

All values are bytes. The arena occupies `0x201a0200..0x201a1200`, aligned to 16
bytes inside BSS. The GC region starts at `0x201b69e8` and ends at `0x20260000`.
Those ranges are disjoint. GC extent is a link-time region, not available runtime
memory; 4 KiB is a link diagnostic, not a selected signing capacity.

## What the linked code establishes

The parameterless hook runs after data/BSS initialization and the stack-guard
store. It initializes the arena before constructing synthetic keys or the Engine.
The wrapper uses `linked_list_allocator::Heap`, exact pointer/layout forwarding
and `SpinMutex::try_lock`, with no heap reset or GC routing. Initialization uses
Heap's existing empty-state marker under the same lock.

Final disassembly and inline source identities show retained `begin`, `approve`,
`sign`, actual RedDSA RNG/scalar multiplication and both PCZT serialization paths.
The result is consumed through a volatile store. These observations establish
code retention; `black_box` alone is not a guarantee of retention or feasibility.

Allocation failure returns null. Under this image's `immediate-abort` build,
RawVec allocation errors trap with `udf #254`, bypassing the source
`alloc_error_handler` shim. Explicit allocator invariant failures use `udf #0`.
No trap or startup path was executed.

The ELF contains 3,366 individual stack-frame entries. The synthetic function's
10,752-byte frame and validation's 13,088-byte frame match their disassembly
prologues. No whole-call-chain bound or runtime stack high-water measurement exists.
These local frames do not establish fit within the 32 KiB stack.

## Dependency and component differences

The firmware registry inventory grows from 105 to 206 packages, with no existing
firmware package removed or changed in the lock. All added packages already occur
in the accepted probe except the separately audited allocator 0.10.6. Critical
PCZT, Orchard, RNG and approval features match the probe. Shared utility versions
and features unify with firmware; the entire feature graph is not identical.
Examples include `zeroize` gaining `alloc` and `num-traits` gaining `i128`.
`feature-comparison.json` records the complete comparison. No validation feature
was disabled; signature equivalence under this combined runtime remains untested.

The new kernel binary is byte-identical to baseline. The newly built secure-monitor
binary differs despite unchanged source. Static comparison accounts for two
shorter embedded `__FILE__` strings, 219 relocated literal words and alignment.
The derivative directory name `firmware-arena-link` is five characters shorter
than `firmware-target-baseline`. Both ELFs contain those paths in
`smcall_dispatch.c` and `smcall_verifiers.c`, explaining the ten-byte string-pool
shrink and subsequent padding changes;
compared instruction bytes are unchanged. The `.data` change relocates `PIN_EMPTY`
to the same empty string. This explains data/layout changes, not historical
header-signature equivalence. The firmware/kernel
still embed the same source-pinned secure-monitor blob, not that newly built
monitor. The experiment does not change factory attestation or claim every
separately built component is byte-identical.

The outer xtask command is locked; upstream xtask does not forward `--locked` to
inner builds. Before/after lock hashes and resolved dependency/source inventories
bind this observed build, including eight approval and 118 librustzcash path-
dependency files. Their source inventory is in `resolved-current-hashes.json`;
path dependencies have no registry checksum. This is not a claim that xtask
enforces locked resolution.

## Evidence and review status

The first build timed out during dependency compilation. The unchanged source and
settings resumed successfully in 550.115 seconds. Both attempts remain recorded.
The coordinator independently rehashed all 247 sealed files and recomputed arena,
GC, BSS and stack arithmetic from the actual ELF symbols.

- Complete report: `work/firmware-arena-link-final/report.json`, SHA-256
  `d3514a7806a86843be131d36a88ae472c169ee83db223c41436d6349480c4bd2`.
- Sealed manifest: SHA-256
  `9fcd64d8a3a1344826316fe162956e769b64cedd7f126b0de2b1bd0b12654e98`.
- First-link firmware ELF: SHA-256
  `7f1333ea0e7663eb928541dadd450421b29c31f96f9f5434ed2381a1e5a23b76`.
- Corrected patch firmware ELF: SHA-256
  `6f4371ef69d34718d2b87adf447245e7b9199c74eaaa112b295a9739e4c1c504`.
- Final allocator source: SHA-256
  `407f619e92aacbbeed0c883d0ee83f5243d1ee6282e69b2d02597175696d2d53`.
- Firmware binary (identical across correction): SHA-256
  `7132dac5f4d87df05a1b7060c44569a14cfb85e2d1127637dafad977efa35d62`.
- Parent verification: `work/firmware-arena-link-parent-verification.json`.

Clarity review requested a precise locking-helper name and a narrower optimizer
comment. Both are applied; the correction build passed in 60.969 seconds and its
firmware binary is byte-identical. The coordinator verified all 97 new evidence
records. The new ELF differs only in nonallocated debug/symbol sections.
Correction report: `work/firmware-arena-link-v2/report.json`, SHA-256
`bef7751b05e09669a7bcced0bb8907a3917a8075912fadd710c9ab1b48e51529`.
The [complete patch](../experiments/firmware-arena-link/README.md) includes the
resolved lock and embedded public fixture.

 The post-login Claude Code
review found no memory-safety defect in the documented scope, but reported Opus 5
despite an explicit Fable request. It is retained as additional review evidence,
not counted as the requested Fable review. The final configured-model review
reported `claude-fable-5-1` and found no blocking issue in the compile-only scope.
Its documentation corrections are applied: worktree-path cause, final artifact
hashes, and shared-utility feature scope. The frozen correction report
`baseline_entries` field refers to the preceding derivative build02, not the
unchanged target baseline. No runtime or production conclusion follows from this link.

The separate [review record](reviews/TARGET_ALLOCATOR_LINK.md) lists findings,
resolutions and actual model provenance.
