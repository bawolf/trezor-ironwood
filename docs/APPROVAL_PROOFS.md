# Approval state and accounting proofs

The `proofs/` package is an independent Lean 4.30.0 model of the
[profile 1 host adapter](APPROVAL_CONTRACT.md). It imports only Lean's bundled
`Std`. It is not an Ironwood circuit proof or a Trezor firmware proof.

Run `python3 scripts/check.py approval-proofs`. The lane checks the theorem census,
then runs `lake build --wfail` on **both** `Approval` and `AxiomCheck` default
targets. Every named theorem has an exact `#guard_msgs` / `#print axioms` check.
The machine-readable manifest is `proofs/axioms.json`. Expected dependencies are
Lean's standard `propext`, `Classical.choice` and `Quot.sound`, varying by theorem;
`sign_consumes` uses none. No admitted proof or additional axiom is accepted.
The census checks coverage and guard text; Lean checks the actual dependencies.

| Theorem | Executable correspondence | Boundary |
| --- | --- | --- |
| `sign_consumes` | `Engine::sign` takes `self.pending` before checks or signer calls | Rust ownership and execution must preserve this order |
| `replay_rejected` | A second `sign` without a fresh request sees no pending state | No claim about a separate engine process or copied private state |
| `cancelled_request_cannot_sign` | `cancel` clears pending state | Dropping values does not prove memory erasure |
| `failed_sign_has_no_receipt` | Every signer failure exits before `Signed` is returned | Model's success boolean abstracts completion of all signing calls |
| `successful_sign_preserves_approved_context` | `sign` uses the owned approved PCZT; there is no replacement-byte parameter | Model stores exact context, not Blake2b; collision resistance remains an assumption for its digest representation |
| `begin_requires_fresh_approval` | `begin` installs a new pending object with `approved = false` | Cryptographic validation and UI correctness are separate boundaries |
| `malformed_replacement_cancels` | `begin` cancels before validating any replacement bytes | The old request cannot survive parse failure |
| `old_token_cannot_approve_replacement` | New request counter is greater than every earlier counter in a session | Rust uses checked u64; exhaustion rejects after clearing state, whereas model Nat is unbounded |
| `different_session_rejected` | Token includes a locally generated session ID | Entropy and session-ID uniqueness are not proved |
| `accounting_conserves` | Checked totals, ordered subtraction, fee cap and exact payment/change partition | Nat model starts with totals; Rust's bounded per-action accumulation and crypto ownership checks are exercised by tests, not formally refined |
| `overspend_rejected` | `checked_sub` rejects output totals above inputs | No statement about chain membership, proofs or spendability |

The accounting function computes the fee only after checking ordered subtraction
and bounds. Conservation is derived from those checks, rather than supplied as a
precondition. Concrete accepted accounting and approved-signing examples establish
that the model does not reject everything. The state theorem allows arbitrary
context bytes, effects and projections; it proves preservation, not the correctness
of the projection originally computed by the validator.

## Remaining refinement work

This is a reviewed-by-author correspondence table, **not a machine-checked
refinement of Rust**. PCZT deserialization, note/value commitments, encryption,
FVK ownership, digest construction, random signatures, key secrecy, display
rendering, compiler correctness and device behavior remain outside this model.
The test suite uses the actual pinned primitives to exercise these boundaries.
A future device adapter must also bind authenticated UI events to the exact
projection and cover transport framing, interruption and memory constraints.

Do not label this package as proof that the wallet or all Ironwood cryptography
is safe. The much larger pinned upstream `lake build --wfail` is tracked separately
under the `lean` lane and retains its own target set and axiom/census policy.
