# Safe 5 heap sampler preparation

10 September 2026 UTC. Unadopted diagnostic component; no device execution.

The fixed-size C sampler is implemented and compiles with the recorded Safe 5
native C configuration. Eight host checks pass against the actual pinned
MicroPython garbage collector. The sampler records occupied bytes, free bytes
and the largest contiguous free run at six named phases, without allocating or
forcing collection. It stores counters only, with a validity bit for each phase.

This makes the measurement component concrete. It is not yet connected to the
signing workflow or a USB retrieval endpoint, and no new firmware image was linked.
The prior caller candidate remains at **23.5 KiB flash headroom**, with actual
native memory peaks and latency still unmeasured.

## What the checks establish

The host harness compiles the unmodified collector source at MicroPython revision
`579c7624bd2224c7e038504e4bc3de591a9fbcf9`. It compares sampler results with a
separate occupancy model based on returned allocation addresses and rounded
request sizes. That model does not read the collector's allocation table.

The eight checks cover empty pools and unit conversion, separate-pool allocation
failure, all six phase records, phase overwrite, invalid represented enum values,
fragmentation, collection/recovery and explicit reset. In a fragmented host case,
**24,256 bytes were free but the largest run was only 32 bytes**; a 64-byte
allocation correctly failed. Earlier records survived that failure. This tests
why aggregate free space alone is insufficient.

The harness uses 32 KiB and 16 KiB backing arrays, 64-bit pointers and 32-byte
collector blocks. It supplies explicit test roots, disables automatic collection
for controlled allocation failures, and invokes real marking/collection directly.
It does not exercise VM stack/register roots, native UI roots, real firmware
cancellation, finalizer-bearing objects or automatic collection after OOM.

Two private source mutations were rejected at their intended assertions: removing
the block-to-byte conversion and omitting a validity bit. Independent local
source, clarity and evidence review passed without a sampler change.

## Native component cost

| Evidence from the unlinked ARM object | Bytes |
|---|---:|
| Fixed storage for six records and validity | 76 |
| Three functions, total code | 192 |
| Capture function's own stack frame | 40 |

The native instructions multiply the collector's largest-run count by 16,
matching the selected target block size. The object's external references are
the collector statistics function, `memset` and stack-protector support; it has
no heap allocator reference. A source review checks that the selected collector
statistics path also performs no allocation or collection.

These object sizes are not net changes to a linked firmware image. Placement,
alignment, stack callers, scanning time and later USB serialization must be
accounted for after integration. Phase records hold the latest value for each
phase; they are not continuous peak measurements. They also exclude the separate
Rust signing arena.

## Remaining work

Connect capture to the native validation/review/response/sign/cancel boundaries,
preserve records through failures, and retrieve them only after cleanup through
a bounded synthetic USB path. The sampler requires an initialized, quiescent
collector and serialized calls from the existing trusted executor. Those
preconditions are documented, not enforced by this standalone component.

Then measure real heap fragmentation and allocation recovery alongside complete
stack/arena use and processor timing. No debugger access to the unopened retail
Safe 5 is assumed. Existing pending Fable packets remain unchanged; this new
component still needs adversarial review before adoption. Automatic approval
review rejected its frozen packet before process creation because it requires
exact-payload and destination authorization. A grouped approval request covers
all four pending packets; nothing was transmitted.
