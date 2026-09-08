# Synthetic allocator boundary

Prepared 2026-09-08. Original proposal followed by a measured lifetime amendment below.
Assume the unchanged actual `ironwood-approval` core, `default-features = false`,
synthetic regtest fixtures/public keys and fixed ChaCha20 RNG. No production entry point.
One synchronous invocation owns Engine, input, Review and Signed. No request-owned
allocation or reference escapes; successful output is staged outside the arena and
exported after teardown. The amendment below separately accounts for public constants.
No Python callback, GC allocation, longjmp, task switch or transport call inside that invocation.
Global Rust allocation is image-wide: audit every caller; initialize before any alloc use.
## Concrete choice and dependency cost

Use `linked_list_allocator = { version = "=0.10.6", default-features = false }`,
its `Heap` behind existing `spin = { version = "=0.9.9", default-features = false,
features = ["spin_mutex"] }`, and one thin `GlobalAlloc` wrapper in the harness binary.
Reuse `spin::mutex::SpinMutex<Heap>` with `try_lock`; do not implement a general allocator.
Allocator: no_std, MIT OR Apache-2.0, MSRV 1.61 ([manifest](https://docs.rs/crate/linked_list_allocator/0.10.6/source/Cargo.toml)); spin: MIT, MSRV 1.38.
With these features the new allocator has zero enabled normal dependencies;
optional `spinning_top` and unstable `alloc_ref` stay disabled. Spin is already locked
at 0.9.9 in both firmware and core; this adds one registry package, not another lock crate.
Future experiment-only manifest/lock records its checksum (saved in `work/allocator-research/candidate-provenance.json`) and feature tree;
preserve every accepted core/upstream pin and license notice, including firmware licensing.
0.10.6 includes the huge-layout panic fix missing from 0.10.5 [A]. The original
proposal inspected source only; the first arena prototype subsequently compiled
on the pinned nightly for native and Thumb targets. Final firmware linking remains separate.
Local firmware `static-alloc` 0.2.6 has no-op `GlobalAlloc::dealloc`; its renderer resets
borrowed bump storage. That cannot measure reclaiming frees in repeated core lifecycles.
`without-alloc` 0.2.2 supplies alternative containers, not the existing alloc::Vec boundary.
Local evidence: firmware `core/embed/Cargo.{toml,lock}` and cached `static-alloc-0.2.6/src/bump.rs`
871–906, `without-alloc-0.2.2/src/lib.rs`; exact paths/hashes: `work/allocator-research/inspected-inputs.json` [F].
## Ownership, allocation and failure contract

Reserve one zero-initialized, explicitly aligned static byte arena (e.g. align(16))
in ordinary `.bss`; obtain its raw address once without creating overlapping references.
Use `Heap::bottom().is_null()` under the lock as the initialization state; no second flag.
Reject double init before creating any mutable reference to the arena, then give its
exclusive, static MaybeUninit slice once to `Heap::init_from_slice`; never extend/reset it.
A compile-time assertion must check the fixed buffer against the crate's minimum size.
Guard pre-init allocator use.
Arena bytes belong exclusively to Rust, outside `_heap_start.._heap_end`; never hand
arena pointers to gc_free/free, borrow a GC block for storage, or overlap GC metadata.
Ordinary Rust Drop owns reclamation; GC roots/finalizers do not own these allocations.
The arena must not be the sole holder of any Python/Gc/GcBox pointer: GC does not scan it.
Copy bounded input into Rust-owned storage before execution; keep any source Python owner
rooted during that copy; stage successful output in fixed caller-owned storage, then
drop Rust owners before exporting it. Never export partial results.
Pinned `gc.rs` cannot honor arbitrary alignment and requires GC visibility [F].
Delegate nonzero Layout allocation to `Heap::allocate_first_fit`, failure to null,
and deallocation to `Heap::deallocate` with the original pointer and exact Layout [B].
Arena alignment is not a maximum supported object alignment: satisfy each requested
power-of-two alignment within the arena or return null, never return a misaligned block.
Use GlobalAlloc's provided alloc_zeroed and realloc initially: zero returned bytes;
realloc allocates the new layout, copies min(old,new), then frees old on success [C].
Failure leaves old allocation/data live; count old+new overlap in the event peak.
A successful realloc uses the new Layout thereafter. Vec handles zero-sized elements;
do not test GlobalAlloc with invalid zero-size layouts or double/foreign frees.
Every heap/initialization/counter access uses the same nonallocating try_lock;
spin 0.9.9 uses Acquire compare-exchange and Release unlock. Contention/reentry
immediately traps/terminates the experiment; no waiting spin and no interrupt masking.
No allocator use from interrupts or foreign threads is allowed by this experiment.
Release the guard before copy/zero work; default realloc re-enters alloc/dealloc separately.
No allocation, formatting, callbacks or panicking bookkeeping inside allocator operations.
First-fit allocation/free are O(number of holes), not bounded MCU latency [B].
Allocation exhaustion returns null; infallible Vec paths reach a harness-owned
nonreturning allocation-error handler. Do not promise the core's Error for OOM.
Use a nonallocating immediate trap on target and process termination in emulator;
resolve/check the exact nightly handler and trap symbols in the final link/disassembly.
Panic, lock violation and arithmetic/invariant failure also fail-stop without Python
exceptions, unwinding or partial signature export. Failure injection uses a fresh process.
Do not call an uninspected fatal-screen/log path while holding the heap lock.
Normal completion/error/cancel/replacement drops all owners; require live count and
Heap::used back at baseline. Before the lifecycle, find a successful near-arena-size
allocation and free it; after teardown require allocation with the same Layout to
succeed again, then free it. Never reset a live global heap.
Abort runs no destructors; restart the process/image before reuse. Memory clearing after
abort and secret zeroization are not established by this synthetic public-key experiment.
## Needed data and first isolated linked/runtime experiment

1. Freeze core/locks/fixture hashes and firmware revision [F]. Work only in a later
   isolated copy; keep baseline checkouts clean. Rebuild the concrete real-core path
   with nightly-2026-03-16, thumbv8m.main-none-eabihf, optz+LTO+immediate-abort,
   one codegen unit. Use the completed size-only comparison [T] as diagnostic context.
2. First build paired baseline/integration complete target ELFs/maps using T3W1
   secmon layout, existing kernel/secmon/images and unchanged region/stack assertions.
   A 4 KiB arena is a link/failure diagnostic seed, not a runnable budget or runtime evidence.
   Keep a reachable synthetic boot harness and consume its output so LTO cannot discard
   validation/signing. Record actual linked reachability, arena bounds, all section deltas,
   32 KiB stack symbols, GC extent and remaining flash; retain link failures as findings.
3. Separately run the same allocator boundary in the Safe7 emulator's synthetic boot
   harness, initially 128 KiB solely as a host diagnostic cap; it may fail. Exercise
   with_rng→begin→approve→sign→drop on the 15 existing fixtures, retaining input/Review.
   Autoapproval stays compiled into this synthetic test only; no callable transport,
   device key-store or generic preverified signing API. Check effects/signatures with
   the independent pinned oracle outside the measured lifecycle; never skip verification.
4. Measure allocation-event requested/rounded live peaks, allocator used/free, largest
   request, failures and realloc overlap in fixed counters. Record GC boot/idle/phase
   occupancy and fragmentation, both 8,704-byte THP payloads and live UI/runtime objects.
   Requested and rounded allocation sizes both depend on host/target layouts; neither
   transfers directly to the MCU. Heap blocks also round in usize units. These are host
   observations, not target upper bounds. Initial emulator diagnostics precede a separate
   pressure run capped from a linked candidate's GC extent, counting the arena once;
   emulator malloc-backed GC does not automatically shrink when Rust BSS grows.
   Snapshots miss transient peaks; retain event counters and pressure outcomes too.
5. Target arena capacity stays TBD: use linked baseline headroom, target layouts,
   allocator padding/fragmentation, concurrent GC/UI/THP needs and explicit reserve.
   The 80,821-byte sample excludes allocator overhead/realloc overlap and covers only
   1,236–10,037-byte inputs, not all admitted 65,536-byte inputs [R]. Larger/hostile cases
   need measurements. Never increase linker regions or weaken validation to obtain fit.
## Acceptance tests and limits

- Direct valid-layout tests: powers-of-two alignments 1..=4096 in the 128 KiB host arena,
  with smaller-arena expectations derived separately; test odd sizes, zeroing,
  grow/shrink copy integrity, forced realloc failure retaining old bytes, hole reuse/
  coalescing and arena canaries. Huge valid layouts fail cleanly; no out-of-arena writes.
- Lifecycle: all 15 oracle-verified fixtures plus cancel/replacement/repetition restore
  baseline; oversized input/nine-action rejection still precedes core allocations.
- Fresh-process OOM injection during begin and sign, plus pre-init/double-init/lock
  reentry: deterministic rejection or fail-stop, no hang and no signed result export.
- In a separate allocator ownership test, retain Rust Vecs across forced MicroPython GC;
  check contents, disjoint ranges and both teardown baselines, outside the core invocation.
Passing these gates establishes only the tested synthetic boundary. The opt3/noLTO/abort
33,000-byte nested-path warning remains. The completed optz/noLTO/abort comparison [T]
changes four of eight direct edges: do not reuse the old path for a new frame subtotal.
It establishes no whole-stack bound or final optz+LTO+immediate-abort firmware fit.
Arena capacity, 32 KiB stack success, MCU latency/entropy and production/funds use remain unestablished.
## Amendment: immutable public tables live with the image

The first native probe reached signing/serialization for all 15 fixtures, then
correctly failed its empty-heap teardown. Pinned pasta_curves 0.5.1 owns five lazy
Fp square-root table allocations: a 1,098-byte vector and arrays of 256, 256, 256
and 129 field elements. `SqrtTables::new` derives them solely from ROOT_OF_UNITY
and fixed hashing constants. They contain no account or transaction data and
remain referenced by the library's static for the life of the image.
The original source snapshot, binary and failures remain frozen; none becomes a pass.

The next isolated prototype makes this lifetime explicit:

- Initialize only the identified Fp tables through a fixed public field operation,
  after Heap initialization and before keys, PCZTs or requests. Check that repeating
  the operation allocates nothing. Do not run a transaction as a warm-up baseline.
- Record cold initialization, the exact expected five live layouts and their
  allocation identities. Keep those blocks resident and immutable; reject attempts
  to free them. No manual free, heap reset, feature change or OS fallback.
- Every request must restore that same constant set and release every later
  allocation. A newly retained cache, including a late Fq table, fails the gate;
  it is never absorbed into another baseline. Keep allocation/free deltas as well
  as live requested/used/block counts.
- Measure absolute event peaks including the resident tables. Phase counter resets
  must preserve live occupancy. A successful large Layout is allocated and freed
  before the request and must succeed again afterward; available capacity now
  excludes the identified resident blocks and their fragmentation.

This is a bounded change to the synthetic experiment under the user's existing
local implementation authorization. It requires fresh Fable and independent clarity
review of the implementation and evidence. It does not permit arbitrary retained
owners or claim whole-program memory safety, MCU capacity or successful runtime fit.

[A]: https://docs.rs/crate/linked_list_allocator/0.10.6/source/Changelog.md
[B]: https://docs.rs/linked_list_allocator/0.10.6/struct.Heap.html
[C]: https://doc.rust-lang.org/core/alloc/trait.GlobalAlloc.html
[F]: ../SAFE7_INTEGRATION.md
[R]: ../RESOURCE_RESULTS.md
[T]: ../TARGET_CODEGEN_RESULTS.md
