# Synthetic arena: change reviews

Scope: the standalone native C/no_std signing experiment in
`experiments/arena-probe`, based on `36f56ed`. The accepted approval core, protocol
limits and pinned upstream sources are unchanged. No PR was published.

The first implementation correctly failed its original zero-owner teardown gate:
five allocations survived signing. Pinned Pasta source identifies those owners as
immutable Fp square-root tables derived solely from public field constants. They
retain 29,802 requested bytes (29,808 allocator bytes on this host). No signed
output was exported by that failing run; its source, binary and evidence remain
frozen.

The amended experiment initializes those public constants before keys or input,
checks the exact five layouts, and seals their original addresses. It does not
free or reset the tables. Every later request must release all its owners and
restore the same baseline, with balanced allocation/free deltas and a repeated
64 KiB contiguous-allocation probe. A new retained allocation fails teardown;
a sealed-table free is rejected inside the wrapper before `Heap::deallocate`.
The diagnostic invokes that guard directly without attempting an invalid free.

## Findings and resolutions

The initial confirmed Fable review (`work/reviews/arena-probe-fable/`) identified
several ways the evidence runner could misreport results:

- Python assertions could disappear under optimization, and empty stdout could
  pass. Explicit checks now enforce exact report counts, statuses, completed
  phases, counters and export state; regressions run normally and with `-O`.
- Missing or partial fatal diagnostics could prevent saving the final report.
  Diagnostics are optional; invalid payloads remain generic invariant failures,
  and every command result is retained.
- The lockfile exception was not bound to the full build lock. The checker now
  proves parsed equality after removing only the exact allocator package, binds
  both hashes, and checks its downloaded/cache archive against the published
  index checksum. The unchanged shared checker covers the other 128 packages.
- The native personality stub needed the pinned five-argument C ABI and status
  return. Its only behavior is immediate process termination; it is absent from
  Thumb builds.
- Oracle wording overstated the evidence. Fifteen distinct signed outputs pass
  the independent upstream oracle. The repetition test replaces three of those
  outputs after consecutive requests in one process; its second oracle checks
  that resulting set of fifteen.

Independent clarity review found stale dependency metadata could hide a manifest
feature change. Each audit now resolves fresh offline, locked metadata and saves
it separately. A real feature-toggle regression demonstrates rejection despite
unchanged cached metadata. It also requested named fault modes and a shorter,
organized README. Those changes passed the final independent review.

The old host resource report is clarified: key construction and fixture metadata
inspection precede its per-request baseline. Its 80,821-byte peak excludes
already resident public tables. The arena experiment's counters never reset and
include those tables, cold initialization and recovery probes; the observed
maximum is 111,903 requested / 111,976 used bytes. Neither is an MCU bound.

## Validation and provenance

The v3 binary passed all 35 process cases and both independent signature-oracle
checks. Separately, all eleven evidence-runner tests passed normally and under
Python optimization; those tests include a positive control.
Formatting and warning-fatal Clippy passed with the source-pinned nightly on both
native and actual Thumb targets; actual Thumb object/static-library generation
also passed. Earlier leak-test optimizer elision, oracle timeout and temporary
regression-fixture setup failure are preserved as failures.

- Final report: `work/arena-probe/v3/verification-01/report.json`.
- Final evidence manifest: `work/arena-probe/frozen-evidence-v3.json`, SHA-256
  `2d29661ab750765675e5442ba94faf821f93242d1d807274c2bafca7dd58fded`
  (154 source/artifact/log records).
- Original failing manifest: SHA-256
  `5370b67a3cd54845b20522013e7cec7146525fcbcc771f883ad8a4c1b0d4210f`.
- Passed v2 manifest, retained before the final clarity corrections: SHA-256
  `4ba4bdd23e02523d7cc2b596c614dc1f16c90ec8b19d9cfd195eb266149099d4`.
- Readability reviewer: `01a08030-6113-7c71-bb6e-54a8c5665175`; final delta had
  no actionable findings. Review was read-only; test execution was separate.
- The first final Fable request failed authentication. After login refresh,
  `work/reviews/arena-probe-fable-refreshed/` reported `claude-fable-5-1`: no
  blocking findings. It used the configured `fable[1m]` model, no tools, and a
  USD 5 reported-usage limit (USD 4.479968 reported).

The six small C/Python improvements passed the v4 run: 35 process cases, both
exact oracle censuses, twelve evidence-runner tests in both Python modes, and
byte-identical outputs for all three freshly repeated requests. A scratch C shim
triggers the existing Rust panic before request three: the corrected driver
preserves two earlier reports, while the original driver preserves none. No new
driver mode was added. The lock hash is recorded alongside binary hashes; build
provenance still depends on the frozen source/library and command records.

The final v4 manifest is `work/arena-probe/frozen-evidence-v4.json`, SHA-256
`b1c5794f3f2abab619d5b19dcb3f1f161956e4e3dd7ad6cf610cf2b8b5f4e809`
(167 files). The coordinator rehashed all 146 worker evidence records and checked
the changed source hashes. Rust and its pinned native/Thumb checks are unchanged
from v3. The bounded delta review also reported `claude-fable-5-1` and no blocking code
finding (USD 2.60227175 reported against a USD 3 limit). Its remaining questions
concerned context omitted from the packet: `v4/result.json` already records the
Rust library hash, exact changed source hashes and twelve-test census. The small
`v4/verify.py` and `negatives.py` wrappers import the experiment scripts; they are
not alternate verifier implementations. Their sources and the original-driver
control shim are included in the frozen evidence. The coordinator checked these
bindings and the raw test logs. `WRITE_ERROR` is a distinct driver failure code.

The final clarity change makes the stderr comment conditional on an inherited
file description. Relinking that comment-only change produced a byte-identical
v4 binary; `work/arena-probe/final/comment-correction.json` records both source and
library hashes. Reproduction commands now use fresh target/output directories.
Named sealed-free and late-owner tests assert termination with exit 84; missing
optional diagnostic payloads are not treated as proof of the precise failure
origin. Ownership measurements come from the complete signed-request reports.

 Fable suggested checksumming public-table contents; that is
not added to this ownership diagnostic. The seal checks identity, layouts and live
counts, not arbitrary memory corruption or byte integrity. Its observations do
not claim such protection. The saved reports are authoritative; compact excerpts
in earlier review prompts are not raw verifier output.

Costs and reported model identities, including failed or substituted requests, are recorded in `ops/review-usage.json`.
These are experimental host results and target compilation, not firmware execution,
stack safety, MCU resource bounds, entropy integration or production approval.

Final source/binary binding: `work/arena-probe/final-manifest.json`, SHA-256
`abceca69bba4bca6e4be283c680755414bb7fda948b6e3f249d213c9cf45f234`.
