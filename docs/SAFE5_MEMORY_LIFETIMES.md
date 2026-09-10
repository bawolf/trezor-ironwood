# Safe 5: memory that must coexist during signing

The response buffer remains the clearest immediate RAM opportunity. Its current
65,537-byte request occupies **65,552 bytes after GC block rounding**. Only the
primary heap can satisfy that single allocation. After collector metadata, that
heap has **90,752 usable bytes**, leaving at most **25,200 bytes** before other
live objects. Whether a contiguous block that large survives boot and review is
still unmeasured.

These are source-derived capacities and ownership relationships for the settled
native image `ab110d7e1709c4e3b28f6042226c489a738b1d5819f42ad546ee9b59d1452c12`.
The firmware has not executed on a device. No allocation or transaction limit
changed in this investigation.

## Raw reservations versus usable pools

| Region | Raw reservation | Collector metadata, descriptor and alignment | Usable pool |
| --- | ---: | ---: | ---: |
| Primary | 92,880 B | 2,128 B | **90,752 B** |
| Secondary | 41,696 B | 992 B | **40,704 B** |
| Combined | 134,576 B | 3,120 B | **131,456 B** |

The pools remain separate. Adding their free bytes cannot make one larger
contiguous allocation. These pool capacities precede runtime occupancy; none is
a measurement of available memory after boot.

## What stays live

| Phase | MicroPython heap | Rust signing arena |
| --- | --- | --- |
| Validate input | Caller owns input for the call | Decoded PCZT, verification clone and temporary parsed data |
| Construct/retain review | Review objects; input only if the caller retains it | Retained PCZT, signing indices and two review projections |
| Allocate response | **65,552-byte buffer**, token and any retained review/input | Retained request still exists |
| Sign and serialize | Full response buffer remains allocated | Signing and bundle-replacement data, then owned PCZT and growing serialized vector |
| Copy result to C | Same response buffer receives the bytes | Serialized vector and local review/signature owners; consumed PCZT has already dropped |
| Return to Python | Buffer shrinks in place; bytes-object header added | Request owners have dropped; permanent table baseline remains |

The bridge borrows the input during validation; it does not make a full Rust
raw-input copy. The final Python bytes object reuses the C response storage, so
there is no second C payload copy. These useful properties do not eliminate the
overlap between that buffer and the arena's temporary allocations.

The compiled allocator grows a vector by allocating the new block, copying, then
freeing the old block. For example, **if** a vector grows from 8 KiB to 16 KiB,
those two buffers temporarily require 24 KiB together. That example is not an
observed capacity sequence or a measured arena peak for the signed fixtures.

## Stack result and measurement tooling

Fresh disassembly of parser candidate
`0481ef96c34419a3538c1420d016f3292ba03d35d3dd0570d203f56a8e8066b0`
closes one previously unresolved subtree: successful byte-vector growth uses at
most **256 bytes of ordinary stack from the reserve entry**. Allocation, copying
and freeing are sequential. This is not the whole serializer/signing stack, and
it excludes faults, interrupts and callers above reserve. The independent review
checked the other successful calls, indirect targets and tail-call restoration.

Trezor's existing unused-stack estimator is excluded by the current `PYOPT`
configuration. It scans for overwritten nonzero bytes, which can miss reserved
but untouched or zero-written frame space. Future measurements must pair that
kind of watermark with stack-pointer observations and static frame accounting.
The existing 48 KiB stack reservation and all previously reported full-peak
uncertainties remain unchanged.

## Next acceptance gate

The native module still needs its concrete trusted caller. That caller must use
`finally: cancel()` around validation, review and signing: Python review creation
or response allocation can raise before Rust consumes the retained request.
The C module documents this obligation but does not install the caller. Once
Rust returns normally from signing, its request owners are released before the
C idle check. Arena exhaustion instead traps without unwinding and needs its
own failure evidence.

The first runtime checks should measure primary-pool occupancy and largest free
run immediately before response allocation, plus complete arena/stack peaks.
Force review-object, response-buffer and final bytes-header allocation failures;
check cancellation, baseline restoration and subsequent collection separately.
Retain raw input only as long as required by the real caller.

The 16 KiB response proposal and its signing regression tests still await their
pending Fable reviews. Their earlier twelve measured signed responses were
10,100–10,389 bytes; those sizes alone do not establish whole-call RAM fit.

This investigation used the retained ARM C layout, source identities and actual
ELFs. The coordinator independently checked GC arithmetic and rehashed all thirty
audited source files. A separate agent reviewed the growth analysis for correctness
and human clarity. No new Fable review ran and no implementation was adopted.


## Subsequent host arena measurement

The instrumented host probe now builds with the settled engine/PCZT bodies and
computed-S/compact dependency configuration. One offline, locked metadata/build/link
sequence passed. The coordinator checked all 529 frozen preparation files and the
resulting binary, `b5ec02090686f918ac64b24d4472cd9882d169602b387c3f6cd465bdacea21d9`.

A single diagnostic sweep completed **12/12 cases in 8.25 seconds**. The largest
observed cumulative arena peak was **112,191 requested / 112,264 used bytes**
within the fixed 131,072-byte host arena. Every request restored the public-table
baseline of 29,802 requested / 29,808 used bytes and recovered a 65,536-byte
contiguous allocation afterward. No failure, timeout or retry occurred. The
coordinator revalidated all twelve raw reports and output-file hashes.

The largest peak first appeared during begin; it includes earlier startup/probe
activity and is not an isolated phase peak. End-of-serialization live requested
bytes were 4,576 lower than immediately after signing in every case, a net
observation that combines PCZT releases with output-vector allocations.

This probe owns a Rust input copy, creates its Engine per request, and uses static
C staging. It does not measure the persistent native bridge, MicroPython GC,
processor stack or target latency. The twelve newly emitted outputs still need
independent signature verification; allocator checks are not full signing acceptance.
