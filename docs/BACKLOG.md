# Backlog

Work one bounded item per scheduled turn. Do not re-run passing expensive checks
without a change, a new failure, or a specific unresolved concern.

| ID | Status | Work | Acceptance criteria |
| --- | --- | --- | --- |
| M0.1 | Complete | Establish workspace, pins, local checks and budget policy | Pins checked out; harness failure cases pass; no additional paid service enabled. |
| M0.2 | In progress | Record upstream test and proof baselines | Exact commands, revisions, logs, result counts and failures recorded; incomplete proof lanes explicitly distinguished. |
| M0.3 | Complete | Assess Trezor PRs 2472 and 2510 | Fetch exact PR heads into separate checkouts; map changed crypto, host protocol, device UI, tests, licenses, current-build incompatibilities and unresolved reviews. Produce a concrete reuse recommendation. |
| M0.4 | Complete | Build current Safe 7 emulator baseline | Install documented local dependencies, pin Rust nightly from source, initialize required submodules; build `t3w1`; run existing Zcash tests using the emulator and record commands. No device flashing. |
| M1.1 | In progress | Define PCZT-to-device approval contract | Enumerate received fields, bounds, trust decisions, accounting, display projection and immutable context; identify exact upstream validation APIs and missing checks. |
| M1.2 | Pending M1.1 | Implement host conformance harness | Use actual pinned PCZT types; positive control plus malicious mutation cases for recipient, value, change, fee, network, pool, replay and post-approval substitution. No cryptographic reimplementation. |
| M1.3 | Pending evidence | Prepare first upstream proposal | One small useful change, reproducible before/after evidence, appropriate destination and local issue text. Send only after authorization; satisfy maintainer acknowledgment before PR. |
| M2.1 | Pending M1 | Prototype Safe 7 shielded review/sign flow | Synthetic receive/send succeeds in emulator; hostile host and cancel/retry tests pass; accurate display and bounded memory measured. |
| M2.2 | Pending contract | Prove selected approval/accounting properties | Non-vacuous Lean statements, warning-fatal build, expected axioms only, implementation correspondence documented and reviewed. |
| M3 | Later | Independent review, hardware and release path | Cryptographic/embedded review, device matrix, dedicated hardware tests, recovery/privacy UX and upstream acceptance. |

## Escalation rules

If one command fails twice, diagnose or switch to an independent ready task.
Preserve failures. Escalate only a concrete decision or external dependency after
completing unaffected work. Do not claim the full project is blocked because one
toolchain or maintainer response is pending.
