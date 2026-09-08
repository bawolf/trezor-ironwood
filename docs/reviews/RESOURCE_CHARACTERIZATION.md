# Resource characterization: change reviews

Scope: new standalone fixture/oracle and allocation/timing tools plus their
coordinated evidence runner, based on `12c25c8`. The accepted approval core and
pinned upstream sources did not change. Two bounded agents implemented the tools;
the coordinator integrated the runner and evidence. No PR or upstream message was
published.

## Findings and resolutions

| Review | Finding | Resolution |
| --- | --- | --- |
| Fable and independent readability | The signed artifacts were verified, but report metadata/digests were not bound to them by the runner. | Compare all reported fixture facts and sighashes to the independently checked manifest, and signed lengths to the actual files before marking the report verified. |
| Independent readability | Phase continuity, warm-up and failure retention needed durable checks. | One run validator checks carried allocations, owned input, all phases and complete teardown for warm-up and every record; failure paths must restore their baseline. |
| Fable | Empty instrumentation could produce plausible-looking zero measurements. | Require observed allocation and timing work for begin/sign, verify event balance, and recompute timing summaries from raw samples. |
| Fable | Dependency feature monitoring omitted direct crypto dependencies. | Monitor every direct core dependency and measurement helper for std/getrandom leakage, alongside exact core/PCZT feature checks. |
| Independent readability | The empty-instrumentation regression could fail for an unrelated reason. | Require its specific instrumentation error so deleting that guard cannot leave a passing test. |
| Coordinator, checked by readability reviewer | “Deterministic originals” overstated fixed builder seeds. | Explain upstream IoFinalizer's OsRng dummy signatures and preserve each run's exact corpus hashes. |
| Independent readability | READMEs contained agent history and duplicated preliminary results. | Keep operation/measurement contracts in READMEs and accepted evidence in RESOURCE_RESULTS.md. |

The counter's private critical sections remain nonallocating and nonpanicking;
no generic lock framework was added for hypothetical future callbacks. Counts
exclude allocator internals and stack, and five instrumented host samples are not
MCU timing bounds. These limits remain attached to the measurements.

## Review provenance

Claude Code ran the actual `claude-fable-5` model through `--model fable`, using
the existing Max subscription. The initial review used a frozen source snapshot,
read-only Read/Glob/Grep tools and a USD 10 limit. It completed 18 turns with no
permission denials and no blocking defect. A focused, tool-free follow-up reviewed
the Python/test/documentation delta with a USD 3 limit; it completed one turn with
no remaining actionable finding. The reviewers did not run tests.

Raw prompts, source hashes, responses and command records are retained under
`work/reviews/resource-fable/` and `work/reviews/resource-fable-followup/`.
The independent readability agent was `01a07ffa-fd0d-75c3-86f3-9fbee9a46f75`;
it reviewed the implementation and subsequent deltas without writing files.
After the Fable follow-up, one test assertion was narrowed to require the intended
error; runtime code remained unchanged. The project and resource lanes were then
rerun against that final snapshot.

The follow-up noted nonblocking limits: the environment-override guard is hygiene,
not a hermetic-build or hostile-environment boundary; missing signed files fail
loudly, and the separate oracle checks the complete directory and fixed policy.
Review-output capacity is reported as a descriptive subset of measured occupancy,
not an independent accounting proof. No additional controls or signing paths were
added for those observations.

These two resource reviews reported USD 4.162670 in list-price model usage; the
ledger conservatively reserves USD 4.18. This is not an observed billed charge.
Across all four reviews so far, reported usage is USD 11.374857 and the bookkeeping
reserve is USD 11.40 of the user's initial USD 300. Existing Codex usage remains
unavailable in dollars. See `ops/review-usage.json` and `ops/budget.json`.

[RESOURCE_RESULTS.md](../RESOURCE_RESULTS.md) records actual checks and resource
measurements separately from the review conclusions.
