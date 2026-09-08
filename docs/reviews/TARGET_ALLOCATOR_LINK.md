# Compile-only allocator link: change reviews

Scope: the isolated Safe 7 firmware patch, its linked artifacts and memory/stack
claims. The accepted approval core and clean pinned baselines are unchanged.
No image was executed and no PR was published.

Independent clarity review requested `lock_initialized_heap` for the guard-returning
helper and a narrower comment about optimizer hints. Both changes are applied.
The pinned rebuild passed in 60.969 seconds; firmware.bin and every loaded ELF
section remain byte-identical. The coordinator rehashed all 97 correction records
in addition to the 247 original records.

The first review response was unusable; two related requests failed authentication.
After login refresh, an explicit older Fable model request returned an Opus review.
That review is retained under its actual model identity. The final configured-model
review (`work/reviews/firmware-arena-link-final-configured/`) reported
`claude-fable-5-1` and found no blocking issue in the compile-only scope.

Its findings were resolved as follows:

- The secure-monitor delta is caused by two embedded paths whose worktree names
  differ by five characters. Direct ELF section reads show that substituting those
  names makes the entire string pool identical. The paths name `smcall_dispatch.c`
  and `smcall_verifiers.c`; the review's reference to `smcall_probe.h` concerns
  macro source, not the second emitted filename. Relocated literals and alignment
  explain the layout change; historical header-signature equivalence is unclaimed.
- The source inventory covers approval and librustzcash path dependencies as well
  as registry packages. Outer-locked/inner-unlocked xtask behavior is explicit;
  before/after inventories bind the observed build rather than asserting an
  upstream lock-enforcement guarantee.
- The results now give the corrected patch's ELF and allocator-source hashes,
  alongside the first-link evidence. The raw `baseline_entries` field means the
  preceding derivative build02; frozen history was clarified rather than rewritten.
- Feature unification is scoped to shared utilities. Multiple inherited major
  dependency versions remain; no validation feature was removed.
- Tree isolation is accepted for this retention diagnostic. No production feature
  interface is added to the compile-only patch. Runtime signing and whole-stack
  evidence remain separate prerequisites.

The final run used tools-disabled input, a USD 5 reported-usage limit and reported
USD 3.18980075. Actual model usage and response hashes are in
`ops/review-usage.json`; these estimates are not observed invoices. The separate
readability reviewer was `01a08030-6113-7c71-bb6e-54a8c5665175`.

See [results](../TARGET_ALLOCATOR_LINK.md) and the
[complete patch](../../experiments/firmware-arena-link/README.md). Acceptance is
limited to the captured static experiment; it does not approve execution or funds.
