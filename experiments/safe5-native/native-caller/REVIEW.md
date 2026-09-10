# Native caller review record

10 September 2026 UTC. This proposal is **not adopted**. All review statements
below concern synthetic source or artifact evidence, not device acceptance.

An independent integration/clarity reviewer checked the additive feature, derived
C capability, frozen substitution and stock lazy dispatcher. Two required fixes
are present in the compiled source: importing the capability explicitly in
`trezor.utils`, and replacing the missing-task assertion with `ProcessError` so
the guard survives optimization. The stock loader's module basename matches the
handler function; no boot import or extra dispatch wrapper is needed.

The native compile guard and baseline feature block remain byte-identical. The
C bridge implementation is unchanged apart from its opening comment. An inherited
upymod Cargo comment still mentions T3W1 even though the actual guard requires
T3T1; this optional wording correction is deferred to avoid changing the frozen
candidate after compilation. The current-task check does not independently prove
workflow registry membership. Actual scheduler/context ownership remains a
runtime acceptance requirement.

The local artifact review verifies compiled bytecode and protobuf bytes inside
allocated ELF sections, their module/descriptor registration, selected C macros,
source identities and preservation of the retained image. It does not turn the
stubbed caller tests into native execution evidence. The separate portable test
export preserves test semantics and accepts one explicit firmware root. A second
independent reviewer verified its ASTs, raw log hashes and 10/216 count record.
No blocker was found. An inherited runner limitation remains: a 60-second timeout
preserves raw logs but raises before writing run.json. The retained successful
run has its complete record; future failure evidence must retain this distinction.

Fable transmission was rejected **before process creation** by automatic approval
review. Its stated reason was that standing general authorization does not clearly
approve the newly assembled source payload and destination. The exact 62,058-byte
packet is frozen at SHA-256
`3f6c04236ba1ea381369dc19c3f4376db1eb01ed2d7b366824e58d344dc02762`.
It targets the existing Claude Code/Fable account with a $15 reported-usage
allowance. Nothing was transmitted; no model result, model identity or usage is
available. An exact-packet approval request is pending.

This is a distinct native caller/test review. The prior response-capacity and
signed-response-test packets remain unchanged and separately blocked. No response
allocation proposal or production interface can be accepted through this review.
The budget retains all three pending $15 allowances. No invoice was observed.

`RESULTS.json` and `SOURCE_MANIFEST.json` bind the source, compilation, tests and
artifact review. Raw logs and local reviewer records remain preserved. Fable
adversarial review, actual native lifecycle/resource tests and clean-checkout
reproduction remain open before adoption.
