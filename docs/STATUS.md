# Project status

Updated 2026-09-09 UTC.
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

- Project: `work/runs/20260909T204659Z-project-efe3d148/report.json`.
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

The [first synthetic emulator signing flow now passes](EMULATOR_SIGNING_RESULTS.md):
verified context/output/receiver/totals pages, short-press rejection, animated final
hold, signed response and independent verification of both new real-spend signatures.
Real menu cancellation, an injected post-validation UI failure, and cancellation
followed by a second complete approval in one process pass their exact outcome and
cleanup checks. The retry response is byte-identical to the verified oracle input. The retained fixed-fixture image is
`82608d19eedfe07a97433c4cb3cca6eae92cad8530ce6197f7e2fce7e0843c8b`.

The [desktop-to-emulator THP flow now passes](TRANSPORT_RESULTS.md): bounded
caller upload, native validation, all seven trusted review pages, rejected short
press, final hold and complete signed response. An independent oracle verifies
both returned real-spend signatures. The isolated image is
`36237692d909d9d4274d231cf924946b76a57eb7a14f2c7c0f63c53a3780d241`.
Its first runtime caught an incorrect Python type check on native protobuf
definitions. A one-line native-API correction, regression with firmware-shaped
message doubles, rebuild and actual rerun pass; all failed evidence is preserved.

The [native caller-input bridge](HOST_INPUT_RESULTS.md), typed protocol and host
client retain the accepted core and existing memory limits. Twelve host tests,
twelve actual-scheduler lifecycle cases, and eleven retained UI plus two relocated
validation cases pass their stated scopes. Both approved source packets completed
on confirmed Fable 5.1; [independent dispositions](reviews/TRANSPORT.md) reject
unsafe/redundant cleanup or accounting changes and identify concrete remaining
runtime cases. Two follow-up Fable requests failed (budget exhaustion, then a
provider timeout); the user-approved Opus 5 fallback delivered a review of the
current driver and descriptor correction. It supports the firmware design but
identifies acceptance-driver gaps. Source disposition is complete; a separate
driver rerun closed several concrete gaps but exposed an abnormal native
shutdown, described below. Scoped source
reviews are authorized through the existing account; substantive reviews now use
a $15 allowance within the total project budget.

Actual host Cancel at final hold followed by a fresh complete approval/signature
passes in the same emulator/session/channel. Ordinary upload timeout followed by
GetFeatures also passes. A deliberately late chunk instead triggers a
NoiseInvalidMessage authentication error before the expected timeout read; that
failed recovery is preserved. Source/packet analysis and a small real-cipher
component test identify a discarded response in the pinned desktop channel. A
[local proposal](proposals/THP_CROSSED_RESPONSE.md) records the mechanism, Fable
findings and the limits of that evidence. A reconnect-test agent was blocked by
an automated safety filter before execution; recovery remains unproven.
Admission-bound rejection,
response ACK loss, final-hold deadline and reachable channel preemption remain.
Hardware is available; MCU stack fit and production keys remain gates.

A stricter acceptance rerun completed all seven pages, rejected the short press,
returned the same independently verified bytes and passed the explicit three-chunk
positive control. During cleanup the emulator logged `Fatal: Assert at vm.c:327`
and exited with SIGBUS. Its harness incorrectly reported success; the parent
acceptance record explicitly rejects the overall result. Processes were reaped.
A separate unrun harness correction rejects abnormal exits, with a small
failure-classification regression passing; shutdown cause remains under diagnosis.
The earlier passing image/core was unchanged.

A separate ARM compiler experiment measures the actual begin/sign callbacks.
An isolated two-line candidate prevents inlining of the existing verification
function: selected validation falls 33,688 to 30,688 bytes; selected signing stays
31,952 bytes. Only 816 bytes remain before unmeasured C/VM costs, so this is not a
stack-fit result. A follow-up found the upstream parser already uses direct push;
no small source cleanup justified adding another abstraction. The candidate remains
unintegrated and the accepted core is unchanged. Local reports are under
`work/bridge-stack-probe/`. A [second stack experiment](STACK_PROGRESS.md) outlines
the existing serializer: selected signing parsing drops to 26,648 bytes, while
the selected serialization path is 18,360 bytes. The full maximum is unknown.
The single combined experiment reproduces both measured gains: begin 30,688,
signing parse 26,648 and serialization 18,360 bytes. No integration or hardware-fit
claim follows. Source inspection now establishes that the stack reservation is a firmware
choice inside fixed shared application RAM. An illustrative 64 KiB stack would
cost 32 KiB of GC space while retaining existing stack-limit enforcement. No
limits were changed; integrated target maps and concurrent heap/stack measurements
now drive the next decision, rather than assuming an immutable 32 KiB ceiling. M2.1c/M2.1d continue beyond the fixed-fixture demonstration.

The [target-native integration](TARGET_NATIVE_INTEGRATION.md) now has a reviewed
CPU-context/lifetime adapter, a real ARM object, seven negative configuration
checks, and isolated frozen dependencies. Fable5.1 and independent clarity reviews
are dispositioned. The small standalone adapter and compiler recipe are tracked.
The isolated application now links with the unchanged source, 32 KiB stack and
128 KiB arena. The map assigns 565,052 bytes to GC and 2,639,360 bytes to the full
flash load extent; caller/failure-path inspection and runtime fit remain separate
acceptance checks. A candidate linked path has 32,912 bytes of local frames,
above the reservation; simultaneous stack/control-flow analysis remains pending.
The first attempt failed because core was rebuilt without alloc;
the command-only correction matches the prior allocator build. No firmware or
hardware execution occurred. The shutdown source diagnosis identifies a VM frame
tracking assertion; asynchronous interrupt/context interaction is a hypothesis,
not an established root cause or a native fix.

The [model portability assessment](MODEL_PORTABILITY.md) identifies Safe 5 as the
closest follow-on and newer Safe 3 as a plausible button-UI port. Model T and
older Safe 3 require a different resource plan; Model One cannot fit the current
arena integration unchanged. These are source findings, not new device builds.
The [Trezor handoff requirements](TREZOR_HANDOFF.md) are now part of the standing
project instructions: focused upstream changes, standard integration, complete
provenance, explicit test/product boundaries and clean-checkout reproduction.
A fresh clone passes all 27 Python project checks; the complete emulator prototype
still needs portable source/fixture export. The user has now confirmed an unopened
Safe 5 dedicated to testing. Finish the Safe 7 artifact inspection and prepare an
isolated Safe 5 baseline, then its native, Delizia UI and older-wire integration.
The [hardware session plan](HARDWARE_SESSION.md) groups physical actions; no Safe 5
Ironwood image is ready. The missing host libusb dependency is installed and the
offline host-input check passes without device enumeration or access.

The local proofs have a documented correspondence to Rust, not machine-checked
Rust or firmware refinement. Mixed pools and general memo/address/batch support
require contract extensions before acceptance.

The existing `trezor-ironwood-development` heartbeat continues every two hours in
the coordinating task, one bounded item per scheduled run, reporting meaningful
changes. Manual development can continue across milestones without waiting for it.
No new automation is needed. Keep the machine on and Codex running.

## Limits and external dependencies

- No physical device accessed or flashed, no real-funds transaction, no production
  seed loaded. A synthetic emulator signer now runs; production device support remains unimplemented.
- Automated adversarial/readability reviews are recorded; independent specialist
  cryptographic/embedded review and eventual hardware validation remain.
- No upstream maintainers have been contacted. A PR to librustzcash would require
  their prior acknowledgment; using the libraries and local prototyping can continue.
- GitHub CI remains a template at `ci/project-workflow.yml`; the OAuth credential
  lacks the `workflow` scope. No GitHub Actions run has occurred.
- The initial budget is USD 300 total. No paid service, cloud runner, API credit or
  subscription purchased. Thirty completed Claude Code review requests reported
  USD 51.03919725 at list prices; USD 51.21 is reserved for that reported usage.
  Twenty-three requests identify Fable; that count includes failed requests and is not
  a count of accepted reviews. Earlier substitutions, budget/provider failures
  and authentication failures remain recorded. The user accepts documented Opus
  fallbacks; actual model identities are checked and substitutes are never labeled Fable.
  Actual subscription billing and Codex dollar usage are not observed here.
  One user-authorized existing Codex reset credit was redeemed at 98% usage;
  two credits remain. No further reset has been authorized.

These milestones do not complete the shielded-support project or establish that
the wallet, circuit or eventual firmware is ready for funds.
