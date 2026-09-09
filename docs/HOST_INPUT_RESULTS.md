# Bounded host-input bridge candidate

The isolated native bridge now validates caller-supplied PCZT bytes instead of a
compiled fixture. The first host run passes failed-replacement, ownership and
signing checks, including a second distinct valid transaction. This is a local
candidate under `work/emulator-host-input/`. It is now integrated into a separate
[passing THP emulator](TRANSPORT_RESULTS.md); the earlier fixed-fixture image
remains unchanged. Hostile transport acceptance and current-source follow-up review
remain separate.

## Behavior and checks

Every `begin` attempt cancels any prior review. Null, empty and inputs above 65,536
bytes are rejected before constructing the Rust slice. The unchanged approval core
owns the parsed PCZT after this synchronous call; neither language adapter retains
the caller pointer. Keys, RNG, policy, signing and cancellation remain synthetic
and unchanged. The C binding accepts one readable MicroPython buffer and preserves
executor, arena and conversion checks. Trusted Python must still cancel in `finally`.

| Check on 2026-09-08 | Result |
| --- | --- |
| Project evidence-runner baseline | 27 passed, 2.24 seconds |
| Native C-ABI lifecycle with actual approval core | One serial scenario passed; 112.438 seconds including fresh offline compilation |
| Invalid replacement and replay | Empty, truncated, exact-limit malformed, oversized and null input revoke earlier consent; consumed tokens cannot sign again |
| Caller storage ownership | Overwrite and free the input after validation; the independently verified signed result preserves the original transaction |
| Distinct valid caller input | 2,429-byte two-input fixture and 10,037-byte eight-output fixture both sign |
| Independent signature/effects oracle | Both new responses pass, three newly generated real-spend signatures, 2.914 seconds |
| Pinned C headers/qstr with GCC 15 | Compile-only object passed with warnings fatal, 1.228 seconds |
| Pinned Rust Clippy | All targets passed with warnings fatal, 35.305 seconds |

The oracle requires fifteen corpus entries. Thirteen old responses are controls;
its printed total of 43 signatures is not 43 new signatures from this candidate.
The native responses contain 2,557 and 10,101 bytes respectively. Their SHA-256s:

- Two-input response: `19442ea37fd2e4ae7b0120ae79d1e2ccbab67b643594b8ac70c3f4497e7aa532`.
- Eight-output response: `5863e3e6d29c4c663d164c9e467ce5c15ed8758208210056ab93560712c5f9b4`.

## Integration status

The [typed THP upload and signed response now pass](TRANSPORT_RESULTS.md) in a
separate derivative with 1024-byte chunks, existing trusted review and cleanup.
That result executes the real native bridge with the fixed 128 KiB arena; the
host-native measurements above continue to use a host allocator. Neither result
establishes a new arena peak, MCU stack fit or production key integration.

The confirmed Fable 5.1 transport packet includes this native Rust/C candidate.
Independent clarity review and the [finding dispositions](reviews/TRANSPORT.md)
explain remaining runtime obligations. The original exact-payload approval blocker
is resolved; both approved review packets completed. A new packet covering the
later THP driver and one-line descriptor correction is now running after approval.
Candidate hashes remain in `work/emulator-host-input/verification.json`.
