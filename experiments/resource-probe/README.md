# Synthetic host resource probe

This standalone workspace characterizes the actual `ironwood-approval` core with
`default-features = false`. It is the first host measurement harness described in
`docs/SAFE7_INTEGRATION.md`, based on accepted repository HEAD
`12c25c8eb9d9045483a2dbfebc0483a779bd0944`. No core or upstream source is modified.
It is not a firmware integration, allocator adapter, wallet, or MCU fit result.

Only public synthetic inputs are supported: account `SpendingKey::from_bytes([0;
32])`, regtest height 10,000,000, maximum fee 100,000, and `ChaCha20Rng` initialized
with `[42; 32]` for every run. RNG initialization and use are measured; account-key
derivation is preparation outside the windows. There is no production entropy
adapter or configurable seed/policy. Automatic approval is local to this harness.

## Run

From the repository root, use the existing cache and a separate target directory:

```sh
export CARGO_HOME="$PWD/work/cargo-home"
export CARGO_TARGET_DIR="$PWD/work/resource-target"
export CARGO_BUILD_JOBS=4
cargo fmt --manifest-path experiments/resource-probe/Cargo.toml --check
cargo check --locked --offline --manifest-path experiments/resource-probe/Cargo.toml
cargo clippy --locked --offline --manifest-path experiments/resource-probe/Cargo.toml --all-targets -- -D warnings
cargo test --release --locked --offline --manifest-path experiments/resource-probe/Cargo.toml -- --test-threads=1
cargo build --release --locked --offline --manifest-path experiments/resource-probe/Cargo.toml
"$CARGO_TARGET_DIR/release/resource-probe" work/resource-fixtures work/resource-signed > work/resource-measurements.json
```

The CLI takes exactly `<fixture-directory> <signed-output-directory>`. Its input
set is `outputs-1.pczt` through `outputs-8.pczt`, then `inputs-2.pczt` through
`inputs-8.pczt`, produced beforehand by the separate fixture experiment. Outputs
use the same filenames in a different directory. Only compact JSON is written to
stdout; any failed assertion or I/O operation fails the process. Do not accept
partial signed files from an unsuccessful run.

`scripts/resource_check.py` runs the measurement and separate upstream oracle.
The probe reports `oracle_verified: false` until that runner has verified the
exact representative files against the originals.
Every one of the five recorded runs asserts identical serialized signed bytes
and digest to the warm-up representative, so successful oracle verification of
that representative covers those identical results as well.

## Measurement and report contract

Top-level `schema_version` is 1. `cases` contains each of the 15 names exactly
once, without `.pczt`. Each case reports `wire_bytes`, `signed_wire_bytes`, actual
`action_count`, `signature_count`, `output_count` (positive outputs),
`padding_outputs`, `dummy_spends`, `anchor_present`, `ock_count`, and
`sighash_hex`. An upstream Verifier inspects fixture fields before the runs; no
builder, independent oracle, or reporting serialization enters the windows.
The positive counts are checked against the two prescribed series. The parsed
fixture object is dropped before measurement.

Each case has one `warmup` and exactly five measured `runs`, in chronological
order. Warm-up allocation phases are recorded but untimed (`elapsed_ns: 0`).
`runs[0]` is the first recorded result, preserved separately from the other four.
`timing_summary_ns` supplies each phase's first, median, and maximum over the five
recorded runs, excluding warm-up and any human review delay.

Each run has `input_capacity_bytes`, `review_output_capacity_bytes` (the returned
Review's output Vec storage), `process_baseline_bytes`,
`teardown_retained_bytes`, and six named entries in `phases`:

| Phase | Included operation and ownership |
| --- | --- |
| `constructor` | Policy/FVK clone, fixed RNG initialization, `Engine::with_rng`, including session randomness. |
| `begin` | Actual core admission, parsing, validation, retained Pending and returned Review. |
| `approve` | Actual token-bound `Engine::approve`. |
| `sign` | Actual private retained-PCZT signing path, digest recheck, RNG cost and returned Signed. Raw input, Engine and returned Review all remain live. |
| `serialize` | Pinned `Pczt::serialize` consumes the returned PCZT, releases its storage and creates the serialized output Vec. No PCZT clone is introduced to serialize it. Raw input and Review remain live. |
| `teardown` | Drops serialized bytes, signature Vec/token, returned Review, Engine and the owned raw input. PCZT storage was already dropped by serialization; both phases are necessary for full teardown. |

`process_baseline_bytes` is the global allocator's live requested bytes just
before creating this run's owned input copy. That copy is prepared outside the
phase windows and kept through signing. The baseline includes the borrowed
fixture, previous report records, public keys and any representative comparison
buffer; these are harness objects, excluded from core attribution. Subtract this
run baseline from a phase's `peak_live_bytes` or `live_bytes` to obtain measured
occupancy attributable to the run, including its raw input. Do not subtract the
phase baseline: it includes earlier core allocations that are still live.

`review_output_capacity_bytes` is already included in live bytes, not an extra
quantity to add. It describes the returned Review Vec, not the retained Pending
copy or the Review's inline/stack storage. Input and Review lifetimes are explicit
through signing. The complete core/serialization/input teardown must return
exactly to the run baseline. Any nonzero `teardown_retained_bytes`, underflow, or
allocator accounting error terminates the probe, including during warm-up.

Each phase reports:

- `allocations`: allocation calls, including `alloc_zeroed` and failed requests.
- `reallocations`: reallocation calls, including failures; not counted again as
  alloc/dealloc calls.
- `deallocations`: explicit deallocation calls.
- `failed_requests`: null alloc/zeroed/realloc results.
- `requested_bytes`: cumulative requested sizes for alloc/zeroed and the **full
  new size** for realloc, including failed requests; not net growth.
- `largest_request_bytes`: largest requested alloc/zeroed/realloc size.
- `baseline_live_bytes`, `peak_live_bytes`, `live_bytes`: absolute process-wide
  requested layout bytes before, at the greatest observed logical occupancy, and
  after the phase. `live_bytes` means retained at that phase boundary, not a leak.
- `accounting_errors`: lifetime-sticky checked live-byte arithmetic failures.
- `elapsed_ns`: elapsed instrumented host time for the operation, including its
  allocator hooks and RNG cost, excluding phase reset/snapshot and formatting.

Phase resets preserve all carried live allocations and initialize the new peak
to that live total. Allocation results update live bytes only on success; a null
realloc result leaves the old allocation fully counted. System receives the
original pointer/layout/alignment/new size; its `alloc_zeroed` is forwarded as
such. Counter updates hold a nonallocating atomic spin lock and call System
directly. There are no background workers in this binary. Event counters use
saturating arithmetic (the documented counters cannot represent values beyond
`usize::MAX`); live arithmetic errors are fatal at the next snapshot check.

Serialization is separately instrumented in every run, then the warm-up result
is written or the recorded result compared outside windows. File I/O, fixture
parsing/construction, signature-oracle work, metadata inspection and JSON
formatting/logging are excluded. The final report is formatted only after all
measurements. Sum of phase times would exclude these deliberate gaps; it is not
wall-clock transaction latency.

## Small failure characterization

`failure_checks` contains `max_cancel_drop`, `max_replacement_drop`,
`oversize_65537_admission`, and `nine_action_admission`. Each records allocation
metrics and asserts zero retained bytes relative to its own baseline.

Cancel and replacement reuse `inputs-8.pczt` with all returned Review objects
kept until teardown. The replacement check approves the new token and then drops
the pending request. The oversized buffer and nine-action
v2 encoding (an appended duplicate action, serialized by upstream PCZT) are prepared before their windows; each is passed to `Engine::begin`
on an already constructed idle Engine. These checks require the precise admission
error and zero alloc/realloc/dealloc calls across the whole begin call, proving
no Rust protocol allocation in these two rejection paths. No allocation cap,
session-entropy interruption, or firmware cleanup claim is part of this bounded
probe. The larger SAFE7 failure matrix remains later work.

## Evidence limits and interpretation

Counts measure Rust `GlobalAlloc` requested layouts backed by host `System`.
They exclude allocator metadata, size-class rounding, internal transient overlap
inside System realloc, direct C/malloc calls, stack frames, static storage,
process RSS, and shared firmware/UI/THP memory. Absolute process peaks include
harness baselines; use the per-run subtraction above for attributable occupancy.
The counter lock and instrumented allocator add latency. Host pointer sizes,
optimizer behavior and CPU scheduling differ from MCU execution.

Source-visible contributors to interpret alongside the peaks are the retained
parsed PCZT plus the Verifier clone in `begin`, retained and returned Review Vecs,
effect extraction during validation/signing, and signing/result ownership.
This harness measures whole phases; it does not separately attribute every
allocation to one of those copies. Inspect the source and phase deltas before
attributing a peak. Host binary size and Rust `size_of` do not establish target
flash, call-chain stack, native heap high-water, or MCU timing.

The release profile is explicit: opt-level 3, thin LTO, one codegen unit,
`panic = "unwind"`. Panic unwinding is not evidence of MCU abort/reset cleanup.
A compiler/target/profile/source/lock/fixture/binary identity record and the
separate oracle results are required when accepting a measurement. No claim is
made that the observed maxima bound all admitted PCZTs or fit Safe 7 RAM, flash,
32 KiB stack, latency, or watchdog constraints.

## Validation and results

Run the complete measurement from the repository root:

```sh
python3 scripts/resource_check.py
```

The runner checks formatting, warning-fatal Clippy, dependency identity and three
allocator tests before measurement. The tests cover System alignment/zeroing,
reallocation prefix preservation, carried live bytes, complete teardown, sticky
accounting errors and null-result ownership. They do not force OS exhaustion.
The separate fixture tool has three tests of its signature/directory oracle.

[Resource results](../../docs/RESOURCE_RESULTS.md) record the accepted run,
methodology, source hashes and review findings. Raw reports and synthetic PCZTs
remain under ignored `work/runs/`.
