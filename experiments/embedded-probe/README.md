# Safe 7 compile-only probe

`python3 scripts/check.py embedded-probe`

This isolated workspace compiles the exact profile 1 wire scanner and the pinned
PCZT full-FVK parsing/value commitment/nullifier/randomized-key/note commitment
APIs for `thumbv8m.main-none-eabihf`, using the firmware baseline's
`nightly-2026-03-16` toolchain. Trezor's pinned `T3W1/model.toml` selects STM32U5G;
its xtask configuration maps that processor to this Rust target.

The crate is `no_std`, enables only PCZT's `orchard` feature and disables default
features. The independent workspace prevents the host adapter's signer/test
features from being unified into the probe. Dependency versions and checksums
remain those in the pinned librustzcash Cargo.lock. It shares the scanner source
by path so this experiment cannot silently test a different wire parser.

**This is not an approval validator or a signer.** Its public compile entry point
exists solely to exercise the relevant APIs on the MCU target. It omits policy,
accounting, encryption and consent. Never connect it to host transport or key
storage. It does not link a firmware image or measure runtime, flash, stack, heap,
allocator failure, watchdog behavior, entropy or side channels.

The initial `cargo check` passed after installing the official target component
in the existing project-local Rust toolchain. An earlier `-Z build-std=core,alloc`
attempt failed offline because the Rust sysroot resolver needed an uncached
`dlmalloc` package; no upstream incompatibility was implied. Using the official
prebuilt target libraries avoided a custom sysroot build.

Next: isolate the complete validator and signature-digest path behind device RNG
and allocation interfaces; keep immutable consent and all conformance cases.
Only then integrate into the existing Safe 7 firmware and measure actual resources.
The low-level preverified signer must remain inaccessible without full validation
over identical PCZT bytes. Its existence does not substitute for verification.
