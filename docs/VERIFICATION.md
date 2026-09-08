# Verification plan and claim boundaries

## Evidence ladder

1. Pinned source and toolchain identity, clean baseline and reproducible commands.
2. Upstream vectors and targeted tests, then adapter tests using the actual APIs.
3. Adversarial/property tests and fuzzing of protocol/transport boundaries.
4. Lean specifications and proofs of selected state/accounting properties, with
   reviewed assumptions and a documented refinement to the executable adapter.
5. Emulator flows, memory/performance measurements, and independent review.
6. Dedicated hardware validation and upstream maintainers' release decisions.

A passing test does not prove all inputs safe. A source census is not proof
elaboration. A Lean theorem about a model does not establish firmware behavior
without the implementation connection. Do not describe any of these as complete
wallet or circuit safety.

## Current lanes

| Lane | Scope | What it does not establish |
| --- | --- | --- |
| `project` | Failure-path tests for local lock, timeout, pin validation, test counts and budget bookkeeping | A sandbox, provider spending cap or crypto verification |
| `pczt` | Upstream PCZT library tests, four Ironwood integration tests, four legacy firmware wire-compatibility tests | Whole librustzcash workspace, Safe 7 firmware, all v6 scenarios, consensus validation |
| `ironwood-source` | Six upstream source/census/fixture scripts | Lean proof success, all CI checks or complete fixture regeneration |
| `firmware build` / `firmware zcash` | Current Safe 7 emulator identity, pinned source/toolchain, nine existing Zcash signing tests | Physical-device behavior, production firmware, shielded support, full UI screenshot baselines |
| `approval` | Pinned actual-PCZT conformance, dependency identity, exact local input hashes, formatting and warning-fatal Clippy | Device behavior, exhaustive hostile inputs or consensus validation |
| `embedded-probe` | Actual core with default features disabled, source-pinned Safe 7 target toolchain, LLVM C tools, dependency identity and core input hashes | Concrete RNG code generation, linking, runtime signatures, heap/stack limits, firmware consent or entropy |
| `resources` (`scripts/resource_check.py`) | 15 synthetic layouts, allocation/lifecycle accounting, instrumented host timing, independently verified signatures, manifest binding and frozen source/binary hashes | Safe 7 link/runtime fit, MCU native stack or latency, all admitted inputs, allocator OOM behavior |
| `target-codegen` experiment | Concrete RNG instantiation, optimized ARM objects, per-function frames and a scoped nested-call trace; same-source optz comparison | Linked firmware, complete call-chain stack bound, runtime signatures, allocator/entropy/UI integration |
| `approval-proofs` | Eleven structural theorems, exact axiom guards and theorem census | Machine-checked Rust refinement, cryptography or firmware proofs |
| `lean` | `lake build --wfail` with all six pinned default targets | Reproducible Rust fixture regeneration, full firmware correctness or reviewed cryptographic assumptions |

The firmware compatibility fixture comes from **Keystone 3**, not Trezor. Its role
is a shared PCZT encoding regression baseline, not evidence of Trezor support.

The Ironwood build's fixture target and axiom checks remain enabled. A failing or
timed-out build stays incomplete. Additional upstream CI requirements include
layout-dump checksum/stamp consistency, book validation and fixture regeneration;
the six-script lane must not be reported as the entire CI pipeline.

## Candidate first formal property

After the adapter and its validation preconditions are concrete, formalize that
signing preserves the approved effect projection and that allowed v6 authorizing
data updates cannot alter that projection. Distinguish this structural property
from cryptographic collision resistance, note ownership, key secrecy and display
correctness. Avoid vacuous proofs where the desired property is simply assumed.

Retain upstream axiom whitelists and dependency census checks. No accepted `sorry`
or unexplained axiom additions. Keep adversarial proof-checker tests separate from
the production theorem dependency graph as upstream already does.

## Independent change reviews

Use two distinct reviews before accepting a proposed change. Claude Code with
Fable reviews adversarial correctness: what hostile input or state transition
breaks the claimed behavior, whether upstream APIs provide the assumed guarantees,
and which concrete regressions are missing. A separate agent reviews clarity,
conciseness, names and necessary abstractions. One coordinator resolves findings
and runs the relevant acceptance lanes after integration. Reviewers do not publish
comments or PRs; those actions still require their separate authorization.

Freeze the reviewed source, record its hashes and the base revision, and preserve
the review result under ignored `work/reviews/`. Save a concise finding/resolution
record in `docs/reviews/`. Any later substantive change needs review of that delta.
Run Fable through the existing Claude Code subscription with `--model fable`, a
per-run budget limit and read-only tools; do not silently substitute another model.
Record reported model usage separately from actual billing. Reviews are evidence
of scrutiny, not proof of cryptographic safety or approval for production funds.
