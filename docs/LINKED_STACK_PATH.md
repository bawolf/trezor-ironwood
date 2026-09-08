# Safe 7 linked validation stack path

The corrected Safe 7 test-preset ELF, built with optimization `z` and LTO,
contains a retained validation/action-parser chain with **40,752 bytes of nested
local frames**, conditional on reaching the selected calls. Including the
24-byte synthetic boot wrapper gives **40,776 bytes**, exceeding the
**32,768-byte application stack reservation by 8,008 bytes**. Without the
wrapper, the excess is 7,984 bytes. The reservation and build context come from
[TARGET_ALLOCATOR_LINK.md](TARGET_ALLOCATOR_LINK.md).

This is a conditional structural result. Branch predicates, preceding call
results and input feasibility are unproved. No target execution, observed
overflow, runtime high-water measurement or whole-program stack bound follows.
The image's deliberately insufficient **4 KiB allocator arena cannot run
signing**; reaching this path with the embedded fixture is not established.

The image is `work/firmware-arena-link-v2/artifacts/firmware.elf`, SHA-256
`6f4371ef69d34718d2b87adf447245e7b9199c74eaaa112b295a9739e4c1c504`.
The subtotal stops at `0x080daa2e`, immediately after the `parse_action_inner`
prologue. All values below are bytes; function names are shortened.

| Function / entry | Prologue frame calculation | Selected ordinary BL: callsite → callee |
| --- | ---: | --- |
| `ironwood_synthetic_boot` / `0x080b3cb0` | 24 | `0x080b3cf8` → `0x080b0250` |
| `synthetic_approval` / `0x080b0250` | 20 + 16 + 10,688 + 28 = 10,752 | `0x080b0480` → `0x080c1eec` |
| `validate` / `0x080c1eec` | 20 + 16 + 12,992 + 60 = 13,088 | `0x080c43c0` → `0x080da280` |
| `Bundle::into_parsed_inner` / `0x080da280` | 20 + 16 + 8,832 + 12 = 8,880 | `0x080da6be` → `0x080daa20` |
| `parse_action_inner` / `0x080daa20` | 20 + 16 + 7,968 + 28 = 8,032 | Stop after prologue |

The four BL encodings are, in table order, `f7fc faaa`, `f011 fd34`,
`f015 ff5e` and `f000 f9af`. These are linked machine-code calls. Each
continuation is callsite + 4; BL writes LR, so no extra return-address word is
added to the saved-register frames.

The selected control-flow witnesses retain every enclosing frame: their only SP
writes are the prologues. Earlier calls are assumed to return normally with
ABI-preserved SP; their temporary depths are excluded. The parser witness
includes one prepass iteration before the nonempty action loop, without proving
its predicates satisfiable. DWARF places `Engine::begin` within the synthetic
frame, and `Verifier::with_ironwood`, `into_ironwood_parsed` and
`into_parsed_with_version` within `validate`; these inline calls add no separate
frames. Completed outlined helpers preserve SP, including their tail branches;
shared restoring epilogues are off the selected nested witnesses.

The diagnostic report (`work/linked-stack-path/REPORT.md`),
machine-readable result (`work/linked-stack-path/report.json`) and
80-file manifest (`work/linked-stack-path/manifest.json`) preserve the original
evidence. Reused first-link disassembly was checked against the corrected ELF:
load headers/bytes and stack metadata match, selected function bytes were
validated, and fresh corrected-image disassembly was captured. The
parent check (`work/linked-stack-path-parent-check.json`) records 80 rehashed
files with no mismatches, plus independent ELF BL/prologue decoding and
agreement with `.stack_sizes`. The earlier no-LTO object-path result contributes
nothing to this arithmetic.

Use the clarified path summary (`work/linked-stack-path-clarification/path-evidence.json`)
with the correction record (`work/linked-stack-path-clarification/report.json`).
It removes one `bic.w` instruction from the raw branch-summary list: BIC clears
bits and falls through. The original control-flow witness and arithmetic were
correct; the frozen raw evidence remains intact. The
[review record](reviews/LINKED_STACK_PATH.md) documents the accepted Opus fallback
and clarity finding.

Earlier startup frames, interrupts/exceptions, deeper callees, indirect or
recursive paths and other inputs remain outside this subtotal. Runtime
feasibility, a complete stack bound and any remedy require separate work.
