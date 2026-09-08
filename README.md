# Trezor–Ironwood

An engineering workspace for contributing shielded Zcash support to Trezor,
starting with the Safe 7 and a desktop host. The goal is a receive-and-send flow
whose on-device approval is tied to independently verified transaction effects.

This repository contains pinned upstream baselines, a bounded PCZT approval
reference, hostile-host conformance tests, selected Lean proofs and a Safe 7
emulator baseline. **It does not yet implement a
Trezor shielded signer, and no firmware is ready for use with funds.**

- [Current status](docs/STATUS.md)
- [Upstream findings and reuse map](docs/UPSTREAM.md)
- [Trezor shielded PR reuse assessment](docs/TREZOR_REUSE.md)
- [Safe 7 emulator setup and evidence](docs/FIRMWARE_BASELINE.md)
- [Approval contract](docs/APPROVAL_CONTRACT.md) and [conformance results](docs/APPROVAL_RESULTS.md)
- [Synthetic resource measurements](docs/RESOURCE_RESULTS.md) and [Safe 7 constraints](docs/SAFE7_INTEGRATION.md)
- [Approval/accounting proofs and boundaries](docs/APPROVAL_PROOFS.md)
- [PCZT validation obligations](docs/PCZT_VALIDATION_MAP.md)
- [Backlog and acceptance criteria](docs/BACKLOG.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Verification boundaries](docs/VERIFICATION.md)
- [Local setup and scheduled work](docs/OPERATIONS.md)

## Checks

Python 3.11+ is sufficient for the project checks. Upstream lanes additionally need
their documented toolchains and dependencies.

```sh
python3 scripts/check.py project
python3 scripts/bootstrap.py
python3 scripts/check.py ironwood-source
python3 scripts/check.py pczt
python3 scripts/check.py approval
python3 scripts/resource_check.py
python3 scripts/check.py approval-proofs
python3 scripts/check.py lean
```

Checkouts are exact, detached revisions from `upstreams.lock.json`; bootstrap never
updates an existing checkout. Changes to a pin need a reviewed compatibility reason.
The standalone Orchard checkout is for research; the PCZT build uses Orchard from
**librustzcash's own Cargo.lock**, not that checkout.

Detailed logs and machine-readable reports are stored under ignored `work/runs/`.
The runner rejects dirty/wrong-revision baseline checkouts, empty Rust test runs,
concurrent runs within each verification lock, and timed-out subprocesses.
The firmware runner has a separate lock and explicit model/nonempty-test checks;
see its setup guide before running it.

GitHub CI is prepared as `ci/project-workflow.yml`. Enabling it requires placing
it at `.github/workflows/project.yml` through an account with workflow permission.
The current OAuth credential lacks that scope; local checks are operational.

## Budget

The initial authorized total is **USD 300**. No additional paid service is enabled.
`ops/budget.json` records paid commitments and expenditure, but existing Codex
account usage has no dollar telemetry here. It is not a hard cap on Codex billing.

Original orchestration code in this repository is MIT licensed. Downloaded upstream
code retains its own license; in particular Trezor firmware license requirements
must be preserved in derivative work.
