# Synthetic arena signing probe

The final native run passed 35 process cases, including two independent oracle
checks. Evidence: `work/arena-probe/v4/verification-01/report.json`. The separate
[review record](../../docs/reviews/ARENA_PROBE.md) records findings and resolutions.

A test-only C executable drives the unchanged no_std approval Engine through
begin, approve, sign and serialization, using public account `[0;32]`, ChaCha20
`[42;32]`, regtest height 10,000,000 and fee cap 100,000. No production keys,
transport, hardware or Safe7 emulator integration is involved.

## Initialization and ownership

C initializes the fixed 128 KiB Rust arena before any Rust allocation. Before
reading input or constructing keys, explicit image initialization calls only
`pasta_curves::Fp::ONE.sqrt()` through `ff::Field`. The pinned source routes this
to FP_TABLES, immutable ROOT_OF_UNITY-derived public constants. Fq is not initialized.
The five expected survivors are computed from target Layouts: a 1098-byte vector,
three arrays of 256 Fp values and one array of 129 Fp values. On this native build
they retain 29,802 requested / 29,808 used bytes in five blocks. Observed startup performed
30 allocations and 25 frees, with peaks of 37,994 requested / 38,000 used bytes.
Calling the initializer again changes no counters.

A fixed six-slot tracker covers only table construction (five owners plus realloc
overlap). Initialization verifies the exact surviving layout multiset and seals
those original addresses. Any later attempt to free a sealed block fail-stops;
newly retained allocations fail request teardown. Constants are never manually
freed, replaced or rebaselined. A valid guard test rejects a sealed free before any
GlobalAlloc call; a separate real retained allocation tests late-cache rejection.

The thin GlobalAlloc wrapper uses exact linked_list_allocator 0.10.6 and spin
0.9.9 SpinMutex::try_lock. Heap.bottom under that lock is the arena initialization
state; repeat init is rejected before constructing the unique static mutable
MaybeUninit slice. A const assertion checks the arena minimum size. The aligned
BSS arena has disjoint canaries, cannot extend/reset and has no GC-backed storage.
Default zeroed/realloc behavior preserves layouts, copy/overlap and old ownership
on allocation failure. No System routing or custom allocator is present.

Every request retains its owned raw input and Review through signing. All fallible
Engine/serialization work finishes before copying to C staging; every request owner
drops before C exports. Requested/used/block counts restore the explicit public
baseline, allocation/free deltas balance, and the same Layout (65,536 bytes,
alignment 16) succeeds before and after. This half-arena probe is a demonstrated
contiguous block, not an inference from total free space or a maximum-size claim.

## Measurements and failure evidence

Counters never reset. Reports distinguish cold initialization, repeated initialization,
request start/phases/teardown and the final large probe. Allocation-event peaks are
absolute and include resident constants, startup and probe overlap; the probe can
dominate smaller cases. The observed maximum across the corpus remains 111,903
requested / 111,976 used bytes. These are host observations, not MCU heap bounds.
Heap.free measures total free bytes, not largest free block.

Only a synchronous image-wide caller is supported: no concurrent/interrupt Rust
allocation, callbacks, GC pointers, longjmp or unwinding across FFI. OOM, lock,
initialization and invariant failures terminate. Native panic/allocation/personality
handlers call `_Exit`; the personality has the pinned native five-argument C ABI
and status return, with no unwinding machinery. It is excluded from target builds.
The target handler emits UDF; no firmware fault-policy claim follows. Optional
nonblocking exit-84 diagnostics contain counters only; absent, partial or invalid
payloads remain generic invariant failures and never erase the final runner report.

`verify.py` uses the exact saved 15-fixture corpus and separate existing oracle.
Each request needs exactly one report; varied same-process repetition needs three.
It verifies statuses, completed phases, instrumentation, baseline and both probes.
The layout-case JSON is a status; actual Rust assertions and exit zero are its
gate. C flushes each report before the next request can fail-stop. Oracle census
lines match exactly, three repeated outputs must match their primary hashes, and
the report records and rechecks Cargo.lock. Every command records `exit_matched`
separately from evidence `passed`; all failures
are saved. Python optimization cannot remove its checks. Twelve evidence-runner tests include a positive control and cover
empty output, partial diagnostics, wrong states, missing work and changed lock
projections and stale dependency metadata, both normally and with `python -O`. Fatal-process deadlines remain
30 seconds; cryptographic oracle work has a separate 120-second deadline.

`check_dependencies.py` proves parsed projection equality with the full build lock
minus ONLY the allocator package. It resolves fresh offline, locked metadata and
saves each audit in a new directory. It binds both lock hashes, matches the saved and
cached allocator archive to the published index checksum, and runs the unchanged
shared checker over all 128 existing registry packages. Direct pasta_curves 0.5.1
and ff 0.13.0 dependencies reuse existing exact versions and enable no features;
the entire dependency feature graph matches v1. No builder/signer/std features are
added to core. No download or install was needed for this refinement.

## Reproduction and saved inputs

This experiment requires the saved synthetic corpus, oracle and original failing
binary referenced by `verify.py`, plus the prepared offline Cargo cache. It is not
a standalone fresh-checkout test. Exact v4 commands, environment and logs are in
`work/arena-probe/v4/commands.jsonl`; the earlier v2 evidence remains frozen.

For a reproduction, use a fresh target and output directory so the saved v3/v4
artifacts remain unchanged. From the repository root on the prepared machine:

```sh
export PATH="$PWD/work/rustup/toolchains/nightly-2026-03-16-aarch64-apple-darwin/bin:$PATH"
export CARGO_HOME="$PWD/work/arena-probe-cargo"
export CARGO_TARGET_DIR="$PWD/work/arena-probe-reproduction-target"
export CARGO_NET_OFFLINE=true
export CARGO_BUILD_JOBS=2
export TARGET_CC=/opt/homebrew/opt/llvm/bin/clang
export TARGET_AR=/opt/homebrew/opt/llvm/bin/llvm-ar
mkdir work/arena-probe/reproduction
cargo build --offline --locked --release --manifest-path experiments/arena-probe/Cargo.toml
clang -std=c11 -O2 -Wall -Wextra -Werror -pedantic -mmacosx-version-min=26.2 experiments/arena-probe/driver.c "$CARGO_TARGET_DIR/release/libironwood_arena_probe.a" -Wl,-dead_strip -o work/arena-probe/reproduction/arena-probe
python3 -O - <<'DIAG'
import sys
sys.path.insert(0, "experiments/arena-probe")
import verify
verify.BINARY = verify.ROOT / "work/arena-probe/reproduction/arena-probe"
sys.argv = ["verify.py", str(verify.ROOT / "work/arena-probe/reproduction/verification")]
sys.exit(verify.main())
DIAG
python3 experiments/arena-probe/check_dependencies.py
python3 -O -m unittest discover -s experiments/arena-probe -p test_runner.py -v
```

Choose another fresh reproduction directory for a later run. The verifier still
reads its original v1 binary and negative-test captures from v2. Native/target
compilation uses nightly-2026-03-16, optz/LTO/one codegen unit/panic abort. Matching
nightly Clippy checked native and actual Thumb builds with `-D warnings`. Rust
and those target checks are unchanged from v3; v4 relinks C and checks Python.

Original zero-owner failures, snapshot and manifest remain unchanged at
`work/arena-probe/verification-01`, `verification-02`, `frozen` and
`frozen-evidence.json`. The copied original binary reproduces the cold fail-stop
without export. Refinement failures remain in the earlier verification directories; none is
reported as success.

## Limits

This experiment establishes only the captured synthetic native results and target
compilation. It does not establish linked firmware fit, target runtime, GC/arena
range disjointness, 32 KiB stack safety, MCU timing/entropy, zeroization or production
readiness. The 128 KiB cap is diagnostic and unchanged.
