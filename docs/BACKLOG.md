# Backlog

Work one bounded item per scheduled turn. Do not re-run passing expensive checks
without a change, a new failure, or a specific unresolved concern.

| ID | Status | Work | Acceptance criteria |
| --- | --- | --- | --- |
| M0.1 | Complete | Establish workspace, pins, local checks and budget policy | Pins checked out; harness failure cases pass; no additional paid service enabled. |
| M0.2 | Complete for documented source, PCZT and Lean baseline lanes | Record upstream test and proof baselines | Exact commands, revisions, logs, result counts and failures recorded; incomplete proof lanes explicitly distinguished. |
| M0.3 | Complete | Assess Trezor PRs 2472 and 2510 | Fetch exact PR heads into separate checkouts; map changed crypto, host protocol, device UI, tests, licenses, current-build incompatibilities and unresolved reviews. Produce a concrete reuse recommendation. |
| M0.4 | Complete | Build current Safe 7 emulator baseline | Install documented local dependencies, pin Rust nightly from source, initialize required submodules; build `t3w1`; run existing Zcash tests using the emulator and record commands. No device flashing. |
| M1.1 | Complete for experimental profile 1 | Define PCZT-to-device approval contract | Enumerate received fields, bounds, trust decisions, accounting, display projection and immutable context; identify exact upstream validation APIs and missing checks. |
| M1.2 | Complete for experimental profile 1 | Implement host conformance harness | Use actual pinned PCZT types; positive control plus malicious mutation cases for recipient, value, change, fee, network, pool, replay and post-approval substitution. No cryptographic reimplementation. |
| M1.3 | Pending evidence | Prepare first upstream proposal | One small useful change, reproducible before/after evidence, appropriate destination and local issue text. Send only after authorization; satisfy maintainer acknowledgment before PR. |
| M2.1 | In progress: allocator and linked/runtime preparation after target diagnostics | Prototype Safe 7 shielded review/sign flow | Synthetic receive/send succeeds in emulator; hostile host and cancel/retry tests pass; accurate display and bounded memory measured. |
| M2.1a | Complete for experimental profile 1 | Compile portable approval core for Safe 7 target | Complete default-features-disabled core, upstream digest/signature equivalence, entropy interruption tests and independent adversarial/readability reviews. |
| M2.1b | Host and concrete codegen gates complete; linked/runtime and whole-stack evidence pending | Measure synthetic approval resource use | Record reproducible allocation/peak-heap and latency results for 1–8 actions, identify copy/stack costs, compare against source-defined device budgets; keep host measurements distinct from MCU results. |
| M2.1c | Pending resource evidence | Implement trusted emulator review and consent | Show every payment/change/fee from the immutable projection, bind physical UI events to its token, test cancellation and replacement; no transport-triggered approval. |
| M2.1d | Pending trusted review | Integrate bounded emulator transport and signing | Fragmentation/size limits, disconnect/replay/failure tests and actual synthetic signed response; no production key-store or physical-device use. |
| M2.2 | In progress: eleven host-model proofs pass; firmware refinement pending | Prove selected approval/accounting properties | Non-vacuous Lean statements, warning-fatal build, expected axioms only, implementation correspondence documented and reviewed. |
| M3 | Later | Independent review, hardware and release path | Cryptographic/embedded review, device matrix, dedicated hardware tests, recovery/privacy UX and upstream acceptance. |

## Escalation rules

If one command fails twice, diagnose or switch to an independent ready task.
Preserve failures. Escalate only a concrete decision or external dependency after
completing unaffected work. Do not claim the full project is blocked because one
toolchain or maintainer response is pending.

Profile 1 is synthetic regtest, Ironwood-only, bounded to eight actions with empty
memos and single-account ownership. Its numerical limits are prototype
limits; the 15-layout host measurements do not bound every admitted PCZT. M1 completion does not imply the full pool/device matrix is supported.
See `APPROVAL_CONTRACT.md`, `APPROVAL_RESULTS.md` and `APPROVAL_PROOFS.md`.


The user explicitly approved the portable RNG/digest/private-signing refactor.
It is applied, tested and independently reviewed; see `proposals/PORTABLE_APPROVAL_CORE.md`.
Bounded workers completed core compatibility, adversarial regressions, readability
and the source-defined Safe 7 resource map (`SAFE7_INTEGRATION.md`).
Claude Code with Fable provides the requested separate adversarial change review.
Host memory/timing evidence is recorded in `RESOURCE_RESULTS.md`. Device linking,
native stack, shared runtime memory, trusted UI and entropy integration remain pending.
