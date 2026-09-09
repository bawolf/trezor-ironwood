# Safe 7 stack progress

The accepted signing core compiles for the actual Safe 7 processor, but its
complete firmware stack requirement is still unproven. The application stack is
32,768 bytes. Selected Rust call paths alone can consume most or all of that;
MicroPython, C adapters, executor and interrupt costs must also fit.

## Small changes under measurement

Both candidates prevent inlining at existing function boundaries. They do not
change source-level cryptographic calculations, validation, transaction semantics
or APIs; emitted machine code does change.
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
Each combined table cell was measured from the combined objects, not inferred
by adding separate experiments. Removing the two attributes and one added comment
reproduces the two
baseline source files exactly. No conformance or signature tests ran on this
combined source, and it is not accepted into the implementation.

## Shared memory changes the decision

Source inspection of the actual pinned target linker, application header,
scheduler and MPU configuration establishes that **32 KiB is a firmware
reservation, not a fixed hardware capacity**. The stack lives within the existing
819,200-byte application RAM allocation. The scheduler derives its hardware stack
limit from the linked header; a larger reservation would preserve that protection
and reduce GC space. No stack or protection setting has been changed.

Using the retained target maps as a reference, replacing the 4 KiB diagnostic
arena with a separate 128 KiB arena gives these conditional GC extents:

| Stack reservation | Projected GC extent before additional integration statics |
| --- | ---: |
| 32 KiB | 566,808 bytes minus unknown additional static/alignment delta |
| 64 KiB | 534,040 bytes minus the same delta |

The 64 KiB option costs exactly 32,768 additional GC bytes under this layout.
These are arithmetic projections, not a linked integrated image or runtime fit.
GC metadata, live objects, transient copies and fragmentation still consume that
space. Two 8,704-byte THP buffers allocate inside GC; they must not also be counted
as additional static reservations. The native arena remains separate from GC.

The hardware limit also reserves 256 bytes within the stack, and MicroPython's
check leaves a 1,024-byte recovery margin. These margins overlap; they are not
separate RAM allocations. Selected Rust frame sums cannot consume the entire
nominal reservation. Exception/FPU saves on the application stack and C/VM callers
remain to be included, with kernel-stack costs accounted separately.

The source/map report is `work/stack-budget-options/REPORT.md`. It covers the
retained hardware **test preset**, not a production-security configuration.
The next decision gate is an integrated target map and concurrent GC/arena/full
execution-stack measurements. Further parser optimization is conditional on that
budget, rather than an assumed immutable 32 KiB ceiling. The combined outlining
candidate has independent clarity and confirmed Fable 5.1 source reviews.
Fable found no functional source defect and requested bounded functional checks,
clearer comments and fuller branch/call-site evidence before acceptance. Its
reported usage was $0.96407875 against a $15 allowance. Functional and firmware
acceptance remain open.

## Evidence and limits

The serialization-only pair completed all eight compiler commands in 49.970
seconds, with 51.604 seconds for compilation plus object extraction. The ARM
callback and nested frame measurements come from actual emitted objects with
instruction-level checks. Its 4 KiB allocator capsule is deliberately compile-only
and was never executed. It is not the 128 KiB arena in the working emulator.

Earlier read-only analysis failures and the corrected SP accounting are retained
under `work/bridge-stack-next/`; `ANALYSIS_RESULTS.md` records their timing,
corrections and limits. The combined witness already uses the corrected accounting.
The selected serialization path is the v2 clone/allocation/error path, not the
v1 conversion skipped by this V6-only profile. Selected parser branches are
identified in `work/bridge-stack-combined/analysis/selected-results.json`; no
claim that they are the deepest among all admitted branches is made.

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
