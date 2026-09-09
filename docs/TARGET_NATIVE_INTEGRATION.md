# Safe 7 native integration progress

The emulator bridge now has a reviewed target execution-context adapter and isolated frozen build inputs. **The full target application has not yet been linked or run.** Accepted approval core, passing emulator images, 32 KiB stack and 128 KiB arena are unchanged.

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

Two failed offline attempts are preserved: the initial cache lacked linked_list_allocator; metadata then needed baseline dev-dependency archives such as fastrand. The missing archives were found in the retained allocator-build cache and verified against lock checksums. No dependency pin changed and no network download was used.

Fable raised the correct integration concern that a global allocator affects all linked Rust code. The next single bounded ELF/map build must inspect allocation/deallocation callers, pre-bind and teardown paths, the actual panic/OOM path, context-check callers, kernel compatibility, and arena/stack/GC/flash placement. Source searches and this one C object cannot establish those properties. A link itself executes none of the firmware; its result is not accepted until those checks pass. Runtime resource/concurrency/fault/consent tests and hardware authorization remain separate gates.

Exact local evidence is under `work/target-native-integration/`: `build-inputs/resolution-03.json`, `executor-compile/report.json`, `executor-compile/instruction-review.json`, both clarity reviews, and `PARENT_DISPOSITION.json`. The frozen original proposal/failed attempts stay intact. The public adapter's sole C delta from the Fable-reviewed source is the recommended comment clarification; emitted instructions/relocations match.

- Fable packet SHA-256: `8187ce33ff5acb169bcb39657d5b4edcd509e1670f31236023a87e4c9fdb257d`.
- Reviewed C source: `90931dfff8be6ea1905478ac7e1430f136c346e61f5abf08979d9ef232fcf216`.
- Public C source: `1baa02fc8e2e3cdf7d29c5d6de7e9373e7cb22e4dd76a71960e2bd2ad83e5105`.
- Full-flags C object: `2b596893bba99fc684b67b4c7d45a5d958d79eea09e012d5e0961a4c9119a70a`.
- Derivative lock: `e76245fd1c3ec4247d5ce621ff18c62f787d37f8f9e811cfe773ff2d6f5a476b`.
- Project log: `f07bc4ea1ca93dc41e2cd68c781d300204352cf50bbd5d92e85e33a1baadbdcf`.

The source and compiler prerequisites are materially clearer; no integrated RAM/stack fit, complete clean-checkout demonstration or production readiness is claimed.
