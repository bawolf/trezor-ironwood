# Safe 7 compile-only approval-core probe

This standalone `no_std` workspace imports the actual `ironwood-approval` crate
with `default-features = false`. It type-checks the complete library and its
upstream dependencies for `thumbv8m.main-none-eabihf`, using the firmware
baseline's `nightly-2026-03-16` toolchain. Trezor's pinned `T3W1/model.toml`
selects STM32U5G; its xtask configuration maps that processor to this Rust target.

`compile_probe<R: RngCore + CryptoRng>` accepts caller-supplied synthetic PCZT
bytes, trusted test policy, matching synthetic viewing/signing keys and an RNG.
It calls `Engine::with_rng`, `begin`, `approve` and `sign`, returning the core's
review and signed result. The core performs its actual profile 1 validation,
accounting, ciphertext recovery and digest/signing checks. The probe does not
copy the scanner or implement a second validator, digest or signer.

**This harness automatically approves its synthetic review.** That exercises the
API sequence only; it provides no trusted user consent. Never expose this helper
to host transport or production key storage. The experiment contains no RNG
implementation or seed. A future device integration must separately supply and
validate its trusted RNG, allocator, key handling and review/approval UI.

The independent workspace prevents host adapter/test features from being unified
into this build. The probe's direct dependencies all disable default features;
the core's optional OS randomness feature is disabled. Registry dependency
versions, sources and checksums must match the pinned librustzcash `Cargo.lock`.

## Reproduce directly

Run from the repository root, using the existing project-local toolchain and cache:

```sh
export CARGO_HOME="$PWD/work/cargo-home"
export RUSTUP_HOME="$PWD/work/rustup"
export CARGO_TARGET_DIR="$PWD/work/embedded-target"
export CARGO_BUILD_JOBS=4
export LC_ALL=C
export TARGET_CC=/opt/homebrew/opt/llvm/bin/clang
export TARGET_AR=/opt/homebrew/opt/llvm/bin/llvm-ar
export PATH="$RUSTUP_HOME/toolchains/nightly-2026-03-16-aarch64-apple-darwin/bin:$PATH"
rustc --version --verbose
python3 scripts/check_approval_dependencies.py experiments/embedded-probe/Cargo.lock
cargo fmt --manifest-path experiments/embedded-probe/Cargo.toml --check
cargo check --locked --offline --manifest-path experiments/embedded-probe/Cargo.toml --target thumbv8m.main-none-eabihf
```

Expected compiler: `rustc 1.96.0-nightly (1e2183119 2026-03-15)`.
The official prebuilt target component is installed in that local toolchain.
The target C compiler/archive tool are the existing Homebrew LLVM 22.1.1. The
pinned `secp256k1-sys` build script supplies its own embedded fallback headers;
no upstream source or dependency feature is changed to compile the C dependency.

The coordinating runner is `python3 scripts/check.py embedded-probe`. Run that
lane only after core integration and the input inventory are stable. Its environment
sets the target C tools above and records their versions. Its input inventory includes
the approval manifest and every core source file, including `effects.rs`. The final
runner passed in `work/runs/20260908T064723Z-embedded-probe-313ddb21/`: dependency
identity, formatting and target checking all passed with unchanged source hashes.
The earlier direct-check evidence is retained below.

## Evidence and limits

Direct checks on 2026-09-08 UTC, using the environment above:

| Check | Result |
| --- | --- |
| `rustc --version --verbose` | Exit 0; exact firmware-pinned nightly shown above |
| `cargo fmt --manifest-path experiments/embedded-probe/Cargo.toml --check` | Exit 0 |
| `python3 scripts/check_approval_dependencies.py experiments/embedded-probe/Cargo.lock` | Exit 0; all 126 registry packages match upstream versions/checksums |
| `cargo check --locked --offline --manifest-path experiments/embedded-probe/Cargo.toml --target thumbv8m.main-none-eabihf` | Exit 0 in 175.53 seconds; checked both `ironwood-approval` and `ironwood-embedded-probe` |

The core manifest/all core sources and the probe manifest/lock/source hashes were
unchanged across the passing target check. Target-filtered Cargo metadata showed
`ironwood-approval` features `[]`, PCZT features `["orchard"]` and `rand_core`
features `[]`; neither the core's OS convenience feature nor `rand_core/getrandom`
was enabled. The lockfile was resolved offline from the pinned upstream lock.

The first expanded core check exited 101 in 82.45 seconds because
`secp256k1-sys` could not find `arm-none-eabi-gcc`; the old runner environment
lacked a target C compiler. The passing retry used the installed LLVM tools above.
The earlier scanner/verifier-only result is separate, narrower evidence.

An earlier `-Z build-std=core,alloc` attempt failed offline because the Rust
sysroot resolver needed an uncached `dlmalloc` package; no upstream incompatibility
was implied. The official target component avoids a custom sysroot build.

`cargo check` type-checks this generic harness and the actual core for the target;
it does not monomorphize a concrete device RNG, execute a synthetic transaction,
verify runtime signatures or link a firmware image. It does not measure runtime,
flash, stack, heap, allocation failure, watchdog behavior, entropy or side channels.
Host conformance results are separate evidence. No device support or firmware
readiness is claimed. Safe 7 firmware/UI integration and measured resources remain
future work, using only synthetic inputs until separately authorized.
