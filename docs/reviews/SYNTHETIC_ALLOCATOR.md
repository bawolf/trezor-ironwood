# Synthetic allocator proposal review

Reviewed 2026-09-08. Scope: the proposed isolated allocator boundary, using the
unchanged approval core, public synthetic keys and released allocator sources.
This accepts a design for experiments, not a passing implementation or firmware.

Claude Code with Fable reviewed the proposal and a focused revision with all tools
disabled. The fixed input contained only the authored proposal and public allocator
source. Independent Codex reviewer James checked naming, ownership wording and
experiment order. The coordinator inspected the relevant source and resolved:

- Use Heap's own initialization state; reject repeat initialization before forming
  another mutable arena reference. Check minimum buffer size at compile time.
- Test coalescing by allocating and freeing the same large Layout before and after
  the lifecycle, as well as comparing live counters.
- Scope large-alignment tests to the host diagnostic arena; derive smaller-arena
  expectations separately. Neither requested nor rounded host sizes bounds the MCU.
- State which arena owners cannot escape, and distinguish outside-arena output
  staging from export after teardown. Separate initial emulator diagnostics from
  pressure tests based on a linked candidate's GC extent.

The coordinator rejected two factual suggestions from the first Fable response:
requested Layout sizes also vary by target, and 8,704 bytes describes a THP buffer,
not every fixture's size. The follow-up accepted both corrections and reported no
unresolved actionable design errors. James's final sentence-level correction makes
clear that the first large allocation is freed before the lifecycle.

An earlier worker attempted a broader file-enabled review; automatic approval
rejected it before execution because it would export local source without specific
destination authorization in that worker's context. No usage was incurred. The
coordinator completed the narrower tools-disabled reviews under the user's explicit
“Claude Code with Fable” instruction. That rejection is resolved, not pending approval.
The original rejection is preserved in `work/allocator-research/review-status.json`.

Local frozen prompts, inputs and results:

- `synthetic-allocator-fable`: result SHA-256 `3b19dbc15f916ee52987ab037b7cc80e7e1d49a54e73b0a344c0d8c033561e58`; reported USD 1.020386.
- `synthetic-allocator-followup`: result SHA-256 `2fb894c592ced2ba6ce9b887779b87989807dfa585f18ceb722d21d0f2e9e3f7`; reported USD 0.350541.

These are reported list-price estimates through the existing Max subscription,
not observed invoices. Conservative holds are in `ops/budget.json`.

The subsequent arena prototype exposed public upstream lazy tables that outlive a
request. The original no-escaping-owner gate correctly fails. A revised image-lifetime
constant-table boundary requires separate implementation evidence and both reviews;
this proposal review does not convert that failure into a pass.
