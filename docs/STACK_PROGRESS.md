# Safe 7 stack progress

The accepted signing core compiles for the actual Safe 7 processor, but its
complete firmware stack requirement is still unproven. The application stack is
32,768 bytes. Selected Rust call paths alone can consume most or all of that;
MicroPython, C adapters, executor and interrupt costs must also fit.

## Small changes under measurement

Both candidates prevent inlining at existing function boundaries. They do not
change cryptographic calculations, validation, transaction semantics or APIs.
The accepted core and passing emulator image remain unchanged.

| Conditional selected path, bytes | Baseline | `verify_bundle` only | `Pczt::serialize` only | Combined |
| --- | ---: | ---: | ---: | ---: |
| Begin validation | 33,688 | 30,688 | 33,688 | 30,688 |
| Signing parser | 31,952 | 31,952 | 26,648 | 26,648 |
| Serialization allocation/error branch | 16,208 | Not measured | 18,360 | 18,360 |

These are separate phases, so their depths are compared rather than added.
They are measured structural paths, not a complete worst-case bound or evidence
that a particular transaction traverses every listed branch. The serialization
candidate reduces the selected parser path by 5,304 bytes while increasing the
selected encoding path by 2,152 bytes. That supports testing the two changes
together; it does not establish hardware fit.

The combined paired compile passed in 29.002 seconds under
`work/bridge-stack-combined/`; its selected-path analysis completed in a separate
208.6-second preparation/inspection window. The same pinned compiler, dependencies
and LTO settings were used on both sides. The observed gains compose, as shown
above; 116 original inputs, 451 cached files and five tools remained unchanged.
Removing the two attributes and existing explanatory comment reproduces the two
baseline source files exactly. No conformance or signature tests ran on this
combined source, and it is not accepted into the implementation.

## Evidence and limits

The serialization-only pair completed all eight compiler commands in 49.970
seconds, with 51.604 seconds for compilation plus object extraction. The ARM
callback and nested frame measurements come from actual emitted objects with
instruction-level checks. Its 4 KiB allocator capsule is deliberately compile-only
and was never executed. It is not the 128 KiB arena in the working emulator.

Read-only analysis initially failed because its loader omitted `__file__`.
A separate analysis of the existing objects completed the selected serialization
path without rebuilding. It also corrected an overly broad SP claim: a field
multiplication temporarily saves LR, then restores SP before its nested call.
The selected parser subtotal is unchanged. Failed and corrected evidence remains
under `work/bridge-stack-next/`; `ANALYSIS_RESULTS.md` records the exact limits.
Final evidence sealing exceeded the ten-minute analysis bound by 15.4 seconds;
no further analysis was launched in that assignment.

Indirect calls, unresolved tail edges and missing C helper frames prevent a true
maximum claim. Neither candidate passed the earlier explicit condition requiring
a proven maximum below 31,952 bytes. The combined experiment is a new measurement
of composition, not a relaxation of that acceptance condition. The coordinator
authorized it within the user's standing project scope; the user did not separately
request this exact compiler experiment.

The next device gate needs integrated firmware measurements and a defensible
budget for the full execution stack. More graph enumeration alone does not close
that gap. Fable and independent clarity review, functional equivalence checks,
and hardware validation remain necessary before accepting a device implementation.
