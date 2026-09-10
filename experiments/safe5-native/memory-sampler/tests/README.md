Fixed GC sampler host checks: PASS, eight groups and two intended mutation rejections.

The unmodified proposal is compiled with the actual pinned MicroPython `py/gc.c` (commit `579c7624bd2224c7e038504e4bc3de591a9fbcf9`, SHA-256 `ddb8fe0e6d497488d223dc28994b1bbbd0875ad1cb3c3083fa1650535aa509dc`). No collector measurements are supplied by a fake gc_info implementation. Observation wrappers delegate to actual gc_info/alloc/free/realloc compiled from that source; they count calls without fabricating results. The sampler object's only undefined symbol is gc_info. Capture makes one sampling call and no observed allocation/free/reallocation/collection calls.

Expected occupancy comes from returned allocation addresses and requested lengths rounded to actual block size. A separate per-area occupancy array computes free runs without reading the GC allocation table. Checks cover empty/trailing runs, aggregate free versus a single-area allocation, all six phase bits, overwrite isolation, invalid represented phases, fragmented allocation failure without record erasure, reset and cleanup/recovery. Real collection preserves explicitly rooted allocations, then frees them after those roots are dropped.

Host observations:

| Quantity | Result |
| --- | ---: |
| Pointer / phase enum / block / area header | 8 / 4 / 32 / 64 bytes |
| Raw reservations | 32,768 + 16,384 bytes |
| Actual usable pools | 32,384 + 16,128 bytes |
| Empty free / largest run | 48,512 / 32,384 bytes |
| Rejected request exceeding either pool | 32,416 bytes |
| Fragmented used / free / largest run | 24,256 / 24,256 / 32 bytes |
| Rejected fragmented request | 64 bytes |

The two private sampler copies each fail at the intended assertion: removing max_free's block-to-byte conversion fails largest-free equality; omitting the validity-bit update fails phase validity. The canonical sampler is unchanged. Final baseline evidence is `runs/20260910T184635912539Z/RESULT.json`; mutation evidence is its `negative-controls/RESULT.json`. Each contains exact commands and raw stdout/stderr paths/hashes. Earlier successful runs remain retained; the final rerun followed the requested generated-header trim.

Reproduction uses one positional **MicroPython root**, containing `py/gc.c` and `ports/unix`. Keep the sampler in sibling `proposal/memory_trace.{h,c}` and these tests in `tests/`:

```sh
python3 -B tests/run_tests.py /absolute/path/to/pinned/vendor/micropython
python3 -B tests/negative_controls.py /absolute/path/to/new/run/RESULT.json
```

The actual source root used here was `/Users/bryantwolf/Documents/Codex/2026-09-07/ca/work/safe5-native/firmware/vendor/micropython`. The runner is portable with respect to that source location; its retained compiler/SDK recipe requires the recorded macOS/Xcode installation. It does not claim general cross-platform support. Each subprocess is bounded (compile/link 60 seconds, canonical execution 20 seconds; negative-control commands 60 seconds) and raw attempts are retained in fresh run directories.

The recipe derives from the existing successful `safe5-gc-host` Unix minimal build: SPLIT=1, AUTO=0, finalizers enabled, Python threads disabled, host GC blocks of four pointer words. It retains the original GC optimization/assert settings; test CHECKs remain active independently of NDEBUG. The default GC_HOOK_LOOP is empty (`py/mpconfig.h:787–788`), and GC locking is inactive in this configuration. Only the three generated headers actually listed by the gc/sampler/test dependency files remain in host-config: compressed.data.h, qstrdefs.generated.h and root_pointers.h. Their origin/hashes, compile recipe and MicroPython MIT license are retained. The unused generated headers are archived in an earlier raw run, outside the source package.

Limits: automatic collection is explicitly disabled after initialization to preserve occupancy on allocation failure. The two collection calls use the real collector with an explicit test-root provider, not Unix register/stack discovery or a running VM. No automatic OOM recovery or whole-VM root behavior is established. Finalizer support remains enabled, but allocations have no finalizer flag; unused object-runtime finalizer callbacks abort if reached. This does not test finalizer behavior. Static host arrays replace linker regions; host size/offset results are not native layout measurements.

Invalid-phase checks concern values represented by the host's 4-byte enum. Native `-fshort-enums` can truncate an integer before the function receives it; this is an internal enum API, with no wire-phase endpoint. No arbitrary pre-cast integer rejection is claimed. No native GC execution, caller hooks, UI/wire integration, allocation timing, stack maximum, device, Fable or adoption claim follows from these tests. Parent native-object work is separate.

`FINAL.json` binds the frozen package source hashes and both passing result records. Package only proposal/, this README, the three test/runner scripts and host-config's three required headers/license/provenance/compile recipe; raw runs remain evidence rather than build dependencies.
