# Upstream map — 2026-09-08 UTC

Revision evidence is in `upstreams.lock.json`. All findings below refer to those
revisions or the separately pinned PR heads, not unspecified future main branches.

| Component | Evidence | Reuse and remaining work |
| --- | --- | --- |
| Trezor current firmware | `core/src/apps/zcash/signer.py:37` requires v5; its serializer emits empty shielded components. `hasher.py` implements an empty Orchard hasher. | The existing transparent path is not an Ironwood shielded signer. Design a separate bounded signing flow and assess integration. |
| Existing Trezor shielded work | [PR 2472](https://github.com/trezor/trezor-firmware/pull/2472), open, head `d562254c2195d688ca59296f048ed905047317fe` | Targets Model T/Orchard. Its checklist still lists memory allocation and Python review. Assess code and portability before transplanting; it predates the current Safe 7 build system. |
| Trezor Rust primitives | [PR 2510](https://github.com/trezor/trezor-firmware/pull/2510), open, head `6311675119e9b6f22c49ad8aa6f38c9bf9617aa4` | Candidate curve/signature/Poseidon implementation and test vectors. Must reassess dependency patches, licenses, performance and correctness. Open status is not approval. |
| PCZT host/signing interfaces | `pczt/src/roles/signer/mod.rs`, `low_level_signer/mod.rs`, `signer/batch.rs` | Both Orchard and Ironwood signature responses exist. Batch transport leaves request correlation, limits, and atomic behavior to the application. Low-level signing requires prior verification of the identical PCZT. |
| PCZT defense in depth | [Merged PR 2990](https://github.com/zcash/librustzcash/pull/2990), included in our baseline | Recent transparent-input checks and default SIGHASH_ALL policy already address hostile input metadata. Preserve these protections in mixed-pool flows. This is existing upstream work, not a new finding. |
| Ironwood formalization | [Repository](https://github.com/zcash/ironwood), `lakefile.toml`, `Zcash/TrustBoundary.lean` | Six default targets include source/axiom coverage and fixtures. Reuse the upstream verification machinery. It is not a proof of Trezor firmware or an approval UI. |
| v6 protocol | [ZIP 229](https://zips.z.cash/zip-0229), source pinned in zips checkout | Anchors move to authorization data for Sapling, Orchard, Ironwood; permitted re-anchoring should preserve effect digests. Pool domain separation and approved semantics still need enforcement. |
| Host wallet | [librustzcash](https://github.com/zcash/librustzcash), wallet backend and SQLite crates | Reuse transaction construction, sync and PCZT roles. Parsing alone does not establish consensus validity. |
| Connect/Suite | Main revision recorded, full checkout deferred | Assess protocol messages, viewing-key export consent, sync/proving orchestration, recovery UX, and how to keep desktop and third-party integrations compatible. |

## Contribution route

The original [Trezor proposal](https://forum.zcashcommunity.com/t/trezor-support-for-zcash-shielded-transactions/39420)
links milestone reports in [jarys/ztrezor](https://github.com/jarys/ztrezor).
Read the code and outstanding reviews rather than treating the proposal as shipped support.

The user has admin access to `bawolf/trezor-ironwood`. A read-only permissions check
returned no push/maintain/admin access to `zcash/librustzcash`. Its
[AGENTS.md](https://github.com/zcash/librustzcash/blob/5e770a91ad0d11938dbc713e7889e4aa8009266c/AGENTS.md)
requires an issue discussion acknowledged by a maintainer before a PR. No such
acknowledgment is recorded. Prepare a narrow, evidence-backed proposal locally;
request authorization for maintainer communication only when that proposal is ready.
