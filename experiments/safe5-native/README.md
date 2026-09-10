# Safe 5 native signing experiment

The complete synthetic native slice links on T3T1/U585 with 27,136 bytes of flash
headroom. It has not run on a device. The reviewed memory layout reserves a 48 KiB
stack and two GC regions, but the complete stack bound and runtime memory use
remain unmeasured. Generator computation is slower than a precomputed table.
This is a source package for review and continued
experiments, not installable or production firmware.

## Source layout

- `firmware.patch` applies to Trezor firmware revision
  `7105338e3c2c1e681940e17780609881ce53126b`. It contains the complete native
  experiment, model-specific guards, AUX2 arena placement, small-processor
  dependency features, the upstream secp256k1 2 KiB comb configuration and the
  exact Cargo lockfile. A native-only linker derivative gives the stack 48 KiB
  and assigns the unused AUX1 tail to the existing static split-GC API.
- `bridge/` contains the actual synthetic Rust bridge and its two test fixtures.
  It uses fixed test keys and deterministic randomness. The native module's sign
  entry internally approves the matching token: its caller is trust-bearing.
  This image has no frozen Python, boot or wire caller for that module.
- `sinsemilla-compute.patch` applies to registry Sinsemilla 0.1.0. It substitutes
  the exact upstream S-generator routine for lookup, retaining padding, domains,
  incomplete addition, commitment blinding and the original public table API.
- `stack-inline.patch` contains the two previously reviewed inlining attributes
  applied to the approval core and pinned PCZT implementation. Function bodies
  are unchanged. The larger stack still needs a complete live-frame bound and runtime checks.
- `SOURCE_MANIFEST.json` identifies the exact firmware sources and measured ELF.

Stage a separate working directory with `firmware/` at the firmware revision,
`build-inputs/rust/` copied from `bridge/`, `build-inputs/crates/approval/` copied
from this repository's approval crate, and `build-inputs/upstream/librustzcash/`
at revision `5e770a91ad0d11938dbc713e7889e4aa8009266c`. Apply `firmware.patch`
inside the firmware clone, then `stack-inline.patch` from that working directory.
Apply `sinsemilla-compute.patch` to a separate verified copy of Sinsemilla 0.1.0.
Select that copy with Cargo's `patch.crates-io.sinsemilla.path` configuration.
Do not modify registry caches or the baseline checkouts.

The native feature is `ironwood_target_native_compile_only`. Use the unchanged
Safe 5 test kernel paired with this firmware pin, release optimization, the pinned
nightly-2026-03-16 toolchain and Arm GNU 13.3.Rel1. The measured configuration
retains `universal_fw`, model/board/security settings and synthetic test settings;
it requires `pyopt` (single-heap debug memory diagnostics are unsupported),
disables Rust `debug` and omits `debuglink`, `ui_debug` and
`ui_debug_overlay`. It is not the unchanged upstream test preset. Rebuild both
`core` and `alloc`, and use the frozen lock. No firmware postprocessing, signing
or flashing was performed. Detailed command and artifact evidence is summarized
in `docs/SAFE5_NATIVE.md` in this repository.

## Remaining delivery work

This export removes reliance on ignored native implementation source and bridge
fixtures. Full clean-checkout firmware reproduction, portable source preparation,
the complete host/runtime acceptance harness, Safe 5 trusted screens/legacy-wire
integration and device tests remain. It is not a maintainer-ready submission.
Any future production port must remove synthetic keys/RNG and test auto-approval,
use trusted device key/entropy/UI APIs, and satisfy the complete threat model.

The Trezor derivative retains upstream GPL licensing and notices. The original
bridge is MIT licensed under the repository LICENSE. Sinsemilla retains its
MIT/Apache-2.0 dual license; its patch does not relicense the original library.
Do not treat passing AI reviews or host tests as a cryptographic/device audit.
