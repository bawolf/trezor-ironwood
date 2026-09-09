# Trezor handoff plan

The intended deliverable is a small, reproducible series of changes that Trezor
can evaluate and maintain. This repository is presently an engineering reference
and evidence archive, not that final patch series. The portable approval core and
its tests are tracked; the working emulator integration still relies on ignored
experiment directories, local paths and synthetic adapters. Removing those
dependencies is an explicit delivery requirement.

## What a reviewer should read first

1. [Approval contract](APPROVAL_CONTRACT.md): supported transaction profile,
   validation obligations, displayed effects and binding of consent to signing.
2. [Current status](STATUS.md), [transport results](TRANSPORT_RESULTS.md) and
   [memory/stack work](STACK_PROGRESS.md): successful evidence and unresolved failures.
3. [Verification boundaries](VERIFICATION.md) and [threat model](THREAT_MODEL.md):
   what the tests and formal models establish, and what still needs independent work.
4. [Model portability](MODEL_PORTABILITY.md): source-based priorities and the next
   feasibility gate for each hardware revision.
5. [Earlier Trezor work](TREZOR_REUSE.md) and [upstream map](UPSTREAM.md): provenance,
   APIs reused, existing review concerns and dependency ownership.

The current profile is synthetic regtest, Ironwood-only, single-account and at
most eight actions, with empty memos. It is not general shielded Zcash support.
No physical-device or production-key acceptance is claimed.

## Proposed change boundaries

These are review units, not promises that each will become a separate PR. Trezor
should help choose the final ownership and packaging before a large product patch.

| Review unit | Intended integration | Completion still required |
| --- | --- | --- |
| Approval rules and private signing core | Small Rust component using pinned upstream PCZT/Orchard APIs; final crate location is a maintainer decision | Preserve exact validation/consent contract; dependency/license review; product key and entropy boundaries; accepted regression suite |
| Native allocation and platform adapter | Existing firmware build, task and allocation interfaces | Real target integration, concurrency/cleanup/OOM checks, complete RAM/stack/flash budget and hardware evidence |
| Messages and desktop client | Normal `common/protob` generation and `python` client paths | Maintainer-assigned message IDs, generated bindings, compatibility/admission rules, cancellation and recovery; remove the private experimental registry from the product path |
| Trusted review and receive flow | Existing firmware app/workflow and model layout APIs | Correct key-derived receive addresses, full reviewed effects on each supported screen, physical confirmation and cancel tests per layout |
| Desktop product integration | Connect/Suite or another agreed host boundary | Construction/proving/sync ownership, version negotiation, viewing-key consent and recovery UX; the current Python client is a test driver, not a finished wallet |
| Independently useful upstream fixes | Their owning repository, with a focused reproducer | Confirm protocol intent and a real fix; isolate unrelated work from shielded support. The THP crossed-response proposal is currently a diagnosis, not an accepted fix |

Portable transaction semantics should stay shared. Allocation, trusted key access,
entropy, transport and layouts should use the platform's existing interfaces.
Introduce a new abstraction only when two concrete implementations justify it.
Do not create a generic device framework or duplicate the approval rules for each
model. A model that cannot meet the contract remains unsupported rather than
silently weakening validation or hiding review fields.

## The delivery package

The eventual package must contain:

- A short design note covering the problem, supported profile, data flow, trust
  boundaries and important alternatives. Link exact upstream APIs and dependencies.
- A rebased series against a named upstream revision, with focused commits and a
  clear dependency order. Each commit explains its behavioral change and tests.
- Reproduction from a clean checkout using pinned tools/locks and documented
  commands. Include necessary synthetic fixture sources and evidence manifests;
  do not require this machine, ignored donor checkouts or undocumented local state.
- Standard generated files, upstream style checks, relevant host/firmware/device
  and UI tests, and model-specific changelog entries. Record actual upstream CI
  results separately from this repository's local checks.
- Per-model build/resource/runtime results, including unsupported models and
  rejected runs. Emulator behavior and selected ARM frames are not hardware proof.
- Concise Fable/adversarial and independent clarity review dispositions tied to
  exact source revisions, plus the specialist reviews still required. AI review
  does not stand in for maintainer approval or a cryptographic audit.
- Dependency versions/features, local upstream patches, licensing and attribution
  sufficient for maintainers to audit and update the code. Preserve each source's
  license; this repository's MIT license does not relicense Trezor derivatives.
- Clear product limitations, operator/QA steps and integration ownership. Existing
  transparent signing and unsupported-model behavior need regression coverage.

Synthetic keys/RNG, auto-approval fixtures, debug-only commands, diagnostic arenas,
emulator startup hooks and local process supervisors belong in explicit tests or
experiments. They must not become reachable production signing paths. Product
diffs must not carry model-account configuration, automation state, spending
ledgers or large exploratory logs. Preserve those records in the research archive.

## Upstream process

Checked 2026-09-09 against the pinned firmware sources and published
[contribution guide](https://docs.trezor.io/trezor-firmware/misc/contributing.html)
and [review procedure](https://docs.trezor.io/trezor-firmware/misc/review.html).
Trezor asks for tested/formatted code, current generated files, concise commits,
changelog entries and passing CI. Its process uses structured commits and review
fixups, avoiding force-pushes during active review.

The pinned
[external-contributor template](https://github.com/trezor/trezor-firmware/blob/7105338e3c2c1e681940e17780609881ce53126b/.github/pull_request_template.md)
asks for an issue discussion before a PR. Librustzcash separately requires
maintainer acknowledgment before its PRs; see [the contribution route](UPSTREAM.md).
Prepare concrete proposals for those discussions. No upstream communication is
authorized by this document or has been sent for this handoff.

Published policy currently declines requests for new cryptocurrencies. This work
extends already-supported Zcash, but that distinction is not evidence that Trezor
wants this particular scope, dependency footprint or maintenance burden. Agreement
on the product and architecture is a separate dependency from technical success.

## Current delivery gaps

The whole emulator demonstration cannot yet be reproduced from the public checkout
alone. Target-native integration is being staged, and recovery/shutdown failures
remain open. Production keys/entropy, receive-address confirmation, additional
models, Connect/Suite and external CI are incomplete. The compiler outlining
candidate remains unaccepted pending functional and integrated resource evidence.

Before describing a component as ready for handoff, export its exact patch/source
and fixtures, perform the documented clean-checkout reproduction, and resolve or
explicitly block its acceptance findings. Do this incrementally as components
stabilize, while Safe 7 integration remains the primary implementation task.

A clean local clone of tracked revision `461077bf7b6f4a5f12885fbcf7ea99fffa543a4d`
was used for the Python project-check smoke test on 2026-09-09: all 27 checks
passed in 1.81 seconds. This excludes upstream/core builds and the complete
emulator demonstration. Its exact revision and hashes are recorded in
`work/handoff-reproducibility/report.json`; test-log SHA-256:
`9c5c268fb1bf2e6e10bcbdfc926928fd2daa88b45e051812d0951b805162d278`.
