# Project status

Updated 2026-09-08 UTC.
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
| Fixed-arena synthetic signing | Final native binary passed 35 process cases and 12 evidence-runner tests; Fable5.1 and independent clarity reviews complete for the synthetic scope |
| Unchanged Safe 7 target firmware | Complete test-preset secmon/kernel/firmware link; 697,992-byte GC region and 32 KiB application stack; no runtime claim |
| Current Safe 7 emulator | Nine existing transparent Zcash/v5 tests passed, no skips/failures |
| Full upstream Lean proof build | Passed: all six default targets, warning-fatal build and unchanged upstream axiom/census gates; 3,915 jobs |

Latest ignored local reports:

- Project: `work/runs/20260908T204424Z-project-b1cec119/report.json`.
- Fixed arena: `work/arena-probe/v4/verification-01/report.json`.
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

[Concrete target code generation](TARGET_CODEGEN_RESULTS.md), its size-comparison
Fable review and separate readability reviews are complete. The initial codegen
review reported Opus despite requesting Fable; a confirmed Fable5.1 replacement
now closes that attribution gap. A traced ordinary-call path totals 33,000
frame bytes in the opt3/noLTO experiment, above the source-defined 32 KiB stack.
The identical-source size-optimized build changes the call structure, so no final
stack-fit conclusion follows. The [allocator proposal](proposals/SYNTHETIC_ALLOCATOR.md)
and its two reviews are complete. The [unchanged target firmware](TARGET_FIRMWARE_BASELINE.md)
now supplies a concrete paired-build baseline. The [native arena experiment](../experiments/arena-probe/README.md)
passes its synthetic ownership and signature gates; its [review record](reviews/ARENA_PROBE.md)
tracks final adversarial acceptance. The [separate compile-only allocator image](TARGET_ALLOCATOR_LINK.md)
also linked: 4,208 additional BSS bytes and 265,216 additional flash bytes. Its
4 KiB diagnostic arena cannot run the signing lifecycle. The clarity correction produces byte-identical firmware; the secure-monitor data
relocations are explained. Final Fable5.1 and clarity reviews found no blocking issue. [The linked validation path](LINKED_STACK_PATH.md) has a conditional 40,776-byte
frame subtotal, above the 32 KiB reservation; no actual overflow or executable
input path is claimed. Its documented Opus fallback review is accepted.

The next milestone is one actual synthetic PCZT verified, reviewed, approved and
signed in the Safe 7 emulator. The isolated Rust/MicroPython bridge and frozen
review screens are implemented locally. The real-core host lifecycle passes,
including replacement/replay/cancellation and response bounds; its signed response
matches the independently verified oracle input. Thirteen UI orchestration tests,
two demo error-propagation tests, actual-header C compilation and warning-fatal
Clippy pass. These are not integrated screen, GC or emulator signing results.

Two confirmed Fable5.1 reviews and independent clarity reviews examined the bridge
and corrections. They identified demo exceptions swallowed by the scheduler; the
launcher now propagates those errors at module scope and rejects a missing outcome.
The latest corrections also reject invalid C snapshot kinds/counts and response
lengths. Final runtime acceptance remains pending. Source and evidence are retained
locally under `work/emulator-signing-bridge/` and `work/reviews/emulator-signing-bridge*/`.

The first integrated emulator build reached its 1,200-second process-group limit
without a compiler diagnostic or linked image. Compiled source inputs and resolved
locks stayed unchanged. Its warm build directory and failure evidence are retained
at `work/emulator-signing-build/integration-build-01/`; a second bounded build uses
the reviewed corrections and the same official test preset, features and deadline.
The approval core remains unchanged.

The earlier cold-start image now passes a normal process run through all four
compiled startup/shutdown gates, including a requested two-second sleep and exact
start/end markers. The explicit pinned Python/unbuffered Tropic launcher became
ready in 2.79 seconds under the unchanged ten-second deadline. This does not explain
the historical shebang-launch timeout. LLDB separately stalled before emulator
launch and is parked; no debugger counter snapshot or signing is claimed.
Evidence: `work/emulator-arena-runtime-05/report.json`.

A separate ARM compiler experiment now measures the actual begin/sign callbacks.
An isolated two-line candidate prevents inlining of the existing verification
function: its selected validation subtotal falls 33,688 to 30,688 bytes; selected
signing stays 31,952 bytes. That leaves only 816 bytes before unmeasured C/VM costs
and is not a device-fit result. The candidate is unintegrated, and the next bounded
experiment targets redundant upstream parser staging. See local
`work/bridge-stack-probe/REPORT.md`; the earlier rejected helper is not adopted.
M2.1c requires actual trusted review/consent; bounded host transport remains later.

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
  subscription purchased. Twenty-one completed Claude Code review requests reported
  USD 35.655473 at list prices; USD 35.77 is reserved. Fifteen report Fable by
  name, including both bridge reviews (`claude-fable-5-1`). Earlier substitutions
  and authentication failures remain recorded. The user accepts documented Opus
  fallbacks; actual model identities are checked and substitutes are never labeled Fable.
  Actual subscription billing and Codex dollar usage are not observed here.

These milestones do not complete the shielded-support project or establish that
the wallet, circuit or eventual firmware is ready for funds.
