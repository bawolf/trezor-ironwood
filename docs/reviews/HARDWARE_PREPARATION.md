# Hardware preparation review — 2026-09-09

Scope: the Safe 5 attended-session plan, offline host-input check, and the command-only Safe 7 link correction. No hardware operation or production signing implementation was reviewed or executed.

Fable through the existing Claude Code account completed in 80.76 seconds, requested `fable[1m]`, actual `claude-fable-5-1`. Reported list-price usage was $0.705595 against a $15 allowance; this is not an observed invoice. The frozen 42,431-byte packet and result remain under the coordinating workspace's `work/hardware-session-review/`.

The independent clarity review condensed the separate worker's source-backed plan into the small [attended-session guide](../HARDWARE_SESSION.md): named actions, exact model, current prerequisites, and no unmeasured time promise. This was a parent review of the worker's plan, not a second Fable pass.

## Findings and decisions

1. **Unattended hardware work:** narrowed the guide to existing host/emulator automation. A future Safe 5 debug route is explicitly conditional and unimplemented. Human approval remains a separate physical test.
2. **Recovery ambiguity:** renamed the attended step to connection checking and limited it to idle disconnect/reconnect. Firmware restoration has a separate preparation card; no power-loss or firmware-restoration result is promised.
3. **Unlock consequences:** added storage erasure to the permanent attestation loss already stated. The pinned `wf_unlock_bootloader.c:35–53` confirms physical confirmation, storage erase and unlock. Official firmware does not restore the attestation key.
4. **Proposed extra permission for connection:** not adopted. The user has requested using this machine and the dedicated device when connected; routine identification does not require an invented second authorization. No device has been accessed. Unlocking/installing the exact prepared firmware still needs the explicit decision required by the project instructions.
5. **Model details:** the preparation card must verify Safe 5 bootloader gestures and deadlines. The guide gives no Safe 7 gesture, page-count or timing recipe as a Safe 5 instruction.
6. **Offline host check:** renamed the result to `message_registration_calls_completed: 2`, describing exactly what ran. The review's assertion that uncaught registration exceptions were not checked was incorrect: an exception terminates the script before it writes a report. This check does not claim full mapping equivalence or a functioning Safe 5 client. Imports, native libusb loading, CLI help and retained input hashes pass without creating a USB context; it neither enumerates devices nor verifies new signatures.
7. **Build correction:** Fable agrees `-Zbuild-std=core,alloc` resolves the observed duplicate core identities and matches the earlier successful allocator build. The retry changes no firmware source, profile, feature list, lock or kernel. Link success and unchanged-source checks are recorded separately from image inspection and runtime acceptance. The unstripped ELF file length is not flash occupancy; the ELF load regions/map provide that measurement.

No additional functions, flags, security exceptions or cryptographic changes were introduced. The guide and host result-label corrections above are the post-review deltas. The retained initial host failure records the missing native libusb; installing free Homebrew libusb 1.0.30 resolved it. The corrected check passes. Full Safe 5 integration and hardware execution remain pending.

- Packet SHA-256: `b60f3e2da4e8a43c928345377d19cbf00ca892f8c6e734c3493a2965052917b7`.
- Result SHA-256: `92983d639e5a18b501dda37f9d2fbee5deae249364680718114de40341323f3a`.
- Final guide SHA-256: `695fcb0ce4bb82b7d1b9e8cedbfa8bca4cd14901e47d8445e526bee724201fe1`.
