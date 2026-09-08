# PCZT validation map for the device contract

Source map for M1.1, recorded 2026-09-08. The experimental
[profile 1 contract](APPROVAL_CONTRACT.md), [implemented host conformance adapter](APPROVAL_RESULTS.md)
and [structural proofs](APPROVAL_PROOFS.md) now cover a restricted Ironwood-only
profile. This map is not a new upstream vulnerability report.
The APIs intentionally split responsibilities between transaction construction,
verification and application policy.

Sources: librustzcash `5e770a91ad0d11938dbc713e7889e4aa8009266c` and its locked
Orchard **0.15.3** crate (registry checksum
`e8b67beade27dbebdbfee0819e23170b0b263dc7b4f558ee936151716baf6e1f`).
The published crate records VCS commit `ae3511076ec8ecb39ffc02d9cdaf19c441c5b53d`.
Its `src/pczt/verify.rs` is byte-identical to the separately pinned Orchard
checkout at `be4f659467338a86e93bd3d9ae72a696bebc924b`; this equality was checked
for that file, not assumed for the entire crate.

## API obligations

| Surface | Actual guarantee | Device contract still needs |
| --- | --- | --- |
| `Pczt::parse` | Parses a versioned PCZT representation. The in-memory type explicitly allows incomplete or semantically invalid transactions. | Bounds before allocation; supported transaction/pool policy; required metadata; reject incomplete approval data. |
| `Verifier::new` / `finish` | Holds and returns a PCZT. | An explicit, complete set of verification closures. Instantiating this role is not validation. |
| `Verifier::with_ironwood` / `with_orchard` | Parses the selected protocol bundle and runs the caller's closure; reserializes afterward. | Check all relevant actions and bundle flags, then bind the resulting exact object to approval. |
| `Bundle::verify_cross_address_restriction` | For restricted bundles, checks each spend/output pair has the same expanded receiver; requires recipients when restricted. | Correct pool/epoch policy, dummy handling and explicit invocation. Do not silently treat a missing recipient as verified. |
| `Action::verify_cv_net` | Recomputes the action value commitment from spend value, output value and value-commitment trapdoor. | Checked bundle/transaction accounting, fee calculation and required fields across every included pool. |
| `Spend::verify_nullifier(expected_fvk)` | Checks note construction, FVK/address relationship and nullifier. Expected FVK handling has a deliberate zero-value dummy exception. | Derive the expected account FVK on device; distinguish dummy actions from owned real spends; enforce metadata completeness. |
| `Spend::verify_rk(expected_fvk)` | Checks randomized spend validating key against FVK and alpha. | Derive expected keys; pair with nullifier and value checks, and enforce correct pool/action identity. |
| `Output::verify_note_commitment(spend)` | Checks recipient, value and rseed against the output commitment, with rho derived from the paired spend nullifier. | Output/change classification, memo and ciphertext consistency, display encoding, and preservation of pairing. This method alone does not validate note encryption. |
| Transparent `Input::verify` / `Output::verify` | Accept supported P2PKH/P2SH forms and check a supplied redeem script against its hash. | Key ownership, full signing prerequisites, authenticated value/accounting and device-derived change. |
| `Signer::new` | Extracts transaction effects and computes/caches the signature digest; default transparent policy is `ALL_ONLY`. | Full semantic checks and consent. Do not widen the default sighash policy for the initial adapter. |
| `Signer::sign_ironwood` | Signs one action; attempts nullifier consistency, but deliberately tolerates missing note metadata in several cases. | Reject missing recipient/value/rho/rseed in the approval validator. Signing success is not proof that payment metadata was checked. |
| Low-level `sign_ironwood_with` / `sign_orchard_with` | Uses a preverified parse that omits FVK derivation and restores wire FVK fields with positional checks afterward. | Full prior verification over identical bytes and an immutable, trusted signing closure. A digest-only check cannot replace validation of metadata excluded from the signature digest. |
| `BatchSignRequest` / `BatchSignResponse` | Versioned serialization, ordered PCZTs, signatures tagged by pool and action index. | Session/request correlation, batch-size/uniqueness policy, replay rejection, response cardinality and atomicity policy. Sapling signatures are not represented by this response type. |

Immutable source anchors:

- [PCZT representation and parsing](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/lib.rs#L117).
- [Verifier role](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/roles/verifier/mod.rs#L23)
  and [Orchard-family closures](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/roles/verifier/orchard.rs).
- [Orchard 0.15.3 verification methods](https://github.com/zcash/orchard/blob/ae3511076ec8ecb39ffc02d9cdaf19c441c5b53d/src/pczt/verify.rs).
- [Transparent checks](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/zcash_transparent/src/pczt/verify.rs).
- [Signer construction](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/roles/signer/mod.rs#L135)
  and [Ironwood signing prerequisites](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/roles/signer/mod.rs#L483).
- [Preverified signer contract](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/roles/low_level_signer/mod.rs#L15).
- [Batch transport responsibilities](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/roles/signer/batch.rs#L1).

## Two distinct identities

The adapter needs both an immutable verification context (including metadata
used to establish ownership, accounting and display) and the consensus signature
digest over transaction effects. They serve different purposes. Approval must
reference the exact verified context until signatures are produced; computing
the same signature digest is insufficient to accept a substituted FVK, change
label or other approval metadata.

For v6, the [anchor requirement](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/pczt/src/common.rs#L69)
allows missing anchors during pre-authorization operations because v6 signatures
do not commit to anchors. This does not make arbitrary mid-approval mutation
acceptable. Define post-signing re-anchoring/finalization as a separate operation
and test its effect-preservation and final-validity requirements independently.

The global coin-type metadata also needs explicit network/path policy: it is
not itself a consensus transaction field. Branch ID, transaction version,
version-group ID, expiry and the application's selected network cannot be
replaced by an untrusted network label.

## Scope beyond experimental profile 1

- Enumerate every accepted wire field and the device-side representation, including
  the version-2 ciphertext/memo representation and all relevant optional fields.
- Select a first supported pool combination and reject others explicitly; complete
  the Sapling and transparent accounting map before accepting mixed-pool inputs.
- Establish numerical frame/action/byte/memory/time bounds using Safe 7 measurements;
  enforce limits before deserialization allocations, not only after parsing.
- Specify ciphertext/memo consistency and required output-recovery policy using
  current upstream primitives; do not infer it from commitment verification.
- Define checked signed accounting, zero-value/dummy treatment, ownership-derived
  change and the precise payment/fee/network projection shown on device.
- Define request/session identity, cancellation, retry, replay and partial-signature
  behavior; connect this state machine to positive and hostile-host fixtures.

Key handling and signing follow the explicit profile 1 contract, not this API map
alone. Mixed pools, compact/memo wire encoding, general memos/addresses, measured
device bounds and batch transport require contract extensions before acceptance.
