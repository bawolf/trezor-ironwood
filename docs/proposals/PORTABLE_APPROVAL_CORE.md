# Proposal: portable approval core with trusted device randomness

Status: **explicitly approved by the user; implemented and reviewed**.
The user approved “Approve isolated refactor” for this exact proposal after the
automatic review rejection. Work remains limited to synthetic-regtest profile 1.
No firmware release, physical device, wallet, production key or real transaction
is included in this approval.

## Concrete change under review

1. Keep the public admission policy, full Verifier checks, ciphertext recovery,
   checked accounting, ownership-derived change and immutable review state.
2. Compile the library with `no_std` plus `alloc`; make OS randomness an optional
   host convenience. A generic engine owns a trusted `RngCore + CryptoRng` supplied
   by device integration and obtains the session ID from it. Host transport never
   supplies randomness or an approval callback.
3. Assemble upstream `TransactionData::from_parts_v6` using only the already
   validated global fields and fully parsed Ironwood `extract_effects` result.
   Keep all other bundles absent, as required by profile 1. Compute the consensus
   digest with upstream `TxIdDigester` and `v6_signature_hash`; copy no cryptography.
4. Keep the validated header private beside the owned PCZT. On `sign`, consume
   approval first, enter an internal low-level signer closure, recompute and compare
   the digest, and invoke upstream `Action::sign` only for the owned real inputs.
   Never export an API accepting an unverified PCZT or caller-supplied signing closure.
5. Return pool/index/signature tags only after all signatures succeed. Preserve
   FVK metadata through upstream's positional restoration checks. Do not change
   input order, action count, values, addresses, modification flags or display data.

The [companion patch](portable-approval-core.patch) records the original change
that the user reviewed. It has now been applied; subsequent clarity changes and
regression tests are recorded in the implementation diff. Do not apply this
historical patch again. Acceptance results are in [APPROVAL_RESULTS.md](../APPROVAL_RESULTS.md); independent
review findings and resolutions are in [the review record](../reviews/PORTABLE_APPROVAL_CORE.md).

## Evidence already completed

- The unchanged host reference passed 27 conformance tests, including explicit
  full verification, signature verification, cancel/replay/replacement and
  same-digest metadata substitution cases.
- Eleven local state/accounting theorems passed with exact Lean axiom guards.
  These are structural model proofs, not a machine-checked Rust refinement.
- The bounded scanner and upstream PCZT full-FVK/commitment APIs compiled without
  an OS for Safe 7's MCU target using its source-pinned Rust nightly.
- A new **test-only** digest experiment matched the standard PCZT Signer for
  synthetic transactions with 1–8 positive outputs (2–8 padded actions), alternating
  payments/internal change and both absent/restored v6 anchors. It passed 16 digest
  comparisons and runs the unchanged Engine's full validation for every original
  transaction. No new signing path was exercised or installed by this experiment.

## Acceptance criteria

- All previous tests continue passing; add device-RNG session failure and
  deterministic synthetic signature checks, cross-session replay and wrong-key
  failure, preserving consume-before-sign and no partial response.
- The profile-specific digest continues matching the standard Signer over every
  admitted action count, metadata-only updates and varied positive-value layouts.
- Upstream verifies all emitted signatures; their effect digest and approved
  projection remain unchanged. Signing never skips full verification.
- Warning-fatal Clippy, formatting, exact dependency identity and source hashes pass.
- The **complete** core compiles for `thumbv8m.main-none-eabihf` with default features
  disabled, not merely the current verifier probe. No baseline source is modified.
- Update the contract and Rust/Lean correspondence to describe the actual API and
  remaining entropy, allocator, UI, side-channel and firmware-linking assumptions.

Cross-compilation alone does not demonstrate bounded RAM, a working allocator,
trusted UI consent, entropy quality or hardware security. Those remain separate
Safe 7 integration tasks. No hardware flashing or real-funds authorization is
requested here.

## Approval history

Automatic approval review rejected the combined RNG, digest and low-level signing
rewrite as a broad security-critical change whose correctness and scope of impact
were not yet bounded. It requested explicit approval rather than inferring that
exact change from general project continuation. The rejection was honored: the
engine stayed unchanged, and only the independent read-only digest experiment
proceeded. The user then explicitly authorized applying and testing this isolated
synthetic-data refactor. Firmware release and real funds remain outside scope.
