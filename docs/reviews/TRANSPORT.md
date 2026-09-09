# Emulator transport and runtime reviews

Both explicitly approved source packets completed through the existing Claude
Code account, requested as `fable[1m]`. Both results identify **claude-fable-5-1**;
neither is an Opus substitution. A separate agent performed the clarity review
and later source dispositions. No upstream PR, comment or message was sent.

| Frozen packet | Scope | Reported list-price usage |
| --- | --- | ---: |
| Runtime driver, SHA-256 `b8b936314241e51f919ce7bdf4f7f64a2d658f1773a30f7724b9c40362f4b299` | Historical fixed-fixture driver, demo and UI; excludes the new THP driver | $1.105567, within $2 cap |
| Host transport, SHA-256 `145440f8500555139cd729fbf83308eaf7cb9d886f3f5d013813bd2a636ea00b` | Native caller-input bridge, C adapter, review/transport, protobuf definitions and desktop client | $2.950039, within $5 cap |

These are reported model-usage estimates, not observed subscription invoices.
Exact model usage and result hashes are recorded in `ops/review-usage.json`.

## Findings and dispositions

The historical runtime review correctly identified missing checks for receiver
context/final-hold text, premature-exit diagnostic ordering, and source identity.
The current THP driver checks all seven pages, checks for a premature response
before its post-press layout read, and captures source bytes and old/new image
hashes. Its actual passing run and independent oracle are recorded separately in
[the transport result](../TRANSPORT_RESULTS.md). That later source was not part
of the historical Fable packet.

Two proposed UI changes were rejected after inspecting the native contract.
Moving begin outside every cleanup region would miss Python allocation failures
after native validation retains the request. Unconditional cleanup remains.
Repeating accounting in Python would duplicate checked unsigned accounting already
performed by the core; the host cannot supply the review dictionary directly.

The transport review found no high-severity consent break in the supplied packet.
Its lifecycle concerns were checked against the actual pinned sources:

- **Post-begin idle check:** rejected. Idle requires no retained request allocation;
  successful begin intentionally owns the verified PCZT until sign/cancel. Adding
  that guard there would terminate a valid review.
- **Cleanup and missing cancel calls:** core begin/approve/sign consume or clear
  pending consent before failure; C conversion failures are covered by Python
  finally. Native cancel allocates no Python objects and raises no Python exception.
  Executor/arena violations fail-stop; they are not exceptions to swallow.
- **Seedless session and Session context-manager claims:** resolved against real
  pinned implementations and the successful seedless-session-0 THP run. Existing
  PIN/backup filters remain enabled; locked-profile acceptance is still separate.
- **Bounds and diagnostics:** all current limits agree. A valid near-65,536-byte
  PCZT was not established by the review; restricted field/action parsing matters.
  Native output-capacity failure is tested, but real admission-bound recovery
  remains. Generic native failures currently surface as FirmwareError; no broad
  exception remapping was added.
- **Timeout, late ACK and channel recovery:** require concrete THP transcripts.
  The pinned mailbox clears its taker in finally, but that alone does not prove
  reusable native channel state. Do not add blind drains or automatic re-signing.
- **Review duration and competing workflows:** the 180-second cooperative timer
  is a prototype constraint, not a usability result or preemptive native deadline.
  Same-channel session handling is serialized; actual channel preemption needs
  its own test instead of assuming two arbitrary simultaneous workflows.

The runtime found a separate bug that neither initial packet review caught:
native protobuf definitions cannot be passed as the class argument to
`isinstance`. The one-line correction uses `expected_type.is_type_of(reply)`.
A firmware-shaped message double reproduces the original failure and all twelve
scheduler tests pass after the correction. Independent source/clarity review
accepts this direct use of the native API. No compatibility abstraction was added.

## Clarity and remaining review scope

The separate review found no necessary code refactor. The current driver is long
because it records sources, supervises processes and checks concrete UI/transport
outcomes; it remains a single explicit scenario. Keep small purposeful helpers,
unconditional cleanup and the native accounting authority. Avoid generic runner
modes, extra retry controls and duplicate validation implementations.

The full local finding-by-finding dispositions and source hashes are preserved
under `work/emulator-transport/clarity/`: `RUNTIME_REVIEW_DISPOSITION.md`,
`TRANSPORT_REVIEW_DISPOSITION.md` and `transport-review-disposition.json`.
These local source comparisons do not expand what Fable saw.

A frozen follow-up packet includes the current THP driver/supervisor, descriptor
correction, native descriptor predicate and arena guard source. SHA-256:
`1203fb252c801db1362cb8969710005d96e930d58dbbbd6e128988787e4a39cd`.
Automatic approval review rejected its external transmission because the user's
exact-payload approval covered the two earlier packets. The user then approved this packet and scoped Fable reviews as needed through
the existing account. Transmission is now authorized and the follow-up is running
with a $3 reported-usage cap.

Later real runs now establish host Cancel at final hold/fresh retry and ordinary
upload timeout/GetFeatures recovery. A deliberately late chunk raises a channel
authentication error, so late-ACK recovery remains unresolved. The new test-driver
deltas have local parent review; they are outside the running Fable packet.
Remaining cases include malformed/oversize/nine-action admission, final-hold
deadline, response ACK loss and reachable channel preemption.
Native and scheduler tests support these boundaries but do not substitute for
those real transport cases. None of this establishes MCU fit or production safety.
