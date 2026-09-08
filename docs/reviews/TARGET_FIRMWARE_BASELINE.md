# Target firmware baseline review

Reviewed 2026-09-08. Claude Code with Fable received the authored baseline report
and a fixed packet of nonsecret build evidence, with all tools disabled. Independent
Codex reviewer James compared the document against the saved local records.
The coordinator separately rehashed 94 artifacts/logs and parsed the linked ELF.

Fable found no numeric or image-accounting errors. Its actionable wording findings
and James's clarity finding were resolved as follows:

- State that host data does not establish runtime fit; distinguish emulator GC tests
  from target whole-stack analysis and unmeasured MCU stack high-water.
- Explain the image's header and data-load bytes, and the secmon nested in its kernel.
  Call that secmon source-pinned; byte identity alone does not establish a release.
- Check the test preset and feature filter directly. They disable the OPTIGA/Tropic
  board features while the separate optiga_testing feature remains enabled.
- Describe the official archive check precisely as SHA-256 comparison; no PGP
  signature verification was performed. Remove unnecessary alignment wording.

The coordinator confirmed the source count, Python version, two-job environment
and build-log hash that were outside Fable's initial packet. The different built
and embedded secmon hashes are documented; no unsupported explanation of their
size difference was inferred. All baseline source/locks remained unchanged.

Frozen review: `work/reviews/target-firmware-baseline-fable/`; result SHA-256
`55151b1dda58316c1e06e32744a7ec4af7df2fd8934012f1606c7e9e5eb268cc`. Reported model usage was USD 0.758001 through the existing Max
subscription, not an observed charge. Usage is recorded in the project ledger.

Accepted scope: an unchanged T3W1 hardware-test-preset link and its memory baseline.
This review establishes no execution, shielded integration, runtime fit, hardware
validation or production approval.
