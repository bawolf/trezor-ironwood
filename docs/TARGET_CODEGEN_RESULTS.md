# Target code generation and stack risk

The actual core now has a concrete synthetic RNG instantiation compiled to
Safe 7's Thumb target. The archive inventory contains 3,180 individual stack-frame
entries; the largest is 9,176 bytes. This establishes code generation beyond the
earlier generic `cargo check`. It does not establish linked firmware or runtime fit.

[The experiment README](../experiments/target-codegen/README.md) records commands,
toolchain, source/object identities, frame census and missing metadata. Formatting,
128-package dependency identity, target compilation and warning-fatal host Clippy
passed. Target Clippy was unavailable; its failed attempt is retained. The accepted
core at `12c25c8` remains unchanged.

## A nested parsing path

The coordinator independently inspected emitted ARM instructions, function
prologues and call relocations. The following ordinary-call chain has a frame
subtotal of **33,000 bytes**, already above the source-defined **32,768-byte**
application stack before deeper callees, runtime callers or interrupt overhead.
The limit comes from the pinned [application linker script](https://github.com/trezor/trezor-firmware/blob/7105338e3c2c1e681940e17780609881ce53126b/core/embed/sys/linker/stm32u5g/firmware.ld#L58-L60),
selected by the [Safe 7 source map](SAFE7_INTEGRATION.md).
Names in the table are shortened; full symbols and call offsets are recorded in
the evidence. Each listed edge is a `bl` with an `R_ARM_THM_CALL` relocation.

| Caller, then callee in order | Emitted frame bytes |
| --- | ---: |
| `synthetic_approval` | 4,456 |
| `ironwood_approval::validate` | 1,872 |
| `Verifier::with_ironwood` for the core | 4,440 |
| `pczt::orchard::Bundle::into_ironwood_parsed` | 16 |
| `pczt::orchard::Bundle::into_parsed_inner` | 7,992 |
| `pczt::orchard::Bundle::into_parsed_inner::parse_action_inner` | 6,536 |
| `orchard::pczt::Spend::parse` | 104 |
| `orchard::pczt::Spend::parse_inner` | 7,344 |
| `pasta_curves::curves::Ep::from_bytes` | 240 |

The experiment uses `opt-level=3`, no LTO and panic abort. Pinned firmware instead
uses size optimization (`z`), LTO and immediate abort; its actual entry point also
does not exist yet. This subtotal is a static warning for the experimental build,
not an observed hardware overflow, whole-program upper bound or measurement of
final firmware. A largest-function table alone would have missed the nesting.
The parsed point's `from_bytes` and `from_bytes_unchecked` names share one emitted
frame entry; aliases are counted once.

The next evidence should examine firmware optimization and a concrete linked
integration with explicit allocator/runtime ownership. Preserve verification and
consent invariants when investigating stack reduction; reducing action count alone
need not reduce these fixed compiler frames. Target call-chain coverage, missing
C/sysroot metadata and runtime high-water remain unresolved.

## Controlled size-optimization comparison

The same sources compiled with `CARGO_PROFILE_RELEASE_OPT_LEVEL=z`; LTO remained
off and panic remained abort. The target/toolchain, lock and dependency features
were unchanged. This tests the optimization choice, not the complete firmware
profile. Target build scripts also receive that optimization setting.

| Individual emitted frame | opt3 bytes | optz bytes |
| --- | ---: | ---: |
| Synthetic helper | 4,456 | 3,312 |
| `Pczt::parse` (opt3 archive maximum) | 9,176 | 1,912 |
| PCZT bundle conversion | 7,992 | 8,032 |
| Orchard spend parser | 7,344 | 4,136 |
| Effect digest | 5,168 | 4,536 |
| Concrete low-level signer | 3,968 | 1,272 |

Four of the original path's eight direct edges changed. The root now calls a
separate `Engine::begin` (2,272 bytes); signing also has a separate `Engine::sign`
(2,000 bytes). Parser wrappers use outlined helpers and tail branches, and `Spend::parse_inner`
loses its direct `Ep::from_bytes` call. These are changes in emitted code;
the Rust sources are identical. Therefore
adding the smaller entries from the old path would give an invalid new subtotal.
The diagnostic stops at these structural changes and claims no new stack bound.

The optz archive census has 10,180 entries. Its largest frame is an unrelated
serialization implementation whose reachability is unestablished. The synthetic
entry object's text payload shrank from 17,168 to 11,594 bytes, but its complete
file grew because of object/relocation metadata and separately emitted functions.
Neither is a linked flash measurement. These results support examining the actual
firmware build before changing accepted verification code for size or stack use.

Commands, source/feature comparisons and raw artifacts are retained in
`work/target-codegen-size/RESULTS.md`, `comparison.json`, `call-changes.json` and
`review-manifest.json`. An initial inspection assumption about a direct call failed
because an outlined helper intervened; that failure and the corrected trace are
retained. Compilation passed; no source or dependency changes were made.

## Provenance and review

Frozen experiment inventory: `work/target-codegen/review-manifest.json`, SHA-256
`d9c9558a49fc0a08429d395bc9467a437e562db98507e6767fb52f9f08c6178b`.
The coordinator rechecked every inventoried source, evidence file, archive and
object against its recorded hash before review.

Independent path trace: `work/target-stack-chain/path-evidence.json`, with each
object/disassembly hash, full symbol, prologue and call offset. It uses the same
frozen target objects as the experiment. No ARM transaction was executed.

Fable adversarial review and an independent readability review found no blocking
correctness or material clarity issue. See [review details](reviews/TARGET_CODEGEN.md). The code is a small compile-only synthetic helper, with no
production FFI, allocator, transport or trusted-consent implementation.

Path evidence SHA-256: `7798ea5b84583657a7b22ad2b5eb0091b27f4cfd26297c38c7b8fb867c0153d4`.
