# Portable approval core: change reviews

Scope: the isolated synthetic-regtest portable-core refactor from `9c194e9`,
explicitly approved by the user. This is a local proposed-change review; no PR or
upstream message was published. Review conclusions do not authorize production
funds or firmware release.

## Review ownership

- The coordinator implemented and integrated the approved core and entropy tests.
- An embedded worker replaced the narrow verifier probe with the actual core.
- An adversarial reviewer inspected pinned upstream guarantees, then implemented
  focused action-count and metadata regressions in its own file scope.
- A readability reviewer proposed and implemented five narrow simplifications.
- A fresh independent reviewer then reviewed the final seven core/test/probe files
  and reported no remaining material readability findings. It ran no tests.
- Claude Code with Fable reviews the frozen production change independently, using
  read-only tools and the existing Max subscription with a USD 10 per-run limit.
  Its initial and focused follow-up reviews both completed successfully.

## Findings and resolutions

| Finding | Resolution |
| --- | --- |
| `Signer` hid the switch to an API that skips FVK validation | Import it as `LowLevelSigner`; state beside the call that full verification covered the identical retained PCZT. |
| A five-field validation tuple obscured relationships | Use one private `Validated` struct and `signing_indices` for verified positive inputs. |
| RNG provenance and use were unclear at the constructor | Document independent trusted seeding, session/signature use, and the limits of the `CryptoRng` trait. |
| Digest tests repeated the implementation | Delete the duplicate helper; compare actual `Engine::begin` results to the standard upstream Signer. |
| Wire fields required positional counting to distinguish spend/output | Qualify the existing comments; preserve scanner operations and order. |
| Upstream signing entropy failure escapes `Result` | Document the fail-stop contract; inject failure during the second signature and assert consumed consent with no response. No claim of recoverable entropy errors or verified firmware reset handling. |
| Default padding omitted the admitted one-action boundary | Use an upstream unpadded fixture for exact action counts 1–8; retain other padded fixtures. |
| Digest equality could miss lost FVK/OCK metadata | Compare the entire PCZT before/after, permitting only new real-input signatures; exercise both anchor states and absent/present valid OCKs. |

The adversarial source review found no demonstrated digest mismatch or approval
bypass. Its RNG concern was a failure/recovery boundary, not evidence of unauthorized
signing. The full signing matrix also verifies returned tags through the standard
upstream Signer and rechecks commitments, ownership and all signatures.

## Fable provenance

Raw prompt, frozen inputs, hashes, response and run metadata are kept under ignored
`work/reviews/portable-core-fable/`. The snapshot includes source, manifests,
contract and tests; the primary review scope is production correctness. Subsequent
source changes are checked against the snapshot. Rustfmt-only digest formatting
and test formatting do not change behavior. Any substantive later change requires
a review of that delta.

Fable result: **no blocking defect found**. Primary model was `claude-fable-5`;
the first run took 509.41 seconds/35 turns, with no permission denials or tests run.
The focused follow-up took 59.81 seconds/one turn and confirmed all four advisories
resolved: documented bundle-only recheck scope, a None/Some(0) lock-time regression,
an error description covering parsing/restoration, and the signature type's
Ironwood-only scope. The replacement test was then strengthened to try the new
token first, directly checking it cannot inherit consent. A fresh readability
review also found no material concern in these final changes.

The generic preverified error remains one static message; the private closure
cannot currently alter action positions, so a new diagnostic branch was not added
for that unreachable case. Existing positive cases cover absent lock time; the
new differential supplies explicit zero and compares both encodings.

Two statements in the first Fable response required correction. The old engine
already compared the standard Signer's digest with the approved digest before
signing: this invariant is preserved, not newly established. Also, RedDSA hashes
random bytes, public key and message to derive its nonce. Repeated random bytes
do not alone imply nonce reuse across different messages; predictable bytes still
expose the nonce and can compromise the key from a single signature. The trusted
unpredictable-RNG requirement remains unchanged. The follow-up confirmed that
nonce reasoning; the coordinator checked the old engine in the base revision.

Both runs used the existing Max subscription. Reported list-price usage totals
USD 7.212187, with conservative budget holds totaling USD 7.22. This is not an
observed billed charge; see `ops/review-usage.json` and `ops/budget.json`.

Final validation results are recorded separately in
[APPROVAL_RESULTS.md](../APPROVAL_RESULTS.md); review findings are not test passes.
