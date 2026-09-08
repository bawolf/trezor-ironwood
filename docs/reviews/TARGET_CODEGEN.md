# Target code generation: change reviews

Scope: the standalone synthetic compile-only helper, emitted target objects,
individual frame inventory and a traced nested-frame warning, based on `7f404ec`.
The accepted core and upstream sources are unchanged. No PR was published.

An implementation agent generated and froze the opt3/noLTO target artifacts.
The coordinator rechecked 394 source/evidence/artifact records and independently
traced the ordinary-call path whose emitted frames total 33,000 bytes. A separate
agent reviewed readability. Claude Code reviewed correctness of both
the helper and the evidence claims using a frozen snapshot and read-only tools.

The initial Claude Code review found no blocking defect. It checked frame/prologue arithmetic, call edges,
alias handling and the limits from missing C/sysroot metadata. It requested keeping
the experimental compiler settings beside the stack warning and linking the exact
32 KiB stack definition. The results document now links the pinned linker script;
no final-firmware overflow or whole-stack bound is claimed.

A second bounded diagnostic compiled the identical source with optimization `z`,
keeping LTO off and panic abort. The coordinator rechecked its 342 frozen records.
Fable accepted the comparison: four original edges change, extra Engine frames
appear, and smaller individual frames do not justify reusing the old subtotal.
The independent readability reviewer found no material clarity concern in either
report or the comparison section.

The follow-up suggested naming `Pczt::parse` precisely and explicitly identifying
the lost direct `Spend::parse_inner`→`Ep::from_bytes` call; both are clarified in
the published report. “New code” in the frozen scratch report means newly emitted
machine code, not changed Rust source. Raw diagnostic paths remain absolute for
local provenance; reproduction commands and published explanations are relative
to the repository. The frozen raw evidence was preserved rather than rewritten.

## Provenance

- Initial Claude Code run: `work/reviews/target-codegen-fable/`, requested
  `--model fable`, but usage reports `claude-opus-5` and `claude-opus-4-8`.
  Its earlier attribution to `claude-fable-5` was incorrect. It is not counted as
  confirmed Fable evidence. Eleven turns,
  165.57 seconds, USD 5 limit.
- Size-comparison Fable: `work/reviews/target-codegen-size-fable/`, reported
  `claude-fable-5`,
  20 turns, USD 3 limit. Both used Read/Glob/Grep only, with no permission denials.
- Confirmed replacement review: `work/reviews/target-codegen-confirmed-fable/`,
  requested `fable[1m]` and reported `claude-fable-5-1`; no blocking findings.
  It independently reproduced all nine frame totals and the 33,000-byte sum,
  checked the helper and scope, and closed the historical attribution gap.
  No unchanged build or test was rerun.
- Independent readability reviewer: `01a0800f-b4db-7bc3-9219-01736433ade8`,
  read-only reviews of the helper and final documentation deltas; no tests run.
- Exact prompt/source hashes, command records and responses are retained in those
  ignored directories. Compile/lint/artifact evidence is separate from reviews.

These three reviews reported USD 3.40988225 at list prices through the existing
Max subscription; USD 3.43 is conservatively reserved in the ledger. The full current
request history, including failed requests and reported model identity, is in
`ops/review-usage.json`.
Actual billed charges and Codex dollar usage are not observed here.

See [target results](../TARGET_CODEGEN_RESULTS.md) for measurements and limitations.
