# Safe 7 executor check: standalone compiler experiment

This small candidate checks real CPU mode and one-time Core lifetime binding for the pinned T3W1 configuration. It is a fail-stop integration check, not a security boundary against same-Core code, kernel/IRQ corruption or DMA. No firmware or hardware execution is provided here.

The configuration must have only kernel and Core task slots: external app loading is absent from BOTH matching kernel and application; MicroPython native threads and scheduler are disabled. Same-task callbacks require a closed native call graph; existing Rust reentry and ownership checks remain necessary. Product key/entropy integration must revisit this contract.

Two entry functions check IPSR and CONTROL before accessing ownership state. Two private helpers retain stack protection around real atomic state access. Only the new register-only entry functions omit compiler-inserted canaries; existing protections and limits are unchanged. There is no reset, alternate executor backend or syscall.

## Reproduce the object

Use ARM GNU Toolchain 13.3.Rel1, and Trezor firmware revision `7105338e3c2c1e681940e17780609881ce53126b` with its pinned `vendor/cmsis_5` and `vendor/micropython` submodules. Run from this repository root after preparing that source at `upstream/trezor-firmware`. No generated firmware headers, Cargo cache, review account or local experiment donor is required for this standalone object.

```sh
mkdir -p work/target-executor
arm-none-eabi-gcc -std=gnu11 -Os -fomit-frame-pointer -fno-common \
  -fdata-sections -ffunction-sections -fshort-enums -fstack-protector-all \
  -mthumb -mcpu=cortex-m33 -mfloat-abi=hard -mfpu=fpv5-sp-d16 \
  -Wall -Wextra -Werror -DIRONWOOD_TARGET_NATIVE_COMPILE_ONLY=1 \
  -DTREZOR_MODEL_T3W1 -DSTM32U5G9xx -DUSE_SECMON_LAYOUT=1 \
  -I upstream/trezor-firmware/vendor/cmsis_5/CMSIS/Core/Include \
  -I upstream/trezor-firmware/vendor/micropython \
  -I upstream/trezor-firmware/core/embed/projects/firmware \
  -c experiments/target-executor/executor.c -o work/target-executor/executor.o
arm-none-eabi-objdump -dr work/target-executor/executor.o
```

The parent ran this compiler recipe using the same pinned source in an isolated location. Instructions and relocations match the object compiled with the retained full upymod flags. Seven negative preprocessing cases rejected app loading, production, kernel, secure, emulator, missing opt-in and missing stack-protector-all. This does not test runtime CPU modes or prove the full firmware configuration.

Expected object: mode branches precede state access; wrong bind traps, wrong query returns false. Valid branches alone reach protected helpers with LDREX/STLEX and acquire LDA; no libatomic helper. Bound state is four bytes in BSS. Recheck these properties after the actual firmware link, together with all global allocator callers and failure paths.

See [native integration evidence](../../docs/TARGET_NATIVE_INTEGRATION.md) and [review disposition](../../docs/reviews/TARGET_NATIVE_INTEGRATION.md). The complete native firmware overlay and build inputs remain an explicitly incomplete local experiment; this standalone source does not make the entire demonstration reproducible.

This experiment is GPL-3.0-or-later; see COPYING. Imported firmware and CMSIS/MicroPython sources retain their own licenses.
