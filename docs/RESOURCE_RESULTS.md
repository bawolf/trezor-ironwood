# Synthetic approval resource results

The first host characterization passed for all 15 synthetic layouts, with 75
measured runs and 15 untimed warm-ups. The separate upstream oracle verified all
43 real-spend signatures and preserved transaction effects, metadata and 28
existing dummy signatures. The accepted approval core at `12c25c8` is unchanged.
[Fable and independent readability reviews](reviews/RESOURCE_CHARACTERIZATION.md)
are complete. This measurement is not a Safe 7 fit result.

## Reproduce

```sh
python3 scripts/resource_check.py
```

The two standalone workspaces separate fixture construction/oracle features from
the measured core. The measurement has `ironwood-approval=[]`, `pczt=[orchard]`,
`rand_core=[]`, and alloc-only serde/serde_json. Registry dependencies match the
pinned librustzcash lock. Formatting, warning-fatal Clippy and three tests in each
workspace passed before the coordinated measurement.

The measured build used Apple M2, 24 GiB RAM, `aarch64-apple-darwin`, Homebrew
rustc 1.94.0 (`4a4ef493e3a1488c6e321570238084b38948f6db`, LLVM 21.1.8),
opt-level 3, thin LTO, one codegen unit and panic unwinding. The core uses a public
synthetic account and fixed ChaCha20 randomness; no device RNG is exercised.

## Observed results

Bytes below are requested Rust allocation layouts, including the run's owned raw
input. Peaks subtract the harness baseline recorded before that input copy;
they do not subtract the phase baseline, which contains earlier core allocations.
Each row reports the largest peak and median/maximum instrumented time over five
runs. Warm-ups and human review time are excluded. The raw report retains every
phase's event counts, requested bytes, live occupancy, first/median/maximum time
and teardown result.

| Layout | Input bytes | New signatures | Peak bytes | Begin ms, median / max | Sign ms, median / max |
| --- | ---: | ---: | ---: | ---: | ---: |
| outputs-1 | 1,236 | 1 | 14,340 | 25.07 / 26.38 | 1.14 / 1.76 |
| outputs-2 | 2,493 | 1 | 23,177 | 46.55 / 49.22 | 1.19 / 1.42 |
| outputs-3 | 3,750 | 1 | 33,334 | 72.40 / 79.25 | 1.69 / 2.98 |
| outputs-4 | 5,008 | 1 | 42,832 | 91.36 / 97.04 | 1.94 / 2.24 |
| outputs-5 | 6,265 | 1 | 52,329 | 126.53 / 134.02 | 2.05 / 3.29 |
| outputs-6 | 7,523 | 1 | 61,827 | 130.20 / 130.77 | 2.03 / 2.76 |
| outputs-7 | 8,780 | 1 | 71,324 | 151.73 / 155.65 | 2.09 / 2.67 |
| outputs-8 | 10,037 | 1 | 80,821 | 180.67 / 240.23 | 2.27 / 2.37 |
| inputs-2 | 2,429 | 2 | 23,773 | 44.94 / 60.67 | 2.12 / 3.97 |
| inputs-3 | 3,622 | 3 | 33,206 | 76.53 / 94.04 | 3.41 / 4.37 |
| inputs-4 | 4,816 | 4 | 42,640 | 72.19 / 77.33 | 4.46 / 4.81 |
| inputs-5 | 6,009 | 5 | 52,073 | 90.21 / 102.98 | 5.80 / 6.17 |
| inputs-6 | 7,202 | 6 | 61,506 | 91.41 / 97.41 | 6.25 / 6.48 |
| inputs-7 | 8,395 | 7 | 70,939 | 105.66 / 107.53 | 6.49 / 7.37 |
| inputs-8 | 9,588 | 8 | 80,372 | 115.66 / 119.45 | 8.05 / 9.20 |

The largest observed positive-case peak was 80,821 bytes (78.93 KiB), during
`outputs-8` validation, including its 10,037-byte input. The largest individual
request was 24,000 bytes. `begin` dominates measured time; signing eight real
inputs is separately covered by `inputs-8`. These are sample maxima, not bounds
for all admitted PCZTs; this corpus is only 1,236–10,037 bytes, below the 65,536-byte
admission ceiling, and uses absent anchors/OCKs.

## Ownership and failure paths

For `outputs-8`, retained run occupancy after begin/approve is 32,053 bytes;
signing peaks at 78,045 bytes and leaves 31,797; serialization peaks at 52,757
and leaves 27,221. Full teardown returns to zero. The raw input and returned
Review stay alive through signing. Serialization consumes the PCZT, so its frees
are measured in that phase rather than attributed to the later teardown.

Source-visible copies include the parsed PCZT and Verifier clone, retained and
returned Review vectors, and effect extraction during validation and signing.
Whole-phase counters identify their combined cost; they do not assign every
allocation to an individual source expression. Inline values, native stack frames
and crypto/C temporaries are not counted.

All 90 complete teardowns and maximum-input cancellation/replacement checks
returned to their original baseline. Oversized (65,537-byte) and encoded
nine-action inputs returned the expected admission errors with no alloc, realloc
or dealloc calls. Null-reallocation ownership is unit-tested through the exact
accounting path; this does not test OS exhaustion or an embedded allocator's OOM
handling. Session/signing entropy interruptions remain covered by the accepted
core conformance suite, outside this measurement.

## Device implications

[Safe 7's source map](SAFE7_INTEGRATION.md) identifies 800 KiB shared application
RAM, a 32 KiB native stack and two 8,704-byte THP buffers. The observed peak alone
cannot establish fit: host pointer/layout differences, allocator overhead and
fragmentation, native stack, firmware statics, GC/UI/transport and concurrent
objects still need evidence from a linked integration. Even this small corpus has
individual inputs larger than one THP buffer, confirming the need for bounded
application-level chunking.

Counters exclude direct C allocations, malloc size-class overhead, transient
internal realloc overlap and stack/static storage. Instrumentation and scheduling
affect timing; no MCU latency or watchdog deadline is inferred. A concrete target
build, allocator contract, emulator runtime occupancy and target stack analysis
remain required before trusted UI and transport integration can be accepted.

## Provenance

The coordinated run is
`work/runs/20260908T080145Z-resources-71a70bee/report.json`.
Its full command records, source/lock hashes, resolved features and generated files
remain ignored. Upstream librustzcash stayed clean at
`5e770a91ad0d11938dbc713e7889e4aa8009266c` throughout.

Fixture construction uses fixed builder seeds, but upstream IoFinalizer supplies
OsRng when signing dummy spends. Regeneration can change those signature bytes and
file hashes while preserving layout and effects. Each run records exact original
and signed hashes; every timed signature result is byte-identical to that run's
independently verified representative.

- `report.json` SHA-256: `6c9468ba46cb2181f1969e372333c06d4931c812c16fc028bfff59f7935670ae`.
- `measurements.json` SHA-256: `7e27855c3363478067041ecd2baa4fd3422c3a136eb881fadd5e44623bf3b22d`.
- `fixtures/manifest.json` SHA-256: `c70a27a4c30f3d1a39ad7eb8559cd2e7d3f76b6f43eb9cfbc4aee6de29be4137`.
- `14.log` SHA-256: `dc573d3e8a7abf755a3fb5fd3ef81bfdeddbddda3675262df868aeeea67e1492`.
- `15.log` SHA-256: `fb8ac38a184aed17871d73599f4895fbb01edbcfafca6d9773f6d731db1a2ffe`.
- `resource-fixtures` release binary SHA-256: `111506554978e22291e75ab41fa7a4e6e41227eb8ec7db7ab716734006097823`.
- `resource-probe` release binary SHA-256: `bef891a10217cd2fa64373abfe6d74669d63c9e9b6422ca0384e1ab9e8e45e41`.

The initial coordinated run (`20260908T073249Z-resources-41cd841d`) also passed and is
retained. Its facts and lifecycle continuity were independently cross-checked;
the final runner now enforces those checks and rejects inconsistent evidence.
