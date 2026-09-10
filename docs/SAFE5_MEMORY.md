# Safe 5 memory status

Snapshot: 10 September 2026 UTC. Native image `ab110d7e1709c4e3b28f6042226c489a738b1d5819f42ad546ee9b59d1452c12`.
Firmware base `7105338e3c2c1e681940e17780609881ce53126b` plus the reviewed experimental changes.

**The synthetic image now fits in flash. Runtime RAM and speed remain the main
uncertainties.** The linked image uses 1,637.5 KiB of the actual 1,664 KiB firmware
slot: 26.5 KiB remains, or 1.6%. This is a narrow margin, especially with native
transport/UI integration and production key handling still to add. We do not yet
know their net cost. The file's debug information is excluded from these numbers.

## RAM: what uses the space

The application receives 514.5 KiB in two separate RAM regions. These figures are
reservations from the actual linked image, **not measured live peaks or free heap**.

| Component | Reserved bytes | KiB | Assessment |
|---|---:|---:|---|
| Existing UI image buffer | 115,200 | 112.5 | Large; no proven safe reduction yet. |
| Existing UI drawing buffers | 86,244 | 84.2 | Sharing requires evidence about rendering and concurrent lifetimes. |
| Ironwood signing arena, including guards | 131,104 | 128.0 | Fixed workspace; peak allocations need measurement before shrinking. |
| Primary garbage-collected heap | 92,880 | 90.7 | Main contiguous-allocation constraint. Metadata uses part of it. |
| Secondary garbage-collected heap | 41,696 | 40.7 | Recovered unused space; cannot extend an object in the primary heap. |
| Native function stack | 49,152 | 48.0 | Increased from 32 KiB; complete maximum still unknown. |
| Other statics and alignment | 10,572 | 10.3 | Exact residual reservation. |
| **Total** | **526,848** | **514.5** | All bytes reconciled once. |

The output bridge currently requests **65,537 contiguous bytes even for a small
signed result**. That leaves 27,343 nominal bytes in the primary region before
collector metadata and other live objects. The second heap cannot rescue a large
allocation that is fragmented or too large for the first. Output sizing/lifetimes
are therefore a higher priority than shaving isolated small functions.

The current linked image contains a source-feasible parsing chain totaling
**42,016 bytes (41.0 KiB)** of simultaneously live frames. This leaves only 7,136
nominal bytes of the 48 KiB reservation before interpreter callers, exceptions
and other omitted calls. It is a static subtotal, not a measured peak or whole
maximum. The largest frames are the approval entry (13,984 bytes), bundle parser
(8,880) and action parser (8,032). Reducing their live temporaries is a concrete
priority; the reservation alone does not prove signing fits.

The model also reserves memory outside these application slots, including two
115,200-byte display framebuffers and kernel/boot storage. That space is not an
unassigned application pool. The image buffer above is a separate allocation.

## Flash: component attribution

| Component group | KiB |
|---|---:|
| Shared or unattributed code/data | 476.9 |
| Python runtime, frozen apps and C bindings | 422.8 |
| Trezor Rust UI/services, inferred | 217.6 |
| Embedded kernel | 133.0 |
| C cryptography | 124.6 |
| Other libraries, platform code and padding | 111.2 |
| Embedded bootloader | 91.6 |
| Approval and transaction types, inferred | 59.8 |

Compiler optimization merges code and constants across libraries. These are
disjoint attributed bytes, not complete functional-module costs or predicted
savings from removal. For example, the approval row excludes much cryptography
and shared serialization machinery. Unresolved ownership stays explicit instead
of being assigned to a guessed module. It includes 178,474 bytes of overlapping
*input-map ownership*, not overlapping physical flash allocations.

Trezor's existing binsize source resolver additionally identifies frozen-app
subsets: Bitcoin 42.4 KiB, Monero 39.0, Cardano 32.2, Ethereum 31.3 and Solana 21.4.
These are already included above, exclude shared dependencies, and are not a
proposal to remove coin support.

## Optimizations already made

| Recorded change | Recorded flash extent change | Main tradeoff |
|---|---:|---|
| Python optimization and required Rust debug correction | 34 KiB | Changed test/diagnostic configuration. |
| Existing small-target Blake2b/Pallas inlining features | 40 KiB | Code sharing; arithmetic bodies unchanged. |
| Omit optional debug-link/UI diagnostics | 20 KiB | Fewer diagnostic facilities. |
| Compute Sinsemilla points instead of storing the table | 64.5 KiB net | Largest sampled host hash is about 16× slower; MCU effect unknown. |
| Select upstream's 2 KiB secp256k1 signing table | 20 KiB | Target speed still needs measurement. |
| Add split GC and reserve 48 KiB stack | **Adds 0.5 KiB** | More stack; 40.7 KiB secondary raw heap recovered. |

Early overflowing configurations use failed-link map estimates; successful builds
use their linked ELF extents. The initial native configuration exceeded flash by
151.5 KiB. The current one is 26.5 KiB below it. Total reduction is 178 KiB across these distinct configurations.
Host equivalence, approval, signature and collector tests support their stated
scopes; native execution has not occurred.

## Where to learn, and what to try next

1. **Measure allocation lifetimes first.** Track peak arena use, heap usage and
   largest free block through upload, validation, every review page, response
   creation and cleanup. Trezor documents workflow cleanup, careful persistent
   references and module sizing to reduce fragmentation. Its emulator offers
   memory logging; those desktop numbers must remain separate from MCU numbers.
   [Fragmentation guidance](https://docs.trezor.io/trezor-firmware/core/misc/fragmentation.html),
   [emulator tooling](https://docs.trezor.io/trezor-firmware/core/emulator/index.html).
2. **Continue using upstream compact implementations.** The secp256k1 small-table
   option already yielded a measured saving. Trezor's own binary analyzer supplies
   useful grouping, while our ELF interval accounting reconciles the full slot.
   [secp256k1 configuration](https://github.com/bitcoin-core/secp256k1/blob/master/configure.ac),
   [Trezor binsize](https://github.com/trezor/binsize).
3. **Investigate exact arithmetic and smaller frames from Ledger's Zcash app.**
   At inspected commit `22dc38537f9a84b31b938e3ca95434595ef378d3`, it avoids a lazy
   Pallas square-root table, separates commitment checks into smaller frames and
   borrows ciphertext rather than copying it. Our selected native source and
   machine code confirm that the table is enabled and initialized before PCZT
   processing: five permanent allocations account for 29,804 arena bytes (29.1
   KiB), **within** the 128 KiB workspace above. This is a source-derived allocation
   account, not a runtime measurement or an additional reservation. Disabling it
   would require resolving every dependency that enables it and revising the
   explicit five-allocation startup contract. Upstream provides exact table-free
   arithmetic; its speed and stack tradeoff still needs comparison. Removing the
   table would not automatically shrink the arena. Ledger's streamed design does
   not substitute for our full verification and immutable approval contract.
   [Pallas implementation](https://github.com/LedgerHQ/app-zcash/blob/22dc38537f9a84b31b938e3ca95434595ef378d3/ledger_zcash_crypto/src/hashtocurve.rs#L217),
   [Ironwood verification](https://github.com/LedgerHQ/app-zcash/blob/22dc38537f9a84b31b938e3ca95434595ef378d3/src/parser/pczt/ironwood.rs#L565).

Transformer work provides a useful principle: keep fewer intermediates alive,
tile work, and sometimes recompute instead of storing. FlashAttention demonstrates
exact tiling with attention to memory transfers. Applying that principle here is
an engineering inference, not a directly reusable implementation. Lossy numerical
approximation cannot replace exact cryptographic checks.
[FlashAttention paper](https://arxiv.org/abs/2205.14135).

## Keeping the report current

The offline reporter reads an explicit ELF, map, model memory definition and build
record, checks their identities, and emits a complete byte accounting and largest
symbol lists. It reuses Trezor's grouping/resolution code where applicable. No
firmware execution or cloud service is required. Each future meaningful memory
change should retain the preceding snapshot and compare flash, both raw heaps,
stack reservation, actual peaks, largest free block and target latency. Unknown
runtime values must remain unknown until measured.

## Latest experiment, separate from the settled snapshot

A newly compiled private parser boundary reduces the examined semantic stack
path from 42,016 to 31,504 bytes. A separately examined decoding path grows from
31,432 to 32,408 bytes. The larger candidate subtotal is therefore 9,608 bytes
below the previous semantic subtotal. This is promising evidence about temporary
lifetimes, not a complete stack bound or an executed hardware result. The helper
returns before semantic verification. Other callers/branches remain unresolved;
relocated crate identities and a generated version-header difference also limit
causal comparison. Candidate ELF: `0481ef96c34419a3538c1420d016f3292ba03d35d3dd0570d203f56a8e8066b0`.
The visualization and component totals continue to identify the settled image.

A second proposal would reduce the C response reservation from 64 KiB to 16 KiB,
based on a conservative 10,500-byte envelope for the unchanged eight-action
profile. This would remove a 48 KiB allocation request; it is not measured free
RAM. Two isolated tests of the real upstream encoder now pass: a maximal wire
envelope fits within 16 KiB, and a V6 logical round-trip preserves canonical bytes.
Their payloads are encoding placeholders, not cryptographically valid transactions;
exact output lengths were not printed in those encoder tests. A subsequent local
run passed two signing tests covering 44 round trips. The 12 new eight-action
variants produced **10,100–10,389-byte signed responses**, checking 68 new and 28
existing dummy signatures and preserving the entire object except newly added
real signatures. These include eight real spends totaling MAX_MONEY and mixed
real/padding spends, with valid OCK/anchor presence variants. The allocation and
test-source proposals remain unaccepted pending Fable review; neither these samples
nor the unchanged native layout establish a universal bound or runtime RAM fit.

The parser-boundary candidate has a selected signing-reparse subtotal of **27,072 bytes
(26.4 KiB)** and a selected v2 serialization subtotal of **11,016 bytes (10.8
KiB)**. These are separate phases. A coordinator check matched 17 frames and
17 call-edge checks against fresh disassembly and the actual ELF metadata. Neither
is a whole maximum; serialization capacity growth, allocator/drop paths, other
indirect calls, VM ancestry and interrupts remain unresolved. The next useful
measurement covers the complete C signing call rather than adding these sibling
subtotals. No native execution or new implementation change occurred.
