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
| M2.1 | Actual typed THP upload/review/sign passes; hostile recovery and receive flow pending | Prototype Safe 7 shielded review/sign flow | Synthetic receive/send succeeds in emulator; hostile host and cancel/retry tests pass; accurate display and bounded memory measured. |
| M2.1a | Complete for experimental profile 1 | Compile portable approval core for Safe 7 target | Complete default-features-disabled core, upstream digest/signature equivalence, entropy interruption tests and independent adversarial/readability reviews. |
| M2.1b | Safe 7 native application linked; artifact/failure-path inspection and runtime fit pending | Measure synthetic approval resource use | Record reproducible allocation/peak-heap and latency results for 1–8 actions, identify copy/stack costs, compare against source-defined device budgets; keep host measurements distinct from MCU results. |
| M2.1c | Typed THP review/hold and host Cancel/fresh retry pass; Opus follow-up delivered, stricter run exposed shutdown SIGBUS; overall acceptance rejected | Implement trusted emulator review and consent | Show every payment/change/fee from the immutable projection, bind physical UI events to its token, test cancellation and replacement; no transport-triggered approval. |
| M2.1d | Actual signing and ordinary timeout recovery pass; late chunk defect characterized; reconnect unproven | Integrate bounded emulator transport and signing | Fragmentation/size limits, disconnect/replay/failure tests and actual synthetic signed response; no production key-store or physical-device use. |
| M2.2 | In progress: eleven host-model proofs pass; firmware refinement pending | Prove selected approval/accounting properties | Non-vacuous Lean statements, warning-fatal build, expected axioms only, implementation correspondence documented and reviewed. |
| M2.3 | Safe 5 native image fits with 27,136 B flash margin; stack/GC, latency and runtime remain open | Assess other Trezor models | Compare actual model layouts and runtime interfaces; use cheap target/link gates before UI porting; prioritize the available Safe 5 for first hardware testing. |
| M3 | Later | Independent review, hardware and release path | Cryptographic/embedded review, device matrix, dedicated hardware tests, recovery/privacy UX and upstream acceptance. |
| M4 | Delivery requirements established; prototype export incomplete | Prepare maintainable Trezor handoff | Focused upstream patch series, dependency/licenses and reviewed boundaries; clean-checkout reproduction without hidden local inputs; upstream tests/generation/changelog/CI and explicit model evidence. |

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

## Immediate development focus

Safe 5 is the first physical target. The complete synthetic native image now
links with 27,136 bytes of flash margin in the explicitly changed configuration
documented in [SAFE5_NATIVE.md](SAFE5_NATIVE.md). Host approval, bridge lifecycle
and independent signature checks pass with the smaller dependencies. Do not repeat
the completed baseline/fit tests without a change or call this hardware-ready.

The reviewed native layout now links with a 48 KiB stack, 92,880-byte primary
and 41,696-byte secondary GC reservations. The actual C layout and independent
boundary audit establish that the changed GC state has no Rust representation at
this interface; no extra binding is needed. Complete live-stack/peak-lifetime
checks. The selected current parsing path already totals 42,016 frame bytes
before interpreter callers and exception overhead. A larger reservation is
not a proven bound, and the two heaps cannot be combined for a single large
allocation. Host collection/reuse and failure checks pass; native UI, I/O roots,
maximum input/response lifetimes and MCU latency remain the runtime bottleneck.

The supported secp256k1 2 KiB comb configuration now recovers 20,480 bytes in
the actual native image. Its upstream host suites and both source reviews pass.
Computed Sinsemilla is about 16 times slower in the measured host hash operation;
a compressed-table alternative has passed host comparisons but has no accepted
native image. Use target timing to decide the next optimization, rather than
accumulating compiler switches or changing transaction semantics.

The Safe 5 legacy-wire/Delizia emulator delta has both source reviews and now
builds in an independent offline copy of the retained overlay. Source/API checks
pass with their recorded Python 3.14 interpreter. The first rendered exploration
reached context, output, full receiver and Cancel menu, then failed to open the
confirmation screen. Preserve that incomplete run. Actual geometry showed the original coordinate
was valid; waiting past the attach animation enabled cancellation in a fresh run.
Both menu and final-screen cancellation now return ActionCancelled and home;
shutdown still exits 1 after SIGINT, so complete runtime acceptance remains.
The candidate now has selected decode, validation, signing-reparse and serialization
subtotals of 32,408/31,504/27,072/11,016 bytes. Prioritize a complete signing peak
measurement, serializer growth and allocator lifetimes; these subtotals do not
establish full maxima. Review/test the proposed smaller response allocation when
its exact-packet authorization is resolved.
Finish native memory/latency preparation before requesting an attended
installation session. The unopened device remains untouched, and flashing
requires a concrete separate decision.

Keep the Safe 7 reference and every failed Safe 5 artifact. Safe 7's stricter
runtime harness exposed shutdown SIGBUS; its earlier false pass is rejected.
Fresh-channel recovery remains untested after an automated safety filter blocked
that assignment. Do not silently retry that blocked action. Production key/entropy
integration, receive-address consent and the wider model matrix follow these
resource/runtime gates. The tracked native source package is a review checkpoint;
full clean-checkout reproduction and upstream adoption requirements remain open.

For each meaningful memory change, retain the preceding snapshot and refresh
the explicit ELF/map-derived flash/module and RAM allocation report. Record actual
stack/arena/heap peaks, largest free blocks and target latency separately; never
replace unknown runtime values with reserved capacities. Source inspection found
29,804 permanent Pallas-table arena bytes. Investigate upstream table-free
arithmetic only as a measured tradeoff, preserving dependency feature accounting
and the explicit public-allocation startup contract.
