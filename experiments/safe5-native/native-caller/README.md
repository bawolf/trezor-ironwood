# Synthetic Safe 5 native caller proposal

Unadopted proposal. The exact source compiled for T3T1, but has not executed on
native hardware. Adversarial Fable review is pending. This is not installable or
production firmware.

`native-caller.patch` applies after the retained `../firmware.patch` in a separate
firmware checkout. It adds the synthetic messages, their generated definitions,
the existing trusted Python review flow and the stock lazy dispatch entry. The
feature `ironwood_native_caller` includes the existing
`ironwood_target_native_compile_only` feature and adds narrower configuration
requirements. Its C capability and frozen Python substitution derive from the
same feature. The original compile-only image retains no wire caller.

The patch changes 14 files. `SOURCE_MANIFEST.json` records every before/after
hash. Applying it to copied retained sources reproduced every compiled candidate
source hash. The unchanged C implementation still internally approves a matching
synthetic token; the Python review path is therefore a trust boundary.

Keep the parent experiment's pinned dependencies, toolchains, synthetic settings
and generation commands. Add `ironwood_native_caller` to that experimental build's
feature list and run standard `tools/build_protobuf` generation. The included
generated sources match that command. `RESULTS.json` records the actual build
configuration and evidence hashes. Full clean-checkout reproduction is still
outstanding; do not infer it from a successful prepared build.

Run the Python caller contract tests against that source root:

```sh
python3 -B run_tests.py /absolute/path/to/prepared-firmware
```

Python 3.11+ and its standard library suffice. The runner writes fresh logs and
hashes beneath the ignored `runs/` directory. Ten tests cover 216 subcases using
the real Python caller and review functions with boundary stubs. They verify
tested confirmation order, token forwarding, failure cleanup, retry and build
predicates. They do not execute C/Rust, real allocations, MicroPython scheduling,
rendered hold timing, native capability export or cryptographic signing. An ACK
failure can follow transmission of signed bytes.

The native caller adds 3,072 net flash bytes relative to the retained image,
leaving 24,064 bytes. All RAM reservations remain equal. Actual heap/stack peaks,
largest free block, latency and native cancellation/recovery remain unmeasured.
The separate parser-boundary and response-capacity proposals are not applied.
See [the caller checkpoint](../../../docs/SAFE5_NATIVE_CALLER.md) for acceptance
boundaries and [the diagnostic plan](MEASUREMENT_PLAN.md) for the next measurement.

Upstream Trezor licensing and notices remain in force. The test harness follows
this repository's license. These experiment-only guards, messages, fixed keys
and synthetic signing behavior must not become production interfaces.
