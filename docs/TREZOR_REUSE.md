# Trezor shielded work: reuse assessment

Captured 2026-09-08 UTC. This is a source and review-history assessment, not a
cryptographic audit or a successful build of the older branches.

## Recommendation

Build the Safe 7 integration on current firmware and the pinned PCZT APIs. Reuse
selected vectors, test scenarios and reviewed algorithms from the older work
only after checking their current specification and licensing. Do not bulk-merge
the old signing stack: it implements a custom Orchard transaction-v5 protocol,
while the target needs an Ironwood/v6 approval contract, current device UI and
current build interfaces.

## Exact inputs

| Input | Revision | State at capture |
| --- | --- | --- |
| [Shielded signing PR 2472](https://github.com/trezor/trezor-firmware/pull/2472) | `d562254c2195d688ca59296f048ed905047317fe` | Open draft; 67 changed files |
| [Rust primitives PR 2510](https://github.com/trezor/trezor-firmware/pull/2510) | `6311675119e9b6f22c49ad8aa6f38c9bf9617aa4` | Open; 43 changed files |
| Current firmware baseline | `7105338e3c2c1e681940e17780609881ce53126b` | Safe 7 model `t3w1` |

PR 2472 targets `zcash-rust-primitives`, whose captured base commit equals PR
2510's head. They are a stack, not independent implementations. Detached review
worktrees are in `work/reviews/trezor-2472` and `work/reviews/trezor-2510`.

[TREZOR_REUSE_INVENTORY.json](TREZOR_REUSE_INVENTORY.json) records all 110 changed
file entries, source hashes, comparison hashes and unresolved review-thread
URLs. Against the current baseline, no changed-file entry has identical bytes at
the same path: 33 differ and 77 are absent at that path. This is a path-based
comparison; an absent path may have moved, and the counts do not establish that
an algorithm was removed or never incorporated elsewhere.

## Component decisions

| Component | Observed behavior | Reuse decision / required work |
| --- | --- | --- |
| Host protocol | Custom protobuf requests send Orchard note metadata, outputs and an anchor; signature types include transparent and Orchard spend authorization. | Design an explicit PCZT approval/signing adapter. Old message IDs and fields do not define Ironwood support. |
| Transaction signer | Rejects transaction versions other than 5; integrates transparent review/signing with an Orchard signer and empty Sapling serialization. | Use transaction and pool rules from current pinned PCZT validation. Retain mixed-pool accounting scenarios as test ideas. |
| Device reconstruction | Builds and pads actions, shuffles inputs/outputs, derives a shielding seed, computes the Orchard digest including the anchor, and returns signatures by action index. | Review as an algorithmic reference. Establish exactly which reconstruction is necessary for current PCZT verification before porting code. |
| Re-request integrity | Keyed AES message digests include wire type and index, and are accumulated with XOR; a nonempty final accumulator rejects changed messages. | A useful hostile-host scenario, not a proven PCZT binding. Specify immutable approval context and test substitution, duplicate, reorder and omission cases. |
| Accounting and consent | Orchard values feed the shared approver; change is derived using an internal viewing key; high input counts prompt a warning; viewing-key export asks for consent. | Preserve the privacy and accounting intent using current Safe 7 UI. A warning threshold is not a hard memory/resource bound. |
| Cryptographic primitives | Python Orchard/key/note code plus custom Rust/MicroPython wrappers, Poseidon and patched Pasta dependencies. | Prefer maintained upstream primitives. Cross-check vectors, investigate constant-time and FFI properties, and justify any additional device-side implementation. |
| Host library | Custom trezorlib transaction exchange and shielding-seed handling. | Implement current desktop transport around a documented contract; do not expose low-level preverified PCZT signing without equivalent complete verification. |
| Tests | Transparent-to-shielded, shielded-to-shielded, shielded-to-transparent, large bundle, dust inputs, fee/memo errors, addresses/viewing keys and primitive vectors. | Port scenarios selectively, then add Ironwood/v6 and malicious-PCZT mutations. Existing tests are candidates, not evidence they pass on Safe 7. |
| Build/UI integration | Old SCons paths, old Context-based layouts and MicroPython buffer/wrapper APIs. Current firmware uses Cargo xtask and Safe 7 UI. | Start from a clean current `t3w1` emulator baseline. Port narrow interfaces after that baseline runs. |

Source anchors at the reviewed head:

- [Protocol fields and signature types](https://github.com/trezor/trezor-firmware/blob/d562254c2195d688ca59296f048ed905047317fe/common/protob/messages-zcash.proto#L10).
- [Version-5 gate and signing sequence](https://github.com/trezor/trezor-firmware/blob/d562254c2195d688ca59296f048ed905047317fe/core/src/apps/zcash/signer.py#L50).
- [Orchard reconstruction, digest and signature flow](https://github.com/trezor/trezor-firmware/blob/d562254c2195d688ca59296f048ed905047317fe/core/src/apps/zcash/orchard/signer.py#L113).
- [Message accumulator](https://github.com/trezor/trezor-firmware/blob/d562254c2195d688ca59296f048ed905047317fe/core/src/apps/zcash/orchard/accumulator.py#L26).
- [Viewing-key export consent](https://github.com/trezor/trezor-firmware/blob/d562254c2195d688ca59296f048ed905047317fe/core/src/apps/zcash/get_viewing_key.py#L18).
- [Device signing test scenarios](https://github.com/trezor/trezor-firmware/blob/d562254c2195d688ca59296f048ed905047317fe/tests/device_tests/zcash/test_sign_shielded_tx.py#L61).
- [Rust dependency patches](https://github.com/trezor/trezor-firmware/blob/6311675119e9b6f22c49ad8aa6f38c9bf9617aa4/core/embed/rust/Cargo.toml).

The Rust PR uses Pasta 0.4.0 with a patch to `jarys/pasta_curves` revision
`a4f755013aad344982383c9f5af362697d928325`, plus a local `blake2b_hal` patch.
These are part of the review surface; a dependency version bump alone is not a
compatibility or security argument.

## Review status and limits

GitHub reports 73 review threads on PR 2472, eight unresolved; PR 2510 has 13,
one unresolved. These flags are workflow metadata: some replies point to fixes
or say the issue is resolved, so the counts are not a count of remaining bugs.

The [October 2022 review](https://github.com/trezor/trezor-firmware/pull/2472#pullrequestreview-1149090763)
explicitly limited its cryptographic coverage. A later engineering review also
requested address/viewing-key tests and rebasing; those test files are present
at the captured head, so that historical request is not reported as a current
missing-test defect. The
[accumulator cryptography-review request](https://github.com/trezor/trezor-firmware/pull/2472#discussion_r1023843381)
and [buffer-size discussion](https://github.com/trezor/trezor-firmware/pull/2472#discussion_r1023842949)
remain relevant review context. The Rust PR's
[dependency review](https://github.com/trezor/trezor-firmware/pull/2510#pullrequestreview-1177228541)
and [obsolete buffer API discussion](https://github.com/trezor/trezor-firmware/pull/2510#discussion_r1020164920)
reinforce the need to re-evaluate its current integration.

No conclusion about constant-time execution, key erasure, maximum memory,
physical-device behavior, complete cryptographic correctness or maintainers'
current willingness to merge follows from this assessment.

## Licensing

The upstream [license map](https://github.com/trezor/trezor-firmware/blob/7105338e3c2c1e681940e17780609881ce53126b/LICENSE.md)
assigns GPLv3 to core and storage, LGPLv3 to common and Python, and mostly MIT
licenses to crypto with per-file exceptions. Check each actual file before
copying it. The MIT license on this project's orchestration does not relicense
upstream code or vectors. This assessment copies no upstream implementation.

## Next implementation gate

1. Run the current Safe 7 emulator's existing Zcash tests and record the exact
   toolchain and source identity.
2. Define received fields, explicit size limits, device-derived ownership/change,
   fee accounting, network/pool rules and the exact displayed approval projection.
3. Map every validation obligation to a pinned PCZT API or a documented missing
   device check, and bind approval to the exact object later signed.
4. Build positive and adversarial conformance tests with the actual PCZT types
   before adding key handling or a shielded signing UI.
