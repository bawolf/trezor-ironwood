# Safe 5 baseline and next native gate

The first physical test device is a dedicated Safe 5 (T3T1). Its unchanged test-preset build uses firmware pin `7105338e3c2c1e681940e17780609881ce53126b`, STM32U585 and the pinned default board revE. The physical board revision has not been observed. This baseline contains no Ironwood overlay.

**The unchanged baseline builds, but the current Safe 7 arena placement cannot fit.** The resumed build completed with exit zero in 75.674 seconds. Static inspection and source/lock preservation checks pass; no firmware executed.

| Measured region | Bytes |
| --- | ---: |
| AUX1 capacity | 196,096 |
| AUX1 data / BSS / no-DMA buffers | 512 / 123,288 / 28,628 |
| AUX1 unoccupied tail | 43,668 |
| AUX2 stack / buffers / GC region | 32,768 / 57,616 / 240,368 |
| Complete flash image / slot | 1,588,736 / 1,703,936 |
| Unoccupied flash tail | 115,200 |

The 131,104-byte arena including its two guards exceeds AUX1's tail by 87,436 bytes, before other integration state. The retained Safe 7 native image added 269,824 flash bytes, more than this Safe 5 tail; that is a warning for the next measurement, not a measured Safe 5 native delta. Resource feasibility now precedes the execution-adapter and UI port.

The coordinator rechecked all 15 recorded artifacts, every nonempty allocated section and every file-backed flash segment. All lie within the correct nonoverlapping regions. The complete image includes its matching 136,192-byte kernel and loaded data; these are not added again. All 91 frozen first-attempt evidence files remain unchanged.

- Firmware ELF SHA-256: `4c9a9fafbef3bed64f0ae4075e7cdda63ac9877148694ec34995da4a327258cb`.
- Firmware binary SHA-256: `0d9dd6d39b599d93ac71b936984ccb8e1a9d299b55117d29b0c8ead5f10a40e7`.
- Firmware map SHA-256: `682d28fcbd06fee06b4a60bd0ea1fa47804dfea811f012e088a23050c21f62bc`.
- Resumed build log SHA-256: `60bb6f951a455c4bfc783587dbdf371dca5c250a9a6faf0ec3336964b0e1fba3`.

Local evidence: `LOCAL/work/safe5-build-prep/run-02/{report.json,parent-verification.json,artifacts/}`, where LOCAL is the coordinator workspace. Inspection report SHA-256: `68b33477595b6329c7318ef1c207a2524c902c04cb2823324228071d351dc420`. These raw local artifacts are not yet a portable handoff package.

Run from the pinned checkout's `core/embed` with its recursive submodules and source-pinned tools:

```sh
cargo run --locked --profile xtask -p xtask -- build firmware --model t3t1 --preset test
```

The retained environment uses nightly-2026-03-16, Arm GNU 13.3.Rel1, host GCC 15, libclang, Python 3.12.8 and protoc 31.1. Two Cargo jobs and two C workers per build script are configured. Cargo and uv operate offline with separately copied registry inputs verified against the original lock. The test preset uses debug link, development keys and insecure test storage; it disables Optiga/Tropic. The build produces its matching kernel and performs local development-artifact signing/copying. It does not install firmware or test attestation.

The first attempt exited 1 after 991.861 seconds, before its 1,008-second allowance expired. Its matching kernel linked, but protobuf generation reported `/dev/stdout: Operation not permitted`. The unchanged protoc descriptor command then passed with approved execution outside the filesystem sandbox. The second attempt changes that host execution permission and reuses only this Safe 5 run's private compiler output. Original failure records and partial kernel artifacts are preserved separately. No firmware source, dependency pin, preset or memory setting was changed to address the failure.

## Next gate

First establish a viable arena placement and measure the full native flash cost before introducing the 128 KiB signing arena. Stack and Python GC occupy AUX2; their space is not automatically available for an AUX1 arena. A linked layout establishes placement, not concurrent runtime occupancy or a maximum stack bound.

A source-level candidate places only the guarded arena in the existing AUX2 `.buf` section, before GC, leaving 109,264 bytes of GC capacity. It retains the stack, existing section boundaries, kernel clearing and memory protections; it has not been implemented or linked. The remaining GC must still cover Python, UI, transport and response storage. Flash contributors include frozen Python and native code; no evidence supports deleting modules or weakening checks to make a fit claim.

The Safe 7 executor cannot transfer by substituting a model name. T3T1's kernel retains the `secure_mode` feature and its firmware project filters that feature out, but the common C build logic adds `-mcmse` for either `secure_mode` or absence of `secmon_layout`. Missing `SECURE_MODE` therefore does not establish nonsecure Core execution. The existing Safe 7 adapter rejects `__ARM_FEATURE_CMSE & 2`.

Actual project-source commands confirm `-mcmse` in both kernel and firmware, with `SECURE_MODE` only in the kernel and no `USE_SECMON_LAYOUT`. Kernel disassembly stores `0xFFFFFFED` in `systask_init` (`mvn.w r2, #18`). These are compiled facts, not observed runtime execution. After resource feasibility, establish a narrow T3T1 execution contract using these commands and the complete selected scheduler paths. Keep early IRQ/privilege/stack checks, one-time binding after Core memory clearing, reentry defenses and stack/MPU enforcement. Keep MicroPython thread/scheduler settings explicit; the pinned firmware config sets both to zero. Review the small adapter delta before a full native link. A native-only signing function still needs its trusted caller; Delizia review and older-wire transport remain separate integration work before a device session.

The independent clarity reviews are complete for preparation and these source-level claim boundaries. Adversarial review status and dispositions are in [the review record](reviews/SAFE5_BASELINE.md). Neither review accepts a native port or authorizes installation on the unopened device.
