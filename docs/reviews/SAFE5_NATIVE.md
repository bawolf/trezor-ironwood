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
The first computed-S image had 7,168 bytes of flash margin; the later secp change
raises that to 27,648 bytes. Computed-S still has about 16× host
hash slowdown. Treat it as a capacity proof of concept while evaluating faster
small-table options. No hardware action or upstream communication is authorized
by this review record.

## Supported secp256k1 compact table

The frozen source review delivered **Fable5.1**, reported $2.5641985 list-price
usage after provider retries. A separate reviewer checked clarity, xbuild definition
propagation, source provenance and the saved host tests. Both support this minimal
isolated compile experiment; neither certifies target runtime or all consumers.

The vendor directory retains the historical `secp256k1-zkp` name, while pinned
`.gitmodules` explicitly points to bitcoin-core/secp256k1. Its CMake file and all
177 copied source files match the pinned Git blobs. The obsolete table and
GENERATOR defines have no reader in that pinned source. This resolves Fable's
question about a possibly mismatched source packet. Other legacy/crypto Makefiles
still carry their old PREC_BITS=4 setting; they were not changed or built here.

Fable's assertion that the generated-table selector proves cross-translation-unit
consistency is too strong: two separately valid configurations could disagree.
The actual six native compiler commands, exact source hashes, and linked table
size provide the required evidence instead. Existing table/ABI implementation
contains no COMB-sized context array, but runtime initialization has not been tested.
No predicted signing slowdown or leakage improvement is accepted as a measurement.

The native build passed in 52.39 seconds with frozen sources/protected inputs,
40 static checks and 27,648 bytes of flash margin. Full runtime/MCU timing,
constant-time behavior and broader model/build-consumer acceptance remain open.

## Native split-GC layout and diagnostic correction

Fable5.1 accepted the full revision-1 layout for an isolated compile experiment;
its structured reported usage is $5.773228. The independent review found that
non-pyopt `meminfo` assumes one region. Revision 2 adds only an existing-pyopt
requirement and a precise rejection message, preserving all original predicates.
Its separate clarity follow-up closes that finding. The full patch hash is
`f88e1f33953a7dafe7e888cc5266c467aa993e7698b5f2756752e79cfb3f61e6`.
Fable's scoped revision-2/host-evidence review reported $2.729076. Narrative
zero-spend wording is ignored; the ledger uses the structured usage, not an invoice.

The requested caller/GC-state source audit finds only the selected firmware main
calling `gc_init`; Unix calls belong to another binary. The single-area inspector
is excluded by pyopt. Selected C commands now confirm split=1/AUTO=0/PYOPT=1;
generated Rust ABI comparison remains distinct. The final link confirms allocation
boundaries, headers, actual startup-call order and unchanged kernel. DMA/root
lifetimes, complete stack bounds and target execution still need evidence.

The follow-up suggested rejecting `memperf` unless its implementation is compatible.
Inspection resolves that condition: in this pin it only defines a scalar allocation
counter, increments it on every successful `gc_alloc`, and returns that counter.
It contains no area-specific pointer/table traversal. No additional rejection or
configuration option was added. Firmware also has no direct `memperf` feature;
the normal setting is for the Unix project. This does not claim counter overflow
or all debug modes are validated for production.

The follow-up alleged an independent-review hash mismatch. The exact frozen packet
instead labels the original review `7ee854e4…`, matching revision 1; the separately
saved revision-2 follow-up binds `f88e1f33…`. The allegation is rejected against the
packet bytes, and both records remain unchanged. Base HEAD denotes the upstream
pin; per-file hashes explicitly denote the existing modified native working files.

The host range audit had a real generalization risk: a final abbreviated all-free
dump row could understate an area's range. It now fails unless both inferred ranges
sum to the independent GC total; the saved transcripts pass this stricter audit.
No GC test execution was repeated. Graph survival remains conservative-root evidence,
reuse covers the named cycles, and fresh processes are not an in-process restart.
The collector is unchanged relative to Trezor's vendored fork, not claimed to be
an unmodified mainline MicroPython release. The full collector and test scope are
preserved; no new allocator, limits or arithmetic were introduced.

## Selected split-GC representation boundary

The actual ARM C probe records area 32/alignment 4 and memory state 564/alignment
4. Including the unchanged selected generated Rust binding fails E0432: neither
state type exists there. A separate independent interface audit traces the actual
Cargo fingerprints, generated bindings, target sources, C callbacks, assembly and
undefined Rust archive symbols. The changed structures are C-owned state; Rust
receives allocation payload pointers through `gc_alloc`/`gc_free`, not these
descriptors. No representation crosses the inspected boundary, so adding unused
bindings or handmade copies to make a comparison pass would be misleading.
The failed probe and the first comparison-blocker report remain preserved. The
later `ABI_BOUNDARY.md`/JSON close this narrow question, leaving GC roots,
finalization/lifetimes, unrelated FFI and complete native stack/runtime open.
