# Project status

Last updated: 2026-09-08 UTC (2026-09-07 evening in California).

## Implemented

- Initial project structure, MIT-licensed orchestration, upstream source lockfile,
  contribution map, draft threat model and bounded backlog.
- Five pinned local upstream checkouts; Suite recorded for later inspection.
- Local verification runner with OS lock, subprocess-group timeouts, exact source
  revision/cleanliness checks, log hashes and nonempty-test assertions.
- Project-local Lean 4.30.0 installed. PCZT Rust baseline uses Homebrew 1.94,
  not the upstream MSRV toolchain. Firmware uses its separate source-pinned
  nightly-2026-03-16 installation.
- Completed [Trezor PR reuse assessment](TREZOR_REUSE.md), with 110 file entries,
  immutable revisions/hashes and explicit review/licensing limits.
- Added the Safe 7 emulator build/test runner and [toolchain guide](FIRMWARE_BASELINE.md).
- Started the approval contract with a [source-grounded PCZT validation map](PCZT_VALIDATION_MAP.md);
  full field/bounds/display/accounting policy remains to be specified.
- Initial USD 300 total budget recorded. No extra paid service enabled; existing
  Codex account usage cannot be reported in dollars from the available telemetry.

## Validation completed

| Check | Result |
| --- | --- |
| Project failure-path tests | 13 passed, including wrong-model and false-success emulator evidence guards |
| Upstream PCZT library tests | 66 passed, none failed/ignored/filtered |
| Upstream Ironwood integration tests | 4 passed |
| Upstream firmware wire-compatibility tests (Keystone fixture) | 4 passed |
| Ironwood source/census/fixture scripts | All six passed; build coverage contains 480 modules, endpoint census contains 200 declarations |
| Lean 4.30.0 and dependency cache | Installed / downloaded successfully |
| Full Lean project proof build | Incomplete: two 20-minute runs timed out; unchanged full-target resume with a 60-minute limit in progress |
| Current Safe 7 emulator | Build passed under GCC 15; binary reports T3W1, version 2.12.5.0; nine existing Zcash tests now running |

Evidence reports (local, ignored):
- `work/runs/20260908T025735Z-project-9aed3ee4/report.json`
- `work/runs/20260908T030029Z-pczt-7d60e8c5/report.json`
- `work/runs/20260908T025917Z-ironwood-source-6bd99c27/report.json`

The first source-check run hit a 90-second timeout in endpoint census under the
machine's default locale. The unchanged script passed with `LC_ALL=C` in about
30 seconds; the final source lane uses this explicit locale and retains all six
scripts. The initial PCZT test-count expectation (67, taken from PR prose) did
not match the actual pinned library inventory: Cargo ran 66 tests, with no failed,
ignored or filtered tests. The harness correctly rejected that mismatch. The
inventory expectation was corrected to 66 and the complete lane then passed.
These first-run failures remain in local logs; no upstream test was removed.

## Continuing work

An active Codex heartbeat, `trezor-ironwood-development`, is attached to the
coordinating task and runs every two hours. It continues one bounded backlog item,
checks available account capacity, and notifies only on meaningful progress,
failures or required decisions. Keep the machine on and Codex running.

## GitHub CI

The workflow is prepared in `ci/project-workflow.yml`. The current GitHub OAuth
credential cannot publish `.github/workflows/` because it lacks the `workflow`
scope. The initial push was rejected. The template is kept outside that special
path so the project can be published without expanding account permissions.
Local verification and the Codex heartbeat work independently of GitHub Actions.
No GitHub CI run has occurred.

## Remaining

- Complete the full Lean proof build and remaining CI-specific evidence.
- Finish the existing Zcash tests against the current Safe 7 emulator.
- PCZT approval contract and an actual shielded signer integration.
- Independent review of the threat model, cryptography and eventual firmware.
- Maintainer acknowledgment before any librustzcash PR; no outreach has been sent.

This bootstrap does not complete the overall shielded-support project. There is no
new firmware, live-funds testing or proven Trezor integration yet.

## Current continuation evidence

Development branch: `codex/verification-and-reuse`.
The reuse assessment is published in commit `6774cb5`.

- Cold Lean run: `work/runs/20260908T032153Z-lean-ab668874/report.json`
  (timeout, exit 124; partial compilation retained; no target removed).
- Second Lean run: `work/runs/20260908T034209Z-lean-57073a3b/report.json`
  (timeout, exit 124; serial dependency timing diagnosed).
- 60-minute Lean resume: `work/runs/20260908T040233Z-lean-7e86de00/`.
- Initial firmware build: `work/runs/20260908T033656Z-firmware-build/report.json`
  (compiler diagnostic, exit 1; source remained clean).
- Clang 22 retry: `work/runs/20260908T035310Z-firmware-build-46b057bc/report.json`
  (failed on MicroPython half-precision promotion).
- GCC 15 build: `work/runs/20260908T035819Z-firmware-build-f11b9047/report.json`
  (passed; source and submodules remained clean).
- Python dependency sync: `work/runs/firmware-uv-sync.json` (passed).
- Test collection: `work/runs/firmware-zcash-collection.json` (nine collected;
  collection is not execution).

Both C failures reproduce in small examples. GCC 15 accepts both under the
existing warning/error flags. The passing build changes the host compiler
selection, not upstream source or warning gates. No additional paid service has
been enabled, and no physical device has been accessed.
