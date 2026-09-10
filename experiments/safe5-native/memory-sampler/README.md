# Fixed heap sampler proposal

Unadopted synthetic diagnostic component. The native object compiles; eight
host check groups and two rejecting mutation controls pass against the actual
pinned MicroPython GC. It has no firmware caller hooks, USB endpoint or native
runtime evidence. No complete firmware image was changed or rebuilt.

`proposal/memory_trace.c` and its header implement six fixed phase records with
used, free and largest-contiguous-free byte counts. Validity bits distinguish
missing samples from zero. Capture overwrites one phase, reset clears the trace,
and get returns a live const view. The caller must serialize access on the trusted
executor with initialized, quiescent GC. No keys, heap contents or pointers are
stored in the records. These are phase samples, not peak measurements.

The native object contains 76 bytes of fixed storage and 192 bytes of function
text. Capture's own frame is 40 bytes; caller, GC scan and interrupt costs are
separate. These are not net changes to firmware capacity. The native block size
is 16 bytes; the host checks use 32-byte blocks and explicit roots with automatic
collection disabled for controlled failures. See [the test contract](tests/README.md).

With the pinned MicroPython source and the recorded macOS/Xcode installation:

```sh
python3 -B tests/run_tests.py /path/to/trezor-firmware/vendor/micropython
python3 -B tests/negative_controls.py /path/to/new/run/RESULT.json
```

Only the three generated headers required by compiler dependency records are
included. Their provenance and MicroPython license accompany the compile recipe;
raw donor builds are not execution dependencies. Compiler/SDK paths remain those
of the recorded Mac installation, so this is not general cross-platform setup.
`RESULTS.json` binds the source, commands/results and independent local review.

Fable review awaits exact-packet approval after automatic review rejected
transmission. No external model usage occurred. Connect sampling and bounded USB
retrieval only as a separately reviewed experiment, then measure actual native
heap/stack/arena use and timing. Full clean-checkout firmware reproduction and
Trezor adoption remain open. The sampler carries GPL-3.0-or-later; copied
MicroPython generated material retains its supplied MIT notice, and the original
host harness follows the repository license.
