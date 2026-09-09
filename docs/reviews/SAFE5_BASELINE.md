# Safe 5 baseline preparation review

The unchanged baseline passed after a host execution-permission correction. This record covers preparation/evidence logic and the proposed execution-contract boundary. The final static map revealed a separate capacity obstacle; no native adaptation is accepted.

Two identical 53,579-byte source packets requested `fable[1m]` through the existing Claude Code account, with $15 allowances and 420-second limits. Packet SHA-256: `cd3f81c04ca91e7f847689da556232a35284e21a48b96e558595128dbdf89542`.

- First: exit zero after 147.298 seconds, but empty review text. Usage identifies `claude-opus-5`, reported $0.22188525. Recorded as an unsuccessful review.
- Retry: exit zero after 251.113 seconds with a delivered review. Streamed assistant text identifies `claude-opus-4-8`; usage identifies `claude-opus-5`. This is the user-authorized **documented Opus fallback**, not a confirmed Fable review. Reported usage $0.64017575. The differing labels are retained in the raw evidence.

Independent clarity reviews examined baseline preparation and the corrected execution note. The second checked all nine source hashes and twelve excerpts against the pinned Git objects. Neither reviewer ran firmware or accepted a port. Raw packets/results are under coordinator `work/safe5-baseline-review/` and `work/safe5-baseline-review-retry/`; clarity records remain beside the preparation notes.

## Findings and disposition

- **CMSE and runtime state:** accepted. Both actual project configurations use `-mcmse`; only kernel defines `SECURE_MODE`. The inspected kernel initializer stores `0xFFFFFFED`. The existing Safe 7 guard rejects this configuration. A full execution/callback/lifetime witness remains necessary; compiler flags alone do not establish observed runtime state.
- **MicroPython scheduler/thread settings:** retain as explicit contract inputs, but reject the reviewer's unsupported prediction that the scheduler is likely enabled. The pinned firmware `mpconfigport.h:87,136` defines both settings as zero. Do not conflate this scheduler with kernel task switching.
- **Clear before binding:** accepted. Establish binding after Core clears application memory; do not reset the lifetime word during Python teardown or weaken reentry checks.
- **Historical launcher versus active run:** accepted. Preserve the original 1,200-second proposal. Attempt one had a 1,008-second allowance and ended with a command failure, not a timeout. A separately recorded second attempt followed a successful diagnosis of the exact failed protoc command. The review's instruction not to retry described its frozen in-progress packet; it does not supersede the user's authorization for a diagnosed local build correction.
- **Terminal-only evidence and precise cache claims:** accepted. The checkpoint now exits before final hashing when terminal fields are missing or writers may remain. Reports say which recorded donor/index files matched; they do not assert all private cache contents stayed unchanged. The resumed label says unchanged test-preset baseline.
- **Environment completeness:** the actual saved environment provides PATH and exact tool paths. The second unchanged command completed; the first failure is specifically `/dev/stdout` permission. No absent-environment or source-incompatibility explanation is claimed.
- **Model evidence:** the independent review checked the pinned T3T1 model and full firmware feature filter. Final collected commands confirm the actual model/security defines. The first packet's excerpts alone were not a complete configuration witness.
- **Next priority:** the review was written before the map existed. Its CMSE result is not the sole determinant of feasibility: final AUX1 and flash headroom now make resource placement and code size the immediate gate. No generic adapter, forced model flags, relaxed stack/MPU protection, validation removal, or device installation follows from this review.

The corrected local inspection was run only after each build stopped. The coordinator independently rehashed settled artifacts, checked every allocated section and flash load segment, and verified the preserved first-attempt records. That static evidence accepts the unchanged build baseline only; final native memory, stack, callbacks and hardware behavior remain open.
