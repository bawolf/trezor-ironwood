# Safe 7 native integration progress

The full Safe 7 native application now links with the reviewed execution-context adapter and frozen inputs. **Its static RAM/flash layout fits; runtime acceptance remains pending.** Accepted approval core, passing emulator images, 32 KiB stack and 128 KiB arena are unchanged. This native-only slice is neither a physical consent flow nor a Safe 5 image.

The pinned T3W1 configuration has one unprivileged Core task and no external app loader. A real IPSR/CONTROL check plus one-time lifetime binding can reject unsupported execution contexts without a new task-ID syscall. The matching kernel configuration and closed native call graph remain requirements. This catches integration mistakes; it cannot defend against arbitrary same-Core, privileged or DMA corruption.

The [small standalone adapter](../experiments/target-executor/README.md) is now tracked with its license and a portable compiler recipe. The wider frozen native overlay has three dependent review units: arena/startup, native module, and application wiring. Synthetic sign requires a trusted caller; this native-only slice has no trusted Python route or boot/wire invocation. Local dependency placement and product key/entropy/consent integration remain incomplete.

## Completed evidence

| Check | Observed result |
| --- | --- |
| Scheduled project checks | 27 passed, 1.72 seconds |
| Source materialization | 24,440 pinned baseline files match before overlay; baseline remains clean |
| Offline resolution | Frozen metadata succeeds; all 127 existing firmware packages/checksums preserved, 110 packages added |
| Registry archives | 206 match their resolved lock checksums; new registry additions match pinned librustzcash except the already-used allocator 0.10.6 |
| Actual ARM C compilation | Exact candidate compiles with retained upymod flags; wrong-mode branches precede state access; protected helpers and real atomic instructions retained |
| Negative configurations | Seven expected preprocessing rejections; no supported build gate disabled |
| Portable object recipe | Only pinned CMSIS/MicroPython/port headers and ARM compiler needed; instructions/relocations equal the full-flags object |
| Independent reviews | Confirmed Fable5.1 and separate clarity review, with [explicit dispositions](reviews/TARGET_NATIVE_INTEGRATION.md) |
| Full native application link | Exit 0 in 283.303 seconds; frozen ELF/map/381-command C database; unchanged source and protected inputs |

Two failed offline attempts are preserved: the initial cache lacked linked_list_allocator; metadata then needed baseline dev-dependency archives such as fastrand. The missing archives were found in the retained allocator-build cache and verified against lock checksums. No dependency pin changed and no network download was used.

Fable raised the correct integration concern that a global allocator affects all linked Rust code. The linked image retains allocator/executor checks, module registration, startup/teardown checks and selected direct trap paths. Actual application commands preserve the no-loader configuration. Full transitive/indirect allocation callers, all pre-bind/teardown and panic/OOM paths remain under inspection. Source searches and selected machine-code paths do not establish complete coverage; the link executes none of the firmware. Runtime resource/concurrency/fault/consent tests and hardware authorization remain separate gates.

Exact local evidence is under `work/target-native-integration/`: `build-inputs/resolution-03.json`, `executor-compile/report.json`, `executor-compile/instruction-review.json`, both clarity reviews, and `PARENT_DISPOSITION.json`. The frozen original proposal/failed attempts stay intact. The public adapter's sole C delta from the Fable-reviewed source is the recommended comment clarification; emitted instructions/relocations match.

- Fable packet SHA-256: `8187ce33ff5acb169bcb39657d5b4edcd509e1670f31236023a87e4c9fdb257d`.
- Reviewed C source: `90931dfff8be6ea1905478ac7e1430f136c346e61f5abf08979d9ef232fcf216`.
- Public C source: `1baa02fc8e2e3cdf7d29c5d6de7e9373e7cb22e4dd76a71960e2bd2ad83e5105`.
- Full-flags C object: `2b596893bba99fc684b67b4c7d45a5d958d79eea09e012d5e0961a4c9119a70a`.
- Derivative lock: `e76245fd1c3ec4247d5ce621ff18c62f787d37f8f9e811cfe773ff2d6f5a476b`.
- Project log: `f07bc4ea1ca93dc41e2cd68c781d300204352cf50bbd5d92e85e33a1baadbdcf`.

## Linked layout and remaining stack gate

| Region | Linked bytes | Delta from unchanged baseline |
| --- | ---: | ---: |
| Stack | 32,768 | 0 |
| Data | 2,048 | +1,536 |
| BSS | 146,656 | +131,404 |
| Buffers | 72,676 | 0 |
| GC region | 565,052 | -132,940 |
| Flash load extent | 2,639,360 | +269,824 |
| Flash slot remaining | 776,704 | -269,824 |

The contiguous RAM regions sum to 819,200 bytes. The arena storage is 131,104 bytes: a 131,072-byte payload and two separate 16-byte guards. Total extra static RAM is 132,940 bytes, or 1,868 beyond the payload. Flash extent includes loaded data; the 21,685,628-byte debug ELF file size is not flash occupancy. Parent checks confirmed the frozen artifact hashes, RAM arithmetic and actual ELF load headers.

The first attempt stopped with duplicate core metadata because `-Zbuild-std=core` left alloc using prebuilt core. The separate retry uses `-Zbuild-std=core,alloc`, matching the earlier allocator build; no source, profile, lock, feature or kernel changed. A [scoped Fable review](reviews/HARDWARE_PREPARATION.md) also checked this command-only correction. Both attempts remain preserved.

A candidate linked begin → validate → into_parsed_inner → parse_action_inner chain has local frames totaling 32,912 bytes, 144 above the stack reservation before C/VM/deeper costs. This is not yet a simultaneous stack bound: SP/control-flow and input-feasibility analysis remain. No target overflow was observed. Full native stack, concurrent GC/arena occupancy and latency remain acceptance gates; static placement is not runtime fit.

Exact evidence: `work/target-native-integration/LINK_REPORT_02.md` and frozen `link-02/artifacts/`, with selected calls and frame evidence in the same run. ELF SHA-256: `519802795dc6ac51363dac8449f49131b2e942c2cf8612ba2701c82d358c5e48`; map: `9d21fd0ad700c7b27f4e3a56f1e5b4b8006066ade081879c0ceba62ff41c7549`.

The user has an unopened Safe 5 for first hardware testing. It needs its own baseline and native/Delizia/older-wire integration; these Safe 7 figures are not a Safe 5 capacity result. Complete clean-checkout demonstration and production readiness remain unclaimed.
