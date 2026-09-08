# Target code generation: change reviews

Scope: the standalone synthetic compile-only helper, emitted target objects,
individual frame inventory and a traced nested-frame warning, based on `7f404ec`.
The accepted core and upstream sources are unchanged. No PR was published.

An implementation agent generated and froze the opt3/noLTO target artifacts.
The coordinator rechecked 394 source/evidence/artifact records and independently
traced the ordinary-call path whose emitted frames total 33,000 bytes. A separate
agent reviewed readability. Claude Code with Fable reviewed correctness of both
the helper and the evidence claims using a frozen snapshot and read-only tools.

Fable found no blocking defect. It checked frame/prologue arithmetic, call edges,
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

- Initial Fable: `work/reviews/target-codegen-fable/`, primary model
  `claude-fable-5`, 11 turns, 165.57 seconds, USD 5 limit.
- Size-comparison Fable: `work/reviews/target-codegen-size-fable/`, same model,
  20 turns, USD 3 limit. Both used Read/Glob/Grep only, with no permission denials.
- Independent readability reviewer: `01a0800f-b4db-7bc3-9219-01736433ade8`,
  read-only reviews of the helper and final documentation deltas; no tests run.
- Exact prompt/source hashes, command records and responses are retained in those
  ignored directories. Compile/lint/artifact evidence is separate from reviews.

These two reviews reported USD 2.6538015 at list prices through the existing Max
subscription; USD 2.67 is conservatively reserved in the ledger. Across six reviews,
reported usage is USD 14.0286585 and the reserve is USD 14.07 of the initial USD 300.
Actual billed charges and Codex dollar usage are not observed here.

See [target results](../TARGET_CODEGEN_RESULTS.md) for measurements and limitations.
