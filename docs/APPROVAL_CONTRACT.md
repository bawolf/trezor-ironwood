# Experimental Ironwood approval contract, profile 1

This contract governs the portable experimental core and its host harness, not
production firmware. It uses
librustzcash `5e770a91ad0d11938dbc713e7889e4aa8009266c` and the Orchard 0.15.3
crate selected by its Cargo.lock. See [validation API map](PCZT_VALIDATION_MAP.md).
All keys and transactions exercised here are synthetic. The adapter must not be
wired to a seed store or a host-controlled approval event in production.

## Trusted context and supported transactions

A session selects one test account FVK and an immutable policy outside the PCZT.
The first implementation supports synthetic **regtest, NU6.3, transaction v6,
Ironwood note v3 only**, not mainnet or testnet spending. The coin type must be 1;
this metadata alone cannot distinguish testnet from regtest. The selected network
is trusted application configuration, not a host label, and is shown explicitly.
Version and version-group ID use upstream constants; branch ID must equal NU6.3.
Fallback lock time is absent or zero. Expiry must be strictly after the trusted
reference height and at most 100 blocks later. This synthetic height is a test
input, not a claim that a future device has authenticated chain height.

Every positive-value input must belong to the selected account. Zero-value inputs
are padding: require complete note/FVK/randomizer metadata, verify their nullifier
and randomized key with upstream's dummy exception, require and verify their
existing authorization signature, and never ask the account key to sign them.
At least one positive-value input and one positive-value output are required.
Reject duplicate input nullifiers. Initial bundle flags must equal the upstream
Ironwood v3 default (spends, outputs and cross-address transfers enabled). Other
flag profiles need their own encryption/dummy policies before being accepted.

## Wire admission before allocating protocol containers

Accept exactly one v2 PCZT, maximum **65,536 bytes**, with **1–8 Ironwood actions**.
No batch, compressed frame, recursion or transport reassembly is implemented.
A nonallocating scanner walks the pinned Postcard layout before `Pczt::parse`.
It bounds every variable container, requires canonical integer/option/enum tags,
checks truncation/trailing bytes and rejects unsupported containers at their tag.
The upstream parser then validates actual protocol representation. This scanner
is deliberately version-specific and needs differential tests on any pin change.
The byte/action limits are prototype limits, **not measured Safe 7 RAM or latency
limits**. Heap accounting and firmware watchdog/transport limits remain M2 work.

| Wire field | Profile 1 admission and meaning |
| --- | --- |
| Header | `PCZT`, little-endian encoding version 2 |
| Global version/group/branch/expiry/coin type | Canonical u32; policy checks above |
| Global fallback lock time | None or Some(0) |
| Global tx_modifiable | Exactly zero, including reserved/SIGHASH_SINGLE bits |
| All global/spend/output proprietary maps | Empty; no host change labels |
| Transparent, Sapling, Orchard bundles | Absent, including empty-but-noncanonical bundles |
| Ironwood actions | 1–8, all examined; no filtered or hidden actions |
| Ironwood flags, value_sum | Exact default flags; checked input minus output sum must equal the signed bundle balance |
| Ironwood anchor | Absent or fixed 32 bytes; parsed upstream, not asserted to be a chain root |
| Ironwood note_version | V3 |
| Ironwood zkproof, bsk | Absent; finalizer/prover work occurs separately after signing |
| Action cv_net, rcv | Required 32-byte encodings; verify commitment with both values and rcv |
| Spend nullifier, rk | Required 32 bytes; parse and recompute from complete metadata |
| Spend spend_auth_sig | None for real inputs; required 64 bytes for zero-value inputs, verified against this transaction digest |
| Spend recipient/value/rho/rseed/fvk/alpha | All required; fixed 43/32/32/96/32-byte fields and bounded u64 value |
| Spend witness | Absent; v6 permits preauthorization before anchor/witness installation |
| Spend ZIP32 derivation, dummy_sk | Absent; key selection is trusted session context; no host spending keys |
| Output cmx, ephemeral_key | Required 32 bytes; recompute commitment and validate encryption |
| Output enc_ciphertext | Encrypted variant only, exactly upstream ENC_CIPHERTEXT_SIZE (580) |
| Output out_ciphertext | Exactly upstream OUT_CIPHERTEXT_SIZE (80) |
| Output recipient/value/rseed | Required 43/32-byte encodings and bounded u64 value |
| Output ock | Absent or fixed 32 bytes; if present, verify recovery against it |
| Output ZIP32 derivation, user_address | Absent; no unverified derivation or display strings |

The upstream IO Finalizer produces dummy signatures and may populate the empty
Sapling bsk. The host prepares this profile using the upstream Redactor to clear
empty Sapling bsk/anchor, Ironwood bsk, and witnesses; it retains all approval
metadata. The signer does not silently remove unsupported incoming fields.

## Semantic validation and accounting

Invoke `Verifier::with_ironwood`, `verify_cross_address_restriction`, and for every
action `verify_cv_net`, `verify_nullifier(Some(selected_fvk))`,
`verify_rk(Some(selected_fvk))` and `verify_note_commitment(paired_spend)`.
Required-field checks precede dependent use; no missing-data exception is accepted.

Reconstruct each output note with upstream `Note::from_parts`, paired nullifier,
recipient, value, rseed and V3. Use `IronwoodDomain` and
`try_output_recovery_with_pkd_esk` to authenticate ciphertext, ephemeral key,
commitment and recovered note. Require the recovered note/receiver to match and
the memo to equal canonical `MemoBytes::empty()`. Zero-value padding may also
use the upstream builder's all-zero empty-text memo; arbitrary nonempty or binary
memos remain rejected, including on zero-value outputs. For positive outputs additionally
require recovery with the selected account's **external-scope OVK**, including
change; this is an explicit recoverability policy. If OCK metadata is present,
require recovery with it too. Zero outputs may have randomized outgoing
ciphertext under upstream's no-OVK padding policy, but must still pass note
commitment, transmitted note encryption and empty-memo checks. No actual funds
are hidden by zero outputs. Restricted-bundle randomized note ciphertext is
outside this profile and is rejected by the flag rule.

Each value and each running total must be at most `MAX_MONEY` (21 million ZEC in
zatoshis). Use checked integer addition/subtraction, never float arithmetic.
Compute inputs I, all outputs O, internal change C, and payments P. Require
I >= O, fee F = I - O, bundle value_sum = F, and I = P + C + F. A trusted policy
sets the maximum fee (bounded by MAX_MONEY); the exact fee always appears in the
review. This cap is a local test policy, not a fee recommendation or a substitute
for consent. Reject negative balances and inconsistent declared balances.

Only `selected_fvk.scope_for_address(receiver) == Internal` makes positive output
change. External-scope self-payments are ordinary payments. Every other positive
output is a payment. No host labels are accepted. The host projection shows every
positive output in action order with exact raw receiver bytes, action index,
classification and integer amount; zero outputs are counted as padding. It also
shows account/session identity, regtest, Ironwood, NU6.3, expiry, total input,
payments, change and fee, and states that all memos are empty. Raw receiver bytes
are a precise reference projection, **not final human-friendly device address UX**.
Canonical address encoding and complete on-device pagination are M2 requirements.

## Verification, review, consent and signing

The reference engine owns one pending immutable PCZT. A fresh random 32-byte
session ID, monotonic request counter, domain-separated Blake2b-256 context
commitment over the exact received bytes and trusted policy/FVK, and the consensus
signature digest identify the request. These are distinct identities: the digest
does not cover all review metadata. The context commitment must not be logged for
private transactions in a future device integration.

`begin` discards any old approval before validating new bytes. Successful validation
returns an immutable review snapshot and token. A trusted UI may then approve that
exact token; the host must never invoke this transition over transport. `sign`
consumes the approved state **before** attempting signing and accepts no replacement
PCZT. A private `LowLevelSigner` closure recomputes the upstream v6 digest from
the retained header and bundle effects, checks it against the approved digest,
and invokes upstream `Action::sign` only for verified positive inputs. Full FVK,
commitment, ciphertext and policy verification already covered that identical
owned PCZT. The low-level signer and its closure are never exposed to callers.
It returns signatures only after every requested signature succeeds, with pool,
action index, request context and digest. The reference adapter may also return
the signed PCZT for tests; errors never return a partially signed object.

Token mismatch, cancellation, replacement, duplicate approval, sign failure and
replay invalidate pending consent. Starting a replacement never inherits approval,
including when it has the same signature digest. Reconnection creates a fresh
session ID; this relies on a trusted CSPRNG, not host-chosen session identifiers.
The Rust ownership API prevents accidental external mutation, but it is not an
isolation boundary against hostile code in the same process. Dropping state is
not a claim of memory zeroization. Production key lifecycle, entropy, side-channel
and anti-exfiltration work remain separate obligations.

The core uses `no_std` with `alloc`. `Engine::with_rng` owns a trusted
`RngCore + CryptoRng` for both session identity and signing. The default `std`
feature provides `Engine::new` with `OsRng` for host tests. The trait bound does
not authenticate entropy or prevent repeated seeds; independently seeded trusted
randomness remains an integration requirement. Session entropy failure returns
an error. Upstream RedDSA requests signature randomness through infallible
`fill_bytes`: entropy loss must stop execution, never substitute predictable
bytes. A panic/reset during signing produces no response and leaves consent
consumed; the host unwind regression tests this after one internal signature.
This is not a recoverable signing-entropy error or a tested device reset path.
Allocator failure, RNG implementation, reset behavior, key lifetime, stack/heap
limits and firmware linking remain separate integration requirements.

Post-signing v6 anchor/witness/proof/binding-signature finalization is a separate
host operation. It must preserve the effect digest and pass final consensus/proof
validation. No anchor or proof mutation is accepted during this approval session.
The prototype does not assert note membership, unspentness, proof validity,
broadcast success, physical-device security or production readiness.

## Required conformance and refinement evidence

Use actual pinned builder/parser/verifier/signer APIs for positive controls and
mutated PCZTs. Cover recipient, amount, nullifier, randomized key, FVK, commitment,
ciphertexts, OCK, memo, change spoofing, fee, network, pool, required-field redaction,
bounds/overflow, canonical framing, dummy signatures, duplicates, replay, cancel,
replacement and same-digest metadata substitution. Keep unsupported-input rejection
distinct from a cryptographic failure. Test successful signatures with upstream
verification and preserve the effect digest. Later Lean proofs must relate to
these transitions and accounting checks without assuming the desired conclusion;
no firmware refinement or cryptographic proof follows from the reference tests.
