# Concrete MCU code generation

## Assumptions

Recorded before implementation: this standalone `no_std` rlib compiles the real
`ironwood-approval` core with public synthetic account `SpendingKey::from_bytes([0;
32])`, `ChaCha20Rng::from_seed([42; 32])`, and fixed regtest policy: height
10,000,000 and maximum fee 100,000 zatoshis. These match the existing synthetic
fixtures. No transaction is executed by this experiment.

One ordinary public Rust function accepts runtime PCZT bytes, derives the test
keys, creates `Engine<ChaCha20Rng>`, calls `begin → approve → sign`, and returns
`Result<(Review, Signed)>`. Runtime input and returned core objects preserve
observable validation/signing paths. Automatic approval supplies no trusted
consent. Fixed public keys and repeated randomness are intentionally insecure;
never connect this helper to host transport or production keys. It adds no FFI,
signing abstraction, copied cryptography, allocator or runtime.

Release settings are optimization level 3, one codegen unit, panic abort and LTO
disabled. This produces inspectable native objects without a final link; it does
not reproduce final firmware optimization or integration. The pinned firmware
`upstream/trezor-firmware/core/embed/Cargo.toml:34` instead uses `opt-level = "z"`,
`lto = true` and `panic = "immediate-abort"`. The target defaults include hard-float
ABI and frame pointers; no CPU override is added.

## Reproduce offline

Run from the repository root with the existing tool installations. The private
Cargo home copies the existing registry cache; all build outputs are separate
from the embedded and host resource probes. The committed standalone lock was
seeded from the accepted root lock and pruned by offline `cargo metadata`.

```sh
export RUSTUP_HOME="$PWD/work/rustup"
export PATH="$RUSTUP_HOME/toolchains/nightly-2026-03-16-aarch64-apple-darwin/bin:$PATH"
export CARGO_HOME="$PWD/work/target-codegen/cargo-home"
export CARGO_TARGET_DIR="$PWD/work/target-codegen-target"
export CARGO_BUILD_JOBS=4 CARGO_INCREMENTAL=0 CARGO_NET_OFFLINE=true
export TMPDIR="$PWD/work/target-codegen/tmp"
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
export TARGET_CC=/opt/homebrew/opt/llvm/bin/clang
export TARGET_AR=/opt/homebrew/opt/llvm/bin/llvm-ar
export RUSTFLAGS='-Z emit-stack-sizes -C lto=off'
mkdir -p "$CARGO_HOME" "$TMPDIR"
# First run only: reuse installed dependencies without downloading.
test -d "$CARGO_HOME/registry" || cp -R work/cargo-home/registry "$CARGO_HOME/registry"

rustc --version --verbose
rustc -Z help
rustc -C help
/opt/homebrew/opt/llvm/bin/llvm-readobj --help
/opt/homebrew/opt/llvm/bin/llvm-objdump --help
python3 scripts/check_approval_dependencies.py experiments/target-codegen/Cargo.lock
cargo fmt --manifest-path experiments/target-codegen/Cargo.toml --check
cargo metadata --locked --offline --format-version 1 \
  --manifest-path experiments/target-codegen/Cargo.toml \
  --filter-platform thumbv8m.main-none-eabihf
cargo rustc --locked --offline --release --lib \
  --manifest-path experiments/target-codegen/Cargo.toml \
  --target thumbv8m.main-none-eabihf -vv -- --emit=obj,link

export CODEGEN_DEPS="$CARGO_TARGET_DIR/thumbv8m.main-none-eabihf/release/deps"
/opt/homebrew/opt/llvm/bin/llvm-readobj --stack-sizes --demangle \
  --elf-output-style=JSON "$CODEGEN_DEPS"/*.rlib \
  > work/target-codegen/stack-sizes-archives.json
/opt/homebrew/opt/llvm/bin/llvm-objdump --disassemble --reloc --demangle \
  "$CODEGEN_DEPS"/ironwood_target_codegen-*.o \
  > work/target-codegen/entry-disassembly.txt

# Installed stable Clippy is a separate host gate; nightly has no Clippy component.
PATH="/opt/homebrew/bin:$PATH" RUSTC=/opt/homebrew/bin/rustc \
  RUSTFLAGS='-C lto=off' \
  CARGO_TARGET_DIR="$PWD/work/target-codegen-target/host-clippy" \
  /opt/homebrew/bin/cargo clippy --locked --offline --release --lib \
  --manifest-path experiments/target-codegen/Cargo.toml \
  --target aarch64-apple-darwin -- -D warnings
python3 -m unittest discover -s tests -v
```

## Captured evidence: 2026-09-08 UTC

The unchanged core is accepted revision
`12c25c8eb9d9045483a2dbfebc0483a779bd0944`; repository HEAD at final capture is
`7f404ec8ed6bf7a896e21f8cbe3c74f601546cc2`. Clean librustzcash source is
`5e770a91ad0d11938dbc713e7889e4aa8009266c`. All 128 registry packages match its
lock's version, source and checksum. Target metadata shows core, `rand_chacha`
and `rand_core` features `[]`, PCZT features `["orchard"]`.

MCU code generation used `rustc 1.96.0-nightly (1e2183119 2026-03-15)` from
`nightly-2026-03-16`, Rust LLVM 22.1.0 and Homebrew C/inspection LLVM 22.1.1.
Pinned-nightly formatting, actual optimized target compilation, installed host
Clippy 0.1.94 with `-D warnings`, and 27 direct project unit tests passed.
Existing dependency warnings in the nightly build are preserved in its log.
An initial target-Clippy attempt failed before compilation because the installed
stable Clippy rejected `-Z`; no component was installed or warning gate weakened.
Host Clippy is not target Clippy.

The emitted entry object is ELF32 little-endian ARM relocatable code with Thumb
instructions and `.stack_sizes`. `synthetic_approval` has call relocations to
`ironwood_approval::validate` and the concrete `Engine<ChaCha20Rng>` signing
instantiation. The latter retains effect-digest, ChaCha20, RedDSA/Pallas arithmetic
and signature-output paths. Validation retains PCZT parsing, the Ironwood
Verifier and ciphertext recovery calls. `begin`/`approve`/`sign` are largely
inlined: absent separate method symbols do not mean absent work. These are
object-level references, not executed reachability or final linker retention.

Across 98 target rlibs, 102 extracted object members contain 3,180 stack-size
entries (aliases share entries). The table gives **individual emitted frames**;
full names, aliases and object attribution are in `frames.tsv`.

| Emitted function (shortened where generic) | Frame bytes |
| --- | ---: |
| `Pczt::parse` — largest entry in the archive inventory | 9,176 |
| `pczt::orchard::Bundle::into_parsed_inner` | 7,992 |
| `orchard::pczt::Spend::parse_inner` | 7,344 |
| `pczt::orchard::Bundle::into_parsed_inner::parse_action_inner` | 6,536 |
| `ironwood_approval::effects::sighash` | 5,168 |
| `synthetic_approval` | 4,456 |
| `Verifier::with_ironwood` for the approval core | 4,440 |
| `Signer::sign_ironwood_with` for `Engine<ChaCha20Rng>` | 3,968 |
| `ironwood_approval::validate` | 1,872 |

Exact SHA-256 identities:

| File | SHA-256 |
| --- | --- |
| `Cargo.toml` | `be0dd823cc745d8b307fbdebbe0c9d61153c9a390154544a5bc5bcfd684350ee` |
| `Cargo.lock` | `0a432da94f0c76452d6fdfdb0676270224d76228df853c4153ee0e8cfe28baa1` |
| `src/lib.rs` | `029390df6c820d1e80fe5e60b7291c2a6403f844382e953345467df7de3d3954` |
| Entry object, 39,776 bytes | `1a34515686b7087b8d3afaec74b53395f5840d446b64af571193ab9d399a80b8` |
| Entry rlib, 49,404 bytes | `317884c1befa4e564603b3035f337142886945e2e40d9cd2372d8b691c230613` |

The entry object is `work/target-codegen-target/thumbv8m.main-none-eabihf/release/deps/ironwood_target_codegen-4d0d78d82b4efdec.o`;
its sibling rlib is `libironwood_target_codegen-4d0d78d82b4efdec.rlib`.
Their file sizes include object/archive metadata and are not firmware flash sizes.

Ignored evidence in `work/target-codegen/`:

- `source-tool-identity.json`, `baseline.json`: source/lock/tool hashes and revisions.
- `commands.jsonl`, `*.stdout`, `*.stderr`: exact commands, environment, durations,
  exit codes and logs, including the failed Clippy attempt and verbose rustc build.
- `artifact-hashes.json`, `objects/`: all extracted object/rlib and sysroot hashes.
- `stack-sizes.json`, `frames.tsv`, `frame-summary.json`: LLVM metadata and census.
- `entry-object.txt`, `entry-disassembly.txt`, `dependency-disassembly.stdout`,
  `reachability.json`: target attributes, instructions, call offsets and prologues.
- `defined-symbols.txt`, `undefined-symbols.txt`, `object-symbols.stdout`,
  `sysroot-stack-sizes.json`: symbol evidence and missing-metadata boundaries.
- `inspection-commands.json`, `run.py`, `inspect.py`, `summarize.py`: capture details.

## Limits

This rlib/object is not linked firmware. Allocation, panic support, memory helpers
and firmware runtime remain unresolved integration obligations. The prebuilt
`core`/`alloc`/`compiler_builtins` archives contain no emitted stack-size entries.
Four secp256k1 C members also have none: two contain 110 defined functions in total,
two are data-only. Another 21 Rust members have no function symbols or frame
entries. Empty metadata never means a zero stack bound. Dependency archive
presence does not establish that every function is reachable from this helper.

Inlining folds work into caller frames; ordinary callees, dynamic control flow,
recursion, interrupts, runtime and missing C/sysroot evidence still require
separate analysis. No frame maximum or archive total is a whole-call-chain bound.
Nested parser/verifier frames warrant further stack investigation against the
source-defined 32 KiB application stack, with no fit or usable reserve claimed.
Final firmware LTO and the integration entry point may change the frames.
No linked flash/RAM layout, heap capacity, stack high-water, signature execution,
MCU timing, entropy, watchdog, emulator or hardware evidence is provided here.
