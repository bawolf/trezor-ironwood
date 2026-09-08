# Project status

Last updated: 2026-09-08 UTC (2026-09-07 evening in California).

## Implemented

- Initial project structure, MIT-licensed orchestration, upstream source lockfile,
  contribution map, draft threat model and bounded backlog.
- Five pinned local upstream checkouts; Suite recorded for later inspection.
- Local verification runner with OS lock, subprocess-group timeouts, exact source
  revision/cleanliness checks, log hashes and nonempty-test assertions.
- Project-local Lean 4.30.0 installed. Rust baseline uses Homebrew 1.94, not the
  upstream MSRV toolchain.
- Initial USD 300 total budget recorded. No extra paid service enabled; existing
  Codex account usage cannot be reported in dollars from the available telemetry.

## Validation completed

| Check | Result |
| --- | --- |
| Project failure-path tests | 10 passed |
| Upstream PCZT library tests | 66 passed, none failed/ignored/filtered |
| Upstream Ironwood integration tests | 4 passed |
| Upstream firmware wire-compatibility tests (Keystone fixture) | 4 passed |
| Ironwood source/census/fixture scripts | All six passed; build coverage contains 480 modules, endpoint census contains 200 declarations |
| Lean 4.30.0 and dependency cache | Installed / downloaded successfully |
| Full Lean project proof build | Not yet run; first continuation task |

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

- Full Lean project proof build and remaining CI-specific evidence.
- Existing Trezor PR reuse review and a current Safe 7 emulator build.
- PCZT approval contract and an actual shielded signer integration.
- Independent review of the threat model, cryptography and eventual firmware.
- Maintainer acknowledgment before any librustzcash PR; no outreach has been sent.

This bootstrap does not complete the overall shielded-support project. There is no
new firmware, live-funds testing or proven Trezor integration yet.
