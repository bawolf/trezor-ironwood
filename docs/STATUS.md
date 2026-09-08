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
  complete approval core compiles without OS features for Safe 7's
  `thumbv8m.main-none-eabihf` target. This is not a linked firmware image.

## Validation

| Check | Result |
| --- | --- |
| Project failure-path tests | 27 passed, including resource-report, emulator and axiom-census false-success guards |
| Upstream PCZT library tests | 66 passed, none failed/ignored/filtered |
| Upstream Ironwood integration tests | 4 passed |
| Upstream firmware wire-compatibility tests | 4 passed; Keystone fixture, not Trezor |
| Ironwood source/census/fixture scripts | All six passed; 480 modules and 200 endpoint declarations |
| Portable approval conformance | 36 passed; formatting and warning-fatal Clippy passed |
| Host dependency identity | All 133 registry packages match upstream versions/checksums |
| Local approval/accounting Lean model | 11 named theorems; both default targets, census and exact axiom guards passed |
| Safe 7 processor compatibility | Complete `no_std` core passed on the actual Rust MCU target; 126 registry packages match upstream |
| Host resource characterization | 15 layouts, 75 measured runs, 43 independently verified new signatures; all teardowns returned to baseline |
| Concrete target code generation | Actual Thumb objects; 3,180 individual frame entries; compiled optz comparison also passed; no linked/runtime fit claim |
| Current Safe 7 emulator | Nine existing transparent Zcash/v5 tests passed, no skips/failures |
| Full upstream Lean proof build | Passed: all six default targets, warning-fatal build and unchanged upstream axiom/census gates; 3,915 jobs |

Latest ignored local reports:

- Project: `work/runs/20260908T080145Z-project-b14450a0/report.json`.
- Resources: `work/runs/20260908T080145Z-resources-71a70bee/report.json`.
- Approval: `work/runs/20260908T064909Z-approval-748cc20f/report.json`.
- Local proofs: `work/runs/20260908T063118Z-approval-proofs-010aa368/report.json`.
- Embedded probe: `work/runs/20260908T064723Z-embedded-probe-313ddb21/report.json`.
- Emulator: `work/runs/20260908T040947Z-firmware-zcash-f4fcf912/report.json`.

Portable result summaries and hashes are in `BASELINE_RESULTS.json`. Raw logs,
synthetic PCZTs and toolchain caches remain ignored. Earlier failed/partial runs
are retained; see the firmware and approval evidence documents for diagnoses.

The full upstream Lean resume passed at 06:17:01 UTC, reporting 3,915 completed
jobs. `work/runs/20260908T050844Z-lean-f2a9f49d/report.json` records exit zero,
no timeout and command duration 2,506 seconds. Log SHA-256:
`0e9bcba442280d641de6c8dfff2de5bcf99dc711593ee4a7d1e6ad256b11a9df`.
All six default targets and upstream axiom/census checks remained in place.
Earlier partial runs are retained, including the 60-minute timeout at 3,833 jobs.
This is the source-pinned Lean build baseline; it does not claim every separate
upstream CI workflow, fixture regeneration or documentation check was run.

## Continuing

M1 is complete only for the explicit synthetic-regtest, Ironwood-only profile.
The user-approved [portable core refactor](proposals/PORTABLE_APPROVAL_CORE.md)
is implemented and accepted for this experimental profile. Complete host
conformance, exact target compilation and separate [Fable/readability reviews](reviews/PORTABLE_APPROVAL_CORE.md)
passed their stated scopes. The low-level signer remains private over an owned,
fully verified PCZT; device entropy, allocation and trusted UI are still required.

The [Safe 7 source map](SAFE7_INTEGRATION.md) identifies 800 KiB shared application
RAM, a 32 KiB native stack and two 8,704-byte THP buffers. These are shared firmware
constraints, not an approval-core allocation allowance. The first M2.1b gate,
[host resource characterization](RESOURCE_RESULTS.md), is complete: the largest
observed attributable peak was 80,821 bytes including the raw input. Separate
fixture/oracle and measurement agents implemented it; Fable and independent
readability reviews checked the change and its evidence runner.

[Concrete target code generation](TARGET_CODEGEN_RESULTS.md) and its separate
Fable/readability reviews are complete. A traced ordinary-call path totals 33,000
frame bytes in the opt3/noLTO experiment, above the source-defined 32 KiB stack.
The identical-source size-optimized build changes the call structure, so no final
stack-fit conclusion follows. The next project prepares an explicit allocator
boundary and concrete linked/runtime experiment under firmware settings.
M2.1c covers trusted review/consent and M2.1d covers bounded transport/signing.

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
- Automated adversarial/readability reviews are recorded; independent specialist
  cryptographic/embedded review and eventual hardware validation remain.
- No outreach sent. Librustzcash needs maintainer acknowledgment before a PR.
- GitHub CI remains a template at `ci/project-workflow.yml`; the OAuth credential
  lacks the `workflow` scope. No GitHub Actions run has occurred.
- The initial budget is USD 300 total. No paid service, cloud runner, API credit or
  subscription purchased. Six Fable review runs reported USD 14.0286585 at list prices through the
  existing Max subscription; USD 14.07 is conservatively reserved in the ledger.
  Actual subscription billing and Codex dollar usage are not observed here.

These milestones do not complete the shielded-support project or establish that
the wallet, circuit or eventual firmware is ready for funds.
