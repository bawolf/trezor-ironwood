# Safe 5 native caller checkpoint

10 September 2026 UTC. Synthetic test firmware only; candidate not adopted or executed.

The Safe 5 candidate now links the existing trusted review flow to the native
signing bridge through Trezor's normal lazy workflow dispatcher. It fits in the
firmware slot with **23.5 KiB remaining**. This removes a source/build integration
gap; it does not establish that the workflow fits or completes on the processor.

| Evidence | Retained image | Native caller candidate |
|---|---:|---:|
| Occupied flash | 1,676,800 bytes | 1,679,872 bytes |
| Remaining flash | 27,136 bytes | 24,064 bytes |
| Application RAM reservations | 526,848 bytes | 526,848 bytes |
| Native stack reservation | 49,152 bytes | 49,152 bytes |
| Raw GC regions | 92,880 + 41,696 bytes | 92,880 + 41,696 bytes |
| Actual native execution | Not run | Not run |

The net flash increase is 3,072 bytes. It compares the complete images and build
configurations; it is not an isolated measurement of one Python module's cost.
The retained image, source package and memory breakdown remain unchanged.

## What changed and what passed

The candidate adds one explicit build feature and one derived capability flag.
Stock dispatch imports `apps.zcash.sign_pczt` only for its synthetic message.
The feature requires the existing nonproduction T3T1 native configuration plus
frozen universal firmware, Delizia and legacy transport. No boot registration or
new generic signing API was added. The C signing implementation is unchanged.

The reused Python caller retains the complete begin/review/sign operation inside
its cancellation scope and uses the existing context helper in the registered
workflow. All output details and totals precede the final hold and bound-token
sign call. An explicit missing-task error replaces an assertion removed by Python
optimization. That check alone does not prove workflow registry membership.

- Standard protobuf generation and the frozen/offline target build passed.
  Independent checks match actual compiled bytecode and descriptors to allocated
  ELF bytes, including lazy module registration and the optimized task guard.
  The first generation attempt failed before compilation because the sandbox
  denied protoc's `/dev/stdout` output; the authorized retry completed.
- Ten caller tests passed, covering 216 subcases: confirmation order, cancellation,
  simulated allocation failures, stale tokens, cleanup/retry and optimized-build
  guards. The exported portable entry point passed the same cases.
- These tests execute the actual two Python handlers with stubbed C/Rust, UI,
  wire, scheduler and capability services. They do not test real GC roots or
  allocations, actual hold timing, native scheduling or cryptographic signing.
  Some failure cases occur after signed chunks have already been sent.
- Independent local source integration and clarity reviews completed. Required
  namespace and optimized-guard fixes are included in the compiled sources.
  Fable review remains pending exact-packet transmission approval.
- The project checks passed all 27 tests. The reviewable 14-file patch applies
  to a separate copy of the retained experiment and reproduces every candidate
  file hash. This is not yet a clean-checkout, maintainer-ready firmware build.

Candidate ELF SHA-256:
`962755b3e7f094856b4fbd1f7cbdf872c86ab53bffae8f624b654ce5c18d55fe`.
Retained ELF SHA-256:
`ab110d7e1709c4e3b28f6042226c489a738b1d5819f42ad546ee9b59d1452c12`.

## Next steps, in priority order

1. **Measure actual live memory and failure cleanup.** Add small fixed C records
   around validation, review, response allocation, signing and cleanup, with
   retrieval over the synthetic USB workflow after cleanup. Existing collector
   counters can report the largest free run without allocating. This avoids
   assuming debugger access to the unopened device. The diagnostic design is
   prepared, but its code and runtime evidence remain outstanding.
2. **Close complete stack bounds and target timing.** Trace the new image's full
   callers and combine that evidence with target stack/arena measurements.
   Selected static paths and phase SP samples are not complete peaks. Measure
   signing and computed Sinsemilla latency on the processor before choosing
   another speed/space tradeoff.
3. **Complete the pending source reviews and test the response reduction.** The
   current response needs 65,552 contiguous GC bytes; its source-derived primary
   pool has 90,752 usable bytes before other live objects. A proposed 16,400-byte
   block would remove 49,152 allocated bytes, but remains unapplied. Its proof
   and signing-test reviews are separately pending. Sample output lengths alone
   do not establish the bound or actual free memory.
4. **Prepare a short attended Safe 5 session.** Use a pinned, reviewed synthetic
   image and scripted host checks. Device-side confirmations will need the user.
   Define exact installation/recovery steps and expected screens before requesting
   that time. No device access, setup or flashing has occurred.

Production keys and entropy, complete hostile-host recovery, receive-address
consent, other device models and clean upstream reproduction remain later gates.
The current bottleneck is native runtime evidence, not adding more features.

The largest-free-run threshold for the current response is **4,097 blocks of
16 bytes**. Aggregate free bytes cannot answer whether that allocation fits. The
secondary pool is smaller than this request, so a sufficiently large run must
belong to the primary pool. Fixed diagnostic records themselves consume RAM and
scanning costs time; both must be accounted for in the measured image.
