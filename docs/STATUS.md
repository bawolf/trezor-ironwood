# Project status

Updated 2026-09-08 UTC (2026-09-07 evening in California).
Development branch: `codex/verification-and-reuse`.

## Implemented

- Pinned upstream sources, contribution/threat-model research, local evidence
  runners, exact revisions and clean-source checks, timeouts and budget policy.
- [Trezor PR reuse assessment](TREZOR_REUSE.md): 110 inventoried file entries with
  hashes, review state, licensing and current-build compatibility boundaries.
- [Safe 7 emulator baseline](FIRMWARE_BASELINE.md): T3W1 2.12.5.0 built with the
  source-pinned Rust nightly and GCC 15; nine existing Zcash scenarios pass.
- [Profile 1 approval contract](APPROVAL_CONTRACT.md) and actual host reference:
  bounded preflight, full PCZT/FVK/commitment checks, ciphertext recovery, checked
  accounting, ownership-derived change and immutable consent through signing.
- [Conformance suite](APPROVAL_RESULTS.md), dependency identity and local input
  hashes; [eleven Lean structural proofs](APPROVAL_PROOFS.md) with exact axiom guards.
- [Embedded compatibility probe](../experiments/embedded-probe/README.md): the
  shared scanner and upstream verifier APIs compile without an OS for Safe 7's
  `thumbv8m.main-none-eabihf` target. This is not a linked firmware image.

## Validation

| Check | Result |
| --- | --- |
| Project failure-path tests | 16 passed, including emulator and axiom-census false-success guards |
| Upstream PCZT library tests | 66 passed, none failed/ignored/filtered |
| Upstream Ironwood integration tests | 4 passed |
| Upstream firmware wire-compatibility tests | 4 passed; Keystone fixture, not Trezor |
| Ironwood source/census/fixture scripts | All six passed; 480 modules and 200 endpoint declarations |
| Host approval conformance | 28 passed; formatting and warning-fatal Clippy passed |
| Host dependency identity | All 133 registry packages match upstream versions/checksums |
| Local approval/accounting Lean model | 11 named theorems; both default targets, census and exact axiom guards passed |
| Safe 7 processor compatibility | `no_std` verifier probe passed on the actual Rust MCU target |
| Current Safe 7 emulator | Nine existing transparent Zcash/v5 tests passed, no skips/failures |
| Full upstream Lean proof build | Incomplete: two 20-minute timeouts and one 60-minute timeout; unchanged full-target resume running |

Latest ignored local reports:

- Project: `work/runs/20260908T050651Z-project-27cd19de/report.json`.
- Approval: `work/runs/20260908T052631Z-approval-9ff95bb3/report.json`.
- Local proofs: `work/runs/20260908T051419Z-approval-proofs-3abb0f64/report.json`.
- Embedded probe: `work/runs/20260908T050942Z-embedded-probe-067453c0/report.json`.
- Emulator: `work/runs/20260908T040947Z-firmware-zcash-f4fcf912/report.json`.

Portable result summaries and hashes are in `BASELINE_RESULTS.json`. Raw logs,
synthetic PCZTs and toolchain caches remain ignored. Earlier failed/partial runs
are retained; see the firmware and approval evidence documents for diagnoses.

The 60-minute upstream Lean run ended at 05:02:34 UTC with exit 124. Its log
reached 3,833/3,915 jobs without reporting a proof error; it is **not a passing
result**. Seventy-five local source modules still lacked compiled artifacts when
inspected. The unchanged resume launched at 05:08:44 UTC and writes to
`work/runs/20260908T050844Z-lean-f2a9f49d/`. Check its report/lock before launching
another run. All six default targets and upstream axiom/census checks remain in
place; no target, warning gate or axiom policy has been weakened.

## Continuing

M1 is complete only for the explicit synthetic-regtest, Ironwood-only profile.
A test-only digest assembly experiment now matches the standard Signer across
all admitted action counts and both deferred/restored anchors. The combined
portable RNG/digest/signing-core rewrite was rejected by automatic approval review
and remains unapplied, with a [reviewable proposal and patch](proposals/PORTABLE_APPROVAL_CORE.md)
awaiting explicit approval. The working Engine remains unchanged.

Device allocation/entropy interfaces, the complete embedded signature-digest path,
Safe 7 integration, measured resources and authenticated device review remain M2.
The local proofs have a documented correspondence to Rust, not machine-checked
Rust or firmware refinement. Mixed pools and general memo/address/batch support
require contract extensions before acceptance.

The existing `trezor-ironwood-development` heartbeat continues every two hours in
the coordinating task, one bounded item per scheduled run, reporting meaningful
changes. Manual development can continue across milestones without waiting for it.
No new automation is needed. Keep the machine on and Codex running.

## Limits and external dependencies

- No physical device accessed or flashed, no real-funds transaction, no production
  seed loaded. The current shielded signer is a host reference, not device firmware.
- Independent cryptographic/embedded review and eventual hardware validation remain.
- No outreach sent. Librustzcash needs maintainer acknowledgment before a PR.
- GitHub CI remains a template at `ci/project-workflow.yml`; the OAuth credential
  lacks the `workflow` scope. No GitHub Actions run has occurred.
- The initial budget is USD 300 total. No paid service, cloud runner, API credit or
  subscription purchased; existing Codex account usage is not dollar-metered here.

These milestones do not complete the shielded-support project or establish that
the wallet, circuit or eventual firmware is ready for funds.
