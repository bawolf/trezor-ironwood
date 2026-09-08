# Synthetic resource fixtures

Standalone host test tool for `docs/SAFE7_INTEGRATION.md`. It imports
`crates/approval/tests/common/mod.rs` directly: no copied builders or cryptography.
A module-local `dead_code` allowance covers unrelated conformance helpers in that
import; it applies only inside this fixture tool, never to core sources.

## File protocol

`generate <directory>` requires an empty directory and writes `manifest.json` plus
exactly 15 synthetic originals: `outputs-1.pczt` through `outputs-8.pczt`
from `build_actions(n)`, and `inputs-2.pczt` through `inputs-8.pczt` from
`build_inputs(&[100_000; 8][..n])`. Existing files are not overwritten. A failed
run may leave a partial corpus; use a fresh empty directory to retry.

Both sides use the public test account `SpendingKey::from_bytes([0; 32])`, reference
height 10,000,000 and fee cap 100,000. Fixed fixture RNGs come from the imported
helpers. Upstream `IoFinalizer::finalize_io` uses `OsRng` for dummy-spend
signatures, so regenerating the output series can change signature bytes and
file hashes while preserving layout and effects. The manifest binds the exact
corpus used in each run. No production data or hardware is involved.

The measurement binary writes each signed PCZT under the **same basename** in a
separate signed directory. It should serialize the core's returned `Signed.pczt`
without editing metadata. No signed manifest is needed. Run `verify` only after
all 15 signed files are available. The signed directory must contain exactly those
15 regular files: missing/extra entries, symlinks and subdirectories are rejected.
Keep measurement logs outside the signed directory.

The manifest has `height`, `fee_cap`, and an ordered `fixtures` array. Each entry
contains `name`, lowercase `sha256`, `byte_length`, `action_count`,
`real_input_count`, `required_signature_count`, `existing_signature_count`,
`positive_output_count`, `padding_input_count`, `padding_output_count`,
`anchor_present`, per-action `ock_present`, and lowercase `shielded_sighash`.
Counts come from parsed PCZT fields. Positive values distinguish real spends and
outputs from zero-value padding. Originals contain dummy signatures only;
`required_signature_count` counts the unsigned positive inputs the harness signs.
Generation checks the observed layout against each series' intended dimensions.

`verify <original-directory> <signed-directory>` rechecks every original against
its manifest and the fixed core policy, then permits only new real-spend
signatures. It checks their action/pool tags with the standard upstream `Signer`,
requires the original effect digest, and compares all logical PCZT fields.
The full upstream `Verifier` checks cross-address restrictions, commitments,
nullifiers, ownership, randomized keys and **all** signatures, including dummies.
This oracle is outside measurement. It is not a proof/consensus verifier or a
production signing interface. The manifest is local provenance, not an
independently authenticated corpus; preserve its hash with measurement evidence.

## Commands from repository root

Use the existing pinned dependency cache; the committed standalone lock is checked
against upstream versions and checksums. Builder/signer features are confined to
this workspace. Never add this package to the measured binary's dependencies.

```sh
export CARGO_HOME="$PWD/work/cargo-home"
export CARGO_TARGET_DIR="$PWD/work/resource-fixtures-target"
export CARGO_BUILD_JOBS=4
cargo run --release --offline --locked --manifest-path experiments/resource-fixtures/Cargo.toml -- generate work/resource-fixtures
cargo run --release --offline --locked --manifest-path experiments/resource-fixtures/Cargo.toml -- verify work/resource-fixtures work/resource-signed
python3 scripts/check_approval_dependencies.py experiments/resource-fixtures/Cargo.lock
cargo test --release --offline --locked --manifest-path experiments/resource-fixtures/Cargo.toml -- --test-threads=1
cargo fmt --manifest-path experiments/resource-fixtures/Cargo.toml -- --check
cargo clippy --offline --locked --manifest-path experiments/resource-fixtures/Cargo.toml --all-targets -- -D warnings
```

`work/` is already ignored. The measurement harness must be a different standalone
workspace with the approval core's default features disabled. Separate Cargo
invocations prevent this tool's builder/oracle features from unifying into it.
Run `python3 scripts/resource_check.py` for coordinated measurement, independent
verification and evidence capture. See [resource results](../../docs/RESOURCE_RESULTS.md).

The three tests exercise the whole directory protocol with all 15 signed controls,
unsigned/partial/corrupt replies followed by a restored valid control, metadata
preservation, and dummy-signature verification even when the same dummy corruption
is present in both original and signed files. They also reject missing, extra and
malformed reply files. Release mode avoids the slow debug crypto path.
