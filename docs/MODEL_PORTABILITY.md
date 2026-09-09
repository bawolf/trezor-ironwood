# Portability to other Trezor models

Initial feasibility can be assessed with a source comparison and a few targeted
builds, before undertaking a complete port. The source comparison is complete;
the [unchanged Safe 5 baseline](SAFE5_BASELINE.md) now also compiles and links.
No additional model has run, and no Safe 5 native signing port is accepted.
**Safe 5 is the closest follow-on; newer Safe 3 is the next distinct UI case.**
The available first physical test device is an unopened Safe 5. Finish inspecting
the Safe 7 native link and resolve Safe 5 resource placement and flash cost.
The Safe 5 baseline has only 43,668 bytes of AUX1 tail and 115,200 bytes of flash
tail; the existing arena cannot transfer to AUX1 unchanged.
No Safe 7 firmware image is suitable for installation on this unit.

This assessment uses firmware revision
`7105338e3c2c1e681940e17780609881ce53126b`. Model names/revisions also match the
published [model identifier list](https://docs.trezor.io/trezor-firmware/common/reproducible-build.html).
The findings describe those exact configurations, not all future firmware.

| Device | Additional porting effort: current estimate | Main differences | First feasibility gate |
| --- | --- | --- | --- |
| Safe 5, T3T1 | Moderate; best first candidate | Same Rust target as Safe 7 and a touch UI; different RAM placement, smaller flash slot and older wire transport | One isolated link retaining the real core and intended allocator; inspect both RAM regions and complete flash occupancy |
| Safe 3 rev.B, T3B1 | Moderate to high | Same Rust target; more application RAM than Safe 5, but monochrome/button review and older wire transport | A UI-only test of the longest existing review projection using Caesar layouts; preserve every receiver byte/context and physical confirmation |
| Model T, T2T1 | High and uncertain | Different Rust target, 16 KiB stack, tight primary RAM and split flash | One concrete Cortex-M4 core compilation plus a credible revised memory plan before firmware integration |
| Safe 3 rev.A, T2B1 | High and uncertain | Shares the Model T resource obstacle, with less separate CCM RAM and button UI | Reuse the Model T target evidence; establish a phase-by-phase memory layout that actually fits |
| Model One, T1B1 | Very high; architectural work | Legacy C firmware and much less RAM; current 128 KiB arena alone equals its entire RAM region | Require a viable alternative memory/lifetime design before spending on a port |

These are engineering estimates from source, not delivery dates or support claims.
The cheap gates assess specific feasibility questions; none substitutes for full
consent, recovery, security and hardware validation.

## What transfers

The `no_std` approval core, transaction validation/accounting, immutable reviewed
effects, consent state machine, signature rules and adversarial fixtures can stay
shared. `no_std` does not mean allocation-free. Existing allocator, RNG and review
boundaries provide a starting point, while actual device bindings still need work.

Per-model work concerns memory placement, task/fault behavior, trusted entropy and
key lifecycle, transport and physical review. The production key-handle integration
is not implemented even on Safe 7; another model does not inherit it as finished
work. Secure-element presence does not imply support for native Ironwood signing.

At this pin only Safe 7 selects THP among the assessed models. Reuse application
chunking and correlation rules through a reviewed older-wire path; simply removing
the prototype's emulator/THP guards would not provide equivalent behavior. Its
experimental message IDs are not upstream reservations.

The existing review calls mostly fit Safe 5's Delizia and Model T's Bolt APIs.
There is a concrete Caesar incompatibility: its `confirm_value` does not accept
the `subtitle` argument used by the prototype. Resolve that through a small layout
adaptation that preserves context, rather than dropping information or adding a
generic device framework.

## Memory facts behind the estimate

- Safe 5 and newer Safe 3 select STM32U585 and `thumbv8m.main-none-eabihf`, the
  same Rust target already used by our Safe 7 core probe. Their application RAM
  is split: ordinary statics live in AUX1, while stack and GC live in AUX2.
  Safe 5 has 514.5 KiB across those assigned regions; newer Safe 3 has 727.5 KiB.
  These sums are not single contiguous heaps or free-memory measurements.
- Model T and earlier Safe 3 select STM32F427 and
  `thumbv7em-none-eabihf`. A 128 KiB arena plus their 16 KiB stack leaves only
  48,128 primary-region bytes before existing statics. The current 65,536-byte
  GC response cannot fit into that remainder. Moving or shrinking allocations
  requires a new measured design that preserves validation.
- Model One assigns 128 KiB total RAM to firmware statics/buffers and stack.
  The current arena therefore cannot transfer unchanged. Its legacy build does
  not select a Rust target; one would be a new integration decision.
- Safe 5, both Safe 3 variants and Model T have 1,664 KiB assigned to firmware,
  versus Safe 7's 3,336 KiB. These are complete slots, not available additions;
  Model T/earlier Safe 3 also split code and data placement across flash regions.

The full source references, exact region boundaries, placement rules and evidence
limits are preserved in `work/model-portability/REPORT.md`. Key source entry points
are [model definitions](https://github.com/trezor/trezor-firmware/tree/7105338e3c2c1e681940e17780609881ce53126b/core/embed/models),
[linker scripts](https://github.com/trezor/trezor-firmware/tree/7105338e3c2c1e681940e17780609881ce53126b/core/embed/sys/linker),
[layout implementations](https://github.com/trezor/trezor-firmware/tree/7105338e3c2c1e681940e17780609881ce53126b/core/src/trezor/ui/layouts)
and [wire selection](https://github.com/trezor/trezor-firmware/blob/7105338e3c2c1e681940e17780609881ce53126b/core/src/trezor/wire/__init__.py).

Proceed with Safe 5 as the first hardware target, using its own baseline and
integration evidence; the Safe 7 map now gives a measured comparison. Declare support by exact model/revision and ship the evidence through
the [Trezor handoff package](TREZOR_HANDOFF.md). Keep unsupported models explicitly
unsupported; portability must not weaken the approval contract.
