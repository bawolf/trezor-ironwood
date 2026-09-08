# Compile-only Safe 7 allocator derivative

`firmware.patch` is the complete isolated experiment, including its resolved lock
and public synthetic PCZT. Apply only to the firmware pin
`7105338e3c2c1e681940e17780609881ce53126b` in a separate worktree at
`work/firmware-arena-link` beneath this repository; the approval path dependency
assumes that location. The original pinned checkout remains clean.

The patch reserves a 4 KiB Rust arena and inserts an automatic synthetic approval
hook into firmware startup. It deliberately cannot execute the signing lifecycle.
It exists to retain real code for linking, layout and disassembly inspection.
**Do not execute or flash this diagnostic image.** It supplies no transport,
production key handling or trusted user-consent flow.

Use the pinned toolchain and environment documented in
[the target baseline](../../docs/TARGET_FIRMWARE_BASELINE.md), then run from the
worktree's `core/embed` directory:

```sh
cargo run --locked --profile xtask -p xtask -- build firmware --model t3w1 --preset test
```

The baseline notes apply, including upstream xtask's unlocked inner builds and
source-pinned embedded monitor. No linker region, assertion, test-preset component
gate or warning policy is relaxed. The derivative adds `alloc` to the firmware's
existing core sysroot build and unifies its utility features with the approval
core's dependencies. It does not change the accepted approval implementation.

[Results and review boundaries](../../docs/TARGET_ALLOCATOR_LINK.md) include exact
memory regions and artifact hashes. The final clarity correction produces a
byte-identical firmware binary; differences in the ELF are debug/symbol metadata.
Final Fable5.1 review found no blocking issue in this compile-only scope. This patch is not an upstream PR or
an accepted runtime firmware design. Trezor firmware's upstream license and
third-party dependency licenses continue to apply to this derivative.
