# Safe 5 native experiment review disposition

2026-09-10 UTC. Acceptance is limited to source/configuration and static capacity
measurement. No device/runtime, key handling, consent or production acceptance.

## Reviews completed

- Six-file T3T1 executor/arena delta: Claude Code requested Fable, delivered the
  user-authorized Opus fallback (`claude-opus-4-8` text, Opus5 usage). Separate
  execution-contract/clarity review passed. Actual module flags and 14 positive/
  negative compiler configurations close its two configuration questions.
- Paired pyopt capacity experiment: delivered documented Opus fallback and
  independent scope/clarity review. The original pyopt+debug command failed; the
  separate debug=false correction is supported by the pinned qstr/translation
  guards. Both failures and later paired results remain distinct.
- First small-code Fable request identified Fable5.1 but returned only an
  unexecutable tool request, despite a terminal success record. **Rejected as no
  delivered review.** Its reported usage remains in the ledger.
- The replacement frozen packet delivered an Opus fallback review of both the
  small-code dependency features and computed-S patch. Independent clarity/source
  reviews found no actionable normal-execution defect for the experiment.
- Independent final ELF inspection passes 45 static checks, kernel identity,
  module-to-bridge references and positive-control table-byte absence.

## Findings and resolutions

The computation uses exactly the upstream u32/four-byte generator index and
personalization. Exhaustive host generator equality and real baseline/candidate
public API differentials pass. The body keeps its bounds, padding, incomplete
addition and blinding. One Box allocation per hash remains an explicit change;
empty input may now fail allocation even though mathematical output is unchanged.
No identical fault-detection, zeroization or constant-time claim is made.

The two dependency flags only remove inline attributes. Their direct/optional
Cargo structure is necessary to configure the same resolved dependencies, without
adding a crypto wrapper or second implementation. Feature-unification scope and
all unchanged registry versions/checksums are recorded. The package contains the
complete lock change, not only the manifest fragment.

The actual current feature list omits debug/debuglink/UI diagnostics and includes
pyopt and universal support. Earlier JSON snapshots intentionally describe earlier
runs. Review arithmetic that called the progression inconsistent is rejected:
all maps use the same 1,703,936-byte slot; each documented row measures a distinct
explicit configuration. Parent ELF parsing includes load-address gaps/data/headers
instead of assuming a simple sum is always sufficient.

A NOLOAD arena may appear in a PT_LOAD with positive memory size and zero file
size. The review's initial “no PT_LOAD” wording is corrected to **no file-backed
arena payload**, now verified from ELF. Source CMSE/model guards establish compile
configuration; they do not establish runtime TrustZone state. `SECURE_MODE` names
a kernel role here, not the Core application's TrustZone Secure state.

The suggestion to add a feature gate solely to remove the still-public S table is
not adopted. The existing public API is preserved, and actual allocated-byte
inspection proves removal in this exact image. Adding a new configuration lever
would not strengthen that artifact result. Reinspect future dependency changes.
The host oracle intentionally retains the original table.

The reviewer requests a 32-bit execution of the generator tests. That remains a
runtime/target-equivalence gate; it is not required to report the directly measured
ELF capacity. Host mathematical equality and target compilation are stated
separately. No instruction-level or side-channel equivalence is inferred.

The two stack attributes were already reviewed in the standalone combined-stack
experiment. They are measured again in the native image with unchanged bodies;
the latest static chain still exceeds 32 KiB. Prior successful standalone evidence
is not promoted to a complete linked stack bound.

The full existing host approval and bridge suites now pass with the computed-S
dependency and both stack attributes. Independent oracle negatives also pass,
and two fresh bridge responses verify three new real-spend signatures. Source,
fixtures and native shared pins are checked; no test body or assertion changed.
This closes the named host regression gate, with the runtime limits below.

## Open acceptance gates

32-bit execution, stack/live-frame and GC peaks, allocation failure/recovery, MCU latency and physical
leakage, trusted Safe 5 consent/legacy-wire integration, and dedicated hardware.
The computed-S variant has only 7,168 bytes of flash margin and about 16× host
hash slowdown. Treat it as a capacity proof of concept while evaluating faster
small-table options. No hardware action or upstream communication is authorized
by this review record.
