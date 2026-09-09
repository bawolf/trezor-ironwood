# Synthetic THP upload and signing

A desktop client now uploads a synthetic PCZT through the Safe 7 emulator's
normal THP session, receives the trusted on-device review, and obtains the signed
PCZT after the final hold. The independent oracle verifies both returned
real-spend signatures and preservation of the transaction's fields and digests.
This is one successful synthetic transaction, not production device support.

## What ran

The isolated derivative is based on firmware commit
`7105338e3c2c1e681940e17780609881ce53126b`. It uses the existing THP framing,
encryption, protobuf decoder, session dispatcher and UI. Five local prototype
messages use MessageType IDs 32000–32004; no upstream IDs have been assigned.
Only the upload starter is registered, under debug/emulator/THP guards on the
primary interface. The host cannot invoke native approval or signing directly.

The native bridge validates bounded caller bytes and retains its own verified
PCZT. The upload buffer is released before review awaits. Existing trusted
screens display that native projection and sign its token only after a hold.
All exits cancel pending native state. A registered workflow owns the transfer;
the existing scheduler supplies five-second reply timeouts and a separate
180-second overall closer. This is a cooperative deadline: synchronous native
work cannot be preempted by its coroutine timer. It is an experimental review-time
limit, not an established human usability allowance for eight-output transactions.

| Check | Result |
| --- | --- |
| Pinned schema generation and real desktop protobuf/session tests | Generation reproducible; 12 host test methods pass; no collision or native descriptor-ID overflow |
| Device lifecycle with the actual pinned scheduler | 12 pass, including replacement, cancellation, bad chunks, timeout and response failure; native/messages/UI remain doubles in this lane |
| Adapted trusted UI regression suite | 11 retained UI cases and two relocated handler validation cases pass |
| New emulator build | Passed in 484.11 seconds within the 600-second limit |
| Build after native protobuf API correction | Passed in 35.29 seconds, same locked dependencies and resource settings |
| Real THP transaction, 2026-09-09 UTC | Passed in 14.06 seconds; external supervisor passed in 14.50 seconds |
| Final consent | All seven exact review pages checked; 300 ms press plus 2.31-second wait produced no signed response; 2200 ms hold succeeded |
| Response and cleanup | 2557-byte PCZT, final Success, emulator alive after delivery; both process groups gone after explicit cleanup |
| Independent oracle | Passed in 1.54 seconds; two newly returned real-spend signatures verified, fourteen historical corpus responses used only as controls |
| Evidence stability | 794 source/fixture/build-record files unchanged during the run; current and retained image hashes unchanged; 176 PNGs captured |

The host uses the pinned desktop library with seedless THP session 0 and no seed
load. The runtime clears Python/MicroPython path overrides and boots frozen
`main` in a fresh profile. It uses debug-link touches to exercise the real UI;
these are emulator tests, not physical button measurements. The parent visually
inspected receiver, fee and hold PNGs in addition to the raw-layout assertions.

Input and output limits are independently 65,536 bytes, with exact chunks of at
most 1024 bytes. The largest canonical response message is 1053 protobuf bytes,
1076 including THP overhead, inside the existing 8704-byte buffer. These are
application bounds; unknown/duplicate protobuf fields retain upstream semantics.
Input-size admission alone does not promise a valid, signable transaction: the
core additionally restricts fields, encodings and action counts. No valid PCZT
near the byte ceiling has been demonstrated. Native insufficient-output-capacity
tests require zero bytes written and consumed consent; real THP admission-bound
rejection and recovery remain outstanding. Keep these distinctions when assessing
the reviewer's hypothetical near-limit signing expansion.

## Failure found by the real runtime

The first run failed before native validation and before any review screen.
The handler used Python's `isinstance` on a native protobuf message-definition
object, which is callable but is not a Python class. The first 1024-byte chunk
decoded correctly, then the handler returned FirmwareError and cleaned up.

The correction uses the pinned native API, `expected_type.is_type_of(reply)`.
Its implementation compares message-definition offsets and returns false for
the scheduler's integer timeout result. The device test double now models
nonclass callable definitions. It reproduces the old TypeError and passes all
12 lifecycle cases with the correction. No compatibility wrapper was added.
The first failure, exact sources, logs and reports remain preserved.

Earlier scheduler testing also exposed context loss when closing a replaced
workflow. The handler restores its captured context with the existing helper
in the same registered task before I/O. An outer race around the whole UI was
discarded because UI exclusivity would close its own waiting parent. Neither
correction changes the firmware scheduler or adds a second state machine.

## Real cancellation and timeout recovery

A further single-process run sends actual host `Session.cancel()` at the final
hold, from the sole host I/O thread after its ButtonAck. It receives exactly
ActionCancelled (code 4, `Cancelled`), with no signed chunk or Success. The first
host thread finishes before a deliberate second exchange. That exchange uploads
again with a different transfer ID, shows all seven pages again, rejects the
short press, and signs after a fresh hold on the same emulator/session/channel.

The driver passed in 22.71 seconds and supervisor in 24.17 seconds; 796 source
files and both image hashes remained unchanged, with 185 captured PNGs. Its
2557-byte response is byte-for-byte identical to the previously verified oracle
input. The parent recorded that binding in
`cancel-retry/attempt-01/parent-verification.json`; the oracle was not rerun on
identical bytes. This is host cancellation, distinct from the earlier debug-menu
cancellation test.

The separate timeout experiment has a mixed result:

- Withhold the first upload chunk for six seconds, consume the exact timeout
  ActionCancelled, then send GetFeatures: **passed**, returning the original
  device identity on the same session.
- In a second exchange, withhold the chunk for six seconds and send it late
  before reading the timeout: **failed**, raising
  `NoiseInvalidMessage('Failed authentication of message')` on the next read.
  No second GetFeatures was reached. This does not establish the reviewer's
  hypothesized pair of stale Failure replies; the observed result is an
  authenticated-channel error. The later source/packet diagnosis identifies
  discarded ciphertext in the desktop channel; explicit recovery remains unproven.

No signing approval was given in either timeout case. The failed run took 25.46
seconds; its supervisor reported failure with cleanup complete and no surviving
process groups. All 800 captured sources and both images were unchanged. The
experiment made no application retries or blind response drains. Evidence remains
in `recovery/attempt-02/`. An earlier harness-only failure blocked pairing because
it disabled the known setup interaction; its incomplete cleanup-check report and
independent post-run checks remain in `recovery/` and `recovery/attempt-01/`.
The corrected setup did not alter firmware or timeout predicates.

## Stricter rerun: exchange verified, overall acceptance rejected

The separate `acceptance-v2/attempt-01/` rerun completed seven pages, short-press
rejection, hold, three same-class signed chunks whose concatenation equals the
returned PCZT, fresh captures on changed pages and final Success. Its output is
byte-identical to the previously verified oracle input; no new oracle execution
is claimed. Source and image hashes remained unchanged.

The emulator then logged `Fatal: Assert at vm.c:327` and exited with macOS SIGBUS
(code -10) during cleanup. Although no process groups survived, this is **not a
clean native shutdown**. The driver and supervisor incorrectly reported passed;
`parent-acceptance.json` explicitly rejects that overall result and binds both
frozen reports. The cause is under separate source/crash diagnosis.

An unrun `acceptance-v3/` candidate rejects unexpected shutdown exits and emulator
exit before requested cleanup. A small isolated-function regression reproduces
v2's false acceptance of SIGBUS/SIGSEGV and verifies v3 rejects them. It uses fake
process/signals, not another emulator run. The underlying native failure remains
unfixed. Earlier successful evidence and all failed evidence remain preserved.

## Crossed-response diagnosis

The pinned desktop channel advances its receive sequence before the ACK reader
decides to discard a crossed response. That response never reaches Noise
decryption; the next distinct ciphertext uses a later peer nonce and fails
authentication. The [local proposal](proposals/THP_CROSSED_RESPONSE.md) records
the actual trace and component-test boundaries. The revised component test passes
three cases, including the observed timeout/duplicate/buffered-response sequence.
It uses real ciphers with scripted receive I/O and injected channel/workflow state;
it is neither a complete THP test nor a fix. Fable confirmed the mechanism and
identified gaps addressed in the revised local evidence. Ordinary client API
reachability and intended crossed-message semantics remain unresolved.

A separate fresh-channel recovery assignment was blocked by an automated safety
filter before execution. No successful reconnect is claimed.

## Identity and remaining work

- Passing image: `36237692d909d9d4274d231cf924946b76a57eb7a14f2c7c0f63c53a3780d241`.
- Returned PCZT: `f499de162d7df2e6e1df8cfcc09f8b43bf2200bed72a408e93e6a499a9c3c9f9`.
- Oracle log: `fb8ac38a184aed17871d73599f4895fbb01edbcfafca6d9773f6d731db1a2ffe`.

Local source and raw evidence live under `work/emulator-transport/`, with the
passing run in `runtime/attempt-02/` and its independent `oracle/` directory.
`build-attestation-02.json` binds the successful build, integration hashes and
actual external bridge/core inputs. Source snapshots establish byte stability,
not a hermetic build or formal source-to-binary proof. The earlier fixed-fixture
emulator and accepted approval core remain unchanged.

The fixed Rust arena remains 128 KiB; firmware GC and native-stack settings were
not enlarged. No new arena peak, complete MCU stack bound or hardware fit is
claimed. [The stack constraint](STACK_PROGRESS.md) remains a device blocker. The first
verification candidate leaves only 816 bytes before unmeasured C/VM costs; a
separate serializer candidate reduces the selected signing parse path by 5,304
bytes. The combined experiment reproduces both gains on selected paths; the
complete maximum and integrated firmware overhead remain unproven. Hardware is available, but no physical device has been accessed or
flashed. Production key derivation, entropy, receive-address confirmation,
broader transaction support and independent specialist review remain.

Both approved source packets completed on confirmed Fable 5.1. See the
[review dispositions](reviews/TRANSPORT.md) for accepted findings, rejected
suggestions and the scope of the current-source follow-up. A successful happy
path does not complete the hostile-host transport acceptance criteria.
