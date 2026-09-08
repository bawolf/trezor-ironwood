# Safe 7 emulator baseline

Status: build passed with GCC 15; all nine existing Zcash emulator tests passed.
Source: `trezor/trezor-firmware` at
`7105338e3c2c1e681940e17780609881ce53126b`, model `t3w1`.
Worktree: `work/firmware-t3w1`, detached; baseline under `upstream/` unchanged.

## Installed environment

| Tool | Actual selection |
| --- | --- |
| Host | Apple Silicon, macOS 15.6.1 |
| Rust | nightly-2026-03-16, rustc 1.96.0-nightly (1e2183119 2026-03-15), minimal profile plus rust-src and rustfmt |
| Python | 3.12.8, isolated `.venv` |
| uv | 0.12.10, project-local binary |
| Python packages | Upstream `uv.lock`, installed using `uv sync --locked` |
| Protobuf | protoc 31.1; Python protobuf 6.33.5 from upstream lockfile |
| C compiler | Homebrew GCC 15.2.0 (`/opt/homebrew/bin/gcc-15`) |
| libclang for bindgen | Homebrew LLVM 22.1.1 |
| SDL | SDL3 3.4.12, SDL3_image 3.4.4 (Homebrew bottle 3.4.4_1) |
| Build jobs | 2 for Cargo |

The [manual guide](https://github.com/trezor/trezor-firmware/blob/7105338e3c2c1e681940e17780609881ce53126b/docs/core/build/emulator.md)
still lists SDL2. The actual
[BSP build script](https://github.com/trezor/trezor-firmware/blob/7105338e3c2c1e681940e17780609881ce53126b/core/embed/sys/bsp/build.rs#L157)
queries `sdl3` and `sdl3-image`; `shell.nix` also lists those packages and pins
the Rust nightly. The Homebrew `protobuf@32` path on this machine is an alias
for 34.0, so checking the executable version was necessary. Protoc 31.1 is
installed locally to stay compatible with the locked Python runtime.

SDL3 installation used `HOMEBREW_NO_AUTO_UPDATE=1 brew install sdl3 sdl3_image`.
Homebrew also updated codec dependencies and ran its automatic cache cleanup.
For future installs add `HOMEBREW_NO_INSTALL_CLEANUP=1` to avoid unrelated
cleanup. Rust installation used `--no-modify-path`; shell profiles and the global
Rust toolchain were not changed.

## Release artifacts

Official downloads are stored in `work/toolchain-downloads`:

| Artifact | SHA-256 | Verification |
| --- | --- | --- |
| rustup-init 1.28.2, aarch64 macOS | `20ef5516c31b1ac2290084199ba77dbbcaa1406c45c1d978ca68558ef5964ef5` | Matched official release checksum |
| uv 0.12.10, aarch64 macOS archive | `51c6170e8e3a01cef9f33b94f582b7b81ac65046f55d40afb35f9cff5a68c179` | Matched digest in official GitHub release metadata |
| protoc 31.1, macOS universal archive | `99ea004549c139f46da5638187a85bbe422d78939be0fa01af1aa8ab672e395f` | Local archive hash; release API supplied no digest |

Sources: [rustup](https://static.rust-lang.org/rustup/archive/1.28.2/aarch64-apple-darwin/rustup-init),
[uv](https://github.com/astral-sh/uv/releases/tag/0.12.10),
[protobuf](https://github.com/protocolbuffers/protobuf/releases/tag/v31.1).

## Repeatable checks

After setup, run from the project root:

```sh
python3 scripts/check_firmware.py build
python3 scripts/check_firmware.py zcash
```

The runner syncs locked Python dependencies, checks the source and submodule pins,
checks the Rust nightly, verifies the emulator reports `T3W1`, hashes the binary
and logs, and checks source/binary continuity afterward. The Zcash lane explicitly
uses pytest-controlled emulators and requires nine actual passing JUnit testcases,
with no skips, errors or failures. The firmware lock is separate from the Lean/PCZT
lock; use one coordinator and avoid concurrent firmware commands.

## Reproduction

From the project root, create the detached worktree once and initialize its
submodules at the commits recorded by firmware:

```sh
git -C upstream/trezor-firmware worktree add --detach ../../work/firmware-t3w1 7105338e3c2c1e681940e17780609881ce53126b
git -C work/firmware-t3w1 submodule update --init --recursive --depth=1
```

After installing the listed local toolchains, use this environment:

```sh
export TREZOR_IRONWOOD_ROOT="$PWD"
export TREZOR_FIRMWARE_WORK="$TREZOR_IRONWOOD_ROOT/work/firmware-t3w1"
export CARGO_HOME="$TREZOR_IRONWOOD_ROOT/work/firmware-cargo"
export RUSTUP_HOME="$TREZOR_IRONWOOD_ROOT/work/rustup"
export UV_CACHE_DIR="$TREZOR_IRONWOOD_ROOT/work/uv-cache"
export LIBCLANG_PATH=/opt/homebrew/opt/llvm/lib
export CC=/opt/homebrew/bin/gcc-15
export CARGO_BUILD_JOBS=2
export LC_ALL=C
export PATH="$TREZOR_FIRMWARE_WORK/.venv/bin:$CARGO_HOME/bin:$TREZOR_IRONWOOD_ROOT/work/toolchain-downloads/protoc-31.1/bin:/opt/homebrew/opt/llvm/bin:$PATH"
unset CARGO_TARGET_DIR RUSTUP_TOOLCHAIN
cd "$TREZOR_FIRMWARE_WORK"
"$TREZOR_IRONWOOD_ROOT/work/toolchain-downloads/uv-0.12.10/uv-aarch64-apple-darwin/uv" sync --locked --python /usr/local/bin/python3
cd core/embed
cargo run --locked --profile xtask -p xtask -- build firmware --model t3w1 --emulator --preset test
```

The outer Cargo invocation is locked. Upstream xtask launches an inner Cargo
build without forwarding `--locked`; check the worktree after the run rather
than claiming every nested invocation was locked. The run uses the existing
bounded subprocess-group runner, with logs and hashes recorded under `work/runs`.

The `test` preset enables emulator debug support. The emulator output is not a
production firmware artifact. Existing device tests use synthetic/test fixtures
and the software Tropic model. They must use `--control-emulators --model core`
so pytest starts the built emulator instead of searching for a physical device.

## Setup failures retained

The Mac's older uv rejected the relative `exclude-newer = "30 days"` setting and
then refused the locked dependency resolution. Installing uv 0.12.10 resolved
this; no upstream lockfile or dependency constraint was edited. The successful
sync report is `work/runs/firmware-uv-sync.json`.

The first full build failed under Apple Clang 17 with
`-Werror,-Wgnu-folding-constant` in upstream `hash_to_curve.c`. A minimal
reproducer fails under Apple Clang 17 but passes under Homebrew Clang 22.1.1
with the same `-std=gnu99 -Wall -Wextra -Werror` flags. The retry explicitly
selects Homebrew Clang; no warning suppression or upstream source edit was used.
The initial run also reported missing rustfmt; that component was added to the
same pinned nightly. Failure evidence:
`work/runs/20260908T033656Z-firmware-build/report.json`.

The Clang 22 retry then failed on an implicit `_Float16`-to-`float` promotion in
MicroPython (`-Werror,-Wdouble-promotion`). Both Apple Clang 17 and Clang 22 reject
the minimal reproducer; installed GCC 15 accepts both reproducer cases with the
same warning/error flags. The next retry uses GCC 15 for C compilation while
retaining LLVM libclang for bindgen. No C source or warning setting is modified.
Clang retry evidence: `work/runs/20260908T035310Z-firmware-build-46b057bc/report.json`.

## Successful build

The GCC build passed in 418.73 seconds after the Clang attempts populated the
Rust build cache. This is not a cold-build timing claim. Binary properties:
`internal_model=T3W1`, `version=2.12.5.0`, Tropic and BLE enabled.
Emulator SHA-256:
`631f757850a2ff1ab64b56e35dab054800a0ff59a8a036667e6dc922eba62fda`.
Source and submodule checks passed before and after the build.
Evidence: `work/runs/20260908T035819Z-firmware-build-f11b9047/report.json`.

## Successful Zcash test run

All nine cases in `tests/device_tests/zcash/test_sign_tx.py` passed, with no skips,
errors or failures. The pytest command took 55.39 seconds including setup and
teardown. It exercised existing transparent Zcash/v5 flows: one-to-two outputs,
multisig spending/sending, v4/v5 input handling, missing version-group rejection,
replacement-transaction refusal, external presigned inputs and Unified Address
handling. It does not implement or test an Ironwood shielded signer.

The source, submodules and binary hash matched the build before and after testing.
Evidence: `work/runs/20260908T040947Z-firmware-zcash-f4fcf912/report.json`.
JUnit SHA-256: `a759ab2f839bb04ddcb13aab37647d25968d0a1b9daba13c9749996fb3d3284d`.

The first attempt failed because the software Tropic model missed its 10-second
startup deadline. All nine cases were setup errors; no signing test ran. The
retry passed with the unchanged test suite and startup deadline. Per-run logs
are now retained through `TREZOR_PYTEST_LOGS_DIR`. Warm-start effects may explain
the difference; the exact initial startup delay was not captured, so this is not
a claimed root-cause fix. Failure evidence:
`work/runs/20260908T040630Z-firmware-zcash-63577907/report.json`.
