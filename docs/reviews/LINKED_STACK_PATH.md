# Linked stack path: review record

The accepted result is the [conditional structural stack subtotal](../LINKED_STACK_PATH.md)
for the corrected Safe 7 optimization-`z`/LTO ELF, SHA-256
`6f4371ef69d34718d2b87adf447245e7b9199c74eaaa112b295a9739e4c1c504`.
The four nested validation/parser frames total 40,752 bytes; the 24-byte boot
wrapper brings this to 40,776, or 8,008 above the 32,768-byte reservation.
Acceptance covers this bounded static claim only.

The adversarial review requested **`fable[1m]`**, but the reported main review
model was **`claude-opus-5`**. The user explicitly accepted this correctly labeled
Opus fallback for the requested Fable adversarial review. This is an accepted
substitute review, not a Fable run. The run record (`work/reviews/linked-stack-path-fable/run.json`)
records tools disabled (`--tools ""`), return code 0 and no timeout. The
result (`work/reviews/linked-stack-path-fable/result.json`) reports success
and a total cost of **USD 0.77544575**; its usage also includes a separate
`claude-haiku-4-5-20251001` entry. This is reported usage cost, not an invoice.

The review hand-checked supplied evidence and found **no blocking findings for
the limited conditional structural claim**. It confirmed all five frame sums,
the four encoded BL targets, retained caller frames, outlined/tail/epilogue
handling and single counting of saved return addresses. It performed no
independent on-disk verification. The
parent check (`work/linked-stack-path-parent-check.json`) separately records
80 files rehashed without mismatches and independent decoding of the actual
ELF's BLs and prologues, with all five frame sizes matching stack metadata.

The nonblocking observations and their disposition are:

- **Reservation source:** the review did not re-derive 32,768 bytes. The result
  explicitly cites the paired memory layout in
  [TARGET_ALLOCATOR_LINK.md](../TARGET_ALLOCATOR_LINK.md).
- **Feasibility:** selected branch outcomes and preceding calls' results have
  not been shown jointly satisfiable. The result assumes the calls are reached
  and prior calls return with ABI-preserved SP. The prepass witness includes one
  iteration, but remains structural evidence rather than an execution trace.
- **Clarity:** the task handoff identifies James's prior independent clarity
  review and its BIC nit. The raw boot `branches` summary incorrectly included
  `bic.w r2, r2, #15` at `0x080b3cc6` because its reporting filter used
  `startswith(b)`. BIC clears bits and falls through to `0x080b3cca`; it is not a
  branch. The CFG builder already used explicit branch mnemonics, so this was
  only a summary-label error, with no CFG or arithmetic correction needed.

The clarification record (`work/linked-stack-path-clarification/report.json`)
binds the original and corrected summary hashes. The
clarified summary (`work/linked-stack-path-clarification/path-evidence.json`)
differs from the frozen raw summary (`work/linked-stack-path/path-evidence.json`)
only by removal of that one branch-summary entry. Full instruction witnesses,
prologues, call targets and totals are unchanged. James's original reviewer
report was not located in the bounded `work/linked-stack-path*` and relevant
review folders; the correction record is available, while reviewer attribution
comes from the task handoff.

No execution, input-feasibility proof, observed overflow, runtime high-water
measurement or full stack bound was established. The 4 KiB diagnostic allocator
arena cannot run signing. These two documentation files were prepared from
read-only evidence; no build or new model review was run for this write-up.
