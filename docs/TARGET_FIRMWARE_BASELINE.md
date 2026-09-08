# Safe 7 target firmware baseline

The unchanged T3W1 hardware test preset built successfully on 2026-09-08 using
firmware revision `7105338e3c2c1e681940e17780609881ce53126b`. This establishes
linked baseline memory regions for a later paired integration. No firmware ran on
a device; no shielded allocator or approval core is present in this image.

The development secmon, kernel and firmware all linked. The enclosing firmware
image includes its kernel (which embeds the source-pinned secmon), BLE image and
bootloader. Do not add
those components again when comparing flash usage.

| Linked baseline | Bytes / addresses |
| --- | --- |
| Application AUX1 RAM | 819,200 |
| Native application stack | 32,768; `0x20198000..0x201a0000` |
| Data / BSS / buffer sections | 512 / 15,252 / 72,676 |
| GC region | 697,992; `0x201b5978..0x20260000` |
| AUX1 outside the GC region | 121,208 |
| Complete flash image extent | 2,369,536 |
| Flash slot | 3,416,064 |
| Unoccupied flash tail | 1,046,528 |

The image extent includes the 2,048-byte header, 2,366,976-byte `.flash` section
and 512-byte data load image.

The GC region includes future metadata, Python objects, transport/UI activity and
fragmentation. It is neither currently free runtime memory nor a Rust allocation
budget. The linker requires a minimum GC region of 37 KiB (37,888 bytes); that
assertion is unchanged. Stack symbols describe the reservation, not call depth.

## Reproduction and identity

The detached worktree is `work/firmware-target-baseline`; the original upstream
checkout and the existing emulator worktree stayed clean. All 24,440 tracked source
hashes, including locks and submodules, match the pre-build snapshot.
Run from that worktree's `core/embed`, with the environment captured in
`work/target-firmware/build-environment.json`:

```sh
cargo run --locked --profile xtask -p xtask -- build firmware --model t3w1 --preset test
```

The build took 210.055 seconds. It uses the source-pinned nightly-2026-03-16,
`thumbv8m.main-none-eabihf`, release optz/LTO/immediate-abort, two build jobs,
Arm GNU 13.3.Rel1, host GCC 15 and libclang 22.1.1. Arm's archive and published
SHA-256 were downloaded from its official site and compared before extraction;
Only the SHA-256 comparison was performed, not a PGP signature check.
Identities and commands are saved in `arm-checksum-verification.json` and
`commands` in the report. Python 3.12.8, pinned uv and protoc match the documented
[emulator setup](FIRMWARE_BASELINE.md).

The outer Cargo and uv commands use locked resolution. Upstream xtask does not
forward `--locked` to its inner Cargo builds; all resulting lock/source hashes
were checked unchanged. No source, region, required component or warning setting
was changed to obtain the build.

The hardware test fragment in `core/embed/xtask/presets.toml:31–35` sets
`disable-optiga` and `disable-tropic`; `xtask/src/features.rs:85–89` removes those
board features. The separate `optiga_testing` feature is still enabled. The preset
also enables development
keys, insecure test storage, debug link and unoptimized Python. A paired allocator
image must use this same preset. This is not a production build or an attestation
validation. Build-time development signature checks passed.

Although xtask builds a development secmon, the kernel embeds the source-pinned
186,368-byte secmon already pinned in the source tree, not that new secmon binary.
The saved ELF/map inspection checks those exact embedded bytes, the kernel in
firmware, and both ancillary images. This distinction matters for paired builds.

## Evidence and limits

Local evidence is indexed by `work/target-firmware/report.json`, SHA-256
`f9b4e6d31640a1eadfe58e2d04c40382710327bd60b5120b66a1913dbf5ec6c9`.
The worker cross-checked 154 artifact, symbol, section and embedding facts. The
coordinator separately rehashed 94 artifacts/logs and parsed the final ARM ELF's
heap and stack symbols; see `parent-verification.json`.

- Firmware ELF SHA-256: `b839c482ba4da527489ce47cb9f8e8062f8ae915dfc81f6f2e59e063319f8e22`.
- Firmware map SHA-256: `2592356a98047c499c977eee0338596f70aeae66d6467dab19b83d32f12a8ee5`.
- Firmware binary SHA-256: `159df7000441104aae1d7d5c6d07e592060294ce3e52948a01aa3aa193f36700`.
- Build log SHA-256: `9406b4cb59f66884b709e49ea91aab778e9de357ed69c08918b6774abea3a14d`.

An initial evidence parser rejected GNU nm's `?` symbol class. The corrected parser
kept exact address comparisons; both reports and scripts are retained. The firmware
build itself had no failed attempt. There was no hardware access or flashing.

Next evidence is a complete paired allocator image with reachable synthetic
approval code, emulator ownership/GC pressure tests and separate target whole-stack
analysis. MCU runtime stack high-water remains unmeasured. Host resource peaks
and earlier standalone Thumb frames do not establish runtime fit.
