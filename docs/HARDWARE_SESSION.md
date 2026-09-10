# First hardware session: Trezor Safe 5

The available device is an unopened **Trezor Safe 5 — Black Graphite (T3T1)**, dedicated to testing. No device setup is needed until the model-specific preparation is ready. Its hardware revision and bootloader state will be checked when connected.

You will be needed for setup and a compact set of physical approval checks. I will handle the computer, test inputs, logs and signature verification. Current unattended tests run on the host and emulator. A Safe 5 debug route could later automate repeated hardware checks, but that route is not ready; physical approval tests still require you.

## Preparation before your appointment

- Safe 5 baseline and synthetic native links are complete, including a 48 KiB stack and split-GC layout. Finish native ABI, full stack and peak object-lifetime validation; static capacity is not runtime fit. See [the measured image](SAFE5_NATIVE.md).
- Adapt and rehearse the trusted review on Safe 5's Delizia touchscreen and its older wire protocol. Preserve all receiver, value, fee, network and pool information; Safe 7's page count and THP session behavior do not establish Safe 5 behavior.
- Freeze the reviewed image and its fingerprint, source/dependency identities, synthetic inputs and expected results. Prepare bounded host commands, independent signature verification, and a Safe 5 installation/firmware-restoration card. Verify its bootloader gestures and test deadlines during preparation. The existing emulator launcher is not a hardware test runner.
- Resolve the applicable failure cases before booking the session, including reliable cleanup and response handling. Record any remaining limitation rather than treating a test-harness success as firmware acceptance.

**Current readiness:** there is no reviewed, deployable Safe 5 Ironwood image. The host's missing native USB dependency has been installed and checked without enumerating or opening a device; the retained client, fixture and oracle are from the existing emulator work. Safe 5 connection, execution and physical consent remain untested. When connected, start with device identification; installation and unlocking require the separate decision below.

## The attended block

| Step | Your part | My part |
| --- | --- | --- |
| Identify and set up | Connect by USB, enter bootloader if needed, read and confirm the agreed installation screens. | Verify the exact model, selected image and fingerprint; run the prepared commands and capture results. |
| Check rejection | Read the expected transaction fields, try a short press/release, then cancel. | Check that no signed result appears and cancellation leaves the device responsive. |
| Check fresh approval | Start a fresh review, check every required field, and deliberately complete the final hold. | Upload the synthetic transaction, accept only a complete response, and independently verify its signatures and approved effects. |
| Check the connection | Disconnect and reconnect once while idle in the rehearsed case. | Check cleanup, fresh communication and the expected device state; preserve any failure without automatically re-signing. This does not test power loss or firmware restoration. |

I will give one action at a time with the expected screen and outcome. An unexpected display, timeout or crash ends that case; you will not need to sit through debugging. Host analysis and reporting can continue after you leave. We will estimate the appointment length after the Safe 5 rehearsal rather than promising an unmeasured duration.

## Dedicated-device decision

Installing our unofficial firmware may require unlocking the bootloader, which also erases device storage. Trezor states that unlocking Safe devices permanently makes the factory attestation key inaccessible; installing official firmware later does not restore that authenticity check. This needs an explicit decision once the exact image and procedure are ready. The unopened test unit does not need a personal wallet or recovery seed for this synthetic work. [Trezor's unlocking guide](https://trezor.io/learn/security-privacy/how-trezor-keeps-you-safe/unlocking-the-bootloader-on-trezor-safe-devices)

Automated DebugLink interaction is useful for test coverage and supported memory queries. It does not demonstrate that a person saw and approved the physical screen. We will retain those as separate results. [Trezor's device-testing documentation](https://docs.trezor.io/trezor-firmware/tests/device-tests.html)
