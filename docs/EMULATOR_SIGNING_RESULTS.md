# Synthetic Safe 7 emulator signing

A fixed synthetic Ironwood PCZT now completes verified review, timed confirmation
and signing in the Safe 7 emulator. Both new real-spend signatures pass independent
verification, with transaction fields and digests preserved. This is a functional
emulator demonstration; final adversarial review of the runtime driver is pending.

The prototype uses public test secrets and no wallet seed or transaction wire
handler. The PCZT and verified review remain owned by one persistent Rust Engine.
C copies the verified display fields into Python objects after Rust returns. Frozen
Python presents the required screens, obtains confirmation, and supplies the
retained token for the private signer. Its finally cancels on success or failure.
The fixed Rust arena enforces the bound VM executor and sealed public-table owners.

## Observed cases

| Case | Actual result |
| --- | --- |
| Review and sign | Context, payment, complete 43-byte receiver, all three totals pages, expiry and final confirmation visited in order; displayed label/value pairs checked. |
| Short press | Requested 100 ms / debug wire 300 ms; after release and a 2.3-second wait, the final screen remained and no signed result existed. |
| Timed hold | Requested 2,000 ms / wire 2,200 ms with animations enabled; one 2,557-byte signed PCZT, process exit 0. |
| Independent oracle | Both new real-spend signatures verified and fields/digests preserved. The fixed oracle corpus also reused 14 earlier control responses; its total of 43 is not 43 new emulator signatures. |
| Menu cancellation | Actual header-menu and Cancel-item touches; exactly one cancellation marker, no signed marker, exit 0. |
| UI failure after validation | Injected ValueError from the first layout; real finally cancelled native state, the demo propagated the exception at module scope, no outcome/signature marker, exact exit 1 with traceback. |
| Cancel then approve again | One process, two calls to the unchanged frozen review: real menu cancellation, all seven second-review pages, rejected short press, then hold and exactly one PCZT with exit 0. |

All four cases use fresh synthetic profiles and the same image; the retry case
keeps both review flows in one emulator process. The three cold
startup gates and final owner-baseline gate remain compiled and enforced. Their
normal return paths passed; no raw allocator counter dump or emulator peak-heap
measurement is claimed. The Rust arena remains 128 KiB, response capacity 65,536
bytes, and MicroPython GC uses the unchanged source default. The MCU stack was not
changed. Emulator execution does not establish MCU stack or timing suitability.

The driver captured 141 nonempty PNGs for signing, including hold animation frames,
and four for cancellation. Parent inspection confirms full receiver text, readable
amounts/fee and the hold prompt. Structured traces cover the required visited
pages; text traces alone are not a pixel-verification oracle. The pinned DebugLink
helper times out waiting for its final state acknowledgment after the flow exits;
acceptance requires exact process outcomes and result markers, plus the independent
signature check, rather than treating that timeout as a successful response.

## Identity and retained evidence

- Firmware pin: `7105338e3c2c1e681940e17780609881ce53126b`.
- Current native arm64 Mach-O image: `82608d19eedfe07a97433c4cb3cca6eae92cad8530ce6197f7e2fce7e0843c8b`.
- Image size: 16,929,752 bytes; official T3W1 emulator test preset and features.
- Firmware lock: `5106297df32444e4b001de4eed12bc6828e4bd1ac8a109b6ad8dfb94abb210c0`.
- Signed response: `f499de162d7df2e6e1df8cfcc09f8b43bf2200bed72a408e93e6a499a9c3c9f9`.
- Approval core remains unchanged: `3500810c65dd3550bca2efe84248b38d3e725755eccd95cc3f48b061bbb6d5c8`.

The same-process retry completed in 18.536 seconds, with 129 captured PNGs. Parent
inspection rehashed all 160 final evidence files and checked the two real awaits,
exact page associations, outcome ordering and cleanup. Its response is byte-for-byte
identical to the independently verified signing response above, binding the existing
oracle result without another invocation or another unique-signature claim.
Evidence: `work/emulator-retry-test/parent-verification.json` and adjacent reports.

Local evidence remains under ignored `work/emulator-signing-runtime-07/` (sign and
oracle), `-08/` (cancel), `-09/` (failure), and
`work/emulator-signing-build/integration-build-04/` (111.206-second rebuild).
The source snapshot is `work/emulator-signing-bridge/integration-03.json`.
The integrated graph has one ff 0.13.0 and pasta_curves 0.5.1 identity each. It
preserves firmware pins, including 15 deliberately different shared utility/build
versions relative to the standalone bridge. It is not the identical host graph.

## Failures and review limits

Earlier failures remain recorded: first full build timeout; two ten-second model
import timeouts; emulator readiness failures; native sampler timeout; an unavailable
ubinascii import; stale readiness PONGs entering the debug connection; and the
upstream text-summary helper rejecting boolean pagination icons. The import now
uses the pinned bytes.hex API; the driver opens a fresh protocol socket and records
raw layout text/structure. No upstream baseline was edited to fix these issues.
One rebuild-driver preflight also used the wrong lockfile path; it failed before
launching a compiler, was retained, and its path was corrected.

The local model startup allowance is now explicitly 30 seconds after the failed
10-second attempts. An intermediate launch took 18.483 seconds; the accepted three
runs became ready in 0.741, 1.289 and 0.846 seconds. A resource snapshot showed a
24 GiB machine using about 7.9 GiB of swap under heavy concurrent load. This supports
contention as a concern, not a proved explanation of every historical failure.

Two confirmed Fable5.1 bridge reviews and independent clarity reviews preceded the
runtime work. Runtime exposed integration issues that those source/mock reviews
missed. The additional narrowed runtime-driver packet subsequently completed on
confirmed Fable 5.1 after exact-payload approval. Its historical findings and the
current driver's corrections are recorded in [the transport review](reviews/TRANSPORT.md).
The newer THP driver has a separate approved follow-up running; earlier rejected
transmission attempts made no model call. Local testing continued throughout.

The demo has no production entropy, key-store, general PCZT transport, cross-process
replay protection or hardware validation. Mixed pools, general memos and address
presentation remain outside this synthetic profile. A separate
[bounded THP upload/signing flow](TRANSPORT_RESULTS.md) now reuses this lifecycle;
real hostile-transport acceptance continues.
The selected ARM stack concern remains open; the small existing-function outlining
candidate is isolated, and a further parser-staging investigation found no simple
source cleanup to justify another abstraction.
