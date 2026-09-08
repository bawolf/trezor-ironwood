# Host approval conformance evidence

The profile 1 reference adapter is in `crates/approval`. It uses the actual pinned
PCZT builder, parser, verifier and signer. The fixture account uses public test
seed bytes `[0; 32]`; recipient and wrong-key cases use other fixed public seeds.
The funding note and transaction are synthetic regtest data and are never sent
to a network. The tests do not load a device, seed store or wallet database.

## Passing run

`work/runs/20260908T044850Z-approval-875a224d/report.json` records:

- 27 conformance tests passed, none failed, ignored or filtered; 18.18 seconds
  including Cargo startup on this Mac. This is not a device latency measurement.
- `cargo fmt -p ironwood-approval --check` passed.
- `cargo clippy --locked --offline -p ironwood-approval --all-targets -- -D warnings`
  passed. Cargo separately reports an upstream future-compatibility notice for
  locked `document-features 0.2.8`; the pinned dependency was not upgraded.
- Test log SHA-256:
  `8f06ad365ab08577d72c0e32765c911c837a252144a3c15afdd3e1819655768f`.
- All 133 registry dependencies in the new Cargo.lock matched the upstream lock's
  exact versions and checksums. A subsequent dependency gate enforces this, and
  subsequent reports hash local adapter/proof inputs before and after execution.

The positive transaction spends 1,000,000 zatoshis, pays 600,000, returns 390,000
as verified internal change and pays a 10,000-zatoshi fee. Its owned spend receives
one new Ironwood signature; upstream verifies every action signature, and the
consensus signature digest remains unchanged. External-scope self-payment stays
classified as a payment. A second positive transaction exercises zero-value output
padding; a positive OCK control checks optional outgoing recovery metadata.

## Hostile inputs exercised

- Recipient, value, note randomness/commitment, input FVK/recipient/rho/nullifier,
  randomized signing key, alpha and ciphertext/ephemeral-key/OCK mutations.
- Missing mandatory metadata, host change labels and user-address strings.
- Unsupported network/version/expiry/modification flags and other pool bundles.
- Inconsistent bundle balance, negative balance, excessive fee, duplicate actions,
  invalid or missing dummy signatures and injected dummy spending keys.
- Byte/action/money limits, every proper truncation of the positive frame, trailing
  bytes, overlong integer and unsupported encoding version.
- Structured single-byte mutations: any frame the scanner admits must deserialize
  with the actual pinned upstream schema. This is a finite differential regression,
  not exhaustive fuzzing or proof of the scanner.
- Validly encrypted nonempty memos, including a nonempty memo on a zero-value output.
- Signing before approval, cancellation, repeated approval/signing, wrong-key failure,
  cross-session tokens, invalid replacements and same-digest anchor substitution.
- Mutation of the caller's byte buffer after `begin` cannot change the owned PCZT.

Many test functions iterate over several hostile field cases. The reported **27**
is the number of Rust test functions, not a count of every mutation or a security
coverage percentage. See the contract for unsupported inputs and trust boundaries.

## Retained development failures

The first full run (`20260908T044354Z-approval-b79f7258`) passed 22/23 tests; the
remaining fixture incorrectly assumed the upstream builder populated OCK metadata.
The builder leaves it absent even when output recovery with the OVK is supported.
The corrected test injects invalid OCK, and a separate positive test derives a
valid OCK through the upstream domain API before mutating it.

The expanded run (`20260908T044559Z-approval-f5155899`) passed 25/26. It exposed
that upstream zero-value padding uses an all-zero empty-text memo, rather than
the canonical no-memo marker. Profile 1 now explicitly accepts those two empty
encodings for zero-value padding; positive outputs still require the no-memo
marker. A new test verifies nonempty zero-value memos are rejected. No arbitrary
memo or ciphertext-validation exception was added.

Initial compile iterations also corrected nested Cargo-workspace discovery, use
of the public rho deserializer and use of the circuit-free PCZT funding builder.
All upstream baseline checkouts remained unchanged. These are adapter-development
corrections, not newly discovered vulnerabilities in the upstream libraries.

The [eleven structural Lean proofs](APPROVAL_PROOFS.md) are separate evidence.
Neither these tests nor those proofs establish physical Safe 7 behavior, final
proof/consensus validity, mainnet readiness or full implementation refinement.
