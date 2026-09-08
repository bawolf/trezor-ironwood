# Local operations

The authorized checkout is `/Users/bryantwolf/workspace/trezor-ironwood` and its
remote is `https://github.com/bawolf/trezor-ironwood`. Initial machine inspection:
Apple Silicon, macOS 15.6.1, 24 GiB RAM; Homebrew Rust/Cargo 1.94; uv and Docker
are available. A project-local Lean 4.30.0 toolchain is installed under
`work/elan/`; the installed version matches upstream `lean-toolchain`.

## Recreate sources

```sh
python3 scripts/bootstrap.py
```

Existing directories are preserved. If a download was interrupted, inspect that
checkout rather than resetting it automatically. The `check.py` upstream lanes
verify actual HEAD and worktree cleanliness before and after running commands.

Rust builds use the upstream Cargo.lock and project-local `work/cargo-home` and
`work/cargo-target`, with four build jobs. The initial host baseline used Homebrew
Rust 1.94, **not** upstream's 1.88 MSRV toolchain. Do not call it an MSRV check.

## Lean

The local installation used official elan v4.2.4 for aarch64 macOS. Release archive
SHA-256: `7ad829861392c718dfebde3a83b5c8508df47be02af68894b094b0b3952616e5`.
It was installed with `--no-modify-path --default-toolchain none`; no shell profile
was changed. Toolchain: `leanprover/lean4:v4.30.0`.

```sh
export ELAN_HOME="$PWD/work/elan"
export PATH="$ELAN_HOME/bin:$PATH"
cd upstream/ironwood
lake exe cache get
cd ../..
python3 scripts/check.py lean
```

Cache downloads are dependencies, not completed project proofs. The Lean lane
has a 60-minute subprocess limit. The initial 20-minute bound was too short for
the cold dependency chain: `CompElliptic.Isogenies.VeluCertificates` alone took
690 seconds, followed by a long `Homomorphism` elaboration. Extending the execution
window leaves all proof targets and warning/axiom gates unchanged. A cold build may
exceed one bounded run; retain partial compilation and resume without weakening
the targets. The runner kills a timed-out command's subprocess group.
Source checks run with `LC_ALL=C` for deterministic ASCII parsing; the default
locale caused the endpoint census to exceed the initial timeout on this Mac.

## Firmware

The pinned manual emulator guide still lists SDL2, but current build sources
require **SDL3 and SDL3_image**. `shell.nix` pins Rust nightly 2026-03-16 and
protoc 31; the Python runtime is protobuf 6.33.5. Use the source requirements
and the tested setup in [FIRMWARE_BASELINE.md](FIRMWARE_BASELINE.md).
`t3w1` is Safe 7. Builds and tests run in `work/firmware-t3w1`, a detached
worktree at the pinned firmware commit, with project-local Rust and Python
installations. No hardware interaction is needed for this phase.

## Scheduled development

Use a heartbeat attached to the current Codex task, every two hours. It continues
one backlog item, records results in `docs/STATUS.md` and local logs, and only
notifies on useful progress, a failure or a decision requiring the user.
The machine must remain on and Codex must remain running for local scheduled work.
Do not disable sleep settings automatically.

The same task is the coordinator. Use bounded parallel agents with disjoint write
scopes and explicit acceptance criteria. Integrate their changes before freezing
inputs for checks. Adversarial Fable and separate readability reviews follow
[VERIFICATION.md](VERIFICATION.md). The checks runner has its own process lock. Agent time limits are instructions, not a
hard watchdog. Shell checks have actual subprocess timeouts. Neither mechanism
is a billing cap or an independently protected security boundary.

The initial USD 300 budget does not renew. Paid execution is disabled pending
metering/enforcement. Existing account inference consumes account usage; its USD
cost is unavailable. No API keys are needed for this initial setup.

## GitHub publication

The global macOS keychain helper stalled during the first push. A per-command
GitHub CLI helper successfully reached the repository; use:

```sh
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push
```

This does not change global credentials. Workflow publication was separately
rejected for missing OAuth `workflow` scope. The ready template is in
`ci/project-workflow.yml`; do not claim Actions is enabled until it is installed
with suitable authorization and a run is observed.
