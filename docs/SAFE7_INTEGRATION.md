# Safe 7 integration constraints for M2.1b

Source-only preparation, inspected 2026-09-08 UTC. The next project should measure
the **actual `ironwood-approval` core**, then decide whether a bounded firmware
experiment fits. No available approval RAM, flash or latency budget is established
by this document. Profile 1 remains synthetic regtest, Ironwood only.

## Source identity

Paths below use these revision keys (line numbers are inclusive):

- **U**: firmware root `upstream/trezor-firmware/`, revision
  `7105338e3c2c1e681940e17780609881ce53126b` from `upstreams.lock.json`.
  `work/firmware-t3w1/` has the same HEAD. Both checkouts were clean before and
  after inspection, including initialized emulator submodules; neither was edited.
- **M**: `work/firmware-t3w1/vendor/micropython/`, gitlink revision
  `579c7624bd2224c7e038504e4bc3de591a9fbcf9`.
- **I**: portable-core implementation based on
  `9c194e95c033cec11799513b9f287f9629199db1`, with inspected file hashes recorded
  below. Final acceptance hashes are in `BASELINE_RESULTS.json`; compare them
  before using these measurements or source line references.

## Verified resource facts

All sizes use bytes or binary KiB; reservations are shared firmware capacities.

| Fact | Exact source | Consequence for approval code |
| --- | --- | --- |
| T3W1 selects STM32U5G, default revC, **secmon_layout**, Eckhart UI and THP. Target is `thumbv8m.main-none-eabihf`; nightly is 2026-03-16. | U `core/embed/models/T3W1/model.toml:1-32`; `core/embed/projects/firmware/project.toml:4-41`; `core/embed/xtask/src/config.rs:50-55`, `219-250`; `shell.nix:52`. | Follow the selected model/project features, not a chip specification. |
| Non-emulator linking selects `memory_secmon.ld` when `secmon_layout` is enabled and the STM32U5G binary-specific script. Emulator linking uses host libraries instead. | U `core/embed/xbuild/src/trezor.rs:205-244`. | The alternate `core/embed/models/T3W1/memory.ld:54-59` gives 896 KiB AUX1, but is **not this selected layout**. |
| Application AUX1 RAM is **800 KiB (819,200 bytes)** at `0x20198000`. Separate reservations: MAIN_RAM 64 KiB, SECMON_RAM 96 KiB, FB1 768 KiB minus 512 bytes, FB2 768 KiB, boot arguments 512 bytes. | U `core/embed/models/T3W1/memory_secmon.ld:51-66`; `core/embed/sys/linker/stm32u5g/firmware.ld:3-6`. | Application stack, statics, TLS, buffers and heap share AUX1. Kernel, secure-monitor and framebuffer reservations are not additional approval heap. |
| Application stack is **32 KiB**. MicroPython sets its check limit to stack size minus 1,024 bytes (**31 KiB**). A separate enabled Python stack contains 1,024 objects (4 KiB on the 32-bit target). Kernel stack is separately 12 KiB. | U `core/embed/sys/linker/stm32u5g/firmware.ld:58-60`; `core/embed/projects/firmware/main.c:131-145`; `core/embed/projects/firmware/mpconfigport.h:40-43`; `core/embed/sys/linker/stm32u5g/kernel.ld:50-52`. | Rust/C calls consume the application native stack too. The Python check is not instrumentation of every Rust frame. Count the Python stack among statics, not as extra native-stack capacity. |
| GC region is `_heap_start.._heap_end`, after `.stack/.data/.tls/.bss/.buf`, extending to the end of AUX1. **37 KiB is only the link-time minimum-heap assertion.** | U `core/embed/sys/linker/stm32u5g/firmware.ld:24-25`, `58-91`; `core/embed/projects/firmware/main.c:143-145`. | Obtain actual heap extent from the linked image, then subtract GC metadata and simultaneous firmware allocations at runtime. Neither 800 KiB nor 37 KiB is a new Rust allocation allowance. |
| Firmware flash region is **0x342000 = 3,416,064 bytes = 3,336 KiB**, starting at `0x0805e000` (secure alias `0x0c05e000`). It contains headers, embedded kernel, application text/rodata, NRF/bootloader images and initialized data; the kernel embeds secmon. | U `core/embed/models/T3W1/memory_secmon.ld:30-34`; `core/embed/sys/linker/stm32u5g/firmware.ld:28-65`; `core/embed/projects/kernel/build.rs:23-30`. | This is the complete firmware slot, not incremental core space. Determine linked baseline-to-integration delta and remaining slot capacity; host binary size cannot supply it. |
| Emulator GC defaults to `1024*1024*(sizeof(mp_uint_t)/4)`: **2 MiB on its 64-bit host**, allocated with `malloc`. `-X heapsize=` overrides it; a `w` suffix scales with word size. Native-stack check starts from `600000*UNIX_STACK_MULTIPLIER` (normally 1,200,000 bytes on unsanitized AArch64). | U `core/embed/projects/unix/main.c:74-78`, `370-400`, `516-532`, `790-804`; M `ports/unix/stack_size.h:31-50`. | Neither default emulated capacity nor process RSS is a target limit. Even a heap-capped emulator retains host pointer sizes, allocator layout, code generation and timing. |
| Core admission caps the byte slice at **65,536 bytes** and accepts **1–8 actions** before upstream parsing. | I `crates/approval/src/wire.rs:1-7`, `116-149`; `crates/approval/src/lib.rs:327-342`. | These are unmeasured prototype admission limits, not a measured memory bound. Incoming storage must already be bounded before this scanner can inspect it. |
| Existing GC telemetry exposes total/used/free/largest-free space. Low-level `gc_info.max_free` is in blocks; the Python wrapper converts it to bytes. | M `py/gc.h:70-88`; `py/gc.c:813-823`; U `core/embed/upymod/modtrezorutils/modtrezorutils.c:471-531`. | Phase snapshots miss transient peaks. `update_gc_info` also asserts against decreased free space in emulator builds; do not use that leak-check helper as an unrestricted peak sampler. Use allocation-event counters plus snapshots/fragmentation data. |

## Existing integration seams

| Seam | Verified entry points | Smallest integration obligation |
| --- | --- | --- |
| Allocation | U `core/embed/rust/src/micropython/gc.rs:19-61`, `80-103`, `166-199`, `280-288`: `Gc::new/new_slice`, `GcBox::new`, `gc_alloc/gc_free`. Gc allocations require GC visibility, cannot honor arbitrary alignment, and ordinary Gc values do not run Rust destructors. I `crates/approval/src/lib.rs:1-5` uses `alloc::Vec`. | No `global_allocator` or `GlobalAlloc` occurrence was found by a pinned `git grep` over U `core/embed` (exit 1, no matches). GcBox is not automatically the core's allocator. Before linking, specify one allocator owner, capacity/accounting, alignment, root visibility, Drop/reallocation and OOM behavior. Do not merely wrap `gc_alloc` and assume Rust allocation semantics are satisfied. |
| Entropy | U `core/embed/rust/src/trezorhal/random.rs:31-32` calls `random_buffer`; `core/embed/sys/rng/stm32/rng.c:41-88` maps it to MCU RNG. Strong RNG mixes MCU plus enabled Optiga/Tropic sources and fatally checks failures/use flags: `core/embed/sec/rng/rng_strong.c:38-83`. Firmware syscall stubs are `core/embed/sys/syscall/stm32/syscall_stubs.c:669-677`; secmon forwarding is `core/embed/sys/smcall/stm32/smcall_stubs.c:20-25`, `340-347`, with writable-buffer checks in `core/embed/sys/smcall/stm32/smcall_verifiers.c:460-481`. | I `crates/approval/src/lib.rs:173-181`, `253-281` takes trusted `RngCore + CryptoRng`: session generation is fallible; signature RNG failure must stop signing, not supply fallback bytes. The ordinary Rust byte helper is not the strong-RNG helper. Select/adapt this boundary explicitly in a later experiment. |
| Emulator entropy | U `core/embed/sys/rng/build.rs:6-15` enables `USE_INSECURE_PRNG`; `core/embed/sys/rng/unix/rng.c:27-59` guards the host-only deterministic mock. | Useful for reproducible synthetic measurements and failure injection; no evidence of physical entropy quality or secure-element timing. |
| Trusted review events | U `core/src/trezor/ui/__init__.py:402-438` reads `io.BUTTON/io.TOUCH`; `core/embed/rust/src/ui/layout/obj.rs:504-519` dispatches Rust touch events. Eckhart output/total entry points are `core/src/trezor/ui/layouts/eckhart/__init__.py:561-574`, `904-937`; confirmation/cancellation handling is `core/src/trezor/ui/layouts/common.py:43-88`. | Future M2.1c must render I `Review::projection` and invoke `Engine::approve(review.token())` only after the corresponding confirmed layout result. Bind cancellation/replacement to `Engine::cancel/begin`; UI copies remain live alongside Pending. Host `ButtonAck` is protocol synchronization: U `core/src/trezor/wire/protocol_common.py:220-235`, `core/src/trezor/ui/__init__.py:256-277`; it is not consent. |
| Signing/workflow | U `core/src/apps/workflow_handlers.py:94-95` routes SignTx; `core/src/apps/bitcoin/sign_tx/__init__.py:48-105` separates transport calls and UI confirmations. Existing Zcash selects v5 and signs transparent ECDSA inputs: `core/src/apps/zcash/signer.py:34-38`, `65-76`. I `crates/approval/src/lib.rs:241-308` consumes Pending before signing, rechecks its effect digest and returns signatures only after success. | Reuse the workflow/event structure, not the existing Zcash signing algorithm. Keep the retained PCZT and low-level Ironwood signer private; no replacement-PCZT/signing callback from transport. The compile probe auto-approves and must never become a transport handler (I `experiments/embedded-probe/src/lib.rs:11-28`). |
| THP transport | U `core/src/trezor/wire/__init__.py:107-111` allocates two ThpBuffers; `core/src/trezor/wire/thp/memory_manager.py:11-36` fixes each at **8,704 bytes** and rejects larger requests. `core/src/trezor/wire/thp/channel.py:216-227`, `229-236` use them for send/receive. | Reserve **17,408 bytes of buffer payload plus object/protocol overhead** in shared live-memory measurements. 8,704 is not the maximum encoded PCZT payload after framing overhead. A 64 KiB admission cap cannot be treated as a single THP message; M2.1d needs bounded application chunking/reassembly and disconnect cleanup. Packet fragmentation alone does not enlarge these buffers. |

## Smallest resource-measurement acceptance plan

This is proposed work after M2.1a acceptance, **not work executed here**. Keep the
baseline checkouts read-only; put any later harness/instrumentation in an isolated
experiment. Do not add a device key-store, transport handler or consent UI to M2.1b.

1. **Freeze and exercise the real core.** Record source/lock/fixture hashes,
   compiler, target, features, optimization/LTO/panic settings and concrete
   synthetic RNG type. Use `default-features = false` in an isolated measurement
   binary so test builders do not unify their heavier features into the measured
   core. Generate fixtures beforehand using existing helpers, then measure
   `Engine::with_rng → begin → approve → sign → drop`, not the builder, a
   surrogate validator or only `wire::preflight`. Automatic approval is confined
   to this synthetic harness.

2. **Use two small action series.** For n=1..8 use
   `build_actions(n)` (I `crates/approval/tests/common/mod.rs:163-248`), which
   explicitly uses unpadded Ironwood and alternates payments/internal change.
   It has **one real spend**, confirmed by
   `crates/approval/tests/action_bounds/mod.rs:31-52`. Add n=2..8 cases from
   `build_inputs(&[100_000; 8][..n])` (I `crates/approval/tests/common/mod.rs:252-330`)
   to measure multiple signatures: **15 positive fixtures total**, with the n=1
   case shared. Record/assert actual encoded action count, real spend/signature
   count, output count, padding, byte length, anchor and OCK presence; never infer
   count from a helper parameter. Verify every result with the pinned upstream
   signature/digest oracle outside the timed/allocation window. The existing
   action-bounds checks provide that pattern at I
   `crates/approval/tests/action_bounds/mod.rs:46-109`.

3. **Measure native host allocations and latency first.** Run one fixture at a
   time with a counting allocator that does not allocate while recording. Report
   alloc/realloc/dealloc counts, cumulative requested bytes, largest request,
   peak simultaneous live bytes and retained bytes at each phase. Keep the raw
   input buffer and returned Review alive through signing; report their baseline
   and count any serialization buffer separately. Reset phase peaks without
   forgetting allocations carried over from earlier phases. Use one untimed
   warm-up and five recorded runs per fixture, reporting median/max elapsed
   time and the first-run result separately. Exclude fixture construction,
   logging, oracle verification and human review time; retain RNG cost.
   Instrumented timings are host regression evidence, not MCU deadlines.

   Attribute measured peaks to the source-visible copies: parsed PCZT plus
   `pczt.clone()` into Verifier (I `crates/approval/src/lib.rs:342-381`);
   returned and retained Review (same file `227-239`); effect extraction at
   validation and signing (`crates/approval/src/effects.rs:16-34`,
   `crates/approval/src/lib.rs:267-281`); signatures/result ownership
   (`287-308`). Inspect generated target frames for crypto/recovery temporaries
   (`485-537`, including 512-byte memo comparisons). Heap counters do not count
   stack; `size_of` alone does not reveal inlining, spills or call-chain depth.

   Reuse one maximum-action input for cancel/drop, replacement/drop and repeated
   sign/drop checks; require no residual core-owned allocations after full
   teardown. Add a 65,537-byte input and an encoded nine-action header to confirm
   rejection before upstream parsing/allocation. Exercise session-entropy failure
   and interruption after a first signature using the existing randomness-test
   pattern (I `crates/approval/tests/randomness/mod.rs:141-161`). For a capped
   allocator test, require either rejection or fail-stop without a signed response;
   ordinary Vec OOM is not promised to return the core's `Error`. Do not use
   host panic-unwind success as evidence of MCU abort/reset cleanup.

4. **Separate the evidence gates.**

   | Gate | Required evidence and acceptance |
   | --- | --- |
   | Host resource characterization (first bounded deliverable) | A 15-row fixture result table with the phase metrics above, verified signatures/digests, retained-memory/failure results and exact provenance. Identify the observed worst cases and copies. This can complete useful measurement work while target feasibility remains unresolved; the sample matrix is not a worst-case proof for every admitted PCZT. |
   | Target link feasibility | Link a concrete instantiation of the actual core with an explicit bounded allocator/RNG adapter, using the selected T3W1 secmon layout and firmware settings. Record full baseline/integration ELF/map, text/rodata/data/BSS/TLS/buffers, stack symbols and `_heap_start/_heap_end`; ensure the exercised core is not dead-stripped. Include firmware/kernel/secmon and embedded images, not just the probe archive. Require all region constraints, including the 37 KiB minimum, to hold. A reserved arena in BSS reduces the remaining GC heap; account for it once. The existing generic `cargo check` supplies none of these linked-size results. |
   | Shared runtime feasibility | Execute the same core through a minimal synthetic T3W1 emulator entry point with its actual allocator boundary. Observe boot/idle and input/review/signing peaks, GC metadata/fragmentation, allocator failures and teardown, with existing THP buffers and live review objects accounted for. Run a documented heap cap derived from the target-linked extent as a pressure test, not as an exact target model. Collect peaks at allocation events; snapshots alone miss them. UI event/transport consent acceptance remains M2.1c/d. |
   | Remaining MCU claim | Target code/frame inspection is required for the 32 KiB native stack; whole-call-chain evidence must include C/crypto, not merely the largest Rust frame. U `core/embed/upymod/modtrezorutils/modtrezorutils.c:412-446` offers target unused-stack instrumentation, but clearing is disabled in emulator. Host/emulator execution cannot establish MCU stack high-water, MCU latency, physical entropy or watchdog responsiveness. Leave these unresolved until suitable separately authorized target execution; no hardware work is part of this plan. |

For a future shared-heap fit claim, compare **total concurrent allocator occupancy**
(including input, Pending, returned Review, UI/THP, runtime and allocator metadata)
against the linked region, and require a sufficient contiguous free block for
the largest allocation. Report measured residual space and an explicitly chosen
reserve for unmeasured work; no reserve or deadline has yet been justified.
Exceeding a measured capacity is a concrete reason to propose a later reduction
in admitted actions/copies, not permission to enlarge linker regions or bypass
verification. Do not report M2.1b as a Safe 7 fit result while its required link
or runtime evidence is missing.

## Inspected local source SHA-256

| I path | SHA-256 |
| --- | --- |
| `Cargo.lock` | `56d39e1f4ccec7ac6ee6486e7fb27352278210f3f7ba82b697d998f84ee6de9d` |
| `crates/approval/Cargo.toml` | `ea0fbb0a9913e230cb8c83bbd7bbe74869dad04957c627d4809b2a47c86447e8` |
| `crates/approval/src/lib.rs` | `3500810c65dd3550bca2efe84248b38d3e725755eccd95cc3f48b061bbb6d5c8` |
| `crates/approval/src/wire.rs` | `5b05163b419f90d861f1ba5432c62ce0a5690bc747d53c4a9a863804b40413ce` |
| `crates/approval/src/effects.rs` | `1eed05b5b9c8831577f564d071d46d25873530a96df5890a24b3ee33e870f1ef` |
| `crates/approval/tests/common/mod.rs` | `ad225b031d9dc954a82d7046d1766bbf8ae011f5f652117e525c7909268c8c53` |
| `crates/approval/tests/action_bounds/mod.rs` | `3f66e3782b65bc842f7bf530e13d0a21d0137b4791e57e62db385cb62eaccf0f` |
| `crates/approval/tests/randomness/mod.rs` | `7f7daa86cb188ac001fd0136a511aba3f2590698b6f33a0ef68abe9af3ce9e58` |
| `experiments/embedded-probe/src/lib.rs` | `120e9c7dd45eef9edb88ace1b06a62ad5ba3dae1a0c0d0fd02a6ad53ac83a083` |

Evidence here is source inspection, revisions and hashes. No benchmark, target
link, emulator execution or hardware measurement was performed for this document.
